"""Notebook 05 : sur-cotés et sous-cotés (régression par source, résidus)."""
import dash
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html
from scipy.stats import spearmanr

import theme as t
from donnees import PROCESSED, popularite, sur_sous_cotes, table_maitre

dash.register_page(__name__, path="/sur-sous-cotes", name="Sur / sous-cotés", order=2)

SOURCES = {"resid_reddit": "Reddit 2019", "resid_johto": "Johto Times 2025", "resid_trends": "Google Trends"}


def _donnees():
    s = sur_sous_cotes().copy()
    s["resid_moyen"] = s[list(SOURCES)].mean(axis=1)
    return s


def _modeles():
    return pd.read_csv(PROCESSED / "methode_05_modeles.csv")


def _coefs():
    return pd.read_csv(PROCESSED / "methode_05_coefs.csv")


# ---------- 1. La génération (nostalgie) ----------
def bloc_generation():
    p = popularite()
    g = p.dropna(subset=["reddit_pct"]).groupby("generation")["reddit_pct"].mean()
    fig = go.Figure(go.Bar(
        x=[f"Gén. {i}" for i in g.index], y=g.values * 100, marker_cornerradius=4,
        marker_color=[t.ROUGE if gen == 1 else t.GRIS for gen in g.index],
        hovertemplate="%{x} : percentile moyen %{y:.0f}<extra></extra>",
    ))
    fig.add_hline(y=50, line_dash="dot", line_color=t.GRIS_FONCE,
                  annotation_text="moyenne de tous les Pokémon", annotation_position="top right")
    fig.update_yaxes(title="Percentile moyen sur Reddit", range=[0, 80])
    gen_min = g.idxmin()

    # montrer : la longue traîne des votes
    tm = table_maitre().dropna(subset=["reddit_votes"]).sort_values("reddit_votes", ascending=False)
    f1 = go.Figure(go.Bar(x=np.arange(1, len(tm) + 1), y=tm["reddit_votes"], marker_color=t.GLACE,
                          text=tm["nom_fr"], hovertemplate="%{text} : %{y:.0f} votes<extra></extra>"))
    f1.update_xaxes(title="rang du Pokémon sur Reddit")
    f1.update_yaxes(title="votes")
    mediane = tm["reddit_votes"].median()

    # montrer : l'incertitude de Wilson
    o = p.dropna(subset=["reddit_pct"]).sort_values("reddit_pct")
    f2 = go.Figure([
        go.Scatter(x=np.arange(len(o)), y=o["reddit_pct_haut"] * 100, line=dict(width=0), hoverinfo="skip", showlegend=False),
        go.Scatter(x=np.arange(len(o)), y=o["reddit_pct_bas"] * 100, fill="tonexty", fillcolor="rgba(58,120,181,.25)",
                   line=dict(width=0), hoverinfo="skip", name="intervalle à 95 %"),
        go.Scatter(x=np.arange(len(o)), y=o["reddit_pct"] * 100, line=dict(color=t.GLACE, width=2), name="percentile",
                   text=o["nom_fr"], hovertemplate="%{text} : %{y:.0f}<extra></extra>"),
    ])
    f2.update_xaxes(title="Pokémon, du moins aimé au plus aimé")
    f2.update_yaxes(title="percentile")
    f2.update_layout(showlegend=True)

    return t.question(
        "Les vieux Pokémon sont-ils plus aimés ?",
        ["Oui, et c'est l'effet le plus fort. Sur Reddit, un Pokémon de 1re génération est en moyenne au ",
         html.Strong(f"percentile {t.pct(g.loc[1])}"), f", contre {t.pct(g.loc[gen_min])} pour la génération {gen_min}. "
         "C'est la nostalgie : ceux qui votent ont grandi avec Kanto."],
        t.graphe(fig, 340),
        methode=t.etapes([
            ("On a d'abord regardé les votes bruts",
             [html.P(f"Sur Reddit, quelques Pokémon prennent énormément de votes (Dracaufeu en a plus de 1 000) et la "
                     f"moitié en a moins de {mediane:.0f}. C'est une longue traîne : si on faisait des moyennes de votes, "
                     "Dracaufeu et Ectoplasma tireraient tout. Comme on l'a vu en cours pour les variables très asymétriques, "
                     "on a donc travaillé sur les rangs plutôt que sur les valeurs."),
              t.mini(f1, 220, "Les votes de Reddit, Pokémon par Pokémon : quelques stars, puis une très longue traîne.")],
             "exploration"),
            ("Du coup on est passés en percentiles",
             "Chaque Pokémon reçoit un percentile : « il fait mieux que X % des Pokémon de la source ». Un percentile de "
             "90 veut dire la même chose quel que soit le nombre de votants, et c'est ce qui nous permet ensuite de comparer "
             "Reddit, le Johto Times et Google.", "exploration"),
            ("On a vérifié que le classement est fiable",
             [html.P("Une part de votes, c'est une proportion estimée sur environ 52 700 votes. On a calculé son intervalle "
                     "de confiance à 95 % (méthode de Wilson) et regardé à quels percentiles correspondent ses deux bornes. "
                     "On voit que la bande est très fine en haut (2 points) et très large en bas (environ 25 points) : "
                     "Reddit est fiable pour dire qui est très aimé, beaucoup moins pour classer les moins aimés."),
              t.mini(f2, 230, "En bleu clair : où le Pokémon pourrait vraiment se trouver, avec 95 % de confiance.")],
             "hors"),
            ("Puis on a comparé les générations",
             "On a fait la moyenne des percentiles par génération (le graphique du haut), comme les comparaisons par "
             "groupe qu'on faisait au TP d'exploration. La génération 1 est nettement au-dessus de 50.", "exploration"),
            ("Pourquoi on n'a pas pris le Johto Times ici",
             "Dans ce sondage, chacun vote à l'intérieur de chaque génération : toutes les générations ont donc la même "
             "moyenne par construction, et l'effet génération ne peut pas se voir.", "exploration"),
        ], attention="on voit que les anciens sont plus aimés, mais dire que c'est la nostalgie, c'est une interprétation "
                     "(corrélation n'est pas causalité). On la teste sur la page « Design ou nostalgie »."),
    )


