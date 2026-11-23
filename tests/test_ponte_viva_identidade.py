"""Tests de SC-222 (ponte viva T6): vínculo sessão <-> worktree nos registros da tripulação e no snapshot."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from helpers import ROOT, TempRepoCase, run_git

import crew_live
import ponte

HOOK = ROOT / "hooks" / "scripts" / "crew_hook.py"


def iso(minutes: float = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).replace(microsecond=0).isoformat()


class IdentidadeCase(TempRepoCase):
    def fire(self, event: str, sid: str, cwd: Path, **extra) -> str:
        payload = {"hook_event_name": event, "session_id": sid, "cwd": str(cwd), **extra}
        res = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True,
                             text=True, encoding="utf-8")
        self.assertEqual(res.returncode, 0, res.stderr)
        return res.stdout

    def skill(self, name: str, sid: str, cwd: Path) -> str:
        return self.fire("PreToolUse", sid, cwd, tool_name="Skill", tool_input={"skill": name, "args": ""})

    def worktree(self, name: str) -> Path:
        wt = self.tmp / name
        run_git(self.repo, "worktree", "add", "-q", "-b", name, str(wt))
        return wt

    def sessions(self) -> dict:
        return json.loads((self.repo / ".starcode" / "live" / "sessions.json").read_text(encoding="utf-8"))

    def put_sessions(self, data: dict) -> None:
        d = self.repo / ".starcode" / "live"
        d.mkdir(parents=True, exist_ok=True)
        (d / "sessions.json").write_text(json.dumps(data), encoding="utf-8")


class RegistroDaSessaoTests(IdentidadeCase):
    def test_hook_registra_o_worktree_de_cada_sessao(self) -> None:
        a, b = self.worktree("wt-a"), self.worktree("wt-b")
        self.skill("starcode:spock", "sess-a", a)
        self.skill("starcode:worf", "sess-b", b)
        self.skill("starcode:troi", "sess-main", self.repo)
        data = self.sessions()
        self.assertEqual(data["sess-a"]["worktree"], a.resolve().as_posix())
        self.assertEqual(data["sess-b"]["worktree"], b.resolve().as_posix())
        self.assertEqual(data["sess-main"]["worktree"], self.repo.resolve().as_posix())
        # renovar, parar e reativar a sessão mantém o vínculo; ele nunca troca de worktree
        for event in ("PostToolUse", "Stop", "UserPromptSubmit"):
            self.fire(event, "sess-a", a)
        self.assertEqual(self.sessions()["sess-a"]["worktree"], a.resolve().as_posix())
        self.assertEqual(self.sessions()["sess-a"]["member"], "spock")

    def test_renovacao_em_outro_worktree_descomprova_o_vinculo(self) -> None:
        a, b = self.worktree("wt-a"), self.worktree("wt-b")
        self.skill("starcode:spock", "sess-a", a)
        self.fire("PostToolUse", "sess-a", b)  # a sessão passou a rodar em outro worktree
        entry = self.sessions()["sess-a"]
        self.assertNotIn("worktree", entry)
        self.assertEqual((entry["member"], entry["active"]), ("spock", True))
        # e uma sessão antiga, sem o campo, continua sem ele depois de renovada
        data = self.sessions()
        data["sess-velha"] = {"member": "worf", "active": True, "source": "hook", "at": iso(1)}
        self.put_sessions(data)
        self.fire("PostToolUse", "sess-velha", a)
        self.assertNotIn("worktree", self.sessions()["sess-velha"])

    def test_hook_fora_do_git_nao_registra_nada(self) -> None:
        outside = self.tmp / "fora"
        outside.mkdir()
        self.assertEqual(self.skill("starcode:spock", "sess-x", outside), "")
        self.assertFalse((self.repo / ".starcode" / "live" / "sessions.json").exists())

    def test_cli_nao_comprova_sessao_nem_worktree(self) -> None:
        d = crew_live.live_dir(self.repo)
        crew_live.set_status(d, "laforge", 1, ["laforge"])
        self.assertNotIn("worktree", self.sessions()["cli:laforge"])


class SnapshotDaSessaoTests(IdentidadeCase):
    def crew(self) -> dict:
        self.write_repo_config()
        return {c["member"]: c for c in ponte.snapshot(self.repo)["crew"]}

    def test_snapshot_lista_so_sessoes_comprovaveis_com_id_e_worktree(self) -> None:
        wt = self.repo.resolve().as_posix()
        self.put_sessions({
            "sess-1": {"member": "spock", "active": True, "source": "hook", "at": iso(1), "worktree": wt},
            "sess-2": {"member": "spock", "active": True, "source": "hook", "at": iso(2), "worktree": "C:/outro"},
            "sess-antiga": {"member": "worf", "active": True, "source": "hook", "at": iso(3)},
            "sess-parada": {"member": "troi", "active": False, "source": "hook", "at": iso(1), "worktree": wt},
            "sess-velha": {"member": "kirk", "active": True, "source": "hook", "at": iso(30), "worktree": wt},
            "cli:laforge": {"member": "laforge", "active": True, "source": "cli", "at": iso(1)},
            "sess-vazio": {"member": "data", "active": True, "source": "hook", "at": iso(1), "worktree": ""},
            "sess-tipo": {"member": "uhura", "active": True, "source": "hook", "at": iso(1), "worktree": 7},
        })
        crew = self.crew()
        self.assertEqual(crew["spock"]["sessions"], [{"id": "sess-1", "worktree": wt},
                                                     {"id": "sess-2", "worktree": "C:/outro"}])
        self.assertEqual(crew["worf"]["sessions"], [{"id": "sess-antiga", "worktree": None}])
        for sem in ("troi", "kirk", "laforge", "picard"):
            self.assertEqual(crew[sem]["sessions"], [], sem)
        self.assertEqual(crew["data"]["sessions"], [{"id": "sess-vazio", "worktree": None}])
        self.assertEqual(crew["uhura"]["sessions"], [{"id": "sess-tipo", "worktree": None}])
        # o count agregado continua o mesmo (compatibilidade)
        self.assertEqual((crew["spock"]["count"], crew["worf"]["count"], crew["laforge"]["count"]), (1, 1, 1))

    def test_snapshot_sem_ou_com_sessions_invalido_nao_tem_sessoes(self) -> None:
        crew = self.crew()
        self.assertTrue(all(c["sessions"] == [] for c in crew.values()))
        self.put_sessions({"a": "texto", "b": {"member": 3, "active": True, "source": "hook", "at": iso(1)}})
        crew = self.crew()
        self.assertTrue(all(c["sessions"] == [] for c in crew.values()))

    def test_snapshot_de_dois_worktrees_traz_cada_sessao_com_o_worktree_dela(self) -> None:
        a, b = self.worktree("wt-a"), self.worktree("wt-b")
        self.skill("starcode:spock", "sess-a", a)
        self.skill("starcode:worf", "sess-b", b)
        self.write_repo_config()
        for path in (a, b):
            (path / ".specs").mkdir(exist_ok=True)
        snap_a, snap_b = ponte.snapshot(a), ponte.snapshot(b)
        sa = {c["member"]: c["sessions"] for c in snap_a["crew"]}
        sb = {c["member"]: c["sessions"] for c in snap_b["crew"]}
        self.assertEqual(sa["spock"], [{"id": "sess-a", "worktree": a.resolve().as_posix()}])
        self.assertEqual(sa["worf"], [{"id": "sess-b", "worktree": b.resolve().as_posix()}])
        self.assertEqual(sa, sb)  # o registro é do repositório; quem decide o vínculo é o worktree em foco
        self.assertEqual(snap_a["worktree"], a.resolve().as_posix())
        self.assertEqual(snap_b["worktree"], b.resolve().as_posix())


class DecisaoSC222Tests(IdentidadeCase):
    def test_decisions_registra_sc_222(self) -> None:
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        head = "### SC-222:"
        self.assertIn(head, text)
        section = text[text.index(head):]
        nxt = section.find("\n### ", 1)
        section = section if nxt < 0 else section[:nxt]
        decisao = next(line for line in section.splitlines() if line.startswith("- **Decisão**"))
        for termo in ("R8", "R11", "R21", "R22", "sessionId", "workspaceId", "worktree", "sessions",
                      "desconhecido", "título", "contagem", "registro antigo"):
            self.assertIn(termo, decisao, termo)
        pnb = next(line for line in section.splitlines() if line.startswith("- **Por que não é bug**"))
        for nome in ("ponte viva não inventa atividade", "ponte viva atualiza por evento",
                     "ponte viva vincula sessão ao worktree", "ponte viva não infere troca sem vínculo"):
            self.assertIn(nome, pnb, nome)
