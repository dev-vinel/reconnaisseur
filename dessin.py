"""Dessin : descriptions DOT stylées et coloriées des automates, rendu avec Graphviz."""

import shutil
from functools import lru_cache

from syntaxe import EPSILON
from theme import palette, POLICE_INTERFACE

DPI = 160                  # résolution des images PNG
EPAISSEUR_ACTIVE = "3.2"   # épaisseur de l'état courant et de la transition empruntée


class ErreurRendu(RuntimeError):
    """Graphviz est introuvable ou a refusé de dessiner le graphe."""


# ---------------------------------------------------------------------------
# Fonctions pures : elles retournent du texte et n'ont besoin ni de Graphviz
# ni d'une fenêtre (donc elles sont testables).
# ---------------------------------------------------------------------------

def _echapper(texte):
    """Échappe les antislashs et les guillemets pour un texte entre guillemets DOT."""
    return texte.replace("\\", "\\\\").replace('"', '\\"')


def etiquette_arete(symboles):
    """Texte d'une flèche : les symboles séparés par des virgules (ex. 'a,b')."""
    return ",".join(symboles)


def est_epsilon_pur(symboles):
    """Vrai si la flèche ne porte que des ε-transitions."""
    return all(s == EPSILON for s in symboles)


def regrouper_aretes(automate):
    """Fusionne les transitions de mêmes extrémités.

    Retourne une liste triée de (source, cible, symboles), où `symboles` suit
    l'ordre de l'alphabet, avec ε en dernier.
    """
    ordre = list(automate.alphabet) + [EPSILON]
    groupes = {}
    for source, symbole, cible in automate.liste_transitions():
        groupes.setdefault((source, cible), []).append(symbole)
    return [
        (source, cible, tuple(sorted(groupes[(source, cible)], key=ordre.index)))
        for (source, cible) in sorted(groupes)
    ]


def contexte_etape(chemin, index):
    """Situation du calcul à l'étape `index` : (état courant, états visités, transition).

    `visites` contient les états des étapes précédentes ; `transition` est le
    couple (état précédent, état courant), ou None à l'étape 0.
    """
    if not chemin:
        raise ValueError("Le chemin est vide.")
    if not 0 <= index < len(chemin):
        raise IndexError(f"Étape {index} hors du chemin (0 à {len(chemin) - 1}).")
    courant = chemin[index].etat
    visites = frozenset(configuration.etat for configuration in chemin[:index])
    transition = (chemin[index - 1].etat, courant) if index > 0 else None
    return courant, visites, transition


def generer_dot(automate, mode, courant=None, visites=(), transition=None,
                couleur_courant=None):
    """Retourne le DOT stylé de l'automate, aux couleurs du mode (sombre ou clair).

    Sans options, dessine l'automate au repos. Pour une étape de l'animation :
    `courant` est l'état illuminé, `visites` les états atténués, `transition`
    le couple (source, cible) de la flèche empruntée, et `couleur_courant`
    remplace la couleur de l'état courant (verdict final).
    """
    p = palette(mode)
    police = _echapper(POLICE_INTERFACE)
    transition = tuple(transition) if transition is not None else None

    lignes = [
        "digraph automate {",
        (f'    graph [rankdir=LR, bgcolor="{p["dessin_fond"]}", pad=0.4, '
         f'nodesep=0.55, ranksep=0.8, dpi={DPI}, splines=true];'),
        (f'    node [shape=circle, style=filled, fontname="{police}", fontsize=15, '
         f'penwidth=1.8, margin=0.12, fillcolor="{p["dessin_noeud_fond"]}", '
         f'color="{p["dessin_noeud_bord"]}", fontcolor="{p["dessin_noeud_texte"]}"];'),
        (f'    edge [fontname="{police}", fontsize=13, arrowsize=0.8, penwidth=1.5, '
         f'color="{p["dessin_fleche"]}", fontcolor="{p["dessin_etiquette"]}"];'),
    ]

    # Flèche d'entrée : un point invisible relié à l'état initial
    if automate.initial is not None:
        couleur_entree = p["dessin_initial"]
        lignes.append(
            f'    debut [shape=point, width=0.14, label="", '
            f'color="{couleur_entree}", fillcolor="{couleur_entree}"];'
        )

    # États
    for etat in sorted(automate.etats):
        final = etat in automate.finaux
        fond = p["dessin_final_fond"] if final else p["dessin_noeud_fond"]
        bord = p["dessin_final_bord"] if final else p["dessin_noeud_bord"]
        texte = p["dessin_noeud_texte"]
        epaisseur = "1.8"
        if etat == automate.initial:
            bord = p["dessin_initial"]
        if etat in visites:
            fond, texte = p["dessin_visite_fond"], p["dessin_visite_texte"]
        if etat == courant:
            fond = couleur_courant or p["dessin_courant_fond"]
            bord = couleur_courant or p["dessin_chemin"]
            texte = p["dessin_courant_texte"]
            epaisseur = EPAISSEUR_ACTIVE
        attributs = [f'label="q{etat}"']
        if final:
            attributs.append("shape=doublecircle")
        attributs += [
            f'fillcolor="{fond}"', f'color="{bord}"',
            f'fontcolor="{texte}"', f"penwidth={epaisseur}",
        ]
        lignes.append(f'    q{etat} [{", ".join(attributs)}];')

    if automate.initial is not None:
        lignes.append(
            f'    debut -> q{automate.initial} '
            f'[color="{p["dessin_initial"]}", penwidth=2.2, arrowsize=0.9];'
        )

    # Flèches (transitions de mêmes extrémités fusionnées)
    for source, cible, symboles in regrouper_aretes(automate):
        attributs = [f'label="{_echapper(etiquette_arete(symboles))}"']
        if est_epsilon_pur(symboles):
            attributs += [
                "style=dashed",
                f'color="{p["dessin_epsilon"]}"',
                f'fontcolor="{p["dessin_epsilon"]}"',
            ]
        if (source, cible) == transition:
            attributs += [
                f'color="{p["dessin_chemin"]}"',
                f'fontcolor="{p["dessin_chemin"]}"',
                f"penwidth={EPAISSEUR_ACTIVE}",
            ]
        lignes.append(f'    q{source} -> q{cible} [{", ".join(attributs)}];')

    lignes.append("}")
    return "\n".join(lignes)


