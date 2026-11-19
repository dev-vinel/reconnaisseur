import importlib

import pytest

MODULES = [
    "saisie",
    "validation",
    "postfixe",
    "automate",
    # ... tes autres modules
    "theme",
    "dessin",
    "interface",
]


@pytest.mark.parametrize("nom", MODULES)
def test_module_importable(nom):
    importlib.import_module(nom)


