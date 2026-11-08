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