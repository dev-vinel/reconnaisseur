import pytest

from syntaxe import EPSILON
from automate import (
    Automate, Fragment, automate_symbole, automate_epsilon,
    automate_union, automate_concat, automate_etoile,
)


def automate_vide():
    return Automate(["a", "b"])


def test_etats_distincts():
    auto = automate_vide()
    e0 = auto.nouvel_etat()
    e1 = auto.nouvel_etat()
    assert e0 != e1
    assert auto.etats == {e0, e1}


def test_initial_et_finaux():
    auto = automate_vide()
    q0 = auto.nouvel_etat()
    q1 = auto.nouvel_etat()
    auto.definir_initial(q0)
    auto.ajouter_final(q1)
    assert auto.initial == q0
    assert auto.finaux == {q1}


def test_transition_simple():
    auto = automate_vide()
    q0, q1 = auto.nouvel_etat(), auto.nouvel_etat()
    auto.ajouter_transition(q0, "a", q1)
    assert auto.cibles(q0, "a") == {q1}


def test_transition_epsilon():
    auto = automate_vide()
    q0, q1 = auto.nouvel_etat(), auto.nouvel_etat()
    auto.ajouter_transition(q0, EPSILON, q1)
    assert auto.cibles(q0, EPSILON) == {q1}


def test_plusieurs_cibles():
    auto = automate_vide()
    q0, q1, q2 = auto.nouvel_etat(), auto.nouvel_etat(), auto.nouvel_etat()
    auto.ajouter_transition(q0, "a", q1)
    auto.ajouter_transition(q0, "a", q2)
    assert auto.cibles(q0, "a") == {q1, q2}


def test_cibles_vides():
    auto = automate_vide()
    q0 = auto.nouvel_etat()
    assert auto.cibles(q0, "a") == set()


def test_cibles_est_une_copie():
    auto = automate_vide()
    q0, q1 = auto.nouvel_etat(), auto.nouvel_etat()
    auto.ajouter_transition(q0, "a", q1)
    auto.cibles(q0, "a").add(99)
    assert auto.cibles(q0, "a") == {q1}


def test_doublon_ignore():
    auto = automate_vide()
    q0, q1 = auto.nouvel_etat(), auto.nouvel_etat()
    auto.ajouter_transition(q0, "a", q1)
    auto.ajouter_transition(q0, "a", q1)
    assert auto.liste_transitions() == [(q0, "a", q1)]


def test_symbole_inconnu():
    auto = automate_vide()
    q0, q1 = auto.nouvel_etat(), auto.nouvel_etat()
    with pytest.raises(ValueError):
        auto.ajouter_transition(q0, "z", q1)


def test_etat_inconnu_transition():
    auto = automate_vide()
    q0 = auto.nouvel_etat()
    with pytest.raises(ValueError):
        auto.ajouter_transition(q0, "a", 42)


def test_initial_inconnu():
    auto = automate_vide()
    with pytest.raises(ValueError):
        auto.definir_initial(5)


def test_final_inconnu():
    auto = automate_vide()
    with pytest.raises(ValueError):
        auto.ajouter_final(5)


def test_deterministe_vrai():
    auto = automate_vide()
    q0, q1 = auto.nouvel_etat(), auto.nouvel_etat()
    auto.ajouter_transition(q0, "a", q1)
    auto.ajouter_transition(q0, "b", q0)
    assert auto.est_deterministe()


def test_deterministe_faux_plusieurs_cibles():
    auto = automate_vide()
    q0, q1, q2 = auto.nouvel_etat(), auto.nouvel_etat(), auto.nouvel_etat()
    auto.ajouter_transition(q0, "a", q1)
    auto.ajouter_transition(q0, "a", q2)
    assert not auto.est_deterministe()


def test_deterministe_faux_epsilon():
    auto = automate_vide()
    q0, q1 = auto.nouvel_etat(), auto.nouvel_etat()
    auto.ajouter_transition(q0, EPSILON, q1)
    assert not auto.est_deterministe()


def test_liste_transitions_triee():
    auto = automate_vide()
    q0, q1 = auto.nouvel_etat(), auto.nouvel_etat()
    auto.ajouter_transition(q1, "b", q0)
    auto.ajouter_transition(q0, "a", q1)
    assert auto.liste_transitions() == [(0, "a", 1), (1, "b", 0)]
def test_fragment_symbole():
    auto = automate_vide()
    f = automate_symbole(auto, "a")
    assert f.debut != f.fin
    assert auto.etats == {f.debut, f.fin}
    assert auto.liste_transitions() == [(f.debut, "a", f.fin)]


