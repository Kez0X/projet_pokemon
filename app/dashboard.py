"""Le Pokédex de Noël : dashboard Dash du projet « Qu'est-ce qui rend un Pokémon populaire ? ».

En local, depuis la racine du projet :
    .venv/bin/python app/dashboard.py
puis ouvrir http://127.0.0.1:8050

Sur Vercel : « Root Directory » = app, l'entrée est app/index.py (variable `app` = le serveur Flask de Dash).
"""
import dash
from dash import Dash, dcc, html
import theme  # noqa: F401  (enregistre le gabarit Plotly « noel »)

app = Dash(
    __name__,
    use_pages=True,
    title="Le Pokédex de Noël",
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Mountains+of+Christmas:wght@700"
        "&family=Nunito:wght@400;600;800&display=swap"
    ],
    suppress_callback_exceptions=True,
)
server = app.server


# Ordre du menu : les pages de Luka puis celles de Lucas, puis Méthodes
MENU = [
    ("/", "Accueil"),
    ("/classement", "Classement"),
    ("/sur-sous-cotes", "Sur / sous-cotés"),
    ("/conception", "Design ou nostalgie"),
    ("/noms", "Les noms"),
    ("/biologie", "Biologie"),
    ("/reseau", "Le réseau"),
    ("/carte", "Le monde"),
    ("/temps", "Dans le temps"),
    ("/methodes", "Méthodes"),
]


def guirlande(n=28):
    return html.Div(className="guirlande", children=[
        html.Span(className=f"ampoule a{i % 4}") for i in range(n)
    ])


app.layout = html.Div(className="page", children=[
    html.Div(className="neige", **{"aria-hidden": "true"}),
    html.Div(className="neige neige-2", **{"aria-hidden": "true"}),
    html.Header(className="haut", children=[
        guirlande(),
        html.Div(className="marque", children=[
            theme.image(theme.MASCOTTES["cadoizo"], 64, "marque-img"),
            html.Div([
                html.Div("Le Pokédex de Noël", className="marque-titre"),
                html.Div("Qu'est-ce qui rend un Pokémon populaire ?", className="marque-sous"),
            ]),
        ]),
        html.Nav(className="menu", children=[
            dcc.Link(nom, href=chemin, className="boule") for chemin, nom in MENU
        ]),
    ]),
    html.Main(className="contenu-page", children=[dash.page_container]),
    html.Footer(className="bas", children=[
        html.Span("Projet d'analyse de données · M2 · Luka & Lucas · "),
        html.Span("Images : illustrations officielles (The Pokémon Company), via PokéAPI. "),
        html.Span("Joyeux Noël ✨"),
    ]),
])


if __name__ == "__main__":
    app.run(debug=True)
