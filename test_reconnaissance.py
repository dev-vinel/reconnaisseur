import re
from itertools import product

import pytest

from validation import analyser_lexicalement
from preparation import rendre_concat_explicite, vers_postfixe
from automate import thompson
from determinisation import determiniser, minimiser
from reconnaissance import (
    simuler, reconnaitre, Configuration,
    cause_du_resultat, expliquer,
    CAUSE_ACCEPTE, CAUSE_BLOQUE, CAUSE_NON_FINAL,
)

ALPHABET = ["a", "b"]


def construire(expression):
    """De l'expression à l'AFN-ε de Thompson."""
    jetons, erreur = analyser_lexicalement(expression, ALPHABET)
    assert jetons is not None, erreur
    return thompson(vers_postfixe(rendre_concat_explicite(jetons)), ALPHABET)


def afd(expression):
    return determiniser(construire(expression))


ACCEPTES = [
    ("a", "a"), ("ab", "ab"), ("a+b", "b"), ("a*", ""),
    ("a*", "aaa"), ("@", ""), ("(ab)*", "abab"), ("(a+b)*abb", "aababb"),
]

REFUSES = [
    ("a", ""), ("a", "aa"), ("ab", "b"), ("ab", "a"),
    ("a+b", "ab"), ("@", "a"), ("(ab)*", "aba"), ("(a+b)*abb", "abba"),
]


@pytest.mark.parametrize("expression, mot", ACCEPTES)
def test_mot_accepte(expression, mot):
    assert simuler(afd(expression), mot)


@pytest.mark.parametrize("expression, mot", REFUSES)
def test_mot_refuse(expression, mot):
    assert not simuler(afd(expression), mot)


def test_lettre_inconnue():
    with pytest.raises(ValueError):
        simuler(afd("a"), "z")


def test_refuse_un_afn():
    with pytest.raises(ValueError):
        simuler(construire("a+b"), "a")   # contient des ε-transitions


EXPRESSIONS = [
    "a", "ab", "a+b", "a*", "(a+b)*abb", "(ab)*",
    "a*b*", "(a+b)*", "a(b+a)*b", "((a+b)*a)*", "(a*b)*",
]
MOTS = ["".join(p) for n in range(7) for p in product("ab", repeat=n)]


@pytest.mark.parametrize("expression", EXPRESSIONS)
def test_comparaison_avec_re(expression):
    automate = afd(expression)
    mini = minimiser(automate)
    motif = re.compile(expression.replace("+", "|"))
    for mot in MOTS:
        attendu = motif.fullmatch(mot) is not None
        assert simuler(automate, mot) == attendu, f"AFD {expression!r} sur {mot!r}"
        assert simuler(mini, mot) == attendu, f"minimal {expression!r} sur {mot!r}"
def test_chemin_accepte():
    accepte, chemin = reconnaitre(afd("(a+b)*abb"), "babb")
    assert accepte
    assert chemin == [
        Configuration(0, "babb"),
        Configuration(2, "abb"),
        Configuration(1, "bb"),
        Configuration(3, "b"),
        Configuration(4, ""),
    ]


def test_chemin_rejet_etat_non_final():
    accepte, chemin = reconnaitre(afd("(a+b)*abb"), "abab")
    assert not accepte
    assert chemin == [
        Configuration(0, "abab"),
        Configuration(1, "bab"),
        Configuration(3, "ab"),
        Configuration(1, "b"),
        Configuration(3, ""),
    ]


def test_chemin_accepte_ab_etoile():
    accepte, chemin = reconnaitre(afd("ab*"), "abbb")
    assert accepte
    assert chemin == [
        Configuration(0, "abbb"),
        Configuration(1, "bbb"),
        Configuration(2, "bb"),
        Configuration(2, "b"),
        Configuration(2, ""),
    ]


def test_chemin_bloque_au_depart():
    accepte, chemin = reconnaitre(afd("ab*"), "ba")
    assert not accepte
    assert chemin == [Configuration(0, "ba")]


def test_chemin_bloque_au_milieu():
    accepte, chemin = reconnaitre(afd("ab"), "aa")
    assert not accepte
    assert chemin == [Configuration(0, "aa"), Configuration(1, "a")]


