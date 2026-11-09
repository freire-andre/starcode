"""Exemplo com bypass plantado para o aceite da Fase 9 (nunca importar)."""
import unittest

import requests


def fetch(url):
    return requests.get(url, verify=False)


class PlantedTests(unittest.TestCase):
    @unittest.skip("")
    def test_fetch(self):
        self.assertTrue(fetch("https://example.invalid"))
