"""Thème de Noël : couleurs, gabarit Plotly et briques de mise en page communes."""
import plotly.graph_objects as go
import plotly.io as pio
from dash import dcc, html

from donnees import sprite

# Couleurs (ordre fixe, vérifié avec le validateur de palette : rouge et vert jamais côte à côte)
ROUGE = "#c0392b"
OR = "#c8901a"
SAPIN = "#1f7a52"
GLACE = "#3a78b5"
GRIS = "#c9c4b8"       # tout ce qui n'est pas le message
GRIS_FONCE = "#8a8478"
ENCRE = "#2b2620"
ENCRE_2 = "#5c554b"
CATEGORIES = [ROUGE, OR, SAPIN, GLACE]

# Pokémon de l'hiver qui décorent les pages (numéros de Pokédex)
MASCOTTES = {
    "cadoizo": 225,       # Cadoizo, le livreur de cadeaux
    "blizzi": 459,        # Blizzi
    "blizzaroi": 460,     # Blizzaroi
    "polarhume": 613,     # Polarhume
    "sorbebe": 582,       # Sorbébé
    "stalgamin": 361,     # Stalgamin
    "cerfrousse": 234,    # Cerfrousse
    "obalie": 363,        # Obalie
    "givrali": 471,       # Givrali
    "marcacrin": 220,     # Marcacrin
    "lokhlass": 131,      # Lokhlass
    "pingoleon": 875,     # Pingoléon
}

pio.templates["noel"] = go.layout.Template(
    layout=dict(
        font=dict(family="Nunito, sans-serif", size=14, color=ENCRE),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=CATEGORIES,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis=dict(gridcolor="#ece6d9", zerolinecolor="#d8d0bf", linecolor="#d8d0bf", automargin=True),
        yaxis=dict(gridcolor="#ece6d9", zerolinecolor="#d8d0bf", linecolor="#d8d0bf", automargin=True),
        hoverlabel=dict(bgcolor="#fffdf7", bordercolor=ROUGE, font=dict(family="Nunito", color=ENCRE)),
        legend=dict(orientation="h", y=1.08, x=0, bgcolor="rgba(0,0,0,0)"),
        bargap=0.25,
    )
)
pio.templates.default = "noel"

GRAPH_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]}


def image(dex, taille=96, classe="sprite", titre=None):
    return html.Img(src=sprite(dex), className=classe, width=taille, height=taille,
                    alt=titre or "", title=titre or "")


def entete_page(titre, sous_titre, mascotte):
    """Bandeau de page : titre festif + un Pokémon de l'hiver."""
    return html.Div(className="entete-page", children=[
        html.Div([html.H1(titre), html.P(sous_titre, className="sous-titre")]),
        image(MASCOTTES[mascotte], 130, "mascotte"),
    ])


def question(q, reponse, contenu, methode=None, id_ancre=None):
    """Un bloc = une question, la réponse en une phrase, un graphique qui la prouve.
    Le détail technique est replié dans « Déballer la méthode »."""
    enfants = [
        html.Div(className="ruban"),
        html.H2(q, className="question"),
        html.P(reponse, className="reponse"),
        html.Div(contenu, className="contenu"),
    ]
    if methode:
        enfants.append(html.Details(className="methode", children=[
            html.Summary("🎁 Déballer la méthode"),
            html.Div(methode, className="methode-texte"),
        ]))
    extra = {"id": id_ancre} if id_ancre else {}
    return html.Section(className="carte-question", children=enfants, **extra)


COURS = {
    "exploration": ("Cours Exploration", "cours-exploration"),
    "clustering": ("Cours Clustering", "cours-clustering"),
    "reseaux": ("Cours Réseaux", "cours-reseaux"),
    "transfo": ("Cours Transformations", "cours-transfo"),
    "hors": ("Hors cours", "cours-hors"),
}


def etapes(liste, attention=None):
    """Méthode détaillée : une suite d'étapes (titre, texte, [cours…]).
    Chaque étape dit quelle notion du cours on a utilisée, ou si c'est hors cours."""
    items = []
    for titre, texte, cours in liste:
        cours = [cours] if isinstance(cours, str) else cours
        items.append(html.Li(className="etape", children=[
            html.Div(className="etape-tete", children=[
                html.Strong(titre),
                *[html.Span(COURS[c][0], className=f"tag-cours {COURS[c][1]}") for c in cours],
            ]),
            html.Div(texte, className="etape-texte"),
        ]))
    enfants = [html.Ol(items, className="etapes")]
    if attention:
        enfants.append(html.Div(className="attention", children=[html.Strong("⚠️ À garder en tête : "), attention]))
    return html.Div(enfants)


def mini(fig, hauteur=240, legende=None):
    """Petit graphique dans une étape de méthode (il se redimensionne quand on ouvre le bloc)."""
    fig.update_layout(height=hauteur, margin=dict(l=10, r=10, t=10, b=10), showlegend=fig.layout.showlegend)
    enfants = [dcc.Graph(figure=fig, config={"displayModeBar": False}, responsive=True, className="mini-graphe")]
    if legende:
        enfants.append(html.Div(legende, className="mini-legende"))
    return html.Div(enfants, className="mini")


def graphe(fig, hauteur=380, **kw):
    fig.update_layout(height=hauteur)
    return dcc.Graph(figure=fig, config=GRAPH_CONFIG, **kw)


def tuile(valeur, legende):
    return html.Div(className="tuile", children=[
        html.Div(valeur, className="tuile-valeur"),
        html.Div(legende, className="tuile-legende"),
    ])


def galerie(dexs, noms, legendes=None, taille=88):
    """Rangée de Pokémon avec leur nom (et une légende facultative)."""
    legendes = legendes or [None] * len(dexs)
    return html.Div(className="galerie", children=[
        html.Div(className="galerie-item", children=[
            image(d, taille, titre=n),
            html.Div(n, className="galerie-nom"),
            html.Div(l, className="galerie-legende") if l else None,
        ]) for d, n, l in zip(dexs, noms, legendes)
    ])


def cadeau_ferme(titre, qui, contenu_prevu, mascotte):
    """Page pas encore faite : un cadeau encore emballé."""
    return html.Div([
        entete_page(titre, "Page en préparation", mascotte),
        html.Section(className="carte-question cadeau-ferme", children=[
            html.Div("🎁", className="gros-cadeau"),
            html.H2("Ce cadeau n'est pas encore déballé"),
            html.P([f"Cette page est préparée par {qui}. Elle répondra à : "]),
            html.Ul([html.Li(c) for c in contenu_prevu]),
        ]),
    ])


def pct(x, dec=0):
    return f"{x * 100:.{dec}f}".replace(".", ",")


def fr(x, dec=2):
    return f"{x:.{dec}f}".replace(".", ",")
