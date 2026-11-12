from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT, run_git
from test_impact import ImpactCase, write

import impact

SKIP = {"node_modules", "dist", ".git", "target"}


class TestImpactTs(ImpactCase):
    def test_ts_imports_relativos_extensoes_e_index(self) -> None:
        write(self.repo, {
            "src/a.ts": "export const a = 1;\n",
            "src/b.tsx": "export const b = 2;\n",
            "src/lib/index.js": "module.exports = {};\n",
            "src/c.mjs": "export const c = 3;\n",
            "src/exato.json.ts": "export {};\n",
            "src/util/deep.ts": "export const d = 4;\n",
            "src/t_a.test.ts": "import { a } from './a';\n",
            "src/t_b.test.ts": "import type {\n  B,\n} from \"./b\";\nimport './c.mjs';\n",
            "src/t_lib.test.ts": "const l = require('./lib');\n",
            "src/t_dyn.test.ts": "const m = await import('./util/deep');\n",
            "src/t_re.test.ts": "export * from '../src/a';\n",
            "src/t_pkg.test.ts": "import x from 'react';\nimport y from '@scope/pkg';\nimport z from 'node:fs';\n",
        })
        self.commit()
        graph = impact.build_graph(self.repo, impact.repo_files(self.repo))
        self.assertEqual(graph["src/t_a.test.ts"], {"src/a.ts"})
        self.assertEqual(graph["src/t_b.test.ts"], {"src/b.tsx", "src/c.mjs"})
        self.assertEqual(graph["src/t_lib.test.ts"], {"src/lib/index.js"})
        self.assertEqual(graph["src/t_dyn.test.ts"], {"src/util/deep.ts"})
        self.assertEqual(graph["src/t_re.test.ts"], {"src/a.ts"})
        self.assertEqual(graph["src/t_pkg.test.ts"], set())
        res = impact.select(self.repo, changed=["src/lib/index.js"])
        self.assertEqual(res["tests"], ["src/t_lib.test.ts"])

    def test_aliases_ts_roda_tudo(self) -> None:
        write(self.repo, {
            "src/a.ts": "export const a = 1;\n",
            "src/a.test.ts": "import { a } from './a';\n",
            "tsconfig.json": '{\n  // comentário\n  "compilerOptions": {\n    "strict": true,\n  },\n}\n',
        })
        self.commit()
        res = impact.select(self.repo, changed=["src/a.ts"])
        self.assertEqual(res["verdict"], "selected")
        write(self.repo, {"tsconfig.json": '{\n  // alias\n  "compilerOptions": {\n    "paths": {"@/*": ["src/*"]},\n  },\n}\n'})
        res = impact.select(self.repo, changed=["src/a.ts"])
        self.assertEqual(res["verdict"], "run-all")
        self.assertEqual(impact.format_text(res), "rodar tudo: aliases do TypeScript não resolvidos")
        write(self.repo, {"tsconfig.json": '{"compilerOptions": {"baseUrl": "."}}'})
        self.assertEqual(impact.select(self.repo, changed=["src/a.ts"])["verdict"], "run-all")
        write(self.repo, {"tsconfig.json": "{}", "src/b.ts": "import { a } from '@/a';\n"})
        self.assertEqual(impact.select(self.repo, changed=["src/a.ts"])["reason"], impact.TS_ALIAS_REASON)
        write(self.repo, {"src/b.ts": "import { a } from '~/a';\n"})
        self.assertEqual(impact.select(self.repo, changed=["src/a.ts"])["reason"], impact.TS_ALIAS_REASON)

    def test_ts_malformado_com_marcador_roda_tudo(self) -> None:
        write(self.repo, {
            "src/a.ts": "export const a = 1;\n",
            "src/a.test.ts": "import { a } from './a';\n",
        })
        self.commit()
        write(self.repo, {"src/a.ts": "export const a={{broken\n"})
        res = impact.select(self.repo, changed=["src/a.ts"])
        self.assertEqual(res["verdict"], "run-all")
        self.assertTrue(impact.format_text(res).startswith("rodar tudo: grafo incompleto: src/a.ts: "), impact.format_text(res))

    def test_impact_fixture_telas(self) -> None:
        tmp = tempfile.TemporaryDirectory(prefix="impact-telas-")
        self.addCleanup(tmp.cleanup)
        dest = Path(tmp.name) / "telas"
        shutil.copytree(ROOT / "aceite" / "telas", dest,
                        ignore=lambda _d, names: [n for n in names if n in SKIP])
        run_git(dest, "init", "-q", "-b", "main")
        run_git(dest, "config", "user.email", "t@example.com")
        run_git(dest, "config", "user.name", "T")
        run_git(dest, "config", "commit.gpgsign", "false")
        run_git(dest, "add", "-A")
        run_git(dest, "commit", "-q", "-m", "base")
        res = impact.select(dest, changed=["src/greeting.ts"])
        self.assertEqual(res["verdict"], "selected")
        self.assertIn("src/greeting.test.ts", res["tests"])


if __name__ == "__main__":
    unittest.main()
