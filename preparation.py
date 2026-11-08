"""Préparation : rendre l'expression exploitable par la construction."""

from syntaxe import CONCAT, PRIORITES
from validation import (
    Jeton, FIN_OPERANDE, DEBUT_OPERANDE,
    TYPE_SYMBOLE, TYPE_EPSILON, TYPE_UNION, TYPE_ETOILE,
    TYPE_PAR_OUV, TYPE_PAR_FERM,
)

TYPE_CONCAT = "CONCAT"


def rendre_concat_explicite(jetons):
    """Insère un jeton '.' entre deux opérandes voisins (tâche 4.1).

    Suppose une expression déjà validée. Retourne une nouvelle liste.
    """
    resultat = []
    for i, jeton in enumerate(jetons):
        if i > 0:
            gauche = jetons[i - 1]
            if gauche.type in FIN_OPERANDE and jeton.type in DEBUT_OPERANDE:
                resultat.append(Jeton(TYPE_CONCAT, CONCAT, jeton.position))
        resultat.append(jeton)
    return resultat


def jetons_en_texte(jetons):
    """Recolle les valeurs des jetons en une chaîne, pour affichage et tests."""
    return "".join(jeton.valeur for jeton in jetons)


def vers_postfixe(jetons):
    """Convertit les jetons en forme postfixée, algorithme de la gare de triage (tâche 4.2).

    Suppose une expression validée, avec concaténation explicite.
    Retourne une liste de jetons sans parenthèses.
    """
    sortie = []
    pile = []  # opérateurs et parenthèses ouvrantes en attente

    for jeton in jetons:
        if jeton.type in (TYPE_SYMBOLE, TYPE_EPSILON):
            sortie.append(jeton)

        elif jeton.type == TYPE_ETOILE:
            # postfixe : agit sur l'opérande déjà en sortie
            sortie.append(jeton)

        elif jeton.type in (TYPE_UNION, TYPE_CONCAT):
            while (
                pile
                and pile[-1].type != TYPE_PAR_OUV
                and PRIORITES[pile[-1].valeur] >= PRIORITES[jeton.valeur]
            ):
                sortie.append(pile.pop())
            pile.append(jeton)

        elif jeton.type == TYPE_PAR_OUV:
            pile.append(jeton)

        elif jeton.type == TYPE_PAR_FERM:
            while pile[-1].type != TYPE_PAR_OUV:
                sortie.append(pile.pop())
            pile.pop()  # jette la parenthèse ouvrante

    while pile:
        sortie.append(pile.pop())

    return sortie