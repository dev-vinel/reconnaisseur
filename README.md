# Reconnaisseur de langage régulier

Programme en ligne de commande (Python) qui :

1. lit un **alphabet** et une **expression régulière** ;
2. vérifie que l'expression est bien écrite (avec la position de l'erreur) ;
3. construit l'**automate** correspondant (Thompson, puis déterminisation et minimisation) et affiche ses tables de transitions ;
4. teste des **mots** : accepté ou rejeté, avec la **trace du calcul** et la raison du résultat.

## Prérequis

- Python 3.10 ou plus récent.
- `pytest` (uniquement pour lancer les tests).
- Un terminal qui affiche l'UTF-8 (caractères `ε`, `→`, `⊢`). Sous PowerShell, si ces caractères s'affichent mal :
  `$env:PYTHONIOENCODING="utf-8"`.

## Installation

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS
pip install pytest
```

## Lancement

```bash
python main.py
```

Le programme pose les questions dans l'ordre : alphabet, expression, puis les mots à tester. On peut tester autant de mots que l'on veut, puis construire un autre automate. `Ctrl+C` quitte proprement.

## Syntaxe des expressions

| Élément | Écriture | Exemple |
|---|---|---|
| Symbole | une lettre ou un chiffre de l'alphabet | `a` |
| Concaténation | implicite | `ab` = a puis b |
| Union | `+` ou `\|` | `a+b` |
| Étoile (0 fois ou plus) | `*` après l'élément | `a*` |
| Groupe | `( )` | `(ab)*` |
| Mot vide | `ε` ou `@` | `a+ε` |

Priorités : étoile, puis concaténation, puis union. Ainsi `ab*` signifie `a(b*)` et `a+bc` signifie `a+(bc)`.

Règles de l'alphabet : chaque symbole est **un seul caractère** (lettre ou chiffre), sans doublon, et jamais l'un des caractères réservés `( ) * + | . ε @`. La casse compte (`a` et `A` sont deux symboles). On sépare les symboles par des espaces ou des virgules, ou on les colle (`ab`).

Pour tester le **mot vide**, appuyer sur Entrée sans rien taper (ou écrire `ε` ou `@`).

## Exemple de session (extrait)

```
Alphabet (ex : a b ou a,b) : a b
Expression régulière (ε ou @ pour le mot vide) : (a+b)*abb
Expression bien écrite.
... tables de l'AFN-ε, de l'AFD et de l'AFD minimal ...
Mot à tester (Entrée, ε ou @ pour le mot vide) : babb
(q0, babb) ⊢ (q0, abb) ⊢ (q1, bb) ⊢ (q2, b) ⊢ (q3, ε)
Conclusion : mot accepté.
Mot accepté : tout le mot est lu et l'état q3 est final.
```

La trace utilise la notation du cours : `(état, mot restant)`, et chaque `⊢` correspond à une lettre lue. Les mots sont testés sur l'**AFD minimal**.

## Comment ça marche

```
saisie → validation → forme postfixée → AFN-ε (Thompson) → AFD (sous-ensembles) → AFD minimal → reconnaissance
```

1. **Validation** : analyse lexicale, parenthèses, opérateurs. La première erreur est signalée avec sa position.
2. **Préparation** : la concaténation est rendue explicite (`ab*` devient `a.b*`), puis l'expression est convertie en forme postfixée (algorithme de la gare de triage).
3. **Thompson** : un automate par symbole, assemblés par union, concaténation et étoile, avec des ε-transitions.
4. **Déterminisation** : construction des sous-ensembles. Le chemin d'un mot devient unique.
5. **Minimisation** : algorithme de Moore (raffinement de partition).
6. **Reconnaissance** : lecture lettre par lettre ; le chemin est conservé pour la trace et l'explication d'un rejet (calcul bloqué, ou état non final).

## Organisation des fichiers

| Fichier | Rôle |
|---|---|
| `main.py` | point d'entrée, boucle principale |
| `syntaxe.py` | opérateurs, symboles réservés, priorités |
| `saisie.py` | lecture de l'alphabet, de l'expression et du mot |
| `validation.py` | analyse lexicale et contrôles de l'expression |
| `preparation.py` | concaténation explicite, forme postfixée |
| `automate.py` | classe `Automate`, construction de Thompson |
| `determinisation.py` | AFN-ε vers AFD, minimisation |
| `affichage.py` | tables de transitions, trace du calcul |
| `reconnaissance.py` | simulation, chemin, explication du résultat |
| `test_*.py` | tests automatiques |

## Tests

```bash
pytest
```

Les tests comparent le programme avec le module `re` de Python sur tous les mots courts de nombreuses expressions. Le module `re` n'est utilisé que dans les tests, jamais dans le programme.

## Limites connues

- Les symboles de l'alphabet n'ont qu'**un seul caractère**.
- **Aucun dessin** pour l'instant : les automates sont affichés sous forme de tables de texte.
- La déterminisation peut faire **croître très vite** le nombre d'états : un AFN de n états peut donner jusqu'à 2ⁿ états. C'est le cas par exemple de `(a+b)*a(a+b)(a+b)(a+b)`, où chaque `(a+b)` ajouté double l'automate.
- Pas de classes de caractères ni d'opérateurs étendus (`?`, `+` au sens « une fois ou plus », `[a-z]`), seulement les trois opérations de base.

## Évolutions prévues

- Dessin des automates (fichier DOT et image avec Graphviz), puis surlignage du chemin d'un mot.
- Interface graphique.
- Un module dédié aux jetons, pour que `automate.py` ne dépende plus de `validation.py` et `preparation.py`.