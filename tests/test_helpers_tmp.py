"""TempRepoCase guarda a pasta temporária já resolvida (SC-226)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import TempRepoCase


_RealTmp = tempfile.TemporaryDirectory


class _NonCanonicalTmp:
    """Substitui TemporaryDirectory: `name` tem `..`, logo não é canônico."""

    def __init__(self, *args, **kwargs):
        self._real = _RealTmp(*args, **kwargs)
        real = Path(self._real.name)
        (real / "sub").mkdir()
        self.name = str(real / "sub" / "..")

    def cleanup(self) -> None:
        self._real.cleanup()


class TempResolvedTest(unittest.TestCase):
    def test_tmp_dir_resolved(self) -> None:
        class Probe(TempRepoCase):
            def runTest(self) -> None:
                pass

        probe = Probe()
        with mock.patch("helpers.tempfile.TemporaryDirectory", _NonCanonicalTmp):
            probe.setUp()
        try:
            self.assertIn("..", Path(probe._tmp.name).parts)
            self.assertEqual(probe.tmp, probe.tmp.resolve())
            self.assertEqual(probe.repo, probe.repo.resolve())
            self.assertNotIn("..", probe.tmp.parts)
        finally:
            probe.tearDown()


if __name__ == "__main__":
    unittest.main()