def dot_etape(automate, chemin, index, mode, accepte=None):
    """DOT colorié de l'étape `index` du calcul.

    Si `accepte` vaut True ou False, la dernière étape prend la couleur du
    verdict (vert ou rouge) ; avec None, elle garde la couleur de l'état courant.
    """
    courant, visites, transition = contexte_etape(chemin, index)
    couleur_courant = None
    if accepte is not None and index == len(chemin) - 1:
        couleur_courant = palette(mode)["accepte" if accepte else "rejete"]
    return generer_dot(
        automate, mode, courant=courant, visites=visites,
        transition=transition, couleur_courant=couleur_courant,
    )


def dots_du_chemin(automate, chemin, mode, accepte=None):
    """Liste des DOT de toutes les étapes du calcul, dans l'ordre."""
    return [dot_etape(automate, chemin, i, mode, accepte) for i in range(len(chemin))]


# ---------------------------------------------------------------------------
# Rendu avec Graphviz (nécessite le logiciel installé et dans le PATH)
# ---------------------------------------------------------------------------

def graphviz_disponible():
    """Vrai si le programme `dot` de Graphviz est trouvable dans le PATH."""
    return shutil.which("dot") is not None


@lru_cache(maxsize=128)
def _rendre(dot, format_sortie):
    """Appelle Graphviz ; le cache évite de redessiner un DOT déjà rendu."""
    try:
        import graphviz
    except ImportError as erreur:
        raise ErreurRendu(
            "Le paquet Python 'graphviz' n'est pas installé (pip install graphviz)."
        ) from erreur
    try:
        return graphviz.Source(dot).pipe(format=format_sortie)
    except graphviz.ExecutableNotFound as erreur:
        raise ErreurRendu(
            "Graphviz est introuvable. Installe-le, ajoute-le au PATH, "
            "puis ouvre un nouveau terminal (vérification : dot -V)."
        ) from erreur
    except Exception as erreur:
        raise ErreurRendu(f"Graphviz n'a pas pu dessiner le graphe : {erreur}") from erreur


def rendre_png(dot):
    """Retourne l'image PNG (octets) du DOT, avec cache."""
    return _rendre(dot, "png")


def rendre_svg(dot):
    """Retourne l'image SVG (octets) du DOT, avec cache."""
    return _rendre(dot, "svg")


def vider_cache():
    """Vide le cache des images (utile après un changement de thème)."""
    _rendre.cache_clear()


def exporter_image(dot, chemin_fichier, format_sortie="png"):
    """Écrit l'image du DOT dans un fichier ('png' ou 'svg')."""
    if format_sortie not in ("png", "svg"):
        raise ValueError(f"Format inconnu : {format_sortie}")
    with open(chemin_fichier, "wb") as fichier:
        fichier.write(_rendre(dot, format_sortie))