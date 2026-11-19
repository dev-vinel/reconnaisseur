"""Interface graphique : fenêtre CustomTkinter ; les automates sont dessinés par Graphviz."""

import io
import tkinter as tk
from tkinter import filedialog, ttk

import customtkinter as ctk
from PIL import Image, ImageTk

from syntaxe import EPSILON
from saisie import analyser_alphabet, analyser_mot, nettoyer_expression
from validation import analyser_lexicalement, extraire_position, valider_expression
from preparation import jetons_en_texte, rendre_concat_explicite, vers_postfixe
from main import construire_automates
from reconnaissance import expliquer, reconnaitre
from affichage import (
    ecrire_dot, formater_configuration, formater_ensemble, table_en_texte,
)
from dessin import (
    ErreurRendu, dot_etape, exporter_image, generer_dot,
    graphviz_disponible, rendre_png,
)
from theme import (
    HAUTEUR_MIN, ICONES, LARGEUR_MIN, MARGE, MODE_SOMBRE, POLICE_CODE,
    POLICE_INTERFACE, RAYON_COIN, SEUIL_ETATS,
    appliquer_theme, creer_polices, duo, mode_oppose, palette,
)

NOM_AFN, NOM_AFD, NOM_MIN = "AFN-ε", "AFD", "AFD minimal"
ONGLETS = (NOM_AFN, NOM_AFD, NOM_MIN)
NOMS_FICHIERS = {NOM_AFN: "afn", NOM_AFD: "afd", NOM_MIN: "afd_minimal"}

LARGEUR_GAUCHE = 450      # largeur de la colonne de gauche (pixels)
LARGEUR_TEXTE = 390       # largeur de retour à la ligne des textes de la colonne de gauche
DELAI_LECTURE = 900       # durée d'une étape de l'animation (millisecondes)
LIMITE_DESSIN = 150       # au-delà, on n'appelle pas Graphviz (la table reste disponible)

EXEMPLES = (
    ("a b", "(a+b)*abb", "se termine par abb"),
    ("a b", "a*b*", "des a puis des b"),
    ("a b", "(ab)*", "ab répété"),
    ("a b", "a(b+a)*b", "commence par a, finit par b"),
    ("a b", "(a+b)*a(a+b)", "avant-dernière lettre : a"),
    ("a b c", "(a+b+c)*c", "se termine par c"),
    ("0 1", "(0+1)*01", "se termine par 01"),
    ("a b", "a+ε", "a ou le mot vide"),
)

TEXTE_AIDE = """\
SYNTAXE DES EXPRESSIONS RÉGULIÈRES

  a  b  0  1     un symbole de l'alphabet (lettre ou chiffre)
  ab              concaténation : a puis b
  a+b    a|b      union : a ou b
  a*              étoile : a répété 0 fois ou plus
  ( )             groupes, par exemple (a+b)*
  ε    @          mot vide (@ si ton clavier n'a pas ε)

Priorités : étoile, puis concaténation, puis union.
Donc  ab*  signifie  a(b*)  et  a+bc  signifie  a+(bc).

ALPHABET
  Symboles séparés par des espaces ou des virgules : a b  ou  a,b
  Pas de doublon, et jamais l'un des caractères  ( ) * + | . ε @

MOT À TESTER
  Un champ vide (ou ε, ou @) est le mot vide.

RACCOURCIS
  Entrée            construire (champs alphabet et expression)
  Entrée / Ctrl+T   tester le mot
  Alt+←  /  Alt+→   étape précédente / suivante
  Ctrl+P            lecture / pause de l'animation
  Ctrl+D            thème clair / sombre
  F1                cette aide

DESSIN
  Molette : zoom   ·   Glisser : déplacer   ·   Double-clic : recentrer
"""


# ---------------------------------------------------------------------------
# Petites fabriques de widgets (pour garder un style identique partout)
# ---------------------------------------------------------------------------

def _carte(maitre, titre, polices):
    """Crée une carte arrondie avec un titre ; retourne (carte, corps)."""
    carte = ctk.CTkFrame(
        maitre, corner_radius=RAYON_COIN, fg_color=duo("surface"),
        border_width=1, border_color=duo("bordure"),
    )
    ctk.CTkLabel(
        carte, text=titre, font=polices["sous_titre"],
        text_color=duo("texte"), anchor="w",
    ).pack(fill="x", padx=MARGE, pady=(MARGE, 8))
    corps = ctk.CTkFrame(carte, fg_color="transparent")
    corps.pack(fill="both", expand=True, padx=MARGE, pady=(0, MARGE))
    return carte, corps


def _bouton(maitre, texte, commande, polices, principal=True, largeur=None):
    """Crée un bouton arrondi avec effet au survol (principal = couleur d'accent)."""
    options = {}
    if largeur is not None:
        options["width"] = largeur
    return ctk.CTkButton(
        maitre, text=texte, command=commande, font=polices["gras"],
        corner_radius=10, height=38, border_width=0,
        fg_color=duo("accent") if principal else duo("surface_alt"),
        hover_color=duo("accent_survol") if principal else duo("bordure"),
        text_color=duo("accent_texte") if principal else duo("texte"),
        text_color_disabled=duo("texte_doux"),
        **options,
    )


def _champ(maitre, polices, indication):
    """Crée un champ de saisie arrondi en police de code."""
    return ctk.CTkEntry(
        maitre, placeholder_text=indication, font=polices["code"], height=40,
        corner_radius=10, border_width=1, fg_color=duo("surface_alt"),
        border_color=duo("bordure"), text_color=duo("texte"),
        placeholder_text_color=duo("texte_doux"),
    )


def _zone_texte(maitre, polices, hauteur, police="code"):
    """Crée une zone de texte en lecture seule (les balises de couleur sont posées après)."""
    zone = ctk.CTkTextbox(
        maitre, height=hauteur, font=polices[police], wrap="word",
        corner_radius=10, border_width=0, fg_color=duo("surface_alt"),
        text_color=duo("texte"), activate_scrollbars=False,
    )
    zone.configure(state="disabled")
    return zone


def _ecrire_zone(zone, segments):
    """Remplace le contenu d'une zone de texte par des segments (texte, balise ou None)."""
    zone.configure(state="normal")
    zone.delete("1.0", "end")
    for texte, balise in segments:
        if balise:
            zone.insert("end", texte, balise)
        else:
            zone.insert("end", texte)
    zone.configure(state="disabled")


