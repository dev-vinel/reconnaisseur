"""Affichage : présentation des automates (texte d'abord, dessin à la fin)."""

from syntaxe import EPSILON


def formater_ensemble(etats):
    """'{1,2}' pour un ensemble trié, '-' s'il est vide."""
    if not etats:
        return "-"
    return "{" + ",".join(str(e) for e in sorted(etats)) + "}"


def table_en_texte(automate):
    """Retourne la table de transitions sous forme de texte (tâche 6.1)."""
    colonnes = list(automate.alphabet)
    if any(symbole == EPSILON for (_, symbole) in automate.transitions):
        colonnes.append(EPSILON)

    def etiquette(etat):
        initial = "→" if etat == automate.initial else " "
        final = "*" if etat in automate.finaux else " "
        return f"{initial}{final} {etat}"

    entete = ["état"] + colonnes
    lignes_table = [
        [etiquette(e)] + [formater_ensemble(automate.cibles(e, c)) for c in colonnes]
        for e in sorted(automate.etats)
    ]
    largeurs = [
        max(len(ligne[i]) for ligne in [entete] + lignes_table)
        for i in range(len(entete))
    ]

    def formater_ligne(cellules):
        return " | ".join(c.ljust(l) for c, l in zip(cellules, largeurs)).rstrip()

    sortie = [
        "Alphabet : {" + ", ".join(automate.alphabet) + "}",
        "États    : " + formater_ensemble(automate.etats),
        "Initial  : " + ("-" if automate.initial is None else str(automate.initial)),
        "Finaux   : " + formater_ensemble(automate.finaux),
        "",
        formater_ligne(entete),
        "-+-".join("-" * l for l in largeurs),
    ]
    sortie += [formater_ligne(ligne) for ligne in lignes_table]
    sortie += ["", "→ = état initial, * = état final"]
    return "\n".join(sortie)


def afficher_table(automate):
    """Affiche la table de transitions (tâche 6.1)."""
    print(table_en_texte(automate))
def formater_configuration(configuration):
    """'(q1, bb)' ; un reste vide s'écrit ε (tâche 7.4)."""
    reste = configuration.reste or EPSILON
    return f"(q{configuration.etat}, {reste})"


def trace_en_texte(chemin, accepte):
    """Trace du calcul : configurations reliées par ⊢, puis la conclusion (tâche 7.4)."""
    ligne = " ⊢ ".join(formater_configuration(c) for c in chemin)
    verdict = "accepté" if accepte else "rejeté"
    return f"{ligne}\nConclusion : mot {verdict}."


def afficher_trace(chemin, accepte):
    """Affiche la trace du calcul (tâche 7.4)."""
    print(trace_en_texte(chemin, accepte))
def automate_en_dot(automate):
    """Retourne la description DOT de l'automate, sous forme de texte (tâche 6.2).

    États finaux en double cercle, flèche d'entrée sur l'état initial,
    transitions de mêmes extrémités fusionnées en une seule flèche.
    """
    lignes = [
        "digraph automate {",
        "    rankdir=LR;",
        "    node [shape=circle];",
    ]
    if automate.initial is not None:
        lignes.append("    debut [shape=point];")
    for etat in sorted(automate.finaux):
        lignes.append(f"    q{etat} [shape=doublecircle];")
    if automate.initial is not None:
        lignes.append(f"    debut -> q{automate.initial};")

    ordre = list(automate.alphabet) + [EPSILON]
    groupes = {}   # (source, cible) -> symboles des transitions entre ces deux états
    for source, symbole, cible in automate.liste_transitions():
        groupes.setdefault((source, cible), []).append(symbole)
    for source, cible in sorted(groupes):
        symboles = sorted(groupes[(source, cible)], key=ordre.index)
        lignes.append(f'    q{source} -> q{cible} [label="{",".join(symboles)}"];')

    lignes.append("}")
    return "\n".join(lignes)


def ecrire_dot(automate, chemin):
    """Écrit la description DOT de l'automate dans un fichier UTF-8 (tâche 6.2)."""
    with open(chemin, "w", encoding="utf-8") as fichier:
        fichier.write(automate_en_dot(automate) + "\n")