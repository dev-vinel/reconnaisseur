import importlib

import pytest

MODULES = [
    "syntaxe", "saisie", "validation", "preparation",
    "automate", "determinisation", "affichage", "reconnaissance", "main",
]


@pytest.mark.parametrize("nom", MODULES)
def test_module_importable(nom):
    importlib.import_module(nom)


