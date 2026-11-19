"""Thème : palettes de couleurs, polices et constantes de l'interface."""

MODE_SOMBRE = "sombre"
MODE_CLAIR = "clair"

# Correspondance avec les noms de modes de CustomTkinter
_MODES_CTK = {MODE_SOMBRE: "Dark", MODE_CLAIR: "Light"}

# Chaque palette contient exactement les mêmes clés.
# Les clés "dessin_*" servent au rendu Graphviz (voir dessin.py).
PALETTES = {
    MODE_SOMBRE: {
        # --- interface ---
        "fond": "#0F1220",
        "surface": "#181C2F",
        "surface_alt": "#20253D",
        "bordure": "#2C3252",
        "texte": "#E6E9F5",
        "texte_doux": "#8D94B5",
        "accent": "#7C5CFF",
        "accent_survol": "#6A4AE8",
        "accent_texte": "#FFFFFF",
        "accepte": "#2ECC8F",
        "rejete": "#FF5C7A",
        "avertissement": "#FFB547",
        # --- dessin des automates ---
        "dessin_fond": "#181C2F",
        "dessin_noeud_fond": "#20253D",
        "dessin_noeud_bord": "#7C5CFF",
        "dessin_noeud_texte": "#E6E9F5",
        "dessin_final_fond": "#1B3A33",
        "dessin_final_bord": "#2ECC8F",
        "dessin_initial": "#FFB547",
        "dessin_fleche": "#8D94B5",
        "dessin_epsilon": "#FF9F6B",
        "dessin_etiquette": "#E6E9F5",
        "dessin_courant_fond": "#7C5CFF",
        "dessin_courant_texte": "#FFFFFF",
        "dessin_chemin": "#2ECC8F",
        "dessin_visite_fond": "#2C3252",
        "dessin_visite_texte": "#8D94B5",
    },
    MODE_CLAIR: {
        # --- interface ---
        "fond": "#F3F4FB",
        "surface": "#FFFFFF",
        "surface_alt": "#ECEEF8",
        "bordure": "#D9DCEE",
        "texte": "#1D2140",
        "texte_doux": "#6B7194",
        "accent": "#6C4DF5",
        "accent_survol": "#5B3CE0",
        "accent_texte": "#FFFFFF",
        "accepte": "#14A870",
        "rejete": "#E5395B",
        "avertissement": "#E08A00",
        # --- dessin des automates ---
        "dessin_fond": "#FFFFFF",
        "dessin_noeud_fond": "#F3F0FF",
        "dessin_noeud_bord": "#6C4DF5",
        "dessin_noeud_texte": "#1D2140",
        "dessin_final_fond": "#E3F7EE",
        "dessin_final_bord": "#14A870",
        "dessin_initial": "#E08A00",
        "dessin_fleche": "#6B7194",
        "dessin_epsilon": "#E5733B",
        "dessin_etiquette": "#1D2140",
        "dessin_courant_fond": "#6C4DF5",
        "dessin_courant_texte": "#FFFFFF",
        "dessin_chemin": "#14A870",
        "dessin_visite_fond": "#E1E4F3",
        "dessin_visite_texte": "#6B7194",
    },
}

# Polices : Segoe UI pour l'interface, Consolas pour le code (expressions, mots, traces)
POLICE_INTERFACE = "Segoe UI"
POLICE_CODE = "Consolas"

TAILLES = {
    "titre": 24,
    "sous_titre": 16,
    "normal": 13,
    "petit": 11,
    "code": 14,
}

# Icônes Unicode (affichées avec la police Segoe UI Symbol si besoin)
ICONES = {
    "construire": "⚙",
    "tester": "▶",
    "precedent": "◀",
    "suivant": "▶",
    "lecture": "▶",
    "pause": "⏸",
    "recentrer": "⟲",
    "theme_sombre": "☾",
    "theme_clair": "☀",
    "exporter": "⬇",
    "accepte": "✓",
    "rejete": "✗",
    "alerte": "⚠",
    "aide": "?",
    "exemple": "✦",
}

# Dimensions et seuils
RAYON_COIN = 14
MARGE = 16
LARGEUR_MIN = 1100
HAUTEUR_MIN = 720
SEUIL_ETATS = 30   # au-delà, avertissement (la déterminisation peut produire 2^n états)


def mode_oppose(mode):
    """Retourne l'autre mode : sombre devient clair et inversement."""
    return MODE_CLAIR if mode == MODE_SOMBRE else MODE_SOMBRE


def palette(mode):
    """Retourne le dictionnaire de couleurs du mode demandé."""
    if mode not in PALETTES:
        raise ValueError(f"Mode inconnu : {mode}")
    return PALETTES[mode]


def couleur(mode, nom):
    """Retourne la couleur `nom` (code hexadécimal) pour le mode demandé."""
    return palette(mode)[nom]


def duo(nom):
    """Retourne (couleur claire, couleur sombre), le format attendu par CustomTkinter."""
    return (PALETTES[MODE_CLAIR][nom], PALETTES[MODE_SOMBRE][nom])


def appliquer_theme(mode):
    """Applique le mode (sombre ou clair) à toute l'application CustomTkinter."""
    import customtkinter as ctk
    ctk.set_appearance_mode(_MODES_CTK[mode])
    ctk.set_default_color_theme("blue")


def creer_polices():
    """Crée les polices CustomTkinter ; à appeler APRÈS la création de la fenêtre."""
    import customtkinter as ctk
    t = TAILLES
    return {
        "titre": ctk.CTkFont(family=POLICE_INTERFACE, size=t["titre"], weight="bold"),
        "sous_titre": ctk.CTkFont(family=POLICE_INTERFACE, size=t["sous_titre"], weight="bold"),
        "normal": ctk.CTkFont(family=POLICE_INTERFACE, size=t["normal"]),
        "gras": ctk.CTkFont(family=POLICE_INTERFACE, size=t["normal"], weight="bold"),
        "petit": ctk.CTkFont(family=POLICE_INTERFACE, size=t["petit"]),
        "code": ctk.CTkFont(family=POLICE_CODE, size=t["code"]),
        "code_gras": ctk.CTkFont(family=POLICE_CODE, size=t["code"], weight="bold"),
    }