def test_fragment_epsilon():
    auto = automate_vide()
    f = automate_epsilon(auto)
    assert f.debut != f.fin
    assert auto.etats == {f.debut, f.fin}
    assert auto.liste_transitions() == [(f.debut, EPSILON, f.fin)]


def test_symbole_hors_alphabet():
    auto = automate_vide()
    with pytest.raises(ValueError):
        automate_symbole(auto, "z")
    assert auto.etats == set()   # aucun état orphelin


def test_epsilon_refuse_comme_symbole():
    auto = automate_vide()
    with pytest.raises(ValueError):
        automate_symbole(auto, EPSILON)


def test_deux_fragments_independants():
    auto = automate_vide()
    f1 = automate_symbole(auto, "a")
    f2 = automate_symbole(auto, "b")
    assert len(auto.etats) == 4
    assert {f1.debut, f1.fin}.isdisjoint({f2.debut, f2.fin})
    assert len(auto.liste_transitions()) == 2


def test_aucune_transition_sortante_de_fin():
    auto = automate_vide()
    f = automate_symbole(auto, "a")
    g = automate_epsilon(auto)
    for symbole in ["a", "b", EPSILON]:
        assert auto.cibles(f.fin, symbole) == set()
        assert auto.cibles(g.fin, symbole) == set()


def test_determinisme_des_briques():
    auto1 = automate_vide()
    automate_symbole(auto1, "a")
    assert auto1.est_deterministe()

    auto2 = automate_vide()
    automate_epsilon(auto2)
    assert not auto2.est_deterministe()
def test_union_structure():
    auto = automate_vide()
    f1 = automate_symbole(auto, "a")
    f2 = automate_symbole(auto, "b")
    u = automate_union(auto, f1, f2)
    assert len(auto.etats) == 6
    anciens = {f1.debut, f1.fin, f2.debut, f2.fin}
    assert u.debut not in anciens
    assert u.fin not in anciens
    assert u.debut != u.fin
    assert auto.cibles(u.debut, EPSILON) == {f1.debut, f2.debut}
    assert auto.cibles(f1.fin, EPSILON) == {u.fin}
    assert auto.cibles(f2.fin, EPSILON) == {u.fin}


def test_union_transitions_exactes():
    auto = automate_vide()
    f1 = automate_symbole(auto, "a")
    f2 = automate_symbole(auto, "b")
    automate_union(auto, f1, f2)
    assert auto.liste_transitions() == [
        (0, "a", 1),
        (1, EPSILON, 5),
        (2, "b", 3),
        (3, EPSILON, 5),
        (4, EPSILON, 0),
        (4, EPSILON, 2),
    ]


def test_union_aucune_transition_sortante_de_fin():
    auto = automate_vide()
    f1 = automate_symbole(auto, "a")
    f2 = automate_symbole(auto, "b")
    u = automate_union(auto, f1, f2)
    for symbole in ["a", "b", EPSILON]:
        assert auto.cibles(u.fin, symbole) == set()


def test_union_avec_epsilon():
    auto = automate_vide()
    f1 = automate_symbole(auto, "a")
    f2 = automate_epsilon(auto)
    automate_union(auto, f1, f2)
    assert len(auto.etats) == 6
    assert len(auto.liste_transitions()) == 6


def test_union_imbriquee():
    auto = automate_vide()
    f1 = automate_symbole(auto, "a")
    f2 = automate_symbole(auto, "b")
    u1 = automate_union(auto, f1, f2)
    f3 = automate_symbole(auto, "a")
    u2 = automate_union(auto, u1, f3)
    assert len(auto.etats) == 10
    assert auto.cibles(u2.debut, EPSILON) == {u1.debut, f3.debut}


def test_union_non_deterministe():
    auto = automate_vide()
    f1 = automate_symbole(auto, "a")
    f2 = automate_symbole(auto, "b")
    automate_union(auto, f1, f2)
    assert not auto.est_deterministe()
def test_concat_structure():
    auto = automate_vide()
    f1 = automate_symbole(auto, "a")
    f2 = automate_symbole(auto, "b")
    c = automate_concat(auto, f1, f2)
    assert len(auto.etats) == 4          # aucun nouvel état
    assert c == Fragment(f1.debut, f2.fin)
    assert auto.cibles(f1.fin, EPSILON) == {f2.debut}