def test_mot_vide_accepte():
    accepte, chemin = reconnaitre(afd("a*"), "")
    assert accepte
    assert chemin == [Configuration(0, "")]


def test_mot_vide_refuse():
    accepte, chemin = reconnaitre(afd("a"), "")
    assert not accepte
    assert chemin == [Configuration(0, "")]


def test_reconnaitre_refuse_un_afn():
    with pytest.raises(ValueError):
        reconnaitre(construire("a+b"), "a")


def test_reconnaitre_lettre_inconnue():
    with pytest.raises(ValueError):
        reconnaitre(afd("a"), "z")


def test_lettre_inconnue_meme_apres_blocage():
    with pytest.raises(ValueError):
        reconnaitre(afd("a"), "bz")   # le calcul se bloque sur b, mais z est inconnue


@pytest.mark.parametrize("expression", EXPRESSIONS)
def test_chemin_valide(expression):
    automate = afd(expression)
    motif = re.compile(expression.replace("+", "|"))
    for mot in MOTS:
        accepte, chemin = reconnaitre(automate, mot)
        assert accepte == (motif.fullmatch(mot) is not None), f"{expression!r} sur {mot!r}"
        assert chemin[0] == Configuration(automate.initial, mot)
        for avant, apres in zip(chemin, chemin[1:]):
            assert apres.reste == avant.reste[1:]
            assert apres.etat in automate.cibles(avant.etat, avant.reste[0])
        if accepte:
            assert chemin[-1].reste == ""
            assert chemin[-1].etat in automate.finaux
def cause(expression, mot):
    automate = afd(expression)
    _, chemin = reconnaitre(automate, mot)
    return cause_du_resultat(automate, chemin)


def explication(expression, mot):
    automate = afd(expression)
    _, chemin = reconnaitre(automate, mot)
    return expliquer(automate, chemin)


def test_cause_accepte():
    assert cause("(a+b)*abb", "babb") == CAUSE_ACCEPTE


def test_cause_bloque():
    assert cause("ab", "aa") == CAUSE_BLOQUE


def test_cause_non_final():
    assert cause("(a+b)*abb", "abab") == CAUSE_NON_FINAL


def test_explication_accepte():
    assert explication("(a+b)*abb", "babb") == (
        "Mot accepté : tout le mot est lu et l'état q4 est final."
    )


def test_explication_bloque_au_milieu():
    assert explication("ab", "aa") == (
        "Le calcul est bloqué : depuis l'état q1, aucune transition pour la "
        "lettre 'a' (lettre 2 du mot). Lettres possibles depuis q1 : b."
    )


def test_explication_bloque_au_depart():
    assert explication("ab", "ba") == (
        "Le calcul est bloqué : depuis l'état q0, aucune transition pour la "
        "lettre 'b' (lettre 1 du mot). Lettres possibles depuis q0 : a."
    )


def test_explication_bloque_sans_transition_sortante():
    assert explication("ab", "abb") == (
        "Le calcul est bloqué : depuis l'état q2, aucune transition pour la "
        "lettre 'b' (lettre 3 du mot). L'état q2 n'a aucune transition sortante."
    )


def test_explication_non_final():
    assert explication("(a+b)*abb", "abab") == (
        "Tout le mot est lu, mais l'état q3 n'est pas final (états finaux : q4)."
    )


def test_explication_mot_vide_rejete():
    assert explication("a", "") == (
        "Tout le mot est lu, mais l'état q0 n'est pas final (états finaux : q1)."
    )


@pytest.mark.parametrize("expression", EXPRESSIONS)
def test_cause_coherente(expression):
    automate = afd(expression)
    for mot in MOTS:
        accepte, chemin = reconnaitre(automate, mot)
        cause_trouvee = cause_du_resultat(automate, chemin)
        assert (cause_trouvee == CAUSE_ACCEPTE) == accepte, f"{expression!r} sur {mot!r}"
        if cause_trouvee == CAUSE_BLOQUE:
            derniere = chemin[-1]
            assert not automate.cibles(derniere.etat, derniere.reste[0])
        assert expliquer(automate, chemin)