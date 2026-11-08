from saisie import (
    analyser_alphabet,
    saisir_alphabet,
    nettoyer_expression,
    saisir_expression,
    analyser_mot,
    saisir_mot,
)


def test_alphabet_valide():
    assert analyser_alphabet("a b") == (["a", "b"], "")
    assert analyser_alphabet("a,b") == (["a", "b"], "")
    assert analyser_alphabet("ab") == (["a", "b"], "")
    assert analyser_alphabet("a") == (["a"], "")


def test_alphabet_vide():
    alphabet, erreur = analyser_alphabet("   ")
    assert alphabet is None
    assert "vide" in erreur


def test_symbole_reserve():
    alphabet, erreur = analyser_alphabet("a +")
    assert alphabet is None
    assert "+" in erreur


def test_doublon():
    alphabet, erreur = analyser_alphabet("a b a")
    assert alphabet is None
    assert "double" in erreur


def test_saisir_redemande(monkeypatch):
    reponses = iter(["", "a +", "a b"])
    monkeypatch.setattr("builtins.input", lambda _: next(reponses))
    assert saisir_alphabet() == ["a", "b"]


def test_nettoyer_espaces():
    assert nettoyer_expression("( a + b ) *") == "(a+b)*"


def test_nettoyer_tabulations():
    assert nettoyer_expression("a\tb\n") == "ab"


def test_nettoyer_vide():
    assert nettoyer_expression("   ") == ""


def test_saisir_expression(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: " a b* ")
    assert saisir_expression() == "ab*"


def test_saisir_expression_redemande(monkeypatch):
    reponses = iter(["", "   ", "(a+b)*abb"])
    monkeypatch.setattr("builtins.input", lambda _: next(reponses))
    assert saisir_expression() == "(a+b)*abb"
ALPHA = ["a", "b"]


def test_mot_valide():
    assert analyser_mot("abba", ALPHA) == ("abba", "")


def test_mot_avec_espaces():
    assert analyser_mot(" a b ", ALPHA) == ("ab", "")


def test_mot_vide_par_entree():
    assert analyser_mot("", ALPHA) == ("", "")


def test_mot_espaces_seuls():
    assert analyser_mot("   ", ALPHA) == ("", "")


def test_mot_vide_epsilon_et_arobase():
    assert analyser_mot("ε", ALPHA) == ("", "")
    assert analyser_mot("@", ALPHA) == ("", "")


def test_mot_hors_alphabet():
    mot, erreur = analyser_mot("abc", ALPHA)
    assert mot is None
    assert "Position 3" in erreur
    assert "'c'" in erreur


def test_mot_casse_importante():
    mot, erreur = analyser_mot("A", ALPHA)
    assert mot is None
    assert "Position 1" in erreur


def test_epsilon_melange():
    mot, erreur = analyser_mot("aε", ALPHA)
    assert mot is None
    assert "Position 2" in erreur
    assert "seul" in erreur


def test_alphabet_un_symbole():
    assert analyser_mot("aaa", ["a"]) == ("aaa", "")


def test_saisir_mot(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "abb")
    assert saisir_mot(ALPHA) == "abb"


def test_saisir_mot_redemande(monkeypatch):
    reponses = iter(["abc", "a+b", "ab"])
    monkeypatch.setattr("builtins.input", lambda _: next(reponses))
    assert saisir_mot(ALPHA) == "ab"


def test_saisir_mot_vide(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert saisir_mot(ALPHA) == ""