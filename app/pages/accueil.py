"""Accueil : le fil rouge et « ce qu'il faut retenir », sous forme de calendrier de l'Avent."""
import dash
from dash import dcc, html

import theme as t
from donnees import pays, popularite

dash.register_page(__name__, path="/", name="Accueil", order=0)

# (indice sur la porte, Pokémon derrière, ce qu'on a trouvé, page)
CASES = [
    ("Les anciens ou les nouveaux ?", 1,
     "La génération est l'effet le plus fort : on aime les Pokémon de son enfance.", "/sur-sous-cotes"),
    ("Plus aimés que prévu", 197,
     "Les évolutions d'Évoli, Lucario, Zorua… sont sur-cotés dans les trois sources.", "/sur-sous-cotes"),
    ("Le starter du milieu", 5,
     "On aime Salamèche et Dracaufeu… mais pas Reptincel.", "/sur-sous-cotes"),
    ("De plus en plus colorés", 6,
     "Les Pokémon récents ont plus de couleurs : 2,7 en gén. 1 contre 3,7 en gén. 9.", "/conception"),
    ("Design ou nostalgie ?", 460,
     "Le design a changé, mais il n'explique pas pourquoi les récents sont moins aimés.", "/conception"),
    ("Un nom qui pèse lourd", 143,
     "En japonais, plus il y a de sons durs, plus le Pokémon est lourd, et le nom s'allonge quand il évolue.", "/noms"),
    ("Un joli nom suffit-il ?", 582,
     "Le son du nom ne fait pas la popularité, même au Pokémon of the Year (6,6 millions de votes).", "/noms"),
    ("Dis-moi qui te ressemble", 448,
     "Les Pokémon aimés ont des sosies aimés, mais être original ne change rien.", "/reseau"),
    ("La star du monde", 25,
     "Pikachu est le Pokémon le plus cherché dans 62 pays sur 67.", "/carte"),
    ("Des mots, pas des Pokémon", 53,
     "On a retiré 28 noms qui sont aussi des mots (Persian, Ditto, Onix…) : ils faussaient Google.", "/carte"),
    ("Entre voisins", 133,
     "Les pays voisins aiment les mêmes Pokémon : Amérique latine d'un côté, Europe et Asie de l'Est de l'autre.", "/carte"),
    ("Le cadeau bonus", 225,
     "Quels Pokémon portent les couleurs de Noël ? Rouge et vert, au pixel près.", "/conception"),
]


def case(num, indice, dex, texte, lien):
    return dcc.Link(href=lien, className="case", children=html.Div(className="case-interieur", children=[
        html.Div(className="case-face", children=[
            html.Div(str(num), className="case-num"),
            html.Div(indice, className="case-indice"),
        ]),
        html.Div(className="case-dos", children=[
            t.image(dex, 96),
            html.P(texte),
            html.Div("Voir la page →", className="case-lien"),
        ]),
    ]))


def layout():
    p = popularite()
    n_partout = int((p["categorie"] == "partout").sum())
    return html.Div([
        t.entete_page("Joyeux Noël, dresseurs !",
                      "Qu'est-ce qui fait qu'un Pokémon est populaire ? On a ouvert les sondages, Google et "
                      "1 025 illustrations officielles pour le savoir.", "polarhume"),
        html.P(className="intro", children=[
            "On mesure la popularité avec ", html.Strong("trois sources"),
            " : le sondage Reddit de 2019 (52 836 votes), le sondage du Johto Times en 2025 et les recherches "
            "Google dans le monde. Ensuite on cherche ce qui l'explique : l'âge du Pokémon, son design, ses couleurs, "
            "son nom, ses ressemblances avec les autres et le pays où on vit.",
        ]),
        html.Div(className="tuiles", children=[
            t.tuile("1 025", "Pokémon, des 9 générations"),
            t.tuile("3", "sources de popularité"),
            t.tuile(str(n_partout), "Pokémon populaires partout (top 10 % de leur génération)"),
            t.tuile(str(len(pays())), "pays comparés"),
        ]),
        html.H2("Le calendrier de l'Avent : ce qu'il faut retenir", className="titre-section"),
        html.P("Passe la souris sur une case (ou sélectionne-la au clavier) pour l'ouvrir, clique pour aller à la page.",
               className="intro", style={"fontSize": "15px"}),
        html.Div(className="calendrier", children=[
            case(i + 1, indice, dex, texte, lien) for i, (indice, dex, texte, lien) in enumerate(CASES)
        ]),
    ])
