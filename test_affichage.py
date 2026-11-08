from syntaxe import EPSILON
from validation import analyser_lexicalement
from preparation import rendre_concat_explicite, vers_postfixe
from automate import Automate, thompson
from determinisation import determiniser, minimiser
from reconnaissance import Configuration, reconnaitre
from affichage import (
    formater_ensemble, table_en_texte, afficher_table,
    formater_configuration, trace_en_texte, afficher_trace,
    automate_en_dot, ecrire_dot,
)


def petit_automate(symbole):
    """Deux états : 0 --symbole--> 1, initial 0, final 1."""
    auto = Automate(["a"])
    q0, q1 = auto.nouvel_etat(), auto.nouvel_etat()
    auto.definir_initial(q0)
    auto.ajouter_final(q1)
    auto.ajouter_transition(q0, symbole, q1)
    return auto


def test_formater_ensemble_vide():
    assert formater_ensemble(set()) == "-"


def test_formater_ensemble_trie():
    assert formater_ensemble({3, 1, 2}) == "{1,2,3}"


def test_table_symbole_exacte():
    attendu = "\n".join([
        "Alphabet : {a}",
        "États    : {0,1}",
        "Initial  : 0",
        "Finaux   : {1}",
        "",
        "état | a",
        "-----+----",
        "→  0 | {1}",
        " * 1 | -",
        "",
        "→ = état initial, * = état final",
    ])
    assert table_en_texte(petit_automate("a")) == attendu


def test_table_avec_colonne_epsilon():
    attendu = "\n".join([
        "Alphabet : {a}",
        "États    : {0,1}",
        "Initial  : 0",
        "Finaux   : {1}",
        "",
        "état | a | ε",
        "-----+---+----",
        "→  0 | - | {1}",
        " * 1 | - | -",
        "",
        "→ = état initial, * = état final",
    ])
    assert table_en_texte(petit_automate(EPSILON)) == attendu


def test_etat_initial_et_final():
    auto = Automate(["a"])
    q = auto.nouvel_etat()
    auto.definir_initial(q)
    auto.ajouter_final(q)
    assert "→* 0" in table_en_texte(auto)


def test_plusieurs_cibles():
    auto = Automate(["a"])
    q0, q1, q2 = auto.nouvel_etat(), auto.nouvel_etat(), auto.nouvel_etat()
    auto.ajouter_transition(q0, "a", q1)
    auto.ajouter_transition(q0, "a", q2)
    assert "{1,2}" in table_en_texte(auto)


def test_table_de_thompson():
    jetons, _ = analyser_lexicalement("ab", ["a", "b"])
    auto = thompson(vers_postfixe(rendre_concat_explicite(jetons)), ["a", "b"])
    table = table_en_texte(auto)
    assert "Initial  : 0" in table
    assert "Finaux   : {3}" in table
    assert "ε" in table


def test_afficher_table_imprime(capsys):
    auto = petit_automate("a")
    afficher_table(auto)
    assert capsys.readouterr().out == table_en_texte(auto) + "\n"
def afd_de(expression):
    """De l'expression à l'AFD (alphabet {a, b})."""
    jetons, _ = analyser_lexicalement(expression, ["a", "b"])
    return determiniser(thompson(vers_postfixe(rendre_concat_explicite(jetons)), ["a", "b"]))


def test_formater_configuration():
    assert formater_configuration(Configuration(1, "bb")) == "(q1, bb)"


def test_formater_configuration_reste_vide():
    assert formater_configuration(Configuration(4, "")) == "(q4, ε)"


def test_trace_acceptee():
    accepte, chemin = reconnaitre(afd_de("(a+b)*abb"), "babb")
    assert trace_en_texte(chemin, accepte) == (
        "(q0, babb) ⊢ (q2, abb) ⊢ (q1, bb) ⊢ (q3, b) ⊢ (q4, ε)\n"
        "Conclusion : mot accepté."
    )


def test_trace_rejet_etat_non_final():
    accepte, chemin = reconnaitre(afd_de("(a+b)*abb"), "abab")
    assert trace_en_texte(chemin, accepte) == (
        "(q0, abab) ⊢ (q1, bab) ⊢ (q3, ab) ⊢ (q1, b) ⊢ (q3, ε)\n"
        "Conclusion : mot rejeté."
    )