# ---------- 2. Plus aimé que prévu ----------
def bloc_residus():
    s = _donnees()
    sur = s[s["sur_cote"] == "partout"].nlargest(8, "resid_moyen")
    sous = s[s["sous_cote"] == "partout"].nsmallest(8, "resid_moyen")
    d = pd.concat([sous.sort_values("resid_moyen", ascending=False), sur.sort_values("resid_moyen")])
    fig = go.Figure(go.Bar(
        y=d["nom_fr"], x=d["resid_moyen"] * 100, orientation="h", marker_cornerradius=4,
        marker_color=[t.SAPIN if v > 0 else t.ROUGE for v in d["resid_moyen"]],
        customdata=d[list(SOURCES)].values * 100,
        hovertemplate=("<b>%{y}</b><br>écart moyen : %{x:+.0f} points"
                       "<br>Reddit %{customdata[0]:+.0f} · Johto %{customdata[1]:+.0f} · Google %{customdata[2]:+.0f}"
                       "<extra></extra>"),
    ))
    fig.add_vline(x=0, line_color=t.GRIS_FONCE)
    fig.update_xaxes(title="Popularité réelle − popularité prévue (points de percentile)")
    fig.update_yaxes(title=None)
    n_sur = int((s["sur_cote"] == "partout").sum())
    n_sous = int((s["sous_cote"] == "partout").sum())
    mod = _modeles()
    r2 = mod[mod["modele"] == "bonus starter par stade"].set_index("source")["r2_ajuste"]

    # montrer : un effet à la fois (type, Johto Times)
    tm = table_maitre()[["dex", "type1"]].merge(popularite()[["dex", "johto_pct_gen"]], on="dex")
    pt = tm.groupby("type1")["johto_pct_gen"].mean().sort_values()
    f1 = go.Figure(go.Bar(x=pt.index, y=pt.values * 100, marker_cornerradius=3,
                          marker_color=[t.SAPIN if v > .55 else t.ROUGE if v < .45 else t.GRIS for v in pt.values],
                          hovertemplate="%{x} : %{y:.0f}<extra></extra>"))
    f1.add_hline(y=50, line_dash="dot", line_color=t.GRIS_FONCE)
    f1.update_yaxes(title="percentile moyen (Johto)", range=[0, 75])

    # montrer : les coefficients du modèle (Johto Times)
    c = _coefs()
    c = c[(c["source"] == "johto") & (c["variable"] != "constante")
          & ~c["variable"].str.startswith("génération")].sort_values("coef")
    f2 = go.Figure(go.Bar(
        y=c["variable"], x=c["coef"] * 100, orientation="h", marker_cornerradius=3,
        marker_color=[(t.SAPIN if v > 0 else t.ROUGE) if p < .05 else t.GRIS for v, p in zip(c["coef"], c["p_valeur"])],
        customdata=c["p_valeur"], hovertemplate="%{y} : %{x:+.0f} points (p = %{customdata:.3f})<extra></extra>"))
    f2.add_vline(x=0, line_color=t.GRIS_FONCE)
    f2.update_xaxes(title="effet sur le percentile (points), à autres effets égaux")

    # montrer : prévu contre réel
    j = s.merge(popularite()[["dex", "johto_pct_gen"]], on="dex").dropna(subset=["resid_johto"])
    j["prevu"] = j["johto_pct_gen"] - j["resid_johto"]
    coul = np.where(j["sur_cote"] == "partout", t.SAPIN, np.where(j["sous_cote"] == "partout", t.ROUGE, t.GRIS))
    f3 = go.Figure(go.Scatter(
        x=j["prevu"] * 100, y=j["johto_pct_gen"] * 100, mode="markers", text=j["nom_fr"],
        marker=dict(size=6, color=coul, opacity=.8),
        hovertemplate="<b>%{text}</b><br>prévu %{x:.0f} · réel %{y:.0f}<extra></extra>"))
    f3.add_shape(type="line", x0=0, y0=0, x1=100, y1=100, line=dict(color=t.GRIS_FONCE, dash="dot"))
    f3.update_xaxes(title="popularité prévue par le modèle", range=[-5, 105])
    f3.update_yaxes(title="popularité réelle", range=[-5, 105])

    # montrer : le seuil des 10 %
    r = s["resid_johto"].dropna() * 100
    haut, bas = r.quantile(.9), r.quantile(.1)
    f4 = go.Figure(go.Histogram(x=r, nbinsx=50, marker_color=t.GRIS, hovertemplate="%{x} : %{y} Pokémon<extra></extra>"))
    f4.add_vline(x=haut, line_color=t.SAPIN, annotation_text="10 % les plus hauts")
    f4.add_vline(x=bas, line_color=t.ROUGE, annotation_text="10 % les plus bas", annotation_position="top left")
    f4.update_xaxes(title="résidu au Johto Times (points)")

    # montrer : les deux sondages d'accord
    a = s.dropna(subset=["resid_reddit", "resid_johto"])
    rho = spearmanr(a["resid_reddit"], a["resid_johto"])[0]
    f5 = go.Figure(go.Scatter(x=a["resid_reddit"] * 100, y=a["resid_johto"] * 100, mode="markers", text=a["nom_fr"],
                              marker=dict(size=5, color=t.GLACE, opacity=.6),
                              hovertemplate="<b>%{text}</b><br>Reddit %{x:+.0f} · Johto %{y:+.0f}<extra></extra>"))
    f5.update_xaxes(title="résidu Reddit")
    f5.update_yaxes(title="résidu Johto Times")

    options = [{"label": f"{r.nom_fr} (n° {r.dex})", "value": r.dex} for r in s.sort_values("nom_fr").itertuples()]
    return t.question(
        "Quels Pokémon sont plus aimés que ce qu'on attendait ?",
        ["Une fois la génération, le stade, le statut de starter, de légendaire et le type pris en compte, ",
         html.Strong(f"{n_sur} Pokémon sont sur-cotés dans toutes les sources"),
         " (Évoli et ses évolutions, Lucario, Lougaroc, Zorua…) et ",
         html.Strong(f"{n_sous} sont sous-cotés partout"), ", dont beaucoup de Dragons au stade 2. "
         f"Ces effets attendus n'expliquent que {t.pct(r2.min())} à {t.pct(r2.max())} % de la popularité : "
         "le reste, c'est le Pokémon lui-même."],
        html.Div(className="deux-colonnes", children=[
            html.Div([
                html.Div(className="legende-maison", children=[
                    html.Span("■ ", style={"color": t.SAPIN}), "plus aimé que prévu   ",
                    html.Span("■ ", style={"color": t.ROUGE}), "moins aimé que prévu",
                ]),
                t.graphe(fig, 480),
            ]),
            html.Div([
                html.Div(className="controle", children=[
                    html.Label("Choisis un Pokémon à ouvrir 🎁", htmlFor="ssc-choix"),
                    dcc.Dropdown(id="ssc-choix", options=options, value=133, clearable=False),
                ]),
                html.Div(id="ssc-fiche", className="fiche"),
            ]),
        ]),
        methode=t.etapes([
            ("On n'a pas fusionné les sources",
             "Reddit (percentile global), Johto Times (percentile dans la génération) et Google Trends (percentile médian "
             "sur 67 pays). Chaque public garde sa colonne, et on fait tout ce qui suit une fois par source. Pour Google, "
             "les 28 Pokémon dont le nom est aussi un mot (Persian, Ditto…) ont été retirés, donc ils n'ont pas de résidu Google.",
             "exploration"),
            ("On a regardé chaque effet tout seul",
             [html.P("Avant de faire un modèle, on a regardé la popularité moyenne par génération, stade, starter, "
                     "légendaire et type. Par exemple pour le type : Dragon, Spectre et Ténèbres sont au-dessus, Insecte et "
                     "Roche en dessous."),
              t.mini(f1, 220, "Popularité moyenne par type principal au Johto Times (vert = au-dessus de 55, rouge = en dessous de 45).")],
             "exploration"),
            ("On a codé les variables qualitatives",
             "Génération, stade et type sont qualitatives (vu en cours : nominales ou ordinales). On les a transformées en "
             "indicatrices 0/1, avec une modalité de référence : génération 1, stade 1, type Normal. Un coefficient se lit "
             "donc « par rapport à un Pokémon Normal de génération 1 au stade 1 ».", "exploration"),
            ("On a prédit la popularité avec une régression linéaire",
             [html.P(f"Une régression par source (moindres carrés). Elle explique {t.pct(r2['reddit'])} % de la "
                     f"variance sur Reddit, {t.pct(r2['johto'])} % au Johto Times et {t.pct(r2['trends'])} % sur Google "
                     "(R² ajusté). On n'a pas mis le design dans le modèle exprès : c'est justement ce qu'on veut "
                     "retrouver dans ce qui reste. Ici, les effets au Johto Times (en gris : pas significatif) :"),
              t.mini(f2, 520, "À autres effets égaux, de combien de points de percentile chaque effet fait monter ou descendre.")],
             "hors"),
            ("On a corrigé le modèle pour les starters",
             "Avec un seul bonus « starter » pour toute la lignée, les formes du milieu sortaient sous-cotées à tort (voir le "
             "bloc des starters plus bas). Du coup on a mis un effet starter par stade : sur le graphique au-dessus, le "
             "starter de stade 2 ne gagne rien alors que les stades 1 et 3 gagnent beaucoup.", "hors"),
            ("On a calculé les résidus",
             [html.P("Résidu = popularité réelle − popularité prévue. Sur le nuage, un point au-dessus de la diagonale est "
                     "plus aimé que prévu. En vert les sur-cotés partout, en rouge les sous-cotés partout."),
              t.mini(f3, 300, "Johto Times : popularité prévue par le modèle contre popularité réelle.")],
             "hors"),
            ("On a fixé un seuil de 10 %",
             [html.P("Un Pokémon est « sur-coté » dans une source si son résidu est dans les 10 % les plus hauts, "
                     "« sous-coté » dans les 10 % les plus bas : le même seuil que pour dire qu'un Pokémon est populaire. "
                     "« Partout » = dans toutes les sources où il a une valeur."),
              t.mini(f4, 220, "La distribution des résidus au Johto Times et les deux seuils.")],
             "exploration"),
            ("On a vérifié que les sondages sont d'accord",
             [html.P(f"Spearman entre les résidus Reddit et Johto Times : {t.fr(rho)}. Ce qui reste après avoir retiré les "
                     "effets attendus est à peu près le même chez les deux publics, donc ce n'est pas du bruit. On prend "
                     "Spearman et pas Pearson parce qu'on cherche juste un lien monotone, sans supposer une droite."),
              t.mini(f5, 260, "Chaque point est un Pokémon : son résidu sur Reddit et au Johto Times.")],
             "exploration"),
        ], attention="pour quelques Pokémon (générations 8 et 9, ou noms retirés de Google), « partout » ne repose que "
                     "sur deux sources. Et en bas du classement Google, les noms à symboles ou à tiret (Nidoran♀, "
                     "Porygon-Z, Chongjian…) sont sans doute mal tapés, donc sous-estimés."),
    )


