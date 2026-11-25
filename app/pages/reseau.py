"""Notebook 07 : réseau de similarité (graphe kNN, Louvain, centralités, node2vec + t-SNE)."""
from functools import lru_cache

import dash
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html
from scipy.stats import spearmanr

import theme as t
from donnees import PROCESSED, popularite, reseau_aretes, reseau_noeuds

dash.register_page(__name__, path="/reseau", name="Le réseau", order=6)

# toutes les sources en percentile dans la génération, comme dans le notebook 07
SOURCES = {"johto_pct_gen": "Johto Times", "reddit_pct_gen": "Reddit", "trends_pct_gen": "Google"}
MESURES = {"reddit": "Reddit", "johto": "Johto Times", "trends": "Google", "poty": "Pokémon of the Year",
           "resid_reddit": "Reddit (résidus)", "resid_johto": "Johto (résidus)", "resid_trends": "Google (résidus)"}


def _p(p):
    return "< 0,001" if p < .001 else "= " + t.fr(p, 3)


def _m(nom):
    return pd.read_csv(PROCESSED / f"methode_07_{nom}.csv")


@lru_cache
def _noeuds():
    n = reseau_noeuds().merge(popularite()[["dex", *SOURCES, "poty_pct_gen"]], on="dex")
    com = _m("communautes").set_index("communaute")["nom"]
    n["communaute_nom"] = n["communaute"].map(com)
    return n.set_index("dex")


def _voisins(dex):
    a = reseau_aretes()
    v = a[(a["source"] == dex) | (a["cible"] == dex)].copy()
    v["autre"] = np.where(v["source"] == dex, v["cible"], v["source"])
    return v.sort_values("similarite", ascending=False)


@lru_cache
def _aretes_xy():
    n = _noeuds()
    a = reseau_aretes()
    xs, ys = [], []
    for s, c in zip(a["source"], a["cible"]):
        xs += [n.at[s, "tsne_x"], n.at[c, "tsne_x"], None]
        ys += [n.at[s, "tsne_y"], n.at[c, "tsne_y"], None]
    return xs, ys


def _figure(dex_choisi, source):
    n = _noeuds()
    xs, ys = _aretes_xy()
    pop = n[source]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="rgba(150,140,120,.12)", width=1),
                             hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(
        x=n["tsne_x"], y=n["tsne_y"], mode="markers", name="Pokémon",
        marker=dict(size=6 + 10 * pop.fillna(0), color=pop.fillna(-1),
                    colorscale=[[0, "#d9d2c3"], [.001, "#e9e3d6"], [1, t.SAPIN]], cmin=-.001, cmax=1,
                    line=dict(color="#fffaf0", width=.5),
                    colorbar=dict(title="Popularité<br>(percentile dans<br>la génération)", thickness=10, len=.6, tickformat=".0%",
                                  tickvals=[0, .25, .5, .75, 1])),
        text=n["nom_fr"], customdata=np.stack([n.index, n["communaute_nom"], pop.fillna(-1)], axis=1),
        hovertemplate="<b>%{text}</b><br>%{customdata[1]}<extra></extra>",
        showlegend=False,
    ))
    if dex_choisi:
        v = _voisins(dex_choisi)
        pts = [dex_choisi] + list(v["autre"])
        fig.add_trace(go.Scatter(
            x=n.loc[pts, "tsne_x"], y=n.loc[pts, "tsne_y"], mode="markers", showlegend=False,
            marker=dict(size=[20] + [11] * len(v), color=t.ROUGE, line=dict(color="#fffaf0", width=2)),
            text=n.loc[pts, "nom_fr"], customdata=np.stack([pts, n.loc[pts, "communaute_nom"], [0] * len(pts)], axis=1),
            hovertemplate="<b>%{text}</b><extra></extra>",
        ))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x")
    fig.update_layout(height=560, dragmode="pan", uirevision="reseau", clickmode="event")
    return fig


