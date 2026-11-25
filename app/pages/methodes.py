"""Page Méthodes : les méthodes du cours utilisées, page par page, et les sources."""
import dash
from dash import html

import theme as t

dash.register_page(__name__, path="/methodes", name="Méthodes", order=9)

METHODES = [
    ("Exploration et préparation", "Table maître, percentiles, intervalles de confiance de Wilson, corrélation de Spearman",
     "Classement, Sur / sous-cotés, Les noms"),
    ("Régression linéaire et résidus", "Popularité prévue par les effets attendus, puis top / flop des résidus",
     "Sur / sous-cotés"),
    ("Clustering", "k-means sur les pixels (coude, silhouette) ; CAH Ward et k-means sur les pays",
     "Design ou nostalgie, Le monde"),
    ("Analyse en composantes principales", "12 variables de design, trajectoire des générations",
     "Design ou nostalgie"),
    ("Réseaux", "Graphe des k plus proches voisins, communautés de Louvain, centralités",
     "Le réseau"),
    ("Plongements et projections", "node2vec (marches aléatoires + Word2Vec), t-SNE, MDS",
     "Le réseau, Le monde"),
    ("Statistique spatiale", "Indice de Moran et LISA",
     "Le monde"),
    ("Tests (hors cours)", "Transcription phonétique (espeak-ng), test du signe sur les lignées d'évolution, "
     "Mann-Whitney, Kruskal-Wallis, tests par permutation, correction de Holm pour les tests multiples",
     "Les noms, Le réseau"),
]

SOURCES = [
    ("PokéAPI", "Attributs, noms français, anglais et japonais, lignées d'évolution, illustrations officielles"),
    ("Sondage Reddit r/pokemon 2019", "52 836 votes, générations 1 à 7"),
    ("Johto Times / Dragonfly Cave 2025", "Votes par génération, relevés dans la vidéo des résultats"),
    ("Google Trends", "Intérêt par pays, 2021-2026, chaque Pokémon ramené à Ectoplasma (Gengar) ; 28 noms qui sont aussi des mots retirés"),
    ("Pokémon of the Year 2020", "Top 30 par région, plus de 6,6 millions de votes"),
    ("TheToyZone 2024", "Pokémon favori par pays et génération (pour comparer)"),
    ("Natural Earth", "Contours et voisinages des pays"),
]


def tableau(entetes, lignes):
    return html.Table(className="tableau", children=[
        html.Thead(html.Tr([html.Th(e) for e in entetes])),
        html.Tbody([html.Tr([html.Td(c) for c in l]) for l in lignes]),
    ])


def layout():
    return html.Div([
        t.entete_page("Dans la hotte : nos méthodes",
                      "Les méthodes du cours qu'on a utilisées, et où les retrouver.", "lokhlass"),
        html.Section(className="carte-question", children=[
            html.Div(className="ruban"),
            html.H2("Les méthodes", className="question"),
            tableau(["Méthode", "Ce qu'on en a fait", "Pages"], METHODES),
        ]),
        html.Section(className="carte-question", children=[
            html.Div(className="ruban"),
            html.H2("Les sources", className="question"),
            tableau(["Source", "Contenu"], SOURCES),
            html.P("Le détail de la collecte est dans docs/sources_donnees.md, et chaque analyse dans les notebooks 01 à 08.",
                   className="note"),
        ]),
        html.Section(className="carte-question", children=[
            html.Div(className="ruban"),
            html.H2("Les limites à garder en tête", className="question"),
            html.Ul([
                html.Li("Les sondages viennent de publics anglophones de fans : le pays des votants n'est pas connu."),
                html.Li("Google mesure l'attention plus que l'affection. Les noms qui sont aussi des mots (Persian, Ditto, Onix…) ont été retirés, mais d'autres pièges peuvent rester."),
                html.Li("On cherche les noms anglais partout : le Japon, la Corée ou la Chine sont mal mesurés."),
            ]),
            html.P("Texte à compléter par Lucas.", className="note"),
        ]),
    ])