def test_trace_calcul_bloque():
    accepte, chemin = reconnaitre(afd_de("ab"), "aa")
    assert trace_en_texte(chemin, accepte) == (
        "(q0, aa) ⊢ (q1, a)\n"
        "Conclusion : mot rejeté."
    )


def test_trace_mot_vide():
    accepte, chemin = reconnaitre(afd_de("a*"), "")
    assert trace_en_texte(chemin, accepte) == (
        "(q0, ε)\n"
        "Conclusion : mot accepté."
    )


def test_trace_un_symbole_par_lettre():
    accepte, chemin = reconnaitre(afd_de("(a+b)*abb"), "abab")
    premiere_ligne = trace_en_texte(chemin, accepte).split("\n")[0]
    assert premiere_ligne.count("⊢") == 4


def test_afficher_trace_imprime(capsys):
    accepte, chemin = reconnaitre(afd_de("a*"), "aa")
    afficher_trace(chemin, accepte)
    assert capsys.readouterr().out == trace_en_texte(chemin, accepte) + "\n"
def test_dot_symbole():
    assert automate_en_dot(petit_automate("a")) == "\n".join([
        "digraph automate {",
        "    rankdir=LR;",
        "    node [shape=circle];",
        "    debut [shape=point];",
        "    q1 [shape=doublecircle];",
        "    debut -> q0;",
        '    q0 -> q1 [label="a"];',
        "}",
    ])


def test_dot_epsilon():
    assert '    q0 -> q1 [label="ε"];' in automate_en_dot(petit_automate(EPSILON))


def test_dot_fusion_des_etiquettes():
    auto = Automate(["a", "b"])
    q0, q1 = auto.nouvel_etat(), auto.nouvel_etat()
    auto.ajouter_transition(q0, "b", q1)    # b ajouté avant a : l'ordre de l'alphabet doit gagner
    auto.ajouter_transition(q0, "a", q1)
    texte = automate_en_dot(auto)
    assert '    q0 -> q1 [label="a,b"];' in texte
    assert "debut" not in texte             # pas d'état initial défini


def test_dot_etat_initial_et_final():
    auto = Automate(["a"])
    q = auto.nouvel_etat()
    auto.definir_initial(q)
    auto.ajouter_final(q)
    assert automate_en_dot(auto) == "\n".join([
        "digraph automate {",
        "    rankdir=LR;",
        "    node [shape=circle];",
        "    debut [shape=point];",
        "    q0 [shape=doublecircle];",
        "    debut -> q0;",
        "}",
    ])


def test_dot_automate_minimal_classique():
    minimal = minimiser(afd_de("(a+b)*abb"))
    assert automate_en_dot(minimal) == "\n".join([
        "digraph automate {",
        "    rankdir=LR;",
        "    node [shape=circle];",
        "    debut [shape=point];",
        "    q3 [shape=doublecircle];",
        "    debut -> q0;",
        '    q0 -> q0 [label="b"];',
        '    q0 -> q1 [label="a"];',
        '    q1 -> q1 [label="a"];',
        '    q1 -> q2 [label="b"];',
        '    q2 -> q1 [label="a"];',
        '    q2 -> q3 [label="b"];',
        '    q3 -> q0 [label="b"];',
        '    q3 -> q1 [label="a"];',
        "}",
    ])


def test_dot_afn_avec_epsilon():
    jetons, _ = analyser_lexicalement("a+b", ["a", "b"])
    afn = thompson(vers_postfixe(rendre_concat_explicite(jetons)), ["a", "b"])
    texte = automate_en_dot(afn)
    assert texte.count('label="ε"') == 4
    assert texte.count("->") == 7           # 6 transitions + la flèche d'entrée


def test_dot_structure_generale():
    texte = automate_en_dot(afd_de("(a+b)*abb"))
    assert texte.startswith("digraph automate {")
    assert texte.endswith("}")
    assert texte.count("{") == texte.count("}") == 1


def test_ecrire_dot(tmp_path):
    auto = petit_automate("a")
    fichier = tmp_path / "essai.dot"
    ecrire_dot(auto, fichier)
    assert fichier.read_text(encoding="utf-8") == automate_en_dot(auto) + "\n"


def test_ecrire_dot_conserve_epsilon(tmp_path):
    fichier = tmp_path / "epsilon.dot"
    ecrire_dot(petit_automate(EPSILON), fichier)
    assert "ε" in fichier.read_text(encoding="utf-8")