def barre_pop(nom, valeur):
    if pd.isna(valeur):
        return html.Div(className="pop-ligne", children=[html.Span(nom, className="pop-nom"),
                                                          html.Span("pas de valeur", className="pop-vide")])
    return html.Div(className="pop-ligne", children=[
        html.Span(nom, className="pop-nom"),
        html.Div(className="pop-barre", children=html.Div(style={"width": f"{valeur * 100:.0f}%"})),
        html.Span(f"{valeur * 100:.0f}", className="pop-val"),
    ])


def bloc_reseau():
    n = _noeuds()
    a = reseau_aretes()
    paires = pd.DataFrame(np.concatenate([a[["source", "cible"]].values, a[["cible", "source"]].values]),
                          columns=["dex", "voisin"])
    pop = n["johto_pct_gen"]
    paires["pop_voisin"] = paires["voisin"].map(pop)
    moy = paires.groupby("dex")["pop_voisin"].mean()
    rho = spearmanr(pop.loc[moy.index], moy, nan_policy="omit")[0]

    # ---- ce qu'on montre dans la méthode ----
    k = _m("k")
    f_k = go.Figure([
        go.Scatter(x=k["k"], y=k["composantes"], mode="lines+markers", name="morceaux du graphe", line=dict(color=t.ROUGE)),
        go.Scatter(x=k["k"], y=k["degre_moyen"], mode="lines+markers", name="voisins en moyenne", line=dict(color=t.GLACE)),
    ])
    f_k.add_vline(x=10, line_dash="dot", line_color=t.GRIS_FONCE, annotation_text="k = 10")
    f_k.update_layout(showlegend=True)
    f_k.update_xaxes(title="k (nombre de plus proches voisins)")

    pm = _m("petit_monde").set_index("mesure")
    f_pm = go.Figure()
    for col, nom, coul in [("reseau", "notre réseau", t.SAPIN), ("aleatoire", "réseau au hasard", t.GRIS)]:
        f_pm.add_trace(go.Bar(x=pm.index, y=pm[col], name=nom, marker_color=coul, marker_cornerradius=3,
                              text=[f"{v:.2f}" for v in pm[col]], textposition="outside",
                              hovertemplate="%{x} : %{y:.2f}<extra>" + nom + "</extra>"))
    f_pm.update_layout(barmode="group", showlegend=True)

    com = _m("communautes").sort_values("taille")
    f_c = go.Figure(go.Bar(y=com["nom"], x=com["taille"], orientation="h", marker_color=t.GLACE, marker_cornerradius=3,
                           hovertemplate="%{y} : %{x} Pokémon<extra></extra>"))
    f_c.update_xaxes(title="nombre de Pokémon")
    com2 = com.sort_values("johto")
    f_cp = go.Figure()
    for col, nom, coul in [("reddit", "Reddit", t.ROUGE), ("johto", "Johto Times", t.OR), ("trends", "Google", t.GLACE)]:
        f_cp.add_trace(go.Scatter(y=com2["nom"], x=com2[col] * 100, mode="markers", name=nom,
                                  marker=dict(size=10, color=coul), hovertemplate="%{y} : %{x:.0f}<extra>" + nom + "</extra>"))
    f_cp.add_vline(x=50, line_dash="dot", line_color=t.GRIS_FONCE)
    f_cp.update_layout(showlegend=True)
    f_cp.update_xaxes(title="popularité moyenne (percentile)")
    kw = _m("kruskal").set_index("mesure")["p_holm"]

    po = _m("poty").sort_values("rapport")
    p_poty = po["p_global"].iloc[0]
    f_po = go.Figure([
        go.Bar(y=po["nom"], x=po["part_attendue"] * 100, orientation="h", name="attendu vu les générations",
               marker_color=t.GRIS, marker_cornerradius=3, hovertemplate="%{y} : %{x:.0f} % attendus<extra></extra>"),
        go.Bar(y=po["nom"], x=po["part_publiee"] * 100, orientation="h", name="publiés (top 30 de leur génération)",
               marker_color=t.OR, marker_cornerradius=3, customdata=po["p_holm"],
               hovertemplate="%{y} : %{x:.0f} % publiés (p Holm = %{customdata:.3f})<extra></extra>"),
    ])
    f_po.update_layout(barmode="group", showlegend=True)
    f_po.update_xaxes(title="part de la communauté (%)")
    po_bas = po[po["p_holm"] < .05]

    ce = _m("centralites")
    ce = ce[ce["source"].isin(["reddit", "johto", "trends"])].copy()
    ce["centralite"] = ce["centralite"].replace({
        "degre": "degré", "similarite_voisins": "similarité aux voisins", "intermediarite": "intermédiarité",
        "proximite": "proximité", "clustering": "clustering local", "sim_k_voisins": "similarité aux 10 voisins"})
    f_ce = go.Figure()
    for src, nom, coul in [("reddit", "Reddit", t.ROUGE), ("johto", "Johto Times", t.OR), ("trends", "Google", t.GLACE)]:
        s = ce[ce["source"] == src]
        f_ce.add_trace(go.Bar(x=s["centralite"], y=s["rho"], name=nom, marker_color=coul, customdata=s["p_holm"],
                              marker_pattern_shape=np.where(s["p_holm"] < .05, "", "/"),
                              hovertemplate="%{x} : rho = %{y:.2f} (p Holm = %{customdata:.3f})<extra>" + nom + "</extra>"))
    f_ce.update_layout(barmode="group", showlegend=True)
    f_ce.update_yaxes(title="rho de Spearman", range=[-.3, .3])
    f_ce.add_hline(y=0, line_color=t.GRIS_FONCE)

    asso = _m("assortativite")
    asso = asso.assign(mesure=asso["mesure"].map(MESURES))
    f_as = go.Figure([
        go.Bar(x=asso["mesure"], y=asso["assortativite"], name="observée", marker_color=t.SAPIN, marker_cornerradius=3),
        go.Bar(x=asso["mesure"], y=asso["max_hasard"], name="max sur 200 mélanges au hasard", marker_color=t.GRIS,
               marker_cornerradius=3),
    ])
    f_as.update_layout(barmode="group", showlegend=True)
    f_as.update_yaxes(title="assortativité")

    sc = _m("sans_couleur").set_index("mesure")
    def _ligne(nom, cle, fmt):
        return html.Tr([html.Td(nom), html.Td(fmt(sc.at[cle, "avec_couleur"])), html.Td(fmt(sc.at[cle, "sans_couleur"]))])
    tab_sc = html.Table(className="tableau", children=[
        html.Thead(html.Tr([html.Th(""), html.Th("avec la couleur officielle"), html.Th("sans")])),
        html.Tbody([
            _ligne("communautés", "nombre de communautés", lambda v: f"{v:.0f}"),
            _ligne("accord avec les familles de départ (ARI)", "ARI avec le réseau complet", t.fr),
            _ligne("familles différentes au Johto Times (p Holm)", "Kruskal-Wallis johto (p Holm)", _p),
            _ligne("… une fois les effets attendus retirés", "Kruskal-Wallis resid_johto (p Holm)", lambda v: t.fr(v, 2)),
            _ligne("Pokémon of the Year, écart à la génération (p)", "Pokémon of the Year, écart à la génération (p)", _p),
            _ligne("assortativité au Johto Times", "assortativité johto", t.fr),
            _ligne("centralités liées à la popularité (après Holm, sur 36)", "centralités significatives après Holm (sur 36)",
                   lambda v: f"{v:.0f}"),
        ])])
    ari_sc = sc.at["ARI avec le réseau complet", "sans_couleur"]

    ok = moy.index.intersection(pop.dropna().index)
    f_v = go.Figure(go.Scatter(x=pop.loc[ok] * 100, y=moy.loc[ok] * 100, mode="markers", text=n.loc[ok, "nom_fr"],
                               marker=dict(size=5, color=t.SAPIN, opacity=.5),
                               hovertemplate="<b>%{text}</b><br>lui %{x:.0f} · ses voisins %{y:.0f}<extra></extra>"))
    f_v.update_xaxes(title="popularité du Pokémon (Johto)")
    f_v.update_yaxes(title="popularité moyenne de ses voisins")

    options = [{"label": f"{r.nom_fr} (n° {d})", "value": d} for d, r in n.sort_values("nom_fr").iterrows()]
    return t.question(
        "Les Pokémon qui se ressemblent sont-ils aimés pareil ?",
        ["Un peu. Chaque Pokémon est relié à ses 10 plus proches sosies (types, stats, taille, couleurs, forme). "
         "Les Pokémon populaires ont des voisins populaires (", html.Strong(f"rho = {t.fr(rho)}"),
         " au Johto Times), mais le lien fond une fois les effets attendus retirés, et ",
         html.Strong("être au centre du réseau ou au contraire « original » ne change rien à la popularité"), "."],
        html.Div(className="deux-colonnes", children=[
            html.Div([
                html.Div(className="controle", style={"maxWidth": "100%"}, children=[
                    html.Label("Couleur des points = popularité selon :"),
                    dcc.RadioItems(id="reseau-source", value="johto_pct_gen", inline=True, className="radio-noel",
                                   options=[{"label": v, "value": k} for k, v in SOURCES.items()]),
                ]),
                dcc.Graph(id="reseau-graphe", config=t.GRAPH_CONFIG),
                html.P("Clique sur un Pokémon pour voir sa fiche et ses sosies (en rouge sur le graphe). "
                       "Plus le point est gros et vert, plus il est aimé ; les points gris clair n'ont pas de valeur.",
                       className="note"),
            ]),
            html.Div([
                html.Div(className="controle", children=[
                    html.Label("Ou cherche-le ici 🔍", htmlFor="reseau-choix"),
                    dcc.Dropdown(id="reseau-choix", options=options, value=25, clearable=False),
                ]),
                html.Div(id="reseau-fiche", className="fiche"),
            ]),
        ]),
        methode=t.etapes([
            ("On a décrit chaque Pokémon par un vecteur",
             "56 colonnes en 6 blocs : les types (18 indicatrices), les 6 stats, la taille et le poids en log, la couleur "
             "officielle, la forme du corps et les couleurs de l'image (k-means). On n'a pas mis la génération ni la "
             "popularité : on veut un réseau de ressemblance physique, sinon on retrouverait forcément des voisins populaires.",
             "exploration"),
            ("On a standardisé et donné le même poids à chaque bloc",
             "On standardise chaque colonne (sinon le poids, en centaines de kilos, écraserait tout, comme les fruits du TP "
             "clustering), puis on divise chaque bloc par la racine de son nombre de colonnes : les 18 types ne pèsent pas "
             "plus que la taille.", "exploration"),
            ("On a construit le graphe des k plus proches voisins",
             [html.P("Comme le graphe item-item du cours : on mesure la similarité cosinus entre Pokémon et on relie chacun à "
                     "ses k plus proches. Avec k = 2 le graphe est coupé en morceaux, dès k = 3 tout le monde est relié. On a "
                     "pris k = 10 : assez de voisins pour qu'une ressemblance bizarre ne change pas tout, sans relier des "
                     "Pokémon trop différents."),
              t.mini(f_k, 220, "L'effet de k : nombre de morceaux du graphe et nombre moyen de voisins.")],
             ["transfo", "reseaux"]),
            ("On l'a comparé à un réseau au hasard",
             [html.P("Comme au TP réseaux, on compare à un graphe aléatoire de même taille. Notre réseau a beaucoup plus de "
                     "triangles (clustering) avec des chemins à peine plus longs : c'est un « petit monde ». Les voisins "
                     "d'un Pokémon se ressemblent aussi entre eux, il y a des familles."),
              t.mini(f_pm, 240, "Notre réseau contre un réseau au hasard de même taille.")],
             "reseaux"),
            ("On a cherché les familles avec Louvain",
             [html.P(f"Louvain maximise la modularité. On obtient {len(com)} communautés, qui suivent surtout la couleur "
                     "officielle et la forme du corps. Louvain a une part de hasard : on l'a relancé avec plusieurs graines "
                     "et les découpages se ressemblent, donc on garde la graine 0."),
              t.mini(f_c, 320, "La taille de chaque communauté.")],
             "reseaux"),
            ("On a comparé la popularité des familles",
             [html.P(f"Test de Kruskal-Wallis (la version sans hypothèse de normalité de l'ANOVA), avec la correction de Holm "
                     f"sur les 6 tests : les familles n'ont pas la même popularité dans les sondages (p {_p(kw.get('johto', np.nan))} "
                     f"au Johto Times), et un peu aussi sur Google (p {_p(kw.get('trends', np.nan))}), avec un écart plus faible. "
                     "La popularité est en percentile dans la génération : les familles n'ont pas toutes autant de Pokémon "
                     "récents, et les récents sont moins aimés. Une fois les effets attendus retirés (résidus du modèle "
                     f"« Sur / sous-cotés »), plus rien ne tient (p {_p(kw.get('resid_johto', np.nan))} au Johto Times)."),
              t.mini(f_cp, 340, "Popularité moyenne de chaque communauté, source par source.")],
             ["reseaux", "hors"]),
            ("Pokémon of the Year : plus de publiés que prévu ?",
             [html.P(["On ne connaît que le top 30 de chaque génération, donc la chance d'être publié dépend surtout de la "
                      "taille de la génération (20 % en génération 1, 42 % en génération 6). On compare donc la part de publiés "
                      "de chaque famille à celle qu'on attendrait vu ses générations, avec un test par permutation : on mélange "
                      "« publié / pas publié » à l'intérieur de chaque génération, 2 000 fois. Les familles s'écartent bien de "
                      f"ce que prévoit la génération (p {_p(p_poty)}), dans le même ordre que les sondages (Eau, Électrik et "
                      "noirs en haut, carapaces et poissons en bas). Après Holm, une seule famille tient : ",
                      html.Strong(", ".join(po_bas["nom"])), f" ({po_bas['publies'].sum():.0f} publiés au lieu de "
                      f"{po_bas['attendus'].sum():.0f})."]),
              t.mini(f_po, 380, "Part de publiés au Pokémon of the Year 2020, et part attendue vu les générations.")],
             ["hors"]),
            ("Centralités et popularité",
             [html.P("Pour chaque Pokémon : degré, intermédiarité (est-il un pont entre familles ?), proximité, clustering "
                     "local, et similarité moyenne à ses voisins (est-il « original » ?). Puis Spearman avec la popularité, "
                     "et la correction de Holm sur les 36 tests : il ne reste que des liens faibles sur Google (un Pokémon "
                     "au centre du réseau est un peu plus cherché), rien dans les sondages, et rien une fois les effets "
                     "attendus retirés."),
              t.mini(f_ce, 240, "Spearman entre chaque centralité et la popularité (hachuré : pas significatif après Holm).")],
             ["reseaux", "exploration"]),
            ("Les populaires ont-ils des voisins populaires ?",
             [html.P("On a calculé l'assortativité (les deux bouts d'un lien ont-ils une popularité proche ?) et on l'a "
                     "comparée à 200 mélanges au hasard de la popularité (test de permutation). Elle est faible mais au-dessus "
                     "du hasard dans les quatre sources (pour Pokémon of the Year, on regarde « publié ou non » et on mélange "
                     "dans la génération) ; sur les résidus (effets attendus retirés), elle devient très petite."),
              html.Div(className="deux-colonnes", style={"gridTemplateColumns": "1fr 1fr"}, children=[
                  t.mini(f_as, 240, "Assortativité observée contre le hasard."),
                  t.mini(f_v, 240, "La popularité d'un Pokémon et celle de ses voisins."),
              ])],
             ["reseaux", "hors"]),
            ("Et sans la couleur officielle ?",
             [html.P(f"Les familles suivent surtout la couleur officielle, une étiquette assez grossière. On a refait tout le "
                     f"réseau sans elle : les familles changent beaucoup (ARI = {t.fr(ari_sc)}, elles suivent alors la forme "
                     "et le type), mais les conclusions sur la popularité tiennent. Seule nuance : sans elle, quelques "
                     "centralités deviennent faiblement liées aux sondages (|rho| ≤ 0,2), mais rien ne reste une fois les "
                     "effets attendus retirés. On garde la couleur officielle, parce que ses familles se lisent bien."),
              tab_sc],
             ["reseaux", "hors"]),
            ("On a dessiné la carte avec node2vec puis t-SNE",
             "node2vec comme au TP : 10 marches aléatoires de 40 pas par Pokémon servent de « phrases » à Word2Vec, qui "
             "donne un vecteur de 16 nombres par Pokémon. Puis t-SNE (perplexité 30) les place en 2D : c'est le graphique "
             "du haut. On a vérifié avec la trustworthiness (0,99) que les voisins sur la carte sont bien des voisins dans "
             "le réseau.", "transfo"),
        ], attention="sur une carte t-SNE, « proche » a un sens mais « loin » n'en a pas : on ne lit pas les distances "
                     "entre îlots. Et les communautés dépendent beaucoup des variables choisies : sans la couleur "
                     "officielle, ce ne sont plus les mêmes familles, même si les conclusions sur la popularité tiennent."),
    )


