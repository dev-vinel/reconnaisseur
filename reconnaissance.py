"""Reconnaissance : tester si un mot est accepté par l'automate."""

from collections import namedtuple

# Configuration : situation du calcul à un instant donné
Configuration = namedtuple("Configuration", ["etat", "reste"])


def reconnaitre(afd, mot):
    """Simule l'AFD sur le mot ; retourne (accepté, chemin) (tâches 7.2 et 7.3).

    Le chemin est la liste des configurations (état, mot restant), de la
    configuration de départ jusqu'à la dernière atteinte. Si le calcul est
    bloqué, le dernier reste n'est pas vide.
    """
    if not afd.est_deterministe():
        raise ValueError("reconnaitre attend un AFD (sans ε, un seul choix par lettre).")
    for lettre in mot:
        if lettre not in afd.alphabet:
            raise ValueError(f"Lettre inconnue : {lettre}")

    etat = afd.initial
    chemin = [Configuration(etat, mot)]
    for i, lettre in enumerate(mot):
        cibles = afd.cibles(etat, lettre)
        if not cibles:
            return False, chemin          # calcul bloqué
        (etat,) = cibles                  # AFD : exactement une cible
        chemin.append(Configuration(etat, mot[i + 1:]))
    return etat in afd.finaux, chemin


def simuler(afd, mot):
    """True si le mot est accepté (tâche 7.2) ; ignore le chemin."""
    accepte, _ = reconnaitre(afd, mot)
    return accepte
CAUSE_ACCEPTE = "accepte"
CAUSE_BLOQUE = "bloque"
CAUSE_NON_FINAL = "non_final"


def cause_du_resultat(afd, chemin):
    """Retourne CAUSE_ACCEPTE, CAUSE_BLOQUE ou CAUSE_NON_FINAL (tâche 7.5)."""
    derniere = chemin[-1]
    if derniere.reste:
        return CAUSE_BLOQUE
    if derniere.etat in afd.finaux:
        return CAUSE_ACCEPTE
    return CAUSE_NON_FINAL


def expliquer(afd, chemin):
    """Phrase qui explique pourquoi le mot est accepté ou rejeté (tâche 7.5)."""
    derniere = chemin[-1]
    etat = derniere.etat
    cause = cause_du_resultat(afd, chemin)

    if cause == CAUSE_ACCEPTE:
        return f"Mot accepté : tout le mot est lu et l'état q{etat} est final."

    if cause == CAUSE_BLOQUE:
        lettre = derniere.reste[0]
        position = len(chemin)    # la lettre bloquante est la n-ième du mot
        message = (
            f"Le calcul est bloqué : depuis l'état q{etat}, aucune transition "
            f"pour la lettre '{lettre}' (lettre {position} du mot)."
        )
        possibles = [s for s in afd.alphabet if afd.cibles(etat, s)]
        if possibles:
            return message + f" Lettres possibles depuis q{etat} : {', '.join(possibles)}."
        return message + f" L'état q{etat} n'a aucune transition sortante."

    finaux = ", ".join(f"q{e}" for e in sorted(afd.finaux)) or "aucun"
    return (
        f"Tout le mot est lu, mais l'état q{etat} n'est pas final "
        f"(états finaux : {finaux})."
    )