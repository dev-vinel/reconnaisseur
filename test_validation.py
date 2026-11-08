from validation import (
    analyser_lexicalement,
    controler_parentheses,
    controler_operateurs,
    valider_expression,
    extraire_position,
    diagnostiquer,
    TYPE_SYMBOLE, TYPE_UNION, TYPE_ETOILE,
    TYPE_PAR_OUV, TYPE_PAR_FERM, TYPE_EPSILON,
)

ALPHABET = ["a", "b"]


def simplifier(jetons):
    """Ne garde que (type, valeur) pour comparer plus facilement."""
    return [(j.type, j.valeur) for j in jetons]


def test_jetons_simples():
    jetons, erreur = analyser_lexicalement("(a+b)*", ALPHABET)
    assert erreur == ""
    assert simplifier(jetons) == [
        (TYPE_PAR_OUV, "("),
        (TYPE_SYMBOLE, "a"),
        (TYPE_UNION, "+"),
        (TYPE_SYMBOLE, "b"),
        (TYPE_PAR_FERM, ")"),
        (TYPE_ETOILE, "*"),
    ]


def test_union_alternative():
    jetons, _ = analyser_lexicalement("a|b", ALPHABET)
    assert simplifier(jetons)[1] == (TYPE_UNION, "+")


def test_epsilon_arobase():
    jetons, _ = analyser_lexicalement("@", ALPHABET)
    assert simplifier(jetons) == [(TYPE_EPSILON, "ε")]


def test_positions():
    jetons, _ = analyser_lexicalement("ab*", ALPHABET)
    assert [j.position for j in jetons] == [1, 2, 3]


def test_hors_alphabet():
    jetons, erreur = analyser_lexicalement("a+c", ALPHABET)
    assert jetons is None
    assert "Position 3" in erreur
    assert "'c'" in erreur


def test_casse_importante():
    jetons, erreur = analyser_lexicalement("A", ALPHABET)
    assert jetons is None
    assert "Position 1" in erreur


def test_point_interdit():
    jetons, erreur = analyser_lexicalement("a.b", ALPHABET)
    assert jetons is None
    assert "Position 2" in erreur
    assert "réservé" in erreur
def parentheses(expression):
    """Raccourci : analyse lexicale puis contrôle des parenthèses."""
    jetons, _ = analyser_lexicalement(expression, ALPHABET)
    return controler_parentheses(jetons)


def test_parentheses_valides():
    assert parentheses("(a+b)*") == (True, "")
    assert parentheses("((a)b)") == (True, "")


def test_sans_parentheses():
    assert parentheses("ab*") == (True, "")


def test_ouvrante_jamais_fermee():
    ok, erreur = parentheses("(a+b")
    assert not ok
    assert "Position 1" in erreur
    assert "jamais fermée" in erreur


def test_fermante_en_trop():
    ok, erreur = parentheses("a+b)")
    assert not ok
    assert "Position 4" in erreur


def test_fermante_avant_ouvrante():
    ok, erreur = parentheses(")(")
    assert not ok
    assert "Position 1" in erreur


def test_derniere_ouvrante_signalee():
    ok, erreur = parentheses("(a(b")
    assert not ok
    assert "Position 3" in erreur


def test_fermante_en_trop_apres_equilibre():
    ok, erreur = parentheses("(a))")
    assert not ok
    assert "Position 4" in erreur


def test_parentheses_vides_acceptees_ici():
    assert parentheses("()") == (True, "")
def operateurs(expression):
    """Raccourci : analyse lexicale puis contrôle des opérateurs."""
    jetons, _ = analyser_lexicalement(expression, ALPHABET)
    return controler_operateurs(jetons)


def test_operateurs_valides():
    for expr in ["a", "ab*", "(a+b)*abb", "a**", "a+ε", "(a)(b)", "ε*", "a*+b*"]:
        assert operateurs(expr) == (True, ""), expr


def test_etoile_en_debut():
    ok, erreur = operateurs("*a")
    assert not ok
    assert "Position 1" in erreur
    assert "étoile" in erreur


def test_etoile_apres_ouvrante():
    ok, erreur = operateurs("(*a)")
    assert not ok
    assert "Position 2" in erreur
    assert "étoile" in erreur


def test_union_en_debut():
    ok, erreur = operateurs("+a")
    assert not ok
    assert "Position 1" in erreur
    assert "gauche" in erreur


def test_union_en_fin():
    ok, erreur = operateurs("a+")
    assert not ok
    assert "Position 2" in erreur
    assert "droite" in erreur


def test_union_double():
    ok, erreur = operateurs("a++b")
    assert not ok
    assert "Position 2" in erreur
    assert "droite" in erreur


def test_union_apres_ouvrante():
    ok, erreur = operateurs("(+a)")
    assert not ok
    assert "Position 2" in erreur
    assert "gauche" in erreur


def test_union_avant_fermante():
    ok, erreur = operateurs("(a+)")
    assert not ok
    assert "Position 3" in erreur
    assert "droite" in erreur


def test_parentheses_vides():
    ok, erreur = operateurs("a()")
    assert not ok
    assert "Position 2" in erreur
    assert "vides" in erreur
def test_valider_expressions_correctes():
    for expr in ["a", "(a+b)*abb", "ε", "@", "(ab)*+ε", "a|b"]:
        assert valider_expression(expr, ALPHABET) == (True, ""), expr


def test_valider_erreur_lexicale():
    ok, erreur = valider_expression("a+c", ALPHABET)
    assert not ok
    assert "Position 3" in erreur


def test_valider_erreur_parentheses():
    ok, erreur = valider_expression("(a+b", ALPHABET)
    assert not ok
    assert "Position 1" in erreur


def test_valider_erreur_operateurs():
    ok, erreur = valider_expression("a++b", ALPHABET)
    assert not ok
    assert "Position 2" in erreur


def test_parentheses_avant_operateurs():
    ok, erreur = valider_expression("(+a", ALPHABET)
    assert not ok
    assert "jamais fermée" in erreur


def test_lexical_avant_parentheses():
    ok, erreur = valider_expression("(a+c", ALPHABET)
    assert not ok
    assert "Position 4" in erreur
    assert "alphabet" in erreur


def test_extraire_position():
    assert extraire_position("Position 12 : x") == 12
    assert extraire_position("autre chose") is None


def test_diagnostic_valide():
    assert diagnostiquer("(a+b)*", ALPHABET) == "Expression bien écrite."


def test_diagnostic_erreur():
    lignes = diagnostiquer("a++b", ALPHABET).split("\n")
    assert lignes[0].startswith("Erreur : Position 2")
    assert lignes[1] == "  a++b"
    assert lignes[2] == "   ^"