def _legende(maitre, texte, polices, couleur="texte_doux"):
    """Petit titre de champ, aligné à gauche."""
    return ctk.CTkLabel(
        maitre, text=texte, font=polices["petit"], text_color=duo(couleur), anchor="w",
    )


def configurer_style_tableau(mode):
    """Applique les couleurs du mode au style ttk des tables de transitions."""
    p = palette(mode)
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Automate.Treeview", background=p["surface"], fieldbackground=p["surface"],
        foreground=p["texte"], rowheight=30, borderwidth=0, relief="flat",
        font=(POLICE_CODE, 12),
    )
    style.configure(
        "Automate.Treeview.Heading", background=p["surface_alt"],
        foreground=p["texte"], relief="flat", borderwidth=0, padding=6,
        font=(POLICE_INTERFACE, 11, "bold"),
    )
    style.map(
        "Automate.Treeview",
        background=[("selected", p["accent"])],
        foreground=[("selected", p["accent_texte"])],
    )
    style.map("Automate.Treeview.Heading", background=[("active", p["bordure"])])


# ---------------------------------------------------------------------------
# Visionneuse d'image : zoom, déplacement, recentrage
# ---------------------------------------------------------------------------

class VisionneuseImage(ctk.CTkFrame):
    """Affiche une image PNG avec zoom à la molette, déplacement à la souris et recentrage.

    Le Canvas ne sert que de fenêtre d'affichage : le dessin lui-même vient de Graphviz.
    """

    ZOOM_MIN = 0.05
    ZOOM_MAX = 8.0
    PAS_ZOOM = 1.15
    COTE_MAX = 6000       # taille maximale (pixels) de l'image affichée
    MARGE_IMAGE = 24

    def __init__(self, maitre, polices, mode):
        super().__init__(
            maitre, corner_radius=RAYON_COIN, fg_color=duo("surface"),
            border_width=1, border_color=duo("bordure"),
        )
        p = palette(mode)
        self._source = None      # image PIL d'origine
        self._photo = None       # image affichée (référence à garder, sinon Tk l'efface)
        self._zoom = 1.0
        self._x = 0.0
        self._y = 0.0
        self._auto = True        # vrai tant que l'utilisateur n'a ni zoomé ni déplacé
        self._glisse = None
        self._message = None

        self.canvas = tk.Canvas(
            self, highlightthickness=0, bd=0, bg=p["dessin_fond"], cursor="fleur",
        )
        self.canvas.pack(fill="both", expand=True, padx=8, pady=8)
        self.canvas.create_text(
            12, 12, anchor="sw", fill=p["texte_doux"], font=(POLICE_INTERFACE, 10),
            text="Molette : zoom   ·   Glisser : déplacer   ·   Double-clic : recentrer",
            tags="aide",
        )

        self.canvas.bind("<Configure>", self._au_redimensionnement)
        self.canvas.bind("<Enter>", lambda _e: self.canvas.focus_set())
        self.canvas.bind("<MouseWheel>", self._molette)
        self.canvas.bind("<Button-4>", lambda e: self._zoomer(self.PAS_ZOOM, e.x, e.y))
        self.canvas.bind("<Button-5>", lambda e: self._zoomer(1 / self.PAS_ZOOM, e.x, e.y))
        self.canvas.bind("<ButtonPress-1>", self._debut_glisse)
        self.canvas.bind("<B1-Motion>", self._glisse_pas)
        self.canvas.bind("<Double-Button-1>", lambda _e: self.recentrer())

        self.bouton_recentrer = ctk.CTkButton(
            self, text=f"{ICONES['recentrer']}  Recentrer", command=self.recentrer,
            font=polices["petit"], width=104, height=30, corner_radius=8,
            fg_color=duo("accent"), hover_color=duo("accent_survol"),
            text_color=duo("accent_texte"),
        )
        self.bouton_recentrer.place(relx=1.0, x=-18, y=18, anchor="ne")

    # --- affichage -------------------------------------------------------

    def afficher_png(self, donnees, conserver_vue=False):
        """Affiche une image PNG (octets) ; `conserver_vue` garde le zoom et la position."""
        image = Image.open(io.BytesIO(donnees))
        image.load()
        taille_changee = self._source is None or self._source.size != image.size
        self._source = image
        self._message = None
        self.canvas.delete("message")
        if conserver_vue and not self._auto and not taille_changee:
            self._dessiner()
        else:
            self.recentrer()

    def afficher_message(self, texte, nom_couleur="texte_doux"):
        """Remplace l'image par un message centré (erreur, avertissement...)."""
        self._source = None
        self._photo = None
        self._message = (texte, nom_couleur)
        self.canvas.delete("image")
        self.canvas.delete("message")
        largeur = max(self.canvas.winfo_width(), 200)
        hauteur = max(self.canvas.winfo_height(), 100)
        self.canvas.create_text(
            largeur / 2, hauteur / 2, text=texte, justify="center",
            width=max(largeur - 80, 100), font=(POLICE_INTERFACE, 13),
            fill=palette(self._mode_courant())[nom_couleur], tags="message",
        )

    def recentrer(self):
        """Ajuste l'image à la zone d'affichage et la centre."""
        self._auto = True
        if self._source is None:
            return
        largeur = max(self.canvas.winfo_width(), 1)
        hauteur = max(self.canvas.winfo_height(), 1)
        iw, ih = self._source.size
        marge = 2 * self.MARGE_IMAGE
        zoom = min((largeur - marge) / iw, (hauteur - marge) / ih, 1.5)
        self._zoom = max(zoom, self.ZOOM_MIN)
        self._x = (largeur - iw * self._zoom) / 2
        self._y = (hauteur - ih * self._zoom) / 2
        self._dessiner()

    def appliquer_mode(self, mode):
        """Adapte les couleurs du fond et des textes au mode (sombre ou clair)."""
        p = palette(mode)
        self._mode = mode
        self.canvas.configure(bg=p["dessin_fond"])
        self.canvas.itemconfigure("aide", fill=p["texte_doux"])
        if self._message is not None:
            self.canvas.itemconfigure("message", fill=p[self._message[1]])

    # --- interne ---------------------------------------------------------

    def _mode_courant(self):
        """Mode (sombre ou clair) mémorisé, sombre par défaut."""
        return getattr(self, "_mode", MODE_SOMBRE)

    def _dessiner(self):
        """Redessine l'image au zoom et à la position courants."""
        if self._source is None:
            return
        iw, ih = self._source.size
        taille = (max(int(iw * self._zoom), 1), max(int(ih * self._zoom), 1))
        filtre = Image.Resampling.LANCZOS if self._zoom < 1 else Image.Resampling.BICUBIC
        self._photo = ImageTk.PhotoImage(self._source.resize(taille, filtre))
        self.canvas.delete("image")
        self.canvas.create_image(self._x, self._y, anchor="nw", image=self._photo, tags="image")
        self.canvas.tag_lower("image")

    def _zoomer(self, facteur, cx, cy):
        """Zoome autour du point (cx, cy) de la zone d'affichage."""
        if self._source is None:
            return
        iw, ih = self._source.size
        maxi = min(self.ZOOM_MAX, self.COTE_MAX / max(iw, ih))
        nouveau = min(max(self._zoom * facteur, self.ZOOM_MIN), maxi)
        ratio = nouveau / self._zoom
        if ratio == 1:
            return
        self._x = cx - (cx - self._x) * ratio
        self._y = cy - (cy - self._y) * ratio
        self._zoom = nouveau
        self._auto = False
        self._dessiner()

    def _molette(self, evenement):
        """Zoom à la molette (Windows et macOS)."""
        facteur = self.PAS_ZOOM if evenement.delta > 0 else 1 / self.PAS_ZOOM
        self._zoomer(facteur, evenement.x, evenement.y)

    def _debut_glisse(self, evenement):
        """Mémorise le point de départ d'un glisser."""
        self._glisse = (evenement.x, evenement.y)

    def _glisse_pas(self, evenement):
        """Déplace l'image pendant le glisser."""
        if self._glisse is None or self._source is None:
            return
        dx, dy = evenement.x - self._glisse[0], evenement.y - self._glisse[1]
        self._glisse = (evenement.x, evenement.y)
        self._x += dx
        self._y += dy
        self._auto = False
        self.canvas.move("image", dx, dy)

    def _au_redimensionnement(self, evenement):
        """Repositionne les textes et réajuste l'image si l'utilisateur n'a pas zoomé."""
        self.canvas.coords("aide", 12, evenement.height - 10)
        if self.canvas.find_withtag("message"):
            self.canvas.coords("message", evenement.width / 2, evenement.height / 2)
            self.canvas.itemconfigure("message", width=max(evenement.width - 80, 100))
        if self._auto and self._source is not None:
            self.recentrer()


