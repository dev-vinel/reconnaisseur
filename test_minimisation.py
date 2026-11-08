import re
from itertools import product

import pytest

from validation import analyser_lexicalement
from preparation import rendre_concat_explicite, vers_postfixe
from automate import thompson
from determinisation import determiniser, minimiser

ALPHABET = ["a", "b"]


def construire(expression):
    """De l'expression à l'AFN-ε de Thompson."""
    jetons, erreur = analyser_lexicalement(expression, ALPHABET)
    assert jetons is not None, erreur
    return thompson(vers_postfixe(rendre_concat_explicite(jetons)), ALPHABET)


def minimal(expression):
    return minimiser(determiniser(construire(expression)))


def accepte_afd(afd, mot):
    """Parcours d'un AFD, réservé aux tests."""
    etat = afd.initial
    for lettre in mot:
        cibles = afd.cibles(etat, lettre)
        if not cibles:
            return False
        (etat,) = cibles
    return etat in afd.finaux


def test_min_symbole():
    mini = minimal("a")
    assert mini.etats == {0, 1}
    assert mini.finaux == {1}
    assert mini.liste_transitions() == [(0, "a", 1)]


def test_min_epsilon():
    mini = minimal("@")
    assert mini.etats == {0}
    assert mini.finaux == {0}
    assert mini.liste_transitions() == []


def test_min_union():
    mini = minimal("a+b")
    assert mini.etats == {0, 1}
    assert mini.finaux == {1}
    assert mini.liste_transitions() == [(0, "a", 1), (0, "b", 1)]


def test_min_etoile():
    mini = minimal("a*")
    assert mini.etats == {0}
    assert mini.finaux == {0}
    assert mini.liste_transitions() == [(0, "a", 0)]


def test_min_sigma_etoile():
    mini = minimal("(a+b)*")
    assert mini.etats == {0}
    assert mini.finaux == {0}
    assert mini.liste_transitions() == [(0, "a", 0), (0, "b", 0)]


def test_min_ab_etoile():
    mini = minimal("ab*")
    assert mini.etats == {0, 1}
    assert mini.finaux == {1}
    assert mini.liste_transitions() == [(0, "a", 1), (1, "b", 1)]


def test_min_a_etoile_b():
    mini = minimal("a*b")
    assert mini.etats == {0, 1}
    assert mini.finaux == {1}
    assert mini.liste_transitions() == [(0, "a", 0), (0, "b", 1)]


def test_min_classique():
    mini = minimal("(a+b)*abb")
    assert len(determiniser(construire("(a+b)*abb")).etats) == 5
    assert mini.etats == {0, 1, 2, 3}
    assert mini.initial == 0
    assert mini.finaux == {3}
    assert mini.liste_transitions() == [
        (0, "a", 1), (0, "b", 0),
        (1, "a", 1), (1, "b", 2),
        (2, "a", 1), (2, "b", 3),
        (3, "a", 1), (3, "b", 0),
    ]


def test_refuse_afn():
    with pytest.raises(ValueError):
        minimiser(construire("a+b"))   # contient des ε-transitions


def test_afd_non_modifie():
    afd = determiniser(construire("(a+b)*abb"))
    avant = (afd.liste_transitions(), set(afd.etats), set(afd.finaux))
    minimiser(afd)
    assert (afd.liste_transitions(), set(afd.etats), set(afd.finaux)) == avant


EXPRESSIONS = [
    "a", "ab", "a+b", "a*", "(a+b)*abb", "(ab)*",
    "a*b*", "(a+b)*", "a(b+a)*b", "((a+b)*a)*", "(a*b)*",
]
MOTS = ["".join(p) for n in range(7) for p in product("ab", repeat=n)]


@pytest.mark.parametrize("expression", EXPRESSIONS)
def test_pas_plus_grand(expression):
    afd = determiniser(construire(expression))
    assert len(minimiser(afd).etats) <= len(afd.etats)


@pytest.mark.parametrize("expression", EXPRESSIONS)
def test_resultat_deterministe(expression):
    assert minimal(expression).est_deterministe()


@pytest.mark.parametrize("expression", EXPRESSIONS)
def test_langage_conserve(expression):
    mini = minimal(expression)
    motif = re.compile(expression.replace("+", "|"))
    for mot in MOTS:
        attendu = motif.fullmatch(mot) is not None
        assert accepte_afd(mini, mot) == attendu, f"{expression!r} sur {mot!r}"


@pytest.mark.parametrize("expression", EXPRESSIONS)
def test_idempotent(expression):
    mini = minimal(expression)
    assert len(minimiser(mini).etats) == len(mini.etats)