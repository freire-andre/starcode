"""Tests for scripts/review/post_review.py (R14-R16). Uses a fake `gh`, never the real one."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import FIXTURES, ROOT

SCRIPT = ROOT / "scripts" / "review" / "post_review.py"
REVIEW = FIXTURES / "review"

FAKE_GH = r"""
import json, os, sys
d = os.environ["FAKE_GH_DIR"]
args = sys.argv[1:]
inp = None
if "--input" in args:
    inp = open(args[args.index("--input") + 1], encoding="utf-8").read()
with open(os.path.join(d, "calls.jsonl"), "a", encoding="utf-8") as fh:
    fh.write(json.dumps({"args": args, "input": inp}) + "\n")
if os.environ.get("FAKE_GH_FAIL"):
    sys.stderr.write("HTTP 401: sem login\n")
    sys.exit(1)
if args[:2] == ["pr", "view"]:
    print(json.dumps({"author": {"login": os.environ.get("FAKE_GH_AUTHOR", "outro")}}))
elif args[:2] == ["api", "user"]:
    print(os.environ.get("FAKE_GH_ME", "eu"))
else:
    print(json.dumps({"html_url": "https://github.com/o/r/pull/7#pullrequestreview-1"}))
"""


class PostReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="starcode-post-test-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        self.state = self.tmp / "state"
        self.state.mkdir()
        (self.bin / "gh_fake.py").write_text(FAKE_GH, encoding="utf-8")
        if os.name == "nt":
            (self.bin / "gh.cmd").write_text(
                f'@echo off\r\n"{sys.executable}" "{self.bin / "gh_fake.py"}" %*\r\n', encoding="utf-8")
        else:
            sh = self.bin / "gh"
            sh.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{self.bin / "gh_fake.py"}" "$@"\n',
                          encoding="utf-8")
            sh.chmod(0o755)
        self.json = self.tmp / "review.json"
        self.json.write_text((REVIEW / "review_ok.json").read_text(encoding="utf-8"), encoding="utf-8")
        self.md = self.tmp / "review.md"
        self.md.write_text("# Review\n\n**Round**: 1\n**Verdict**: REQUEST_CHANGES\n", encoding="utf-8")

    def post(self, path_env: str | None = None, **extra: str) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env["PATH"] = path_env if path_env is not None else str(self.bin) + os.pathsep + env.get("PATH", "")
        env["FAKE_GH_DIR"] = str(self.state)
        env["PYTHONIOENCODING"] = "utf-8"
        env.update(extra)
        return subprocess.run([sys.executable, str(SCRIPT), str(self.json), "--pr", "7",
                               "--review-md", str(self.md)], env=env, capture_output=True, text=True,
                              encoding="utf-8", timeout=60, stdin=subprocess.DEVNULL)

    def calls(self) -> list[dict]:
        p = self.state / "calls.jsonl"
        return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []

    def test_post_refuses_without_gate_or_when_already_posted(self) -> None:
        data = json.loads(self.json.read_text(encoding="utf-8"))
        data["verdict"] = "APPROVE"
        self.json.write_text(json.dumps(data), encoding="utf-8")
        r = self.post()
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("recusado: review_gate falhou", r.stdout)
        self.assertEqual(self.calls(), [])
        self.json.write_text((REVIEW / "review_ok.json").read_text(encoding="utf-8"), encoding="utf-8")
        self.md.write_text("**Round**: 1\n**Posted**: 2026-11-09 - https://x\n", encoding="utf-8")
        r = self.post()
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("recusado: rodada 1 já publicada", r.stdout)
        self.assertEqual(self.calls(), [])

    def test_post_own_pr_falls_back_to_comment(self) -> None:
        r = self.post(FAKE_GH_AUTHOR="eu", FAKE_GH_ME="eu")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        post = [c for c in self.calls() if c["input"]][0]
        self.assertIn("repos/{owner}/{repo}/pulls/7/reviews", post["args"])
        payload = json.loads(post["input"])
        self.assertEqual(payload["event"], "COMMENT")
        self.assertIn("Veredito pretendido: REQUEST_CHANGES (o GitHub não aceita REQUEST_CHANGES no próprio PR)",
                      payload["body"].splitlines())
        self.assertEqual(payload["comments"][0]["path"], "src/x.py")
        # PR de outra pessoa: usa o veredito como evento
        self.md.write_text("**Round**: 1\n", encoding="utf-8")
        self.assertEqual(self.post(FAKE_GH_AUTHOR="outro", FAKE_GH_ME="eu").returncode, 0)
        payload = json.loads([c for c in self.calls() if c["input"]][-1]["input"])
        self.assertEqual(payload["event"], "REQUEST_CHANGES")
        self.assertNotIn("Veredito pretendido", payload["body"])

    def test_post_gh_failure_and_success_marks_posted(self) -> None:
        before = self.md.read_text(encoding="utf-8")
        r = self.post(FAKE_GH_FAIL="1")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("gh falhou:", r.stdout)
        self.assertEqual(self.md.read_text(encoding="utf-8"), before)
        r = self.post(path_env=str(self.tmp / "vazio"))
        self.assertEqual(r.returncode, 2)
        self.assertIn("gh falhou:", r.stdout)
        self.assertEqual(self.md.read_text(encoding="utf-8"), before)
        r = self.post()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertRegex(self.md.read_text(encoding="utf-8"),
                         r"\*\*Posted\*\*: \d{4}-\d{2}-\d{2} - https://github.com/o/r/pull/7#pullrequestreview-1")

    def test_inline_comment_does_not_repeat_severity_emoji(self) -> None:
        data = json.loads(self.json.read_text(encoding="utf-8"))
        first = data["findings"][0]
        first["body"] = "🔴 TLS desligado na chamada externa."
        second = dict(first, id="W2", line=13, body="Sem emoji no começo do texto.")
        data["findings"].append(second)
        self.json.write_text(json.dumps(data), encoding="utf-8")
        r = self.post()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        payload = json.loads([c for c in self.calls() if c["input"]][0]["input"])
        by_line = {c["line"]: c["body"] for c in payload["comments"]}
        self.assertEqual(by_line[12], "**blocker** (W1): 🔴 TLS desligado na chamada externa.")
        self.assertEqual(by_line[13], "🔴 **blocker** (W1): Sem emoji no começo do texto.".replace("W1", "W2"))
        self.assertEqual(by_line[12].count("🔴"), 1)


if __name__ == "__main__":
    unittest.main()