# ---------------------------------------------------------------------------
# Table de transitions
# ---------------------------------------------------------------------------

class TableTransitions(ctk.CTkFrame):
    """Table de transitions d'un automate, avec les marques → (initial) et * (final)."""

    def __init__(self, maitre, mode):
        super().__init__(
            maitre, corner_radius=RAYON_COIN, fg_color=duo("surface"),
            border_width=1, border_color=duo("bordure"),
        )
        self._items = {}   # état -> identifiant de la ligne
        self.arbre = ttk.Treeview(
            self, show="headings", selectmode="browse", style="Automate.Treeview",
        )
        defilement = ctk.CTkScrollbar(self, command=self.arbre.yview)
        self.arbre.configure(yscrollcommand=defilement.set)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.arbre.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        defilement.grid(row=0, column=1, sticky="ns", padx=(0, 6), pady=10)
        self.appliquer_mode(mode)

    def afficher(self, automate):
        """Remplit la table avec les états et les transitions de l'automate."""
        colonnes = ["etat"] + list(automate.alphabet)
        if any(symbole == EPSILON for (_, symbole) in automate.transitions):
            colonnes.append(EPSILON)
        self.arbre.delete(*self.arbre.get_children())
        self._items = {}
        self.arbre.configure(columns=colonnes)
        for colonne in colonnes:
            self.arbre.heading(colonne, text="état" if colonne == "etat" else colonne)
            largeur = 110 if colonne in ("etat", EPSILON) else 70
            self.arbre.column(
                colonne, width=largeur, minwidth=50, anchor="center", stretch=True,
            )
        for rang, etat in enumerate(sorted(automate.etats)):
            marques = ("→" if etat == automate.initial else "") + (
                "*" if etat in automate.finaux else ""
            )
            valeurs = [f"{marques} q{etat}".strip()]
            valeurs += [formater_ensemble(automate.cibles(etat, c)) for c in colonnes[1:]]
            balises = ["pair" if rang % 2 == 0 else "impair"]
            if etat in automate.finaux:
                balises.append("final")
            self._items[etat] = self.arbre.insert("", "end", values=valeurs, tags=balises)

    def selectionner(self, etat):
        """Met en évidence la ligne d'un état (animation du calcul)."""
        ligne = self._items.get(etat)
        if ligne is not None:
            self.arbre.selection_set(ligne)
            self.arbre.see(ligne)

    def deselectionner(self):
        """Retire toute mise en évidence."""
        self.arbre.selection_remove(*self.arbre.selection())

    def appliquer_mode(self, mode):
        """Adapte les couleurs des lignes au mode (sombre ou clair)."""
        p = palette(mode)
        self.arbre.tag_configure("pair", background=p["surface"])
        self.arbre.tag_configure("impair", background=p["surface_alt"])
        self.arbre.tag_configure("final", foreground=p["accepte"])


# ---------------------------------------------------------------------------
# Un onglet = le dessin Graphviz d'un automate + sa table de transitions
# ---------------------------------------------------------------------------

