"""Vérifie que le code et le README sont documentés (tâche 9.2)."""

import ast
from pathlib import Path

import pytest

DOSSIER = Path(__file__).parent

MODULES = [
    "syntaxe", "saisie", "validation", "preparation", "automate",
    "determinisation", "affichage", "reconnaissance", "main",
]


def charger(nom):
    """Lit un module sans l'exécuter et retourne son arbre syntaxique."""
    return ast.parse((DOSSIER / f"{nom}.py").read_text(encoding="utf-8"))


def definitions_publiques(arbre):
    """Fonctions, classes et méthodes publiques (nom sans '_' initial)."""
    for noeud in arbre.body:
        if isinstance(noeud, ast.ClassDef) and not noeud.name.startswith("_"):
            yield noeud
            for membre in noeud.body:
                if isinstance(membre, ast.FunctionDef) and not membre.name.startswith("_"):
                    yield membre
        elif isinstance(noeud, ast.FunctionDef) and not noeud.name.startswith("_"):
            yield noeud


@pytest.mark.parametrize("nom", MODULES)
def test_module_a_une_docstring(nom):
    assert ast.get_docstring(charger(nom)), f"{nom}.py n'a pas de docstring de module"


@pytest.mark.parametrize("nom", MODULES)
def test_definitions_publiques_documentees(nom):
    manquantes = [
        noeud.name
        for noeud in definitions_publiques(charger(nom))
        if not ast.get_docstring(noeud)
    ]
    assert not manquantes, f"{nom}.py : sans docstring : {manquantes}"


def test_readme_present_et_complet():
    readme = DOSSIER / "README.md"
    assert readme.exists(), "README.md est introuvable"
    texte = readme.read_text(encoding="utf-8")
    for section in ["Installation", "Lancement", "Syntaxe", "Tests", "Limites"]:
        assert section in texte, f"section manquante dans le README : {section}"