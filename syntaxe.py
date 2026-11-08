"""Syntaxe : opérateurs, symboles réservés et priorités des expressions régulières."""

# Opérateurs
UNION = "+"
UNION_ALT = "|"          # accepté aussi, même sens que "+"
ETOILE = "*"
CONCAT = "."             # utilisé en interne seulement (tâche 4.1)

# Parenthèses
PAR_OUVRANTE = "("
PAR_FERMANTE = ")"

# Mot vide : ε ou @ (si le clavier n'a pas ε)
EPSILON = "ε"
EPSILON_ALT = "@"

# Tous les caractères qui ont un sens spécial
SYMBOLES_RESERVES = {
    UNION, UNION_ALT, ETOILE, CONCAT,
    PAR_OUVRANTE, PAR_FERMANTE,
    EPSILON, EPSILON_ALT,
}

# Priorité des opérateurs : plus le nombre est grand, plus on "colle" fort
PRIORITES = {
    UNION: 1,
    CONCAT: 2,
    ETOILE: 3,
}


def est_reserve(caractere):
    """Retourne True si le caractère a un sens spécial."""
    return caractere in SYMBOLES_RESERVES


def est_symbole_valide(caractere):
    """Un symbole d'alphabet valide : 1 caractère, lettre ou chiffre, non réservé."""
    return (
        len(caractere) == 1
        and caractere.isalnum()
        and not est_reserve(caractere)
    )