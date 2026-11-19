"""Tests des fonctions pures de dessin.py (sans Graphviz ni fenêtre)."""

import pytest

from syntaxe import EPSILON
from automate import Automate
from main import construire_automates
from reconnaissance import reconnaitre
from theme import MODE_SOMBRE, MODE_CLAIR, palette
from dessin import (
    etiquette_arete, regrouper_aretes, contexte_etape, generer_dot,
    dot_etape, dots_du_chemin, graphviz_disponible, exporter_image,
)

AFN, AFD, MINIMAL = construire_automates("(a+b)*abb", ["a", "b"])


def ligne(dot, debut):
    """Retourne la ligne du DOT qui commence par `debut`."""
    for texte in dot.split("\n"):
        if texte.strip().startswith(debut):
            return texte
    raise AssertionError(f"Aucune ligne ne commence par {debut!r}")


def test_regrouper_aretes_fusionne():
    auto = Automate(["a", "b"])
    q0, q1 = auto.nouvel_etat(), auto.nouvel_etat()
    auto.ajouter_transition(q0, EPSILON, q1)
    auto.ajouter_transition(q0, "b", q1)
    auto.ajouter_transition(q0, "a", q1)
    assert regrouper_aretes(auto) == [(0, 1, ("a", "b", EPSILON))]


def test_regrouper_aretes_minimal():
    assert regrouper_aretes(MINIMAL) == [
        (0, 0, ("b",)), (0, 1, ("a",)),
        (1, 1, ("a",)), (1, 2, ("b",)),
        (2, 1, ("a",)), (2, 3, ("b",)),
        (3, 0, ("b",)), (3, 1, ("a",)),
    ]


def test_etiquette_arete():
    assert etiquette_arete(("a", "b", EPSILON)) == "a,b,ε"


def test_contexte_etape():
    _, chemin = reconnaitre(MINIMAL, "babb")      # états : 0, 0, 1, 2, 3
    assert contexte_etape(chemin, 0) == (0, frozenset(), None)
    assert contexte_etape(chemin, 2) == (1, frozenset({0}), (0, 1))
    assert contexte_etape(chemin, 4) == (3, frozenset({0, 1, 2}), (2, 3))


def test_contexte_etape_erreurs():
    _, chemin = reconnaitre(MINIMAL, "ab")
    with pytest.raises(ValueError):
        contexte_etape([], 0)
    with pytest.raises(IndexError):
        contexte_etape(chemin, 99)


def test_dot_structure():
    dot = generer_dot(MINIMAL, MODE_SOMBRE)
    assert dot.startswith("digraph automate {")
    assert dot.endswith("}")
    assert "rankdir=LR" in dot
    assert "debut -> q0" in dot


def test_dot_final_double_cercle():
    dot = generer_dot(MINIMAL, MODE_SOMBRE)
    assert 'q3 [label="q3", shape=doublecircle' in dot
    assert "shape=doublecircle" not in ligne(dot, 'q0 [label')


def test_dot_change_avec_le_theme():
    sombre = generer_dot(MINIMAL, MODE_SOMBRE)
    clair = generer_dot(MINIMAL, MODE_CLAIR)
    assert sombre != clair
    assert palette(MODE_SOMBRE)["dessin_fond"] in sombre
    assert palette(MODE_CLAIR)["dessin_fond"] in clair


def test_dot_epsilon_en_pointilles():
    assert "style=dashed" in generer_dot(AFN, MODE_SOMBRE)
    assert "style=dashed" not in generer_dot(AFD, MODE_SOMBRE)


def test_dot_sans_etat_initial():
    auto = Automate(["a"])
    auto.nouvel_etat()
    assert "debut" not in generer_dot(auto, MODE_SOMBRE)


def test_dot_mode_inconnu():
    with pytest.raises(ValueError):
        generer_dot(MINIMAL, "arc-en-ciel")


def test_dot_etape_colore():
    p = palette(MODE_SOMBRE)
    _, chemin = reconnaitre(MINIMAL, "babb")
    dot = dot_etape(MINIMAL, chemin, 2, MODE_SOMBRE)   # état courant : q1
    assert f'fillcolor="{p["dessin_courant_fond"]}"' in ligne(dot, 'q1 [label')
    assert f'fillcolor="{p["dessin_visite_fond"]}"' in ligne(dot, 'q0 [label')
    assert f'fillcolor="{p["dessin_courant_fond"]}"' not in ligne(dot, 'q2 [label')
    arete = ligne(dot, "q0 -> q1 [")
    assert p["dessin_chemin"] in arete and "penwidth=3.2" in arete
    assert p["dessin_chemin"] not in ligne(dot, "q1 -> q2 [")


def test_dot_etape_verdict():
    p = palette(MODE_SOMBRE)
    _, chemin = reconnaitre(MINIMAL, "babb")
    dernier = len(chemin) - 1
    avec = dot_etape(MINIMAL, chemin, dernier, MODE_SOMBRE, accepte=True)
    sans = dot_etape(MINIMAL, chemin, dernier, MODE_SOMBRE)
    assert f'fillcolor="{p["accepte"]}"' in ligne(avec, 'q3 [label')
    assert f'fillcolor="{p["dessin_courant_fond"]}"' in ligne(sans, 'q3 [label')
    _, rejet = reconnaitre(MINIMAL, "abab")           # finit en q2, non final
    dot = dot_etape(MINIMAL, rejet, len(rejet) - 1, MODE_SOMBRE, accepte=False)
    assert f'fillcolor="{p["rejete"]}"' in ligne(dot, 'q2 [label')


def test_dots_du_chemin():
    _, chemin = reconnaitre(MINIMAL, "babb")
    dots = dots_du_chemin(MINIMAL, chemin, MODE_SOMBRE, accepte=True)
    assert len(dots) == len(chemin)
    assert dots[0] != dots[1]


def test_graphviz_disponible_est_un_booleen():
    assert isinstance(graphviz_disponible(), bool)


def test_exporter_format_invalide(tmp_path):
    with pytest.raises(ValueError):
        exporter_image("digraph {}", tmp_path / "x.pdf", "pdf")