class VueAutomate(ctk.CTkFrame):
    """Dessin Graphviz d'un automate à côté de sa table de transitions."""

    def __init__(self, maitre, polices, mode):
        super().__init__(maitre, fg_color="transparent")
        self.automate = None
        self.dot_courant = None
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1, minsize=330)
        self.visionneuse = VisionneuseImage(self, polices, mode)
        self.visionneuse.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.table = TableTransitions(self, mode)
        self.table.grid(row=0, column=1, sticky="nsew")

    def afficher(self, automate, mode):
        """Affiche un nouvel automate : table, puis dessin."""
        self.automate = automate
        self.table.afficher(automate)
        self.redessiner(mode)

    def redessiner(self, mode, dot=None, conserver_vue=False):
        """Dessine l'automate (ou le DOT donné, pour une étape de l'animation)."""
        if self.automate is None:
            return
        n = len(self.automate.etats)
        if n > LIMITE_DESSIN:
            self.visionneuse.afficher_message(
                f"Automate trop grand pour être dessiné ({n} états).\n"
                "La table de transitions reste disponible.", "avertissement",
            )
            return
        if not graphviz_disponible():
            self.visionneuse.afficher_message(
                "Graphviz est introuvable : le dessin est indisponible.\n"
                "Installe-le, ajoute-le au PATH, puis relance (vérification : dot -V).\n"
                "La table de transitions reste utilisable.", "avertissement",
            )
            return
        dot = dot or generer_dot(self.automate, mode)
        try:
            self.visionneuse.afficher_png(rendre_png(dot), conserver_vue)
            self.dot_courant = dot
        except ErreurRendu as erreur:
            self.visionneuse.afficher_message(str(erreur), "rejete")

    def appliquer_mode(self, mode):
        """Adapte les couleurs de la visionneuse et de la table au mode."""
        self.visionneuse.appliquer_mode(mode)
        self.table.appliquer_mode(mode)


# ---------------------------------------------------------------------------
# Fenêtre principale
# ---------------------------------------------------------------------------