@callback(Output("ssc-fiche", "children"), Input("ssc-choix", "value"))
def fiche(dex):
    s = _donnees().set_index("dex")
    r = s.loc[dex]
    vals = [r[c] for c in SOURCES]
    barres = go.Figure(go.Bar(
        x=["Reddit", "Johto", "Google"], y=[v * 100 if pd.notna(v) else 0 for v in vals], marker_cornerradius=4,
        marker_color=[t.SAPIN if v > 0 else t.ROUGE if v < 0 else t.GRIS for v in np.nan_to_num(vals)],
        text=["" if pd.notna(v) else "pas de valeur" for v in vals],
        hovertemplate="%{x} : %{y:+.0f} points<extra></extra>",
    ))
    barres.add_hline(y=0, line_color=t.GRIS_FONCE)
    barres.update_yaxes(title="écart (points)", range=[-60, 60])
    barres.update_layout(height=220, margin=dict(l=10, r=10, t=10, b=10))
    etiquettes = []
    if r["sur_cote"] != "non":
        etiquettes.append(html.Span(f"sur-coté {r['sur_cote']}", className="etiquette vert"))
    if r["sous_cote"] != "non":
        etiquettes.append(html.Span(f"sous-coté {r['sous_cote']}", className="etiquette"))
    if not etiquettes:
        etiquettes.append(html.Span("aimé comme prévu", className="etiquette gris"))
    return [
        t.image(dex, 140),
        html.H3(r["nom_fr"]),
        html.P(f"Génération {r['generation']} · {r['stade_categorie']}"
               + (" · starter" if r["starter"] else "") + (" · légendaire" if r["legendaire"] else "")),
        html.Div(etiquettes),
        dcc.Graph(figure=barres, config={"displayModeBar": False}),
    ]


