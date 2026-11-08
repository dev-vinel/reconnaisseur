import pytest

from main import (
    construire_automates, demander_oui_non, saisir_expression_valide, main, lancer,
)

ALPHABET = ["a", "b"]


def simuler_saisies(monkeypatch, reponses):
    """Remplace input() par une suite de réponses prévues."""
    suite = iter(reponses)
    monkeypatch.setattr("builtins.input", lambda _: next(suite))


def test_construire_automates_classique():
    afn, afd, minimal = construire_automates("(a+b)*abb", ALPHABET)
    assert len(afn.etats) == 14
    assert len(afd.etats) == 5
    assert len(minimal.etats) == 4
    assert not afn.est_deterministe()
    assert afd.est_deterministe()
    assert minimal.est_deterministe()


def test_construire_refuse_expression_invalide():
    with pytest.raises(ValueError):
        construire_automates("a++b", ALPHABET)


def test_oui_non_oui(monkeypatch):
    simuler_saisies(monkeypatch, ["oui"])
    assert demander_oui_non("Question ?") is True


def test_oui_non_non(monkeypatch):
    simuler_saisies(monkeypatch, ["N"])
    assert demander_oui_non("Question ?") is False


def test_oui_non_redemande(monkeypatch, capsys):
    simuler_saisies(monkeypatch, ["peut-être", "o"])
    assert demander_oui_non("Question ?") is True
    assert "Réponds par o ou n." in capsys.readouterr().out


def test_expression_valide_redemande(monkeypatch, capsys):
    simuler_saisies(monkeypatch, ["a++b", "(a", "a+b"])
    assert saisir_expression_valide(ALPHABET) == "a+b"
    sortie = capsys.readouterr().out
    assert sortie.count("Erreur") == 2
    assert "Expression bien écrite." in sortie


def test_session_complete_acceptee(monkeypatch, capsys):
    simuler_saisies(monkeypatch, ["a b", "(a+b)*abb", "babb", "n", "n"])
    main()
    sortie = capsys.readouterr().out
    assert "Expression bien écrite." in sortie
    assert "--- AFN-ε (Thompson) ---" in sortie
    assert "--- AFD minimal ---" in sortie
    assert "(q0, babb) ⊢ (q0, abb) ⊢ (q1, bb) ⊢ (q2, b) ⊢ (q3, ε)" in sortie
    assert "Conclusion : mot accepté." in sortie
    assert "Au revoir." in sortie


def test_session_rejets(monkeypatch, capsys):
    simuler_saisies(monkeypatch, ["a b", "a++b", "a+b", "ab", "o", "", "n", "n"])
    main()
    sortie = capsys.readouterr().out
    assert "Erreur : Position 2" in sortie
    assert "n'a aucune transition sortante" in sortie     # mot "ab" : calcul bloqué
    assert "(q0, ε)" in sortie                            # mot vide
    assert "n'est pas final" in sortie
    assert sortie.count("Conclusion : mot rejeté.") == 2


def test_session_recommence(monkeypatch, capsys):
    simuler_saisies(monkeypatch, ["a", "a*", "aa", "n", "o", "b", "b", "b", "n", "n"])
    main()
    sortie = capsys.readouterr().out
    assert "Alphabet : {a}" in sortie
    assert "Alphabet : {b}" in sortie
    assert sortie.count("Au revoir.") == 1
def test_alphabet_vide_redemande(monkeypatch, capsys):
    simuler_saisies(monkeypatch, ["", "   ", "a", "a", "", "n", "n"])
    main()
    sortie = capsys.readouterr().out
    assert sortie.count("L'alphabet est vide.") == 2
    assert "états finaux : q1" in sortie
    assert "Au revoir." in sortie


def test_expression_vide_redemande(monkeypatch, capsys):
    simuler_saisies(monkeypatch, ["a b", "", "  ", "@", "", "n", "n"])
    main()
    sortie = capsys.readouterr().out
    assert sortie.count("l'expression est vide") == 2
    assert "Conclusion : mot accepté." in sortie      # mot vide, expression @


def test_expression_epsilon_mot_non_vide(monkeypatch, capsys):
    simuler_saisies(monkeypatch, ["a b", "ε", "a", "n", "n"])
    main()
    sortie = capsys.readouterr().out
    assert "(q0, a)" in sortie
    assert "Conclusion : mot rejeté." in sortie
    assert "L'état q0 n'a aucune transition sortante." in sortie


def test_alphabet_un_symbole(monkeypatch, capsys):
    simuler_saisies(monkeypatch, ["a", "a*", "aaa", "o", "", "n", "n"])
    main()
    sortie = capsys.readouterr().out
    assert "Alphabet : {a}" in sortie
    assert "(q0, aaa) ⊢ (q0, aa) ⊢ (q0, a) ⊢ (q0, ε)" in sortie
    assert sortie.count("Conclusion : mot accepté.") == 2


def test_mot_hors_alphabet_redemande(monkeypatch, capsys):
    simuler_saisies(monkeypatch, ["a b", "ab", "abc", "ab", "n", "n"])
    main()
    sortie = capsys.readouterr().out
    assert "Position 3 : la lettre 'c' n'est pas dans l'alphabet." in sortie
    assert sortie.count("Conclusion : mot accepté.") == 1   # "abc" n'a pas été testé


@pytest.mark.parametrize("exception", [KeyboardInterrupt, EOFError])
def test_interruption(monkeypatch, capsys, exception):
    def interrompre(_):
        raise exception
    monkeypatch.setattr("builtins.input", interrompre)
    lancer()
    assert "Programme interrompu." in capsys.readouterr().out


def test_lancer_session_normale(monkeypatch, capsys):
    simuler_saisies(monkeypatch, ["a", "a", "a", "n", "n"])
    lancer()
    sortie = capsys.readouterr().out
    assert "(q0, a) ⊢ (q1, ε)" in sortie
    assert "Au revoir." in sortie
    assert "interrompu" not in sortie