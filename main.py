"""Point d'entrée : enchaîne les modules (tâche 8.1)."""

from saisie import saisir_alphabet, saisir_expression, saisir_mot
from validation import valider_expression, analyser_lexicalement, diagnostiquer
from preparation import rendre_concat_explicite, vers_postfixe
from automate import thompson
from determinisation import determiniser, minimiser
from reconnaissance import reconnaitre, expliquer
from affichage import afficher_table, afficher_trace


def demander_oui_non(question):
    """Pose une question fermée ; retourne True pour oui, False pour non."""
    while True:
        reponse = input(f"{question} (o/n) : ").strip().lower()
        if reponse in ("o", "oui"):
            return True
        if reponse in ("n", "non"):
            return False
        print("Réponds par o ou n.")


def saisir_expression_valide(alphabet):
    """Demande l'expression jusqu'à ce qu'elle soit bien écrite, puis la retourne."""
    while True:
        expression = saisir_expression()
        ok, _ = valider_expression(expression, alphabet)
        print(diagnostiquer(expression, alphabet))
        if ok:
            return expression


def construire_automates(expression, alphabet):
    """De l'expression validée à (AFN-ε, AFD, AFD minimal)."""
    ok, erreur = valider_expression(expression, alphabet)
    if not ok:
        raise ValueError(erreur)
    jetons, _ = analyser_lexicalement(expression, alphabet)
    postfixe = vers_postfixe(rendre_concat_explicite(jetons))
    afn = thompson(postfixe, alphabet)
    afd = determiniser(afn)
    return afn, afd, minimiser(afd)


def afficher_automates(afn, afd, minimal):
    """Affiche les trois tables de transitions."""
    print("\n--- AFN-ε (Thompson) ---")
    afficher_table(afn)
    print("\n--- AFD (sous-ensembles) ---")
    afficher_table(afd)
    print("\n--- AFD minimal ---")
    afficher_table(minimal)
    print()


def tester_mots(automate):
    """Teste des mots un par un, avec trace et explication, jusqu'à ce que l'utilisateur arrête."""
    while True:
        mot = saisir_mot(automate.alphabet)
        accepte, chemin = reconnaitre(automate, mot)
        afficher_trace(chemin, accepte)
        print(expliquer(automate, chemin))
        if not demander_oui_non("Tester un autre mot ?"):
            return


def main():
    """Boucle principale : alphabet, expression, automates, puis test de mots (tâche 8.1)."""
    print("=== Reconnaisseur de langage régulier ===")
    while True:
        alphabet = saisir_alphabet()
        expression = saisir_expression_valide(alphabet)
        afn, afd, minimal = construire_automates(expression, alphabet)
        afficher_automates(afn, afd, minimal)
        tester_mots(minimal)
        if not demander_oui_non("Construire un autre automate ?"):
            break
    print("Au revoir.")


def lancer():
    """Lance le programme ; Ctrl+C ou fin de saisie le ferment proprement (tâche 8.2)."""
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nProgramme interrompu.")


if __name__ == "__main__":
    lancer()