def test_concat_transitions_exactes():
    auto = automate_vide()
    f1 = automate_symbole(auto, "a")
    f2 = automate_symbole(auto, "b")
    automate_concat(auto, f1, f2)
    assert auto.liste_transitions() == [
        (0, "a", 1),
        (1, EPSILON, 2),
        (2, "b", 3),
    ]


def test_concat_aucune_transition_sortante_de_fin():
    auto = automate_vide()
    f1 = automate_symbole(auto, "a")
    f2 = automate_symbole(auto, "b")
    c = automate_concat(auto, f1, f2)
    for symbole in ["a", "b", EPSILON]:
        assert auto.cibles(c.fin, symbole) == set()


def test_concat_imbriquee():
    auto = automate_vide()
    f1 = automate_symbole(auto, "a")
    f2 = automate_symbole(auto, "b")
    c1 = automate_concat(auto, f1, f2)
    f3 = automate_symbole(auto, "a")
    c2 = automate_concat(auto, c1, f3)
    assert c2 == Fragment(0, 5)
    assert len(auto.etats) == 6
    assert auto.liste_transitions() == [
        (0, "a", 1),
        (1, EPSILON, 2),
        (2, "b", 3),
        (3, EPSILON, 4),
        (4, "a", 5),
    ]


def test_concat_avec_union():
    auto = automate_vide()
    f1 = automate_symbole(auto, "a")
    f2 = automate_symbole(auto, "b")
    u = automate_union(auto, f1, f2)
    f3 = automate_symbole(auto, "a")
    c = automate_concat(auto, u, f3)
    assert c == Fragment(u.debut, f3.fin)
    assert len(auto.etats) == 8
    assert auto.cibles(u.fin, EPSILON) == {f3.debut}


def test_concat_avec_epsilon():
    auto = automate_vide()
    f1 = automate_symbole(auto, "a")
    f2 = automate_epsilon(auto)
    automate_concat(auto, f1, f2)
    assert len(auto.etats) == 4
    assert auto.liste_transitions() == [
        (0, "a", 1),
        (1, EPSILON, 2),
        (2, EPSILON, 3),
    ]
def test_etoile_structure():
    auto = automate_vide()
    f = automate_symbole(auto, "a")
    s = automate_etoile(auto, f)
    assert len(auto.etats) == 4
    assert s.debut not in {f.debut, f.fin}
    assert s.fin not in {f.debut, f.fin}
    assert s.debut != s.fin
    assert auto.cibles(s.debut, EPSILON) == {f.debut, s.fin}
    assert auto.cibles(f.fin, EPSILON) == {f.debut, s.fin}


def test_etoile_transitions_exactes():
    auto = automate_vide()
    f = automate_symbole(auto, "a")
    automate_etoile(auto, f)
    assert auto.liste_transitions() == [
        (0, "a", 1),
        (1, EPSILON, 0),
        (1, EPSILON, 3),
        (2, EPSILON, 0),
        (2, EPSILON, 3),
    ]


def test_etoile_aucune_transition_entrante_dans_debut():
    auto = automate_vide()
    f = automate_symbole(auto, "a")
    s = automate_etoile(auto, f)
    assert all(cible != s.debut for (_, _, cible) in auto.liste_transitions())


def test_etoile_aucune_transition_sortante_de_fin():
    auto = automate_vide()
    f = automate_symbole(auto, "a")
    s = automate_etoile(auto, f)
    for symbole in ["a", "b", EPSILON]:
        assert auto.cibles(s.fin, symbole) == set()


def test_etoile_de_etoile():
    auto = automate_vide()
    f = automate_symbole(auto, "a")
    s1 = automate_etoile(auto, f)
    s2 = automate_etoile(auto, s1)
    assert len(auto.etats) == 6
    assert len(auto.liste_transitions()) == 9
    assert s2 == Fragment(4, 5)


def test_etoile_de_union():
    auto = automate_vide()
    f1 = automate_symbole(auto, "a")
    f2 = automate_symbole(auto, "b")
    u = automate_union(auto, f1, f2)
    s = automate_etoile(auto, u)
    assert len(auto.etats) == 8
    assert len(auto.liste_transitions()) == 10
    assert auto.cibles(s.debut, EPSILON) == {u.debut, s.fin}


def test_etoile_de_epsilon():
    auto = automate_vide()
    f = automate_epsilon(auto)
    automate_etoile(auto, f)
    assert len(auto.etats) == 4
    assert len(auto.liste_transitions()) == 5