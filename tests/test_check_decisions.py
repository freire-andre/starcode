import re
import unittest

from helpers import TempRepoCase, run_git

import check_decisions as cd


class CheckDecisionsTests(TempRepoCase):
    def commit(self, path, text, msg):
        f = self.repo / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
        run_git(self.repo, "add", path)
        run_git(self.repo, "commit", "-q", "-m", msg)

    def test_flow(self):
        self.commit("DECISIONS.md", "# d\n", "decisions")
        self.assertEqual(cd.check(self.repo)[0], 0)
        self.commit("skills/x/SKILL.md", "x\n", "skill")
        code, msg = cd.check(self.repo)
        self.assertEqual(code, 1)
        self.assertIn("FALHOU", msg)
        self.commit("DECISIONS.md", "# d\n- F1\n", "decision for skill")
        self.assertEqual(cd.check(self.repo)[0], 0)

    def test_same_commit_ok(self):
        (self.repo / "DECISIONS.md").write_text("# d\n", encoding="utf-8")
        (self.repo / "hooks").mkdir()
        (self.repo / "hooks" / "h.py").write_text("x\n", encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "both")
        self.assertEqual(cd.check(self.repo)[0], 0)

    def test_dirty_watched_without_decisions_fails(self):
        self.commit("DECISIONS.md", "# d\n", "decisions")
        (self.repo / "scripts").mkdir()
        (self.repo / "scripts" / "a.py").write_text("x\n", encoding="utf-8")
        self.assertEqual(cd.check(self.repo)[0], 1)
        (self.repo / "DECISIONS.md").write_text("# d\n- new\n", encoding="utf-8")
        self.assertEqual(cd.check(self.repo)[0], 0)

    def test_missing_file(self):
        self.assertEqual(cd.check(self.repo)[0], 2)


    def test_decisions_f6_1_sandbox_mission_day(self):
        from helpers import ROOT
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        m = re.search(r"^### F6-1: .*\n(.*?)(?=^### |\Z)", text, re.M | re.S)
        self.assertIsNotNone(m, "DECISIONS.md sem F6-1")
        for needle in ("starcode-sandbox", "projeto real", "2026-11-06", "Por que não é bug"):
            self.assertIn(needle, m.group(0))

    def test_clone_raso_sai_2(self):
        import subprocess
        (self.repo / "DECISIONS.md").write_text("# d\n", encoding="utf-8")
        (self.repo / "skills").mkdir()
        (self.repo / "skills" / "x.md").write_text("x\n", encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "both")
        clone = self.tmp / "raso"
        subprocess.run(["git", "clone", "-q", "--depth", "1", self.repo.as_uri(), str(clone)], check=True,
                       stdin=subprocess.DEVNULL, capture_output=True)
        code, msg = cd.check(clone)
        self.assertEqual(code, 2)
        self.assertEqual(msg, "check_decisions: repositório raso; o gate D30 precisa do histórico completo "
                              "(use fetch-depth: 0 no actions/checkout ou rode git fetch --unshallow)")

    def test_raso_indeterminado_sai_2(self):
        from unittest import mock
        (self.repo / "DECISIONS.md").write_text("# d\n", encoding="utf-8")
        real = cd.git
        esperado = ("check_decisions: não foi possível confirmar que o clone é completo "
                    "(git rev-parse --is-shallow-repository)")
        for fake in ((0, "--is-shallow-repository"), (128, "")):
            def fake_git(repo, *args, _fake=fake):
                if args[:2] == ("rev-parse", "--is-shallow-repository"):
                    return _fake
                return real(repo, *args)
            with mock.patch.object(cd, "git", fake_git):
                self.assertEqual(cd.check(self.repo), (2, esperado))

    def _decisions_entry(self, entry_id):
        from helpers import ROOT
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        m = re.search(r"^### " + re.escape(entry_id) + r": .*\n(.*?)(?=^### |\Z)", text, re.M | re.S)
        self.assertIsNotNone(m, f"DECISIONS.md sem {entry_id}")
        for field in ("**Problema:**", "**Decisão:**", "**Motivo:**", "**Por que não é bug:**"):
            self.assertIn(field, m.group(0))
        return m.group(0)

    def test_decisions_v18_1_piloto(self):
        body = self._decisions_entry("V18-1")
        for needle in ("D29", "aprova as tasks", "spec continua com o usuário", "Por que não é bug"):
            self.assertIn(needle, body)

    def test_decisions_v18_2_aprovacao_piloto(self):
        body = self._decisions_entry("V18-2")
        for needle in ("tasks.md", "Mandato confirmado", "spec.md", "piloto:"):
            self.assertIn(needle, body)

    def test_decisions_v18_3_config_model_info(self):
        body = self._decisions_entry("V18-3")
        for needle in ("models.dev", "7 dias", "$$$", "$$", "`$`"):
            self.assertIn(needle, body)

    def test_decisions_v18_4_config_local(self):
        body = self._decisions_entry("V18-4")
        self.assertIn("config.local.json", body)
        self.assertIn("sessão > config local do repositório > config do usuário > padrão do `crew.yaml`", body)

    def test_decisions_v18_5_menu(self):
        body = self._decisions_entry("V18-5")
        for needle in ("menu", "só lê", "skills/"):
            self.assertIn(needle, body)

    def test_decisions_gate_raso(self):
        body = self._decisions_entry("SC-168")
        for needle in ("fetch-depth", "is-shallow-repository", "test_clone_raso_sai_2", "Por que não é bug"):
            self.assertIn(needle, body)


if __name__ == "__main__":
    unittest.main()
