"""Tests de bout en bout : jeux de tests et comparaison avec re (tâche 9.1)."""

import random
import re
from itertools import product

import pytest

from main import construire_automates
from validation import valider_expression
from reconnaissance import simuler

ALPHABET = ["a", "b"]


def mots_sur(alphabet, longueur_max):
    """Tous les mots de longueur 0 à longueur_max sur l'alphabet."""
    return [
        "".join(p)
        for n in range(longueur_max + 1)
        for p in product(alphabet, repeat=n)
    ]


def verifier_contre_re(expression, alphabet, longueur_max):
    """Compare l'AFD et l'AFD minimal avec le moteur re sur tous les mots courts."""
    _, afd, minimal = construire_automates(expression, alphabet)
    motif = re.compile(expression.replace("+", "|"))
    for mot in mots_sur(alphabet, longueur_max):
        attendu = motif.fullmatch(mot) is not None
        assert simuler(afd, mot) == attendu, f"AFD : {expression!r} sur {mot!r}"
        assert simuler(minimal, mot) == attendu, f"minimal : {expression!r} sur {mot!r}"
    assert minimal.est_deterministe()
    assert len(minimal.etats) <= len(afd.etats)


# --- 1. Expressions valides, comparées à re ---------------------------------

JEUX = [
    (["a", "b"], 6, [
        "a", "b", "ab", "ba", "a+b", "a*", "b*", "(a+b)*", "(ab)*",
        "a*b*", "a*b", "ab*", "(a+b)*abb", "(a+b)*a", "a(a+b)*",
        "(a+b)*a(a+b)", "a(b+a)*b", "((a+b)*a)*", "(a*b)*",
        "(a*+b*)*", "(a+b)(a+b)", "a|b", "(a|b)*b", "aab+abb", "a(ab)*b",
    ]),
    (["a", "b", "c"], 5, [
        "(a+b+c)*c", "a*b*c*", "(abc)*", "(a+bc)*", "c(a+b)*c", "a+b+c",
    ]),
    (["a"], 8, ["a*", "aa*", "(aa)*", "a+aa", "(aaa)*"]),
    (["0", "1"], 6, ["(0+1)*01", "1*01*", "(01)*+1", "0(0+1)*1"]),
]

CAS = [
    (alphabet, longueur, expression)
    for alphabet, longueur, expressions in JEUX
    for expression in expressions
]


@pytest.mark.parametrize(
    "alphabet, longueur, expression",
    CAS,
    ids=[f"{''.join(a)}-{e}" for a, _, e in CAS],
)
def test_expression_valide_contre_re(alphabet, longueur, expression):
    verifier_contre_re(expression, alphabet, longueur)


# --- 2. Expressions invalides : position et cause ---------------------------

INVALIDES = [
    ("*a", 1, "étoile"),
    ("*", 1, "étoile"),
    ("a++b", 2, "droite"),
    ("ab||a", 3, "droite"),
    ("a+", 2, "droite"),
    ("(a+)", 3, "droite"),
    ("(a+b)*+", 7, "droite"),
    ("+a", 1, "gauche"),
    ("(a+b", 1, "jamais fermée"),
    ("((a)", 1, "jamais fermée"),
    ("a(", 2, "jamais fermée"),
    ("a+b)", 4, "sans parenthèse ouvrante"),
    (")(", 1, "sans parenthèse ouvrante"),
    ("()", 1, "vides"),
    ("a()", 2, "vides"),
    ("(*a)", 2, "étoile"),
    ("a.b", 2, "réservé"),
    ("a+c", 3, "alphabet"),
    ("A", 1, "alphabet"),
]


@pytest.mark.parametrize("expression, position, mot_cle", INVALIDES)
def test_expression_invalide(expression, position, mot_cle):
    ok, erreur = valider_expression(expression, ALPHABET)
    assert not ok
    assert erreur.startswith(f"Position {position} :"), erreur
    assert mot_cle in erreur


# --- 3. Expressions avec ε : résultats écrits à la main ---------------------

CAS_EPSILON = [
    ("@", {""}),
    ("ε", {""}),
    ("ε*", {""}),
    ("a+ε", {"", "a"}),
    ("aε", {"a"}),
    ("(a+ε)b", {"ab", "b"}),
    ("(ab)*+ε", {"", "ab"}),
    ("(a+ε)(b+ε)", {"", "a", "b", "ab"}),
    ("(ε+a)*", {"", "a", "aa", "aaa"}),
]


@pytest.mark.parametrize("expression, attendus", CAS_EPSILON)
def test_expressions_avec_epsilon(expression, attendus):
    _, afd, minimal = construire_automates(expression, ALPHABET)
    for automate in (afd, minimal):
        acceptes = {m for m in mots_sur(ALPHABET, 3) if simuler(automate, m)}
        assert acceptes == attendus


# --- 4. a** : Python refuse cette écriture, pas nous ------------------------

def test_double_etoile():
    _, afd_double, _ = construire_automates("a**", ALPHABET)
    _, afd_simple, _ = construire_automates("a*", ALPHABET)
    for mot in mots_sur(ALPHABET, 6):
        assert simuler(afd_double, mot) == simuler(afd_simple, mot)


# --- 5. Expressions aléatoires et mot très long -----------------------------

def aleatoire(profondeur, rng):
    """Expression bien écrite tirée au hasard (union et étoile toujours parenthésées)."""
    if profondeur == 0 or rng.random() < 0.25:
        return rng.choice(ALPHABET)
    genre = rng.choice(["union", "concat", "etoile"])
    if genre == "union":
        return f"({aleatoire(profondeur - 1, rng)}+{aleatoire(profondeur - 1, rng)})"
    if genre == "concat":
        return aleatoire(profondeur - 1, rng) + aleatoire(profondeur - 1, rng)
    return f"({aleatoire(profondeur - 1, rng)})*"


@pytest.mark.parametrize("graine", range(60))
def test_expressions_aleatoires(graine):
    expression = aleatoire(3, random.Random(graine))
    verifier_contre_re(expression, ALPHABET, 6)


def test_mot_long():
    _, _, minimal = construire_automates("(a+b)*abb", ALPHABET)
    assert simuler(minimal, "ab" * 1000 + "abb")
    assert not simuler(minimal, "ab" * 1000)