class Application(ctk.CTk):
    """Fenêtre principale : saisie, construction des automates, test de mots, animation."""

    def __init__(self):
        appliquer_theme(MODE_SOMBRE)
        super().__init__()
        self.mode = MODE_SOMBRE
        self.title("Reconnaisseur de langage régulier")
        self.minsize(LARGEUR_MIN, HAUTEUR_MIN)
        self.geometry(f"{LARGEUR_MIN + 140}x{HAUTEUR_MIN + 80}")
        self.configure(fg_color=duo("fond"))
        self.polices = creer_polices()
        configurer_style_tableau(self.mode)

        # État du programme (rempli par _construire et _tester)
        self.alphabet = None
        self.afn = self.afd = self.minimal = None
        self._mot = ""
        self._chemin = None
        self._accepte = None
        self._etape = 0
        self._lecture_id = None
        self._onglet_actif = NOM_MIN
        self._fenetre_aide = None
        self._exemples = {}

        self._construire_widgets()
        self._appliquer_tags()
        self._raccourcis()
        self._reinitialiser_test()
        self._choisir_onglet(NOM_MIN)
        self._valider_en_direct()
        if graphviz_disponible():
            self.lbl_graphviz.configure(text="Graphviz : prêt", text_color=duo("accepte"))
        else:
            self.lbl_graphviz.configure(
                text="Graphviz : introuvable (dessin désactivé)", text_color=duo("avertissement"),
            )
        self._statut("Prêt. Choisis un exemple ou écris une expression, puis « Construire ».")
        self.protocol("WM_DELETE_WINDOW", self._fermer)
        self.after(300, self._construire)

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------

    def _construire_widgets(self):
        """Assemble l'en-tête, la colonne de gauche, les onglets et la barre d'état."""
        pol = self.polices
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- en-tête -----------------------------------------------------
        entete = ctk.CTkFrame(self, fg_color="transparent")
        entete.grid(row=0, column=0, columnspan=2, sticky="ew", padx=MARGE, pady=(MARGE, 10))
        entete.grid_columnconfigure(0, weight=1)
        titres = ctk.CTkFrame(entete, fg_color="transparent")
        titres.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            titres, text="⬡  Reconnaisseur de langage régulier", font=pol["titre"],
            text_color=duo("texte"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            titres,
            text="Expression régulière  →  AFN-ε  →  AFD  →  AFD minimal  →  reconnaissance d'un mot",
            font=pol["petit"], text_color=duo("texte_doux"),
        ).pack(anchor="w")
        boutons = ctk.CTkFrame(entete, fg_color="transparent")
        boutons.grid(row=0, column=1, sticky="e")
        self.btn_export = _bouton(
            boutons, f"{ICONES['exporter']}  Exporter", self._ouvrir_menu_export,
            pol, principal=False, largeur=120,
        )
        self.btn_export.pack(side="left", padx=(0, 8))
        self.btn_aide = _bouton(
            boutons, f"{ICONES['aide']}  Aide", self._ouvrir_aide, pol,
            principal=False, largeur=96,
        )
        self.btn_aide.pack(side="left", padx=(0, 8))
        self.btn_theme = _bouton(
            boutons, ICONES["theme_clair"], self._basculer_theme, pol,
            principal=False, largeur=48,
        )
        self.btn_theme.pack(side="left")

        # --- colonne de gauche -------------------------------------------
        gauche = ctk.CTkScrollableFrame(self, width=LARGEUR_GAUCHE, fg_color="transparent")
        gauche.grid(row=1, column=0, sticky="ns", padx=(MARGE, MARGE), pady=(0, MARGE))
        self._carte_saisie(gauche)
        self._carte_construction(gauche)
        self._carte_mot(gauche)

        # --- colonne de droite : onglets ---------------------------------
        droite = ctk.CTkFrame(self, fg_color="transparent")
        droite.grid(row=1, column=1, sticky="nsew", padx=(0, MARGE), pady=(0, MARGE))
        droite.grid_rowconfigure(1, weight=1)
        droite.grid_columnconfigure(0, weight=1)
        barre = ctk.CTkFrame(droite, fg_color="transparent")
        barre.grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.btns_onglets = {}
        for i, nom in enumerate(ONGLETS):
            bouton = ctk.CTkButton(
                barre, text=nom, font=pol["gras"], corner_radius=10, height=36,
                width=170, border_width=0, command=lambda n=nom: self._choisir_onglet(n),
            )
            bouton.grid(row=0, column=i, padx=(0, 8))
            self.btns_onglets[nom] = bouton
        zone = ctk.CTkFrame(droite, fg_color="transparent")
        zone.grid(row=1, column=0, sticky="nsew")
        zone.grid_rowconfigure(0, weight=1)
        zone.grid_columnconfigure(0, weight=1)
        self.vues = {}
        for nom in ONGLETS:
            vue = VueAutomate(zone, pol, self.mode)
            vue.grid(row=0, column=0, sticky="nsew")
            self.vues[nom] = vue

        # --- barre d'état --------------------------------------------------
        barre_etat = ctk.CTkFrame(self, corner_radius=0, height=34, fg_color=duo("surface"))
        barre_etat.grid(row=2, column=0, columnspan=2, sticky="ew")
        barre_etat.grid_columnconfigure(0, weight=1)
        self.lbl_statut = ctk.CTkLabel(
            barre_etat, text="", font=pol["petit"], anchor="w", text_color=duo("texte_doux"),
        )
        self.lbl_statut.grid(row=0, column=0, sticky="ew", padx=MARGE, pady=6)
        self.lbl_graphviz = ctk.CTkLabel(
            barre_etat, text="", font=pol["petit"], anchor="e", text_color=duo("texte_doux"),
        )
        self.lbl_graphviz.grid(row=0, column=1, sticky="e", padx=MARGE, pady=6)

    def _carte_saisie(self, maitre):
        """Carte « Saisie » : alphabet, expression, aperçu, exemples, bouton Construire."""
        pol = self.polices
        carte, corps = _carte(maitre, f"{ICONES['exemple']}  Saisie", pol)
        carte.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            corps, text="Alphabet", font=pol["gras"], text_color=duo("texte"), anchor="w",
        ).pack(fill="x")
        self.entree_alphabet = _champ(corps, pol, "a b    ou    a,b")
        self.entree_alphabet.pack(fill="x", pady=(4, 2))
        self.entree_alphabet.insert(0, "a b")
        self.lbl_alphabet = ctk.CTkLabel(
            corps, text="", font=pol["petit"], anchor="w", justify="left",
            wraplength=LARGEUR_TEXTE,
        )
        self.lbl_alphabet.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            corps, text="Expression régulière", font=pol["gras"],
            text_color=duo("texte"), anchor="w",
        ).pack(fill="x")
        self.entree_expression = _champ(corps, pol, "(a+b)*abb")
        self.entree_expression.pack(fill="x", pady=(4, 6))
        self.entree_expression.insert(0, "(a+b)*abb")
        _legende(corps, "Aperçu (le caractère fautif apparaît en rouge)", pol).pack(fill="x")
        self.apercu = _zone_texte(corps, pol, 40, "code_gras")
        self.apercu.pack(fill="x", pady=(2, 2))
        self.lbl_expression = ctk.CTkLabel(
            corps, text="", font=pol["petit"], anchor="w", justify="left",
            wraplength=LARGEUR_TEXTE,
        )
        self.lbl_expression.pack(fill="x", pady=(0, 10))

        for champ in (self.entree_alphabet, self.entree_expression):
            champ.bind("<KeyRelease>", self._valider_en_direct)
            champ.bind("<Return>", self._construire)

        libelles = []
        for alphabet, expression, description in EXEMPLES:
            libelle = f"{expression}   —   {description}"
            self._exemples[libelle] = (alphabet, expression)
            libelles.append(libelle)
        self.liste_exemples = ctk.CTkComboBox(
            corps, values=libelles, command=self._choisir_exemple, state="readonly",
            font=pol["normal"], dropdown_font=pol["normal"], height=36, corner_radius=10,
            border_width=1, fg_color=duo("surface_alt"), border_color=duo("bordure"),
            button_color=duo("accent"), button_hover_color=duo("accent_survol"),
            text_color=duo("texte"), dropdown_fg_color=duo("surface"),
            dropdown_text_color=duo("texte"), dropdown_hover_color=duo("accent"),
        )
        self.liste_exemples.set(f"{ICONES['exemple']}  Choisir un exemple…")
        self.liste_exemples.pack(fill="x", pady=(0, 10))

        self.btn_construire = _bouton(
            corps, f"{ICONES['construire']}  Construire les automates", self._construire, pol,
        )
        self.btn_construire.pack(fill="x")
        _legende(
            corps, "Syntaxe : + ou | union · * étoile · ε ou @ mot vide · ( ) groupes", pol,
        ).pack(fill="x", pady=(8, 0))

    def _carte_construction(self, maitre):
        """Carte « Construction » : étapes de l'expression et nombre d'états."""
        pol = self.polices
        carte, corps = _carte(maitre, f"{ICONES['construire']}  Construction", pol)
        carte.pack(fill="x", pady=(0, 12))

        def ligne(titre):
            _legende(corps, titre, pol).pack(fill="x")
            valeur = ctk.CTkLabel(
                corps, text="–", font=pol["code"], text_color=duo("texte"), anchor="w",
                justify="left", wraplength=LARGEUR_TEXTE,
            )
            valeur.pack(fill="x", pady=(0, 8))
            return valeur

        self.lbl_jetons = ligne("Jetons")
        self.lbl_explicite = ligne("Concaténation explicite (le point « . » est inséré)")
        self.lbl_postfixe = ligne("Forme postfixée")

        tuiles = ctk.CTkFrame(corps, fg_color="transparent")
        tuiles.pack(fill="x", pady=(4, 0))
        tuiles.grid_columnconfigure((0, 1, 2), weight=1, uniform="tuile")
        self.nombres = {}
        for i, nom in enumerate(ONGLETS):
            cadre = ctk.CTkFrame(tuiles, corner_radius=12, fg_color=duo("surface_alt"))
            cadre.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 6, 0))
            nombre = ctk.CTkLabel(cadre, text="–", font=pol["titre"], text_color=duo("accent"))
            nombre.pack(pady=(10, 0))
            _legende(cadre, f"états {nom}", pol).pack(pady=(0, 10))
            self.nombres[nom] = nombre

    def _carte_mot(self, maitre):
        """Carte « Test d'un mot » : champ, verdict, trace, explication et animation."""
        pol = self.polices
        carte, corps = _carte(maitre, f"{ICONES['tester']}  Test d'un mot", pol)
        carte.pack(fill="x", pady=(0, 12))

        ligne = ctk.CTkFrame(corps, fg_color="transparent")
        ligne.pack(fill="x")
        ligne.grid_columnconfigure(0, weight=1)
        self.entree_mot = _champ(ligne, pol, "mot à tester (vide = ε)")
        self.entree_mot.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.entree_mot.bind("<Return>", self._tester)
        self.btn_tester = _bouton(
            ligne, f"{ICONES['tester']}  Tester", self._tester, pol, largeur=110,
        )
        self.btn_tester.grid(row=0, column=1)

        self.badge = ctk.CTkLabel(
            corps, text="", font=pol["sous_titre"], corner_radius=12, height=42,
        )
        self.badge.pack(fill="x", pady=(12, 6))
        self.lbl_explication = ctk.CTkLabel(
            corps, text="", font=pol["normal"], text_color=duo("texte"), anchor="w",
            justify="left", wraplength=LARGEUR_TEXTE,
        )
        self.lbl_explication.pack(fill="x", pady=(0, 8))

        _legende(corps, "Mot lu (la dernière lettre lue est en surbrillance)", pol).pack(fill="x")
        self.zone_mot = _zone_texte(corps, pol, 44, "code_gras")
        self.zone_mot.pack(fill="x", pady=(2, 8))
        _legende(corps, "Trace du calcul", pol).pack(fill="x")
        self.zone_trace = _zone_texte(corps, pol, 104)
        self.zone_trace.pack(fill="x", pady=(2, 10))

        self.lbl_etape = ctk.CTkLabel(
            corps, text="", font=pol["petit"], text_color=duo("texte_doux"), anchor="w",
        )
        self.lbl_etape.pack(fill="x")
        commandes = ctk.CTkFrame(corps, fg_color="transparent")
        commandes.pack(fill="x", pady=(4, 0))
        self.btn_prec = _bouton(
            commandes, f"{ICONES['precedent']}  Préc.", self._precedent, pol,
            principal=False, largeur=96,
        )
        self.btn_prec.pack(side="left", padx=(0, 6))
        self.btn_lecture = _bouton(
            commandes, f"{ICONES['lecture']}  Lecture", self._basculer_lecture, pol, largeur=120,
        )
        self.btn_lecture.pack(side="left", padx=(0, 6))
        self.btn_suiv = _bouton(
            commandes, f"Suiv.  {ICONES['suivant']}", self._suivant, pol,
            principal=False, largeur=96,
        )
        self.btn_suiv.pack(side="left")

    def _raccourcis(self):
        """Associe les raccourcis clavier."""
        self.bind("<F1>", lambda _e: self._ouvrir_aide())
        self.bind("<Control-d>", lambda _e: self._basculer_theme())
        self.bind("<Control-t>", lambda _e: self._tester())
        self.bind("<Control-p>", lambda _e: self._basculer_lecture())
        self.bind("<Alt-Left>", lambda _e: self._precedent())
        self.bind("<Alt-Right>", lambda _e: self._suivant())

    def _appliquer_tags(self):
        """Configure les couleurs des balises des zones de texte (dépendent du mode)."""
        p = palette(self.mode)
        self.apercu.tag_config("faute", background=p["rejete"], foreground="#FFFFFF")
        self.zone_mot.tag_config("derniere", background=p["accent"], foreground=p["accent_texte"])
        self.zone_mot.tag_config("lue", foreground=p["texte_doux"])
        self.zone_trace.tag_config("actuel", background=p["accent"], foreground=p["accent_texte"])
        self.zone_trace.tag_config("future", foreground=p["texte_doux"])

    # ------------------------------------------------------------------
    # Petits utilitaires d'affichage
    # ------------------------------------------------------------------

    def _statut(self, texte, genre="info"):
        """Affiche un message dans la barre d'état (info, ok, erreur, avertissement)."""
        icones = {
            "info": "●", "ok": ICONES["accepte"],
            "erreur": ICONES["rejete"], "avertissement": ICONES["alerte"],
        }
        couleurs = {
            "info": "texte_doux", "ok": "accepte",
            "erreur": "rejete", "avertissement": "avertissement",
        }
        self.lbl_statut.configure(
            text=f"{icones[genre]}   {texte}", text_color=duo(couleurs[genre]),
        )

    @staticmethod
    def _dire(etiquette, texte, nom_couleur):
        """Écrit un texte coloré dans une étiquette."""
        etiquette.configure(text=texte, text_color=duo(nom_couleur))

    def _choisir_onglet(self, nom):
        """Affiche l'onglet demandé et met à jour l'apparence des boutons."""
        self._onglet_actif = nom
        self.vues[nom].tkraise()
        for autre, bouton in self.btns_onglets.items():
            actif = autre == nom
            bouton.configure(
                fg_color=duo("accent") if actif else duo("surface_alt"),
                hover_color=duo("accent_survol") if actif else duo("bordure"),
                text_color=duo("accent_texte") if actif else duo("texte"),
            )

    # ------------------------------------------------------------------
    # Saisie et construction
    # ------------------------------------------------------------------

    def _valider_en_direct(self, _evenement=None):
        """Valide l'alphabet et l'expression à chaque frappe ; surligne le caractère fautif."""
        alphabet, erreur = analyser_alphabet(self.entree_alphabet.get())
        if alphabet is None:
            self._dire(self.lbl_alphabet, f"{ICONES['rejete']}  {erreur}", "rejete")
        else:
            self._dire(
                self.lbl_alphabet,
                f"{ICONES['accepte']}  Alphabet : {{" + ", ".join(alphabet) + "}", "accepte",
            )

        expression = nettoyer_expression(self.entree_expression.get())
        position = None
        if not expression:
            self._dire(
                self.lbl_expression,
                "Écris une expression ou choisis un exemple ci-dessous.", "texte_doux",
            )
        elif alphabet is None:
            self._dire(
                self.lbl_expression,
                f"{ICONES['alerte']}  Corrige d'abord l'alphabet pour valider l'expression.",
                "avertissement",
            )
        else:
            ok, message = valider_expression(expression, alphabet)
            if ok:
                self._dire(
                    self.lbl_expression,
                    f"{ICONES['accepte']}  Expression bien écrite.", "accepte",
                )
            else:
                position = extraire_position(message)
                self._dire(self.lbl_expression, f"{ICONES['rejete']}  {message}", "rejete")

        if position is not None and 1 <= position <= len(expression):
            segments = [
                (expression[:position - 1], None),
                (expression[position - 1], "faute"),
                (expression[position:], None),
            ]
        else:
            segments = [(expression, None)]
        _ecrire_zone(self.apercu, segments)

    def _choisir_exemple(self, libelle):
        """Remplit les champs avec l'exemple choisi et construit les automates."""
        alphabet, expression = self._exemples[libelle]
        self.entree_alphabet.delete(0, "end")
        self.entree_alphabet.insert(0, alphabet)
        self.entree_expression.delete(0, "end")
        self.entree_expression.insert(0, expression)
        self._valider_en_direct()
        self._construire()

    def _construire(self, _evenement=None):
        """Valide la saisie, construit les trois automates et met l'affichage à jour."""
        self._arreter_lecture()
        alphabet, erreur = analyser_alphabet(self.entree_alphabet.get())
        if alphabet is None:
            self._statut(f"Alphabet invalide : {erreur}", "erreur")
            return
        expression = nettoyer_expression(self.entree_expression.get())
        if not expression:
            self._statut("L'expression est vide : écris-en une ou choisis un exemple.", "erreur")
            return
        ok, message = valider_expression(expression, alphabet)
        if not ok:
            self._statut(f"Expression invalide. {message}", "erreur")
            return

        self._statut("Construction en cours…")
        self.configure(cursor="watch")
        self.update_idletasks()
        try:
            afn, afd, minimal = construire_automates(expression, alphabet)
            jetons, _ = analyser_lexicalement(expression, alphabet)
            explicite = rendre_concat_explicite(jetons)
            postfixe = vers_postfixe(explicite)
        except Exception as probleme:   # l'interface ne doit jamais s'arrêter sur une erreur
            self._statut(f"Construction impossible : {probleme}", "erreur")
            return
        finally:
            self.configure(cursor="")

        self.alphabet = alphabet
        self.afn, self.afd, self.minimal = afn, afd, minimal
        self._dire(
            self.lbl_jetons, "  ".join(jeton.valeur for jeton in jetons), "texte",
        )
        self._dire(self.lbl_explicite, jetons_en_texte(explicite), "texte")
        self._dire(self.lbl_postfixe, jetons_en_texte(postfixe), "texte")

        trop_grand = []
        for nom, automate in zip(ONGLETS, (afn, afd, minimal)):
            n = len(automate.etats)
            self.nombres[nom].configure(
                text=str(n),
                text_color=duo("avertissement" if n > SEUIL_ETATS else "accent"),
            )
            self.btns_onglets[nom].configure(text=f"{nom}  ·  {n}")
            if n > SEUIL_ETATS:
                trop_grand.append(f"{nom} : {n} états")
            self.vues[nom].afficher(automate, self.mode)

        self._reinitialiser_test()
        self._choisir_onglet(NOM_MIN)
        if trop_grand:
            self._statut(
                "Automate volumineux (" + " ; ".join(trop_grand) + f", seuil {SEUIL_ETATS}). "
                "La déterminisation peut produire jusqu'à 2ⁿ états.", "avertissement",
            )
        else:
            self._statut(
                f"Automates construits pour {expression} : AFN-ε {len(afn.etats)} états, "
                f"AFD {len(afd.etats)}, AFD minimal {len(minimal.etats)}.", "ok",
            )

    # ------------------------------------------------------------------
    # Test d'un mot et animation
    # ------------------------------------------------------------------

    def _reinitialiser_test(self):
        """Efface le résultat du dernier test (nouvel automate ou démarrage)."""
        self._arreter_lecture()
        self._chemin = None
        self._accepte = None
        self._etape = 0
        self.badge.configure(
            text="En attente d'un mot", fg_color=duo("surface_alt"),
            text_color=duo("texte_doux"),
        )
        self.lbl_explication.configure(text="")
        _ecrire_zone(self.zone_mot, [])
        _ecrire_zone(self.zone_trace, [])
        self.lbl_etape.configure(text="")
        for bouton in (self.btn_prec, self.btn_lecture, self.btn_suiv):
            bouton.configure(state="disabled")
        self.vues[NOM_MIN].table.deselectionner()

    def _tester(self, _evenement=None):
        """Teste le mot saisi sur l'AFD minimal et lance l'animation du calcul."""
        if self.minimal is None:
            self._statut("Construis d'abord les automates.", "avertissement")
            return
        mot, erreur = analyser_mot(self.entree_mot.get(), self.alphabet)
        if mot is None:
            self._statut(f"Mot invalide : {erreur}", "erreur")
            self._dire(self.lbl_explication, f"{ICONES['rejete']}  {erreur}", "rejete")
            return

        self._arreter_lecture()
        accepte, chemin = reconnaitre(self.minimal, mot)
        self._mot, self._chemin, self._accepte = mot, chemin, accepte
        if accepte:
            self.badge.configure(
                text=f"{ICONES['accepte']}   ACCEPTÉ", fg_color=duo("accepte"),
                text_color="#FFFFFF",
            )
        else:
            self.badge.configure(
                text=f"{ICONES['rejete']}   REJETÉ", fg_color=duo("rejete"),
                text_color="#FFFFFF",
            )
        self._dire(self.lbl_explication, expliquer(self.minimal, chemin), "texte")
        self._statut(
            f"Mot « {mot or EPSILON} » : {'accepté' if accepte else 'rejeté'} "
            f"({len(chemin) - 1} lettre(s) lue(s)).", "ok" if accepte else "avertissement",
        )
        self._choisir_onglet(NOM_MIN)
        self._etape = 0
        self._afficher_etape()
        self._basculer_lecture()

    def _afficher_etape(self):
        """Affiche l'étape courante : dessin colorié, table, mot, trace et boutons."""
        if self._chemin is None:
            return
        i = self._etape
        dernier = len(self._chemin) - 1
        dot = dot_etape(self.minimal, self._chemin, i, self.mode, self._accepte)
        vue = self.vues[NOM_MIN]
        vue.redessiner(self.mode, dot=dot, conserver_vue=True)
        vue.table.selectionner(self._chemin[i].etat)

        segments = []
        for k, configuration in enumerate(self._chemin):
            if k:
                segments.append(("  ⊢  ", None))
            balise = "actuel" if k == i else ("future" if k > i else None)
            segments.append((formater_configuration(configuration), balise))
        _ecrire_zone(self.zone_trace, segments)

        if self._mot:
            lettres = []
            for k, lettre in enumerate(self._mot):
                balise = "derniere" if k == i - 1 else ("lue" if k < i - 1 else None)
                lettres.append((lettre + " ", balise))
            _ecrire_zone(self.zone_mot, lettres)
        else:
            _ecrire_zone(self.zone_mot, [(EPSILON, None)])

        self.lbl_etape.configure(text=f"Étape {i} / {dernier}   (0 = départ)")
        self.btn_prec.configure(state="normal" if i > 0 else "disabled")
        self.btn_suiv.configure(state="normal" if i < dernier else "disabled")
        self.btn_lecture.configure(state="normal" if dernier > 0 else "disabled")

    def _precedent(self):
        """Revient à l'étape précédente du calcul."""
        if self._chemin is None:
            return
        self._arreter_lecture()
        if self._etape > 0:
            self._etape -= 1
            self._afficher_etape()

    def _suivant(self):
        """Passe à l'étape suivante du calcul."""
        if self._chemin is None:
            return
        self._arreter_lecture()
        if self._etape < len(self._chemin) - 1:
            self._etape += 1
            self._afficher_etape()

    def _basculer_lecture(self):
        """Lance ou met en pause la lecture automatique du calcul."""
        if self._lecture_id is not None:
            self._arreter_lecture()
            return
        if self._chemin is None or len(self._chemin) < 2:
            return
        if self._etape >= len(self._chemin) - 1:   # déjà à la fin : on repart du début
            self._etape = 0
            self._afficher_etape()
        self.btn_lecture.configure(text=f"{ICONES['pause']}  Pause")
        self._lecture_id = self.after(DELAI_LECTURE, self._pas_lecture)

    def _pas_lecture(self):
        """Avance d'une étape pendant la lecture automatique."""
        self._lecture_id = None
        if self._chemin is None:
            return
        if self._etape < len(self._chemin) - 1:
            self._etape += 1
            self._afficher_etape()
        if self._etape < len(self._chemin) - 1:
            self._lecture_id = self.after(DELAI_LECTURE, self._pas_lecture)
        else:
            self.btn_lecture.configure(text=f"{ICONES['lecture']}  Lecture")

    def _arreter_lecture(self):
        """Arrête la lecture automatique si elle est en cours."""
        if self._lecture_id is not None:
            self.after_cancel(self._lecture_id)
            self._lecture_id = None
        self.btn_lecture.configure(text=f"{ICONES['lecture']}  Lecture")

    # ------------------------------------------------------------------
    # Thème, export, aide
    # ------------------------------------------------------------------

    def _basculer_theme(self):
        """Passe du thème sombre au thème clair (et inversement), dessins compris."""
        self.mode = mode_oppose(self.mode)
        appliquer_theme(self.mode)
        self.btn_theme.configure(
            text=ICONES["theme_clair"] if self.mode == MODE_SOMBRE else ICONES["theme_sombre"],
        )
        configurer_style_tableau(self.mode)
        self._appliquer_tags()
        for nom, vue in self.vues.items():
            vue.appliquer_mode(self.mode)
            if nom == NOM_MIN and self._chemin is not None:
                self._afficher_etape()
            else:
                vue.redessiner(self.mode, conserver_vue=True)

    def _ouvrir_menu_export(self):
        """Ouvre le menu d'export sous le bouton « Exporter »."""
        p = palette(self.mode)
        menu = tk.Menu(
            self, tearoff=0, bg=p["surface"], fg=p["texte"], bd=0,
            activebackground=p["accent"], activeforeground=p["accent_texte"],
            font=(POLICE_INTERFACE, 11),
        )
        menu.add_command(label="Fichier DOT…", command=lambda: self._exporter("dot"))
        menu.add_command(label="Image PNG (affichée)…", command=lambda: self._exporter("png"))
        menu.add_command(label="Image SVG (affichée)…", command=lambda: self._exporter("svg"))
        menu.add_command(
            label="Table de transitions (texte)…", command=lambda: self._exporter("table"),
        )
        x = self.btn_export.winfo_rootx()
        y = self.btn_export.winfo_rooty() + self.btn_export.winfo_height()
        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _exporter(self, genre):
        """Exporte l'automate de l'onglet actif (DOT, PNG, SVG ou table en texte)."""
        vue = self.vues[self._onglet_actif]
        if vue.automate is None:
            self._statut("Rien à exporter : construis d'abord les automates.", "avertissement")
            return
        extension, description = {
            "dot": (".dot", "Fichier DOT"), "png": (".png", "Image PNG"),
            "svg": (".svg", "Image SVG"), "table": (".txt", "Texte"),
        }[genre]
        chemin = filedialog.asksaveasfilename(
            parent=self, defaultextension=extension,
            initialfile=f"{NOMS_FICHIERS[self._onglet_actif]}{extension}",
            filetypes=[(description, f"*{extension}")],
        )
        if not chemin:
            return
        try:
            if genre == "dot":
                ecrire_dot(vue.automate, chemin)
            elif genre in ("png", "svg"):
                dot = vue.dot_courant or generer_dot(vue.automate, self.mode)
                exporter_image(dot, chemin, genre)
            else:
                with open(chemin, "w", encoding="utf-8") as fichier:
                    fichier.write(table_en_texte(vue.automate) + "\n")
        except (ErreurRendu, OSError) as probleme:
            self._statut(f"Export impossible : {probleme}", "erreur")
            return
        self._statut(f"Exporté : {chemin}", "ok")

    def _ouvrir_aide(self):
        """Ouvre (ou ramène au premier plan) la fenêtre d'aide sur la syntaxe."""
        if self._fenetre_aide is not None and self._fenetre_aide.winfo_exists():
            self._fenetre_aide.focus()
            return
        fenetre = ctk.CTkToplevel(self)
        fenetre.title("Aide : syntaxe des expressions")
        fenetre.geometry("640x600")
        fenetre.configure(fg_color=duo("fond"))
        texte = ctk.CTkTextbox(
            fenetre, font=self.polices["code"], wrap="word", corner_radius=RAYON_COIN,
            fg_color=duo("surface"), text_color=duo("texte"),
        )
        texte.pack(fill="both", expand=True, padx=MARGE, pady=MARGE)
        texte.insert("1.0", TEXTE_AIDE)
        texte.configure(state="disabled")
        self._fenetre_aide = fenetre
        fenetre.after(200, fenetre.focus)

    def _fermer(self):
        """Ferme proprement la fenêtre (arrête l'animation en cours)."""
        self._arreter_lecture()
        self.destroy()


def lancer():
    """Crée la fenêtre principale et lance la boucle d'événements."""
    Application().mainloop()


if __name__ == "__main__":
    lancer()