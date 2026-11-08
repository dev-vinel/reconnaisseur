import pytest

from validation import (
    analyser_lexicalement, TYPE_SYMBOLE, TYPE_PAR_OUV, TYPE_PAR_FERM,
)
from preparation import (
    rendre_concat_explicite, jetons_en_texte, vers_postfixe, TYPE_CONCAT,
)

ALPHABET = ["a", "b", "c"]


def concat(expression):
    """Raccourci : lexical, concaténation explicite, retour en texte."""
    jetons, _ = analyser_lexicalement(expression, ALPHABET)
    return jetons_en_texte(rendre_concat_explicite(jetons))


CAS = [
    ("a", "a"),
    ("ab", "a.b"),
    ("ab*", "a.b*"),
    ("a*b*", "a*.b*"),
    ("a+b", "a+b"),
    ("a|b", "a+b"),
    ("(a)(b)", "(a).(b)"),
    ("a(b)", "a.(b)"),
    ("(a)b", "(a).b"),
    ("(a+b)*abb", "(a+b)*.a.b.b"),
    ("(ab)*+@", "(a.b)*+ε"),
    ("ab@", "a.b.ε"),
    ("a**b", "a**.b"),
]


@pytest.mark.parametrize("entree, attendu", CAS)
def test_concat_explicite(entree, attendu):
    assert concat(entree) == attendu


def test_type_du_jeton_insere():
    jetons, _ = analyser_lexicalement("ab", ALPHABET)
    types = [j.type for j in rendre_concat_explicite(jetons)]
    assert types == [TYPE_SYMBOLE, TYPE_CONCAT, TYPE_SYMBOLE]


def test_liste_vide():
    assert rendre_concat_explicite([]) == []


def test_entree_non_modifiee():
    jetons, _ = analyser_lexicalement("ab", ALPHABET)
    rendre_concat_explicite(jetons)
    assert len(jetons) == 2
def postfixe(expression):
    """Raccourci : lexical, concaténation explicite, postfixe, retour en texte."""
    jetons, _ = analyser_lexicalement(expression, ALPHABET)
    jetons = rendre_concat_explicite(jetons)
    return jetons_en_texte(vers_postfixe(jetons))


CAS_POSTFIXE = [
    ("a", "a"),
    ("ab", "ab."),
    ("a+b", "ab+"),
    ("a|b", "ab+"),
    ("ab*", "ab*."),
    ("a+bc", "abc.+"),
    ("a*b", "a*b."),
    ("(a+b)*abb", "ab+*a.b.b."),
    ("(ab)*+@", "ab.*ε+"),
    ("a+b+c", "ab+c+"),
    ("abc", "ab.c."),
    ("a**", "a**"),
    ("@", "ε"),
    ("(a)", "a"),
    ("a+b*", "ab*+"),
    ("(a+b)(a+b)", "ab+ab+."),
]


@pytest.mark.parametrize("entree, attendu", CAS_POSTFIXE)
def test_postfixe(entree, attendu):
    assert postfixe(entree) == attendu


def test_pas_de_parentheses_en_sortie():
    jetons, _ = analyser_lexicalement("((a+b)*(ab))*", ALPHABET)
    sortie = vers_postfixe(rendre_concat_explicite(jetons))
    types = {j.type for j in sortie}
    assert TYPE_PAR_OUV not in types
    assert TYPE_PAR_FERM not in types


def test_postfixe_liste_vide():
    assert vers_postfixe([]) == []