# ---------- 3. Les starters ----------
def bloc_starters():
    tm = table_maitre().merge(popularite()[["dex", "johto_pct_gen"]], on="dex")
    st = tm[tm["starter"]].groupby("stade")["johto_pct_gen"].mean()
    autres = tm.loc[~tm["starter"], "johto_pct_gen"].mean()
    noms = {1: "1re forme<br>(Salamèche…)", 2: "forme du milieu<br>(Reptincel…)", 3: "forme finale<br>(Dracaufeu…)"}
    fig = go.Figure(go.Bar(
        x=[noms[i] for i in st.index], y=st.values * 100, marker_cornerradius=4,
        marker_color=[t.ROUGE if i == 2 else t.SAPIN for i in st.index],
        hovertemplate="%{x} : percentile moyen %{y:.0f}<extra></extra>",
    ))
    fig.add_hline(y=autres * 100, line_dash="dot", line_color=t.GRIS_FONCE,
                  annotation_text=f"les autres Pokémon : {t.pct(autres)}", annotation_position="top")
    fig.update_yaxes(title="Percentile (Johto Times)", range=[0, 100])

    # montrer : chaque lignée de starters
    s = tm[tm["starter"]].sort_values(["dex_starter", "stade"])
    f1 = go.Figure()
    for _, l in s.groupby("dex_starter"):
        f1.add_trace(go.Scatter(x=["1re forme", "milieu", "finale"], y=l["johto_pct_gen"] * 100, mode="lines+markers",
                                line=dict(color=t.GRIS, width=1.5), marker=dict(size=5, color=t.GRIS),
                                text=l["nom_fr"], hovertemplate="%{text} : %{y:.0f}<extra></extra>", showlegend=False))
    f1.add_trace(go.Scatter(x=["1re forme", "milieu", "finale"], y=st.values * 100, mode="lines+markers",
                            line=dict(color=t.ROUGE, width=3), marker=dict(size=9, color=t.ROUGE),
                            name="moyenne", hovertemplate="moyenne : %{y:.0f}<extra></extra>"))
    f1.update_yaxes(title="percentile (Johto)", range=[0, 102])

    return t.question(
        "Les starters sont-ils aimés à tous les stades ?",
        ["Pas vraiment : on aime la ", html.Strong("première forme"), " et la ", html.Strong("forme finale"),
         f", mais l'étape du milieu tombe à {t.pct(st.loc[2])} de percentile en moyenne, contre "
         f"{t.pct(st.loc[1])} et {t.pct(st.loc[3])}. On est attaché au compagnon du début et au héros de la fin, "
         "pas à l'ado entre les deux."],
        t.graphe(fig, 340),
        methode=t.etapes([
            ("On a pris une mesure sans effet nostalgie",
             "Le percentile dans la génération du Johto Times 2025 : chaque participant vote dans chaque génération, donc on "
             "compare un starter seulement aux Pokémon de sa génération.", "exploration"),
            ("On a retrouvé les lignées",
             "Les 27 starters des jeux principaux sont saisis à la main (liste de Bulbapedia), puis on a retrouvé leurs "
             "évolutions dans PokéAPI en remontant la lignée : 81 Pokémon, 3 stades par lignée.", "exploration"),
            ("On a tracé chaque lignée",
             [html.P("Chaque ligne grise est une lignée (Bulbizarre → Herbizarre → Florizarre, etc.). Presque toutes font "
                     "un « V » : le creux est au milieu. La ligne rouge, c'est la moyenne."),
              t.mini(f1, 260, "Les 27 lignées de starters, stade par stade.")],
             "exploration"),
            ("Ça a changé notre modèle",
             "C'est ce « V » qui nous a fait mettre un effet starter différent pour chaque stade dans la régression du "
             "bloc d'au-dessus.", "hors"),
        ]),
    )


def layout():
    return html.Div([
        t.entete_page("Sur-cotés et sous-cotés",
                      "Ce qui reste de la popularité quand on retire tout ce qu'on pouvait prévoir.", "pingoleon"),
        bloc_generation(),
        bloc_residus(),
        bloc_starters(),
    ])
