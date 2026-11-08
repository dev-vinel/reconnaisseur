"""Automate : structure de données et construction de Thompson."""

from collections import namedtuple

from syntaxe import EPSILON
from validation import TYPE_SYMBOLE, TYPE_EPSILON, TYPE_UNION, TYPE_ETOILE
from preparation import TYPE_CONCAT


class Automate:
    """Automate fini (AFN-ε ou AFD) : états, transitions, initial, finaux."""

    def __init__(self, alphabet):
        self.alphabet = list(alphabet)
        self.etats = set()
        self.initial = None
        self.finaux = set()
        self.transitions = {}   # (état, symbole) -> ensemble d'états
        self._prochain = 0      # prochain numéro d'état libre

    def nouvel_etat(self):
        """Crée un état avec un numéro unique et le retourne."""
        etat = self._prochain
        self._prochain += 1
        self.etats.add(etat)
        return etat

    def definir_initial(self, etat):
        """Désigne l'état initial."""
        if etat not in self.etats:
            raise ValueError(f"État inconnu : {etat}")
        self.initial = etat

    def ajouter_final(self, etat):
        """Ajoute un état à l'ensemble des états finaux."""
        if etat not in self.etats:
            raise ValueError(f"État inconnu : {etat}")
        self.finaux.add(etat)

    def ajouter_transition(self, source, symbole, cible):
        """Ajoute la transition source --symbole--> cible (symbole peut être ε)."""
        if source not in self.etats or cible not in self.etats:
            raise ValueError("Transition vers ou depuis un état inconnu.")
        if symbole != EPSILON and symbole not in self.alphabet:
            raise ValueError(f"Symbole inconnu : {symbole}")
        self.transitions.setdefault((source, symbole), set()).add(cible)

    def cibles(self, etat, symbole):
        """États atteignables depuis `etat` en lisant `symbole` (ensemble, éventuellement vide)."""
        return set(self.transitions.get((etat, symbole), set()))

    def liste_transitions(self):
        """Toutes les transitions, triées, sous forme (source, symbole, cible)."""
        resultat = []
        for (source, symbole), cibles in self.transitions.items():
            for cible in cibles:
                resultat.append((source, symbole, cible))
        return sorted(resultat)

    def est_deterministe(self):
        """Vrai s'il n'y a aucune ε-transition et au plus une arrivée par (état, symbole)."""
        for (_, symbole), cibles in self.transitions.items():
            if symbole == EPSILON or len(cibles) > 1:
                return False
        return True
    # Un fragment : morceau d'automate avec une seule entrée et une seule sortie
Fragment = namedtuple("Fragment", ["debut", "fin"])


def automate_symbole(auto, symbole):
    """Fragment qui reconnaît le symbole : debut --symbole--> fin (tâche 5.2)."""
    if symbole not in auto.alphabet:
        raise ValueError(f"Symbole inconnu : {symbole}")
    debut = auto.nouvel_etat()
    fin = auto.nouvel_etat()
    auto.ajouter_transition(debut, symbole, fin)
    return Fragment(debut, fin)


def automate_epsilon(auto):
    """Fragment qui reconnaît le mot vide : debut --ε--> fin (tâche 5.2)."""
    debut = auto.nouvel_etat()
    fin = auto.nouvel_etat()
    auto.ajouter_transition(debut, EPSILON, fin)
    return Fragment(debut, fin)
def automate_union(auto, f1, f2):
    """Fragment de l'union f1 + f2 : nouvelle entrée et nouvelle sortie (tâche 5.3)."""
    debut = auto.nouvel_etat()
    fin = auto.nouvel_etat()

    auto.ajouter_transition(debut, EPSILON, f1.debut)
    auto.ajouter_transition(debut, EPSILON, f2.debut)
    auto.ajouter_transition(f1.fin, EPSILON, fin)
    auto.ajouter_transition(f2.fin, EPSILON, fin)

    return Fragment(debut, fin)
def automate_concat(auto, f1, f2):
    """Fragment de la concaténation f1 . f2 : relie f1.fin à f2.debut (tâche 5.4)."""
    auto.ajouter_transition(f1.fin, EPSILON, f2.debut)
    return Fragment(f1.debut, f2.fin)
def automate_etoile(auto, f):
    """Fragment de l'étoile f* : contournement et bouclage en ε (tâche 5.5)."""
    debut = auto.nouvel_etat()
    fin = auto.nouvel_etat()

    auto.ajouter_transition(debut, EPSILON, f.debut)   # entrer dans f
    auto.ajouter_transition(f.fin, EPSILON, fin)       # sortir de f
    auto.ajouter_transition(debut, EPSILON, fin)       # contournement : 0 répétition
    auto.ajouter_transition(f.fin, EPSILON, f.debut)   # bouclage : répétitions

    return Fragment(debut, fin)


def thompson(postfixe, alphabet):
    """Construit l'AFN-ε complet à partir de la forme postfixée (tâche 5.6)."""
    auto = Automate(alphabet)
    pile = []  # pile de fragments

    def depiler():
        if not pile:
            raise ValueError("Forme postfixée invalide : opérande manquant.")
        return pile.pop()

    for jeton in postfixe:
        if jeton.type == TYPE_SYMBOLE:
            pile.append(automate_symbole(auto, jeton.valeur))
        elif jeton.type == TYPE_EPSILON:
            pile.append(automate_epsilon(auto))
        elif jeton.type == TYPE_ETOILE:
            pile.append(automate_etoile(auto, depiler()))
        elif jeton.type == TYPE_UNION:
            f2 = depiler()   # le droit d'abord
            f1 = depiler()
            pile.append(automate_union(auto, f1, f2))
        elif jeton.type == TYPE_CONCAT:
            f2 = depiler()
            f1 = depiler()
            pile.append(automate_concat(auto, f1, f2))
        else:
            raise ValueError(f"Jeton inattendu dans la forme postfixée : {jeton.type}")

    if len(pile) != 1:
        raise ValueError("Forme postfixée invalide : opérande ou opérateur en trop ou manquant.")

    resultat = pile[0]
    auto.definir_initial(resultat.debut)
    auto.ajouter_final(resultat.fin)
    return auto
def epsilon_fermeture(auto, etats):
    """États atteignables depuis `etats` par des ε-transitions (tâche 5.7).

    Les états de départ en font partie. Retourne un frozenset.
    """
    fermeture = set(etats)
    a_explorer = list(etats)
    while a_explorer:
        etat = a_explorer.pop()
        for cible in auto.cibles(etat, EPSILON):
            if cible not in fermeture:
                fermeture.add(cible)
                a_explorer.append(cible)
    return frozenset(fermeture)


def deplacer(auto, etats, symbole):
    """États atteignables depuis `etats` en lisant `symbole` (sans ε-transition)."""
    resultat = set()
    for etat in etats:
        resultat |= auto.cibles(etat, symbole)
    return resultat