@callback(Output("reseau-choix", "value"), Input("reseau-graphe", "clickData"), prevent_initial_call=True)
def clic(click):
    if not click or not click.get("points"):
        return dash.no_update
    cd = click["points"][0].get("customdata")
    if cd is None:
        return dash.no_update
    return int(float(cd[0]))


@callback(Output("reseau-graphe", "figure"), Output("reseau-fiche", "children"),
          Input("reseau-choix", "value"), Input("reseau-source", "value"))
def maj(dex, source):
    n = _noeuds()
    v = _voisins(dex).head(6)
    r = n.loc[dex]
    com = n[n["communaute"] == r["communaute"]]
    fiche = [
        t.image(dex, 120),
        html.H3(r["nom_fr"]),
        html.P(f"Famille « {r['communaute_nom']} » · {int(r['degre'])} liens"),
        html.Div(className="pop-bloc", children=[
            html.Div("Sa popularité (percentile)", className="pop-titre"),
            *[barre_pop(nom, r[col]) for col, nom in SOURCES.items()],
            html.Div("Pokémon of the Year 2020 : " + ("pas votable (après le n° 890)" if dex > 890 else
                     "dans le top 30 de sa génération" if pd.notna(r["poty_pct_gen"]) else "hors du top 30 de sa génération"),
                     className="note"),
            html.Div(f"Moyenne de sa famille : {com['johto_pct_gen'].mean() * 100:.0f} au Johto Times", className="note"),
        ]),
        html.P("Ses plus proches sosies :", style={"fontWeight": 800, "marginTop": "10px"}),
        t.galerie(v["autre"], [n.at[d, "nom_fr"] for d in v["autre"]],
                  [f"{s * 100:.0f} % semblable" for s in v["similarite"]], taille=60),
    ]
    return _figure(dex, source), fiche


def layout():
    return html.Div([
        t.entete_page("Le réseau des sosies",
                      "Chaque Pokémon relié à ceux qui lui ressemblent le plus. Les ressemblances font-elles la popularité ?",
                      "givrali"),
        bloc_reseau(),
    ])
