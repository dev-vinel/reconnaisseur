"""Déterminisation (AFN-ε vers AFD) et minimisation de l'AFD."""

from collections import deque

from automate import Automate, epsilon_fermeture, deplacer


def determiniser(afn):
    """Construction des sous-ensembles : retourne un AFD équivalent (tâche 5.7)."""
    afd = Automate(afn.alphabet)
    numeros = {}          # sous-ensemble (frozenset) -> état de l'AFD
    a_traiter = deque()   # sous-ensembles créés mais pas encore explorés

    def numero(sous_ensemble):
        """État de l'AFD associé au sous-ensemble ; le crée s'il est nouveau."""
        if sous_ensemble not in numeros:
            etat = afd.nouvel_etat()
            numeros[sous_ensemble] = etat
            if sous_ensemble & afn.finaux:
                afd.ajouter_final(etat)
            a_traiter.append(sous_ensemble)
        return numeros[sous_ensemble]

    depart = epsilon_fermeture(afn, {afn.initial})
    afd.definir_initial(numero(depart))

    while a_traiter:
        courant = a_traiter.popleft()
        for symbole in afn.alphabet:
            suivant = epsilon_fermeture(afn, deplacer(afn, courant, symbole))
            if suivant:
                afd.ajouter_transition(numeros[courant], symbole, numero(suivant))

    return afd
def _signature(afd, classe, etat):
    """(classe de l'état, classe d'arrivée pour chaque lettre ; None si pas de transition)."""
    arrivees = []
    for symbole in afd.alphabet:
        cibles = afd.cibles(etat, symbole)
        arrivees.append(classe[next(iter(cibles))] if cibles else None)
    return (classe[etat], tuple(arrivees))


def minimiser(afd):
    """Minimise un AFD par l'algorithme de Moore (tâche 5.8)."""
    if not afd.est_deterministe():
        raise ValueError("minimiser attend un AFD (sans ε, un seul choix par lettre).")

    etats = sorted(afd.etats)
    classe = {e: int(e in afd.finaux) for e in etats}   # partition initiale
    nb_classes = len(set(classe.values()))

    while True:
        numeros = {}
        nouvelle = {}
        for e in etats:
            signature = _signature(afd, classe, e)
            if signature not in numeros:
                numeros[signature] = len(numeros)
            nouvelle[e] = numeros[signature]
        if len(numeros) == nb_classes:      # plus rien ne se coupe
            break
        classe, nb_classes = nouvelle, len(numeros)

    # Un état du nouvel automate par classe
    mini = Automate(afd.alphabet)
    for _ in range(nb_classes):
        mini.nouvel_etat()
    mini.definir_initial(nouvelle[afd.initial])
    for e in afd.finaux:
        mini.ajouter_final(nouvelle[e])
    for source, symbole, cible in afd.liste_transitions():
        mini.ajouter_transition(nouvelle[source], symbole, nouvelle[cible])
    return mini