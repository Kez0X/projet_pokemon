"""Notebook 04 : les noms des Pokémon en japonais et en français (symbolique sonore)."""
import unicodedata

import dash
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html
from scipy.stats import pearsonr, spearmanr

import theme as t
from donnees import noms, popularite, table_maitre

dash.register_page(__name__, path="/noms", name="Les noms", order=4)

PETITS = set("ャュョァィゥェォヮ")
PETITES_VOYELLES = set("ァィゥェォ")


def _voyelle(kana):
    nom = unicodedata.name(kana, "")
    return nom[-1] if nom.startswith("KATAKANA LETTER") and nom[-1] in "AIUEO" else None


def _donnees():
    return (noms()
            .merge(table_maitre()[["dex", "nom_fr", "nom_ja", "nom_ja_roma", "poids_kg", "taille_m",
                                   "total_stats", "stade", "stade_categorie", "generation"]], on="dex")
            .merge(popularite()[["dex", "johto_pct_gen", "reddit_pct_gen"]], on="dex"))


def mores(nom_ja):
    """Découpe un nom en kana en mores (même règle que le notebook 04) : [(texte, voisée ?)]."""
    out = []
    for ch in nom_ja:
        if not ("゠" <= ch <= "ヿ"):
            continue
        voisee = "゙" in unicodedata.normalize("NFD", ch)
        if ch in PETITS and out and not (ch in PETITES_VOYELLES and _voyelle(out[-1][0][-1]) == _voyelle(ch)):
            texte, v = out[-1]
            out[-1] = (texte + ch, v)   # petit kana prononcé avec le kana d'avant (キャ = « kya »)
        else:                           # sinon une more à part (dont ピィ = « pii » : la voyelle est allongée)
            out.append((ch, voisee))
    return out


def tuiles(nom_ja):
    return html.Div(className="tuiles-kana", children=[
        html.Span(texte, className="kana voisee" if v else "kana") for texte, v in mores(nom_ja)
    ])


# ---------- 1. Consonnes dures et poids ----------
def bloc_poids():
    d = _donnees()
    d["classe"] = d["ja_voisees"].clip(upper=3)
    med = d.groupby("classe")["poids_kg"].median()
    eff = d.groupby("classe").size()
    etiq = {0: "aucune", 1: "1", 2: "2", 3: "3 ou plus"}
    fig = go.Figure(go.Bar(
        x=[etiq[i] for i in med.index], y=med.values, marker_cornerradius=4,
        marker_color=[t.GRIS if i == 0 else t.ROUGE for i in med.index],
        customdata=eff.values,
        hovertemplate="%{x} consonne(s) dure(s) : %{y:.0f} kg (médiane, %{customdata} Pokémon)<extra></extra>",
    ))
    fig.update_xaxes(title="Consonnes « dures » dans le nom japonais (b, d, g, z…)", type="category")
    fig.update_yaxes(title="Poids médian (kg)")

    # montrer : Spearman contre Pearson sur le poids
    rs = spearmanr(d["ja_mores"], d["poids_kg"])[0]
    rp = pearsonr(d["ja_mores"], d["poids_kg"])[0]
    rng = np.random.default_rng(0)
    f1 = go.Figure(go.Scatter(
        x=d["ja_mores"] + rng.uniform(-.25, .25, len(d)), y=d["poids_kg"], mode="markers", text=d["nom_fr"],
        marker=dict(size=5, color=t.GLACE, opacity=.5), hovertemplate="<b>%{text}</b> : %{y} kg<extra></extra>"))
    f1.update_xaxes(title="nombre de mores du nom japonais", dtick=1)
    f1.update_yaxes(title="poids (kg, échelle log)", type="log")

    # montrer : tous les liens, japonais et français
    variables = [("ja_mores", "longueur JP"), ("ja_voisees", "consonnes voisées JP"),
                 ("fr_lettres", "longueur FR"), ("fr_voisees", "consonnes voisées FR")]
    cibles = [("taille_m", "taille"), ("poids_kg", "poids"), ("total_stats", "stats")]
    f2 = go.Figure()
    for (cible, nc), coul in zip(cibles, [t.ROUGE, t.OR, t.GLACE]):
        rhos = [spearmanr(d[v], d[cible])[0] for v, _ in variables]
        f2.add_trace(go.Bar(x=[n for _, n in variables], y=rhos, name=nc, marker_color=coul,
                            hovertemplate="%{x} ↔ " + nc + " : rho = %{y:.2f}<extra></extra>"))
    f2.update_layout(barmode="group", showlegend=True)
    f2.update_yaxes(title="rho de Spearman", range=[0, .5])

    options = [{"label": f"{r.nom_fr} (n° {r.dex})", "value": r.dex} for r in d.sort_values("nom_fr").itertuples()]
    return t.question(
        "Un nom qui sonne « dur » fait-il un Pokémon plus lourd ?",
        ["En japonais, oui. Un Pokémon sans consonne dure pèse ", html.Strong(f"{med.loc[0]:.0f} kg"),
         f" (médiane), contre {med.loc[2]:.0f} kg avec deux. On retrouve aussi le résultat de Kawahara (2018) : "
         "plus le nom est long, plus le Pokémon est gros et fort. En français, ça va dans le même sens, mais c'est très faible."],
        html.Div(className="deux-colonnes", children=[
            t.graphe(fig, 340),
            html.Div([
                html.Div(className="controle", children=[
                    html.Label("Écoute le nom d'un Pokémon 🔔", htmlFor="noms-choix"),
                    dcc.Dropdown(id="noms-choix", options=options, value=143, clearable=False),
                ]),
                html.Div(id="noms-fiche", className="fiche"),
            ]),
        ]),
        methode=t.etapes([
            ("On est partis d'une idée de linguistique",
             "La symbolique sonore : on associe souvent les sons durs (b, d, g) à ce qui est gros et lourd (c'est l'idée de "
             "« bouba / kiki »). Kawahara, Noto et Kumagai (2018) l'ont montré sur les noms japonais des Pokémon ; on a "
             "voulu retrouver leur résultat, puis tester le français.", "hors"),
            ("On a découpé chaque nom japonais en mores",
             [html.P("On travaille sur les kana, plus proches de la prononciation que le romaji. Un kana = une more, sauf les "
                     "petits ャ ュ ョ qu'on colle au kana d'avant. Une consonne est voisée (« dure ») si le kana porte le "
                     "petit signe ゛ : on le détecte en décomposant chaque caractère avec Unicode (ガ = カ + ゛). Pour le "
                     "Pokémon choisi au-dessus, en rouge les mores voisées :"),
              html.Div(id="noms-decoupe")],
             "exploration"),
            ("En français, on a codé à partir des lettres",
             "Il n'existe pas de transcription phonétique des noms français, donc on compte les lettres, les syllabes "
             "(groupes de voyelles), les consonnes voisées (b, d, g, v, z, j), les occlusives et les sonantes. On calcule "
             "aussi chaque variable en proportion de la longueur, pour ne pas mesurer deux fois la longueur.", "exploration"),
            ("On a choisi Spearman plutôt que Pearson",
             [html.P(f"Le poids va de 0,1 à 999,9 kg avec quelques géants. Comme on l'a vu en cours, on calcule les deux et "
                     f"on regarde le nuage : ici Pearson vaut {t.fr(rp)} et Spearman {t.fr(rs)}. Pearson est tiré par les "
                     "géants et la relation n'est pas une droite, alors que Spearman travaille sur les rangs et mesure juste "
                     "si ça monte. Du coup on garde Spearman."),
              t.mini(f1, 260, "Chaque point est un Pokémon : la longueur de son nom japonais et son poids.")],
             "exploration"),
            ("On a mesuré tous les liens",
             [html.P("En japonais, la longueur et les consonnes voisées sont liées à la taille, au poids et aux stats "
                     "(p < 0,001). En français, ça va dans le même sens mais les rho ne dépassent jamais 0,13."),
              t.mini(f2, 260, "Spearman entre les variables sonores et le gabarit, en japonais et en français.")],
             "exploration"),
            ("On a regardé la force, pas seulement la p-valeur",
             "Avec 1 025 Pokémon, même un rho de 0,1 devient « significatif ». Comme le conseille le cours, on regarde "
             "aussi l'ampleur dans les vraies unités : c'est pour ça que le graphique du haut est en kilos.", "exploration"),
        ], attention="en français, l'orthographe n'est pas la prononciation (le x de Ronflex, le s de Rosélia qui se dit "
                     "z) : notre codage peut affaiblir les liens. On ne peut pas trancher entre « les noms français n'ont pas "
                     "cette symbolique » et « notre codage est trop grossier »."),
    )


@callback(Output("noms-fiche", "children"), Output("noms-decoupe", "children"), Input("noms-choix", "value"))
def fiche(dex):
    r = _donnees().set_index("dex").loc[dex]
    m = mores(r["nom_ja"])
    fiche = [
        t.image(dex, 130),
        html.H3(f"{r['nom_fr']} · {r['nom_ja']}"),
        html.P(f"« {r['nom_ja_roma']} »"),
        tuiles(r["nom_ja"]),
        html.Div([
            html.Span(f"{len(m)} mores", className="etiquette gris"),
            html.Span(f"{sum(v for _, v in m)} consonne(s) dure(s) en japonais", className="etiquette"),
            html.Span(f"{int(r['fr_lettres'])} lettres en français", className="etiquette gris"),
        ]),
        html.P(f"{r['poids_kg']:g} kg · {r['taille_m']:g} m · {int(r['total_stats'])} de stats au total"),
    ]
    decoupe = html.Div([
        html.Div([html.Strong(f"{r['nom_fr']} : "), html.Span(r["nom_ja"])]),
        tuiles(r["nom_ja"]),
        html.P(f"→ {len(m)} mores, dont {sum(v for _, v in m)} voisée(s).", className="note"),
    ], className="mini")
    return fiche, decoupe


# ---------- 2. Et la popularité ? ----------
def bloc_popularite():
    d = _donnees()
    variables = {"ja_mores": "longueur (japonais)", "ja_voisees_part": "part de sons durs (japonais)",
                 "fr_lettres": "longueur (français)", "fr_voisees_part": "part de sons durs (français)"}
    lignes = []
    for groupe, sous in [("tous les Pokémon", d), ("Pokémon sans évolution", d[d["stade_categorie"] == "sans évolution"])]:
        for v, nom in variables.items():
            x = sous[[v, "johto_pct_gen"]].dropna()
            rho, p = spearmanr(x[v], x["johto_pct_gen"])
            lignes.append(dict(groupe=groupe, variable=nom, rho=rho, p=p))
    r = pd.DataFrame(lignes)
    fig = go.Figure()
    for groupe, couleur in [("tous les Pokémon", t.GRIS_FONCE), ("Pokémon sans évolution", t.ROUGE)]:
        s = r[r["groupe"] == groupe]
        fig.add_trace(go.Bar(
            y=s["variable"], x=s["rho"], name=groupe, orientation="h", marker_color=couleur, marker_cornerradius=4,
            customdata=s["p"], hovertemplate="%{y} : rho = %{x:.2f} (p = %{customdata:.3f})<extra>" + groupe + "</extra>",
        ))
    fig.add_vline(x=0, line_color=t.GRIS_FONCE)
    fig.update_xaxes(title="Corrélation de Spearman avec la popularité (Johto Times, dans la génération)", range=[-.4, .4])
    fig.update_layout(barmode="group", bargroupgap=.1)
    rho_long = r[(r["groupe"] == "Pokémon sans évolution") & (r["variable"] == "longueur (japonais)")]["rho"].iloc[0]

    # montrer : le même lien, stade par stade
    cats = ["stade 1", "stade 2", "stade 3", "sans évolution"]
    f1 = go.Figure()
    for src, nom, coul in [("johto_pct_gen", "Johto Times", t.OR), ("reddit_pct_gen", "Reddit", t.ROUGE)]:
        rhos, ps = [], []
        for c in cats:
            x = d[d["stade_categorie"] == c][["ja_mores", src]].dropna()
            rr, pp = spearmanr(x["ja_mores"], x[src])
            rhos.append(rr)
            ps.append(pp)
        f1.add_trace(go.Bar(x=cats, y=rhos, name=nom, marker_color=coul, customdata=ps,
                            hovertemplate="%{x} : rho = %{y:.2f} (p = %{customdata:.3f})<extra>" + nom + "</extra>"))
    f1.add_hline(y=0, line_color=t.GRIS_FONCE)
    f1.update_layout(barmode="group", showlegend=True)
    f1.update_yaxes(title="rho (longueur JP ↔ popularité)", range=[-.45, .2])

    # montrer : pourquoi le stade est un facteur de confusion
    m = d.groupby("stade_categorie").agg(mores=("ja_mores", "mean"), pop=("johto_pct_gen", "mean")).reindex(cats)
    f2 = go.Figure(go.Bar(x=cats, y=m["mores"], marker_color=t.GLACE, marker_cornerradius=3,
                          hovertemplate="%{x} : %{y:.1f} mores en moyenne<extra></extra>"))
    f2.update_yaxes(title="mores en moyenne", range=[3, 5.5])

    return t.question(
        "Un nom court et doux rend-il un Pokémon plus populaire ?",
        ["Presque pas : toutes les corrélations sont proches de zéro. Seule exception, ",
         html.Strong("chez les Pokémon sans évolution, un nom long est un peu moins aimé"),
         f" (rho = {t.fr(rho_long)} pour la longueur en japonais). Le son du nom dit la taille du Pokémon, pas s'il sera aimé."],
        t.graphe(fig, 360),
        methode=t.etapes([
            ("On a pris une popularité sans nostalgie",
             "Le percentile dans la génération au Johto Times 2025 (et Reddit pour vérifier) : on compare un Pokémon aux "
             "autres de sa génération.", "exploration"),
            ("Spearman, tous les Pokémon ensemble",
             "Tous les rho sont entre −0,08 et 0,05 : pas de lien global (les barres grises du graphique du haut).",
             "exploration"),
            ("On s'est méfiés d'un facteur de confusion : le stade",
             [html.P("Les noms s'allongent avec le stade d'évolution, et les Pokémon évolués sont plus aimés. Un lien « nom "
                     "long ↔ populaire » pourrait donc venir du stade et pas du nom. Comme on l'a vu en cours (corrélation "
                     "n'est pas causalité), on contrôle ce facteur en refaisant la corrélation à l'intérieur de chaque stade."),
              t.mini(f2, 200, "Les noms sont plus longs aux stades avancés.")],
             "exploration"),
            ("Stade par stade, ça change",
             [html.P("Chez les Pokémon sans évolution, les noms longs sont moins aimés dans les deux sondages. Aux stades 2 "
                     "et 3, rien. Le lien global quasi nul cachait donc des liens dans certains groupes seulement."),
              t.mini(f1, 240, "Spearman entre la longueur du nom japonais et la popularité, dans chaque stade.")],
             "exploration"),
        ], attention="le groupe « sans évolution » mélange des légendaires (aux noms souvent longs) et des Pokémon "
                     "ordinaires : le lien peut venir de cette différence plutôt que du nom."),
    )


def layout():
    return html.Div([
        t.entete_page("Les noms des Pokémon",
                      "Pokémonastique : est-ce que le son d'un nom dit quelque chose du Pokémon… et de sa popularité ?",
                      "sorbebe"),
        bloc_poids(),
        bloc_popularite(),
    ])
