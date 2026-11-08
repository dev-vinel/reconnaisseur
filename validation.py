"""Validation : vérifier qu'une expression est bien écrite."""

from collections import namedtuple

from syntaxe import (
    UNION, UNION_ALT, ETOILE, CONCAT,
    PAR_OUVRANTE, PAR_FERMANTE, EPSILON, EPSILON_ALT,
)

# Types de jetons
TYPE_SYMBOLE = "SYMBOLE"
TYPE_UNION = "UNION"
TYPE_ETOILE = "ETOILE"
TYPE_PAR_OUV = "PAR_OUV"
TYPE_PAR_FERM = "PAR_FERM"
TYPE_EPSILON = "EPSILON"

Jeton = namedtuple("Jeton", ["type", "valeur", "position"])


def analyser_lexicalement(expression, alphabet):
    """Découpe l'expression en jetons (tâche 3.1).

    Retourne (jetons, "") ou (None, message d'erreur).
    Les positions commencent à 1.
    """
    jetons = []

    for i, c in enumerate(expression, start=1):
        if c in (UNION, UNION_ALT):
            jetons.append(Jeton(TYPE_UNION, UNION, i))
        elif c == ETOILE:
            jetons.append(Jeton(TYPE_ETOILE, ETOILE, i))
        elif c == PAR_OUVRANTE:
            jetons.append(Jeton(TYPE_PAR_OUV, PAR_OUVRANTE, i))
        elif c == PAR_FERMANTE:
            jetons.append(Jeton(TYPE_PAR_FERM, PAR_FERMANTE, i))
        elif c in (EPSILON, EPSILON_ALT):
            jetons.append(Jeton(TYPE_EPSILON, EPSILON, i))
        elif c == CONCAT:
            return None, (
                f"Position {i} : le caractère '{c}' est réservé "
                "à l'usage interne."
            )
        elif c in alphabet:
            jetons.append(Jeton(TYPE_SYMBOLE, c, i))
        else:
            return None, (
                f"Position {i} : le caractère '{c}' "
                "n'est pas dans l'alphabet."
            )

    return jetons, ""
def controler_parentheses(jetons):
    """Vérifie que les parenthèses sont équilibrées (tâche 3.2).

    Retourne (True, "") ou (False, message d'erreur).
    """
    pile = []  # positions des "(" non encore fermées

    for jeton in jetons:
        if jeton.type == TYPE_PAR_OUV:
            pile.append(jeton.position)
        elif jeton.type == TYPE_PAR_FERM:
            if not pile:
                return False, (
                    f"Position {jeton.position} : parenthèse fermante ')' "
                    "sans parenthèse ouvrante correspondante."
                )
            pile.pop()

    if pile:
        return False, (
            f"Position {pile[-1]} : parenthèse ouvrante '(' jamais fermée."
        )

    return True, ""
# Jetons après lesquels un opérande est "complet"
FIN_OPERANDE = {TYPE_SYMBOLE, TYPE_EPSILON, TYPE_PAR_FERM, TYPE_ETOILE}
# Jetons par lesquels un opérande peut commencer
DEBUT_OPERANDE = {TYPE_SYMBOLE, TYPE_EPSILON, TYPE_PAR_OUV}


def controler_operateurs(jetons):
    """Vérifie le placement des opérateurs (tâche 3.3).

    Retourne (True, "") ou (False, message d'erreur).
    """
    for i, jeton in enumerate(jetons):
        precedent = jetons[i - 1] if i > 0 else None
        suivant = jetons[i + 1] if i + 1 < len(jetons) else None

        if jeton.type == TYPE_ETOILE:
            if precedent is None or precedent.type not in FIN_OPERANDE:
                return False, (
                    f"Position {jeton.position} : l'étoile '*' "
                    "n'a aucun élément à répéter."
                )

        elif jeton.type == TYPE_UNION:
            if precedent is None or precedent.type not in FIN_OPERANDE:
                return False, (
                    f"Position {jeton.position} : l'union '+' "
                    "n'a pas d'opérande à gauche."
                )
            if suivant is None or suivant.type not in DEBUT_OPERANDE:
                return False, (
                    f"Position {jeton.position} : l'union '+' "
                    "n'a pas d'opérande à droite."
                )

        elif jeton.type == TYPE_PAR_FERM:
            if precedent is not None and precedent.type == TYPE_PAR_OUV:
                return False, (
                    f"Position {precedent.position} : "
                    "parenthèses vides '()'."
                )

    return True, ""


def valider_expression(expression, alphabet):
    """Enchaîne les contrôles ; s'arrête à la première erreur (tâche 3.4).

    Retourne (True, "") ou (False, message d'erreur).
    """
    jetons, erreur = analyser_lexicalement(expression, alphabet)
    if jetons is None:
        return False, erreur

    for controle in (controler_parentheses, controler_operateurs):
        ok, erreur = controle(jetons)
        if not ok:
            return False, erreur

    return True, ""


def extraire_position(message):
    """Lit N dans un message 'Position N : ...', ou retourne None."""
    if not message.startswith("Position "):
        return None
    mot = message.split()[1]
    return int(mot) if mot.isdigit() else None


def diagnostiquer(expression, alphabet):
    """Retourne le texte à afficher : confirmation ou erreur avec repère."""
    ok, erreur = valider_expression(expression, alphabet)
    if ok:
        return "Expression bien écrite."

    lignes = ["Erreur : " + erreur]
    position = extraire_position(erreur)
    if position is not None:
        lignes.append("  " + expression)
        lignes.append("  " + " " * (position - 1) + "^")
    return "\n".join(lignes)