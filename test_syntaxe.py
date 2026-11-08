from syntaxe import est_reserve, est_symbole_valide


def test_reserves():
    for c in "()*+|.@ε":
        assert est_reserve(c)


def test_non_reserves():
    for c in "abz019":
        assert not est_reserve(c)


def test_symboles_valides():
    assert est_symbole_valide("a")
    assert est_symbole_valide("7")


def test_symboles_invalides():
    assert not est_symbole_valide("+")    # réservé
    assert not est_symbole_valide("ab")   # deux caractères
    assert not est_symbole_valide("")     # vide
    assert not est_symbole_valide(" ")    # espace