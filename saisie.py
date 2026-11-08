"""Saisie : lecture et nettoyage des entrées de l'utilisateur."""

from syntaxe import est_reserve, est_symbole_valide, EPSILON, EPSILON_ALT

SEPARATEURS = " ,\t"


def analyser_alphabet(texte):
    """Analyse un texte et retourne (alphabet, "") ou (None, message d'erreur).

    Les espaces et les virgules sont ignorés ; chaque autre caractère
    est un symbole de l'alphabet.
    """
    symboles = [c for c in texte if c not in SEPARATEURS]

    if not symboles:
        return None, "L'alphabet est vide."

    for c in symboles:
        if est_reserve(c):
            return None, f"Le symbole '{c}' est réservé."
        if not est_symbole_valide(c):
            return None, f"Le symbole '{c}' n'est pas valide (lettre ou chiffre attendu)."

    doublons = sorted({c for c in symboles if symboles.count(c) > 1})
    if doublons:
        return None, f"Symbole(s) en double : {', '.join(doublons)}."

    return symboles, ""


def saisir_alphabet():
    """Demande l'alphabet jusqu'à ce qu'il soit valide, puis le retourne (tâche 2.1)."""
    while True:
        texte = input("Alphabet (ex : a b ou a,b) : ")
        alphabet, erreur = analyser_alphabet(texte)
        if alphabet is not None:
            return alphabet
        print("Erreur :", erreur)


def nettoyer_expression(texte):
    """Retire tous les espaces blancs (espaces, tabulations, retours à la ligne)."""
    return "".join(texte.split())


def saisir_expression():
    """Demande l'expression jusqu'à ce qu'elle soit non vide, puis la retourne (tâche 2.2)."""
    while True:
        texte = input("Expression régulière (ε ou @ pour le mot vide) : ")
        expression = nettoyer_expression(texte)
        if expression:
            return expression
        print("Erreur : l'expression est vide. Écris ε (ou @) pour le mot vide.")


def analyser_mot(texte, alphabet):
    """Analyse un mot saisi : retourne (mot, "") ou (None, message d'erreur).

    Le mot vide est permis : il est retourné sous la forme "" (tâche 7.1).
    """
    mot = nettoyer_expression(texte)
    if mot in (EPSILON, EPSILON_ALT):
        return "", ""

    for i, c in enumerate(mot, start=1):
        if c in (EPSILON, EPSILON_ALT):
            return None, (
                f"Position {i} : '{c}' représente le mot vide, "
                "il doit être écrit seul."
            )
        if c not in alphabet:
            return None, f"Position {i} : la lettre '{c}' n'est pas dans l'alphabet."

    return mot, ""


def saisir_mot(alphabet):
    """Demande un mot jusqu'à ce qu'il soit valide, puis le retourne (tâche 7.1)."""
    while True:
        texte = input("Mot à tester (Entrée, ε ou @ pour le mot vide) : ")
        mot, erreur = analyser_mot(texte, alphabet)
        if mot is not None:          # attention : "" est un mot valide
            return mot
        print("Erreur :", erreur)