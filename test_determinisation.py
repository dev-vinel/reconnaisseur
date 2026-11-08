import re
from itertools import product

import pytest

from syntaxe import EPSILON
from validation import analyser_lexicalement
from preparation import rendre_concat_explicite, vers_postfixe
from automate import Automate, thompson, epsilon_fermeture, deplacer
from determinisation import determiniser

ALPHABET = ["a", "b"]


def construire(expression):
    """Raccourci : de l'expression à l'AFN-ε de Thompson."""
    jetons, erreur = analyser_lexicalement(expression, ALPHABET)
    assert jetons is not None, erreur
    return thompson(vers_postfixe(rendre_concat_explicite(jetons)), ALPHABET)


def accepte_afd(afd, mot):
    """Parcours d'un AFD, réservé aux tests (la vraie version viendra en phase 7)."""
    etat = afd.initial
    for lettre in mot:
        cibles = afd.cibles(etat, lettre)
        if not cibles:
            return False
        (etat,) = cibles
    return etat in afd.finaux


def chaine_epsilon():
    """0 -ε-> 1 -ε-> 2 et 2 -a-> 3."""
    auto = Automate(ALPHABET)
    for _ in range(4):
        auto.nouvel_etat()
    auto.ajouter_transition(0, EPSILON, 1)
    auto.ajouter_transition(1, EPSILON, 2)
    auto.ajouter_transition(2, "a", 3)
    return auto


# --- ε-fermeture et déplacement -------------------------------------------

def test_fermeture_contient_l_etat_lui_meme():
    assert epsilon_fermeture(chaine_epsilon(), {3}) == {3}


def test_fermeture_chaine():
    assert epsilon_fermeture(chaine_epsilon(), {0}) == {0, 1, 2}


def test_fermeture_ensemble_vide():
    assert epsilon_fermeture(chaine_epsilon(), set()) == frozenset()


def test_fermeture_avec_boucle():
    auto = Automate(ALPHABET)
    auto.nouvel_etat()
    auto.nouvel_etat()
    auto.ajouter_transition(0, EPSILON, 1)
    auto.ajouter_transition(1, EPSILON, 0)
    assert epsilon_fermeture(auto, {0}) == {0, 1}


def test_fermeture_est_figee():
    assert isinstance(epsilon_fermeture(chaine_epsilon(), {0}), frozenset)


def test_deplacer():
    auto = Automate(ALPHABET)
    for _ in range(4):
        auto.nouvel_etat()
    auto.ajouter_transition(0, "a", 1)
    auto.ajouter_transition(2, "a", 3)
    auto.ajouter_transition(2, "b", 0)
    assert deplacer(auto, {0, 2}, "a") == {1, 3}
    assert deplacer(auto, {0, 2}, "b") == {0}
    assert deplacer(auto, {1}, "a") == set()


def test_deplacer_ignore_epsilon():
    assert deplacer(chaine_epsilon(), {0}, "a") == set()


# --- structure de l'AFD ---------------------------------------------------

def test_afd_symbole():
    afd = determiniser(construire("a"))
    assert afd.etats == {0, 1}
    assert afd.initial == 0
    assert afd.finaux == {1}
    assert afd.liste_transitions() == [(0, "a", 1)]


def test_afd_etoile():
    afd = determiniser(construire("a*"))
    assert afd.etats == {0, 1}
    assert afd.finaux == {0, 1}
    assert afd.liste_transitions() == [(0, "a", 1), (1, "a", 1)]


def test_afd_epsilon():
    afd = determiniser(construire("@"))
    assert afd.etats == {0}
    assert afd.finaux == {0}
    assert afd.liste_transitions() == []


def test_afd_union():
    afd = determiniser(construire("a+b"))
    assert afd.etats == {0, 1, 2}
    assert afd.finaux == {1, 2}
    assert afd.liste_transitions() == [(0, "a", 1), (0, "b", 2)]


def test_afd_classique():
    afd = determiniser(construire("(a+b)*abb"))
    assert afd.alphabet == ALPHABET
    assert len(afd.etats) == 5
    assert afd.initial == 0
    assert afd.finaux == {4}
    assert afd.liste_transitions() == [
        (0, "a", 1), (0, "b", 2),
        (1, "a", 1), (1, "b", 3),
        (2, "a", 1), (2, "b", 2),
        (3, "a", 1), (3, "b", 4),
        (4, "a", 1), (4, "b", 2),
    ]


def test_afn_non_modifie():
    afn = construire("(a+b)*abb")
    avant = afn.liste_transitions()
    determiniser(afn)
    assert afn.liste_transitions() == avant
    assert len(afn.etats) == 14


# --- propriétés sur plusieurs expressions ---------------------------------

EXPRESSIONS = [
    "a", "ab", "a+b", "a*", "(a+b)*abb", "(ab)*",
    "a*b*", "(a+b)*", "a(b+a)*b", "((a+b)*a)*", "(a*b)*",
]
MOTS = ["".join(p) for n in range(7) for p in product("ab", repeat=n)]


@pytest.mark.parametrize("expression", EXPRESSIONS)
def test_afd_est_deterministe(expression):
    assert determiniser(construire(expression)).est_deterministe()


@pytest.mark.parametrize("expression", EXPRESSIONS)
def test_afd_equivalent_a_re(expression):
    afd = determiniser(construire(expression))
    motif = re.compile(expression.replace("+", "|"))
    for mot in MOTS:
        attendu = motif.fullmatch(mot) is not None
        assert accepte_afd(afd, mot) == attendu, f"{expression!r} sur {mot!r}"