from itertools import product
import re

import pytest

from syntaxe import EPSILON
from validation import analyser_lexicalement, Jeton, TYPE_UNION
from preparation import rendre_concat_explicite, vers_postfixe
from automate import thompson

ALPHABET = ["a", "b"]


def construire(expression):
    """Raccourci : lexical, concaténation explicite, postfixe, Thompson."""
    jetons, erreur = analyser_lexicalement(expression, ALPHABET)
    assert jetons is not None, erreur
    postfixe = vers_postfixe(rendre_concat_explicite(jetons))
    return thompson(postfixe, ALPHABET)


def fermeture(auto, etats):
    """Tous les états atteignables depuis `etats` par des ε-transitions."""
    resultat = set(etats)
    pile = list(etats)
    while pile:
        e = pile.pop()
        for c in auto.cibles(e, EPSILON):
            if c not in resultat:
                resultat.add(c)
                pile.append(c)
    return resultat


def accepte(auto, mot):
    """Mini-simulateur réservé aux tests (la vraie version viendra en phase 7)."""
    courants = fermeture(auto, {auto.initial})
    for lettre in mot:
        suivants = set()
        for e in courants:
            suivants |= auto.cibles(e, lettre)
        courants = fermeture(auto, suivants)
    return bool(courants & auto.finaux)


def test_symbole_seul():
    auto = construire("a")
    assert len(auto.etats) == 2
    assert auto.liste_transitions() == [(0, "a", 1)]
    assert auto.initial == 0
    assert auto.finaux == {1}


def test_concatenation_simple():
    auto = construire("ab")
    assert len(auto.etats) == 4
    assert len(auto.liste_transitions()) == 3
    assert auto.initial == 0
    assert auto.finaux == {3}


def test_epsilon_seul():
    auto = construire("@")
    assert len(auto.etats) == 2
    assert auto.liste_transitions() == [(0, EPSILON, 1)]
    assert auto.finaux == {1}


def test_taille_classique():
    auto = construire("(a+b)*abb")
    assert len(auto.etats) == 14
    assert len(auto.liste_transitions()) == 16
    assert auto.initial == 6
    assert auto.finaux == {13}


ACCEPTES = [
    ("a", "a"), ("ab", "ab"), ("a+b", "a"), ("a+b", "b"),
    ("a*", ""), ("a*", "aaa"), ("@", ""), ("(ab)*", "abab"),
    ("(a+b)*abb", "abb"), ("(a+b)*abb", "babb"), ("(a+b)*abb", "aababb"),
]

REFUSES = [
    ("a", ""), ("a", "aa"), ("ab", "a"), ("ab", "ba"),
    ("a+b", "ab"), ("a*", "b"), ("@", "a"), ("(ab)*", "aba"),
    ("(a+b)*abb", "ab"), ("(a+b)*abb", "abba"), ("(a+b)*abb", ""),
]


@pytest.mark.parametrize("expression, mot", ACCEPTES)
def test_mot_accepte(expression, mot):
    assert accepte(construire(expression), mot)


@pytest.mark.parametrize("expression, mot", REFUSES)
def test_mot_refuse(expression, mot):
    assert not accepte(construire(expression), mot)


EXPRESSIONS = [
    "a", "ab", "a+b", "a*", "(a+b)*abb", "(ab)*",
    "a*b*", "(a+b)*", "a(b+a)*b", "((a+b)*a)*", "(a*b)*",
]
MOTS = ["".join(p) for n in range(7) for p in product("ab", repeat=n)]


@pytest.mark.parametrize("expression", EXPRESSIONS)
def test_comparaison_avec_re(expression):
    auto = construire(expression)
    motif = re.compile(expression.replace("+", "|"))
    for mot in MOTS:
        attendu = motif.fullmatch(mot) is not None
        assert accepte(auto, mot) == attendu, f"{expression!r} sur {mot!r}"


def test_postfixe_vide():
    with pytest.raises(ValueError):
        thompson([], ALPHABET)


def test_operateur_sans_operande():
    with pytest.raises(ValueError):
        thompson([Jeton(TYPE_UNION, "+", 1)], ALPHABET)


def test_operandes_en_trop():
    jetons, _ = analyser_lexicalement("ab", ALPHABET)   # sans concaténation explicite
    with pytest.raises(ValueError):
        thompson(jetons, ALPHABET)