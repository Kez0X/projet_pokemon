"""Notebooks 03 (couleurs des images) et 06 (design ou nostalgie, ACP)."""
import colorsys

import dash
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

import theme as t
from demo_couleurs import demo
from donnees import PROCESSED, couleurs, pca, table_maitre

dash.register_page(__name__, path="/conception", name="Design ou nostalgie", order=3)


def _palette(chaine):
    """'#hex:part;#hex:part' -> [(hex, part)]"""
    out = []
    for morceau in str(chaine).split(";"):
        if ":" in morceau:
            h, p = morceau.split(":")
            out.append((h, float(p)))
    return out


def barre_palette(pal, titre=None):
    return html.Div([
        html.Div(titre, className="mini-legende") if titre else None,
        html.Div(className="palette", style={"maxWidth": "100%"}, children=[
            html.Div(title=f"{h} · {p * 100:.0f} %", style={"background": h, "flex": p}) for h, p in pal
        ]),
    ])


# ---------- 1. De plus en plus colorés ----------
def bloc_couleurs():
    c = couleurs().merge(table_maitre()[["dex", "generation", "nom_fr"]], on="dex")
    g = c.groupby("generation")["nb_couleurs"].mean()
    fig = go.Figure(go.Scatter(
        x=g.index, y=g.values, mode="lines+markers", line=dict(color=t.ROUGE, width=2),
        marker=dict(size=9, color=t.ROUGE, line=dict(color="#fffaf0", width=2)),
        hovertemplate="Génération %{x} : %{y:.1f} couleurs en moyenne<extra></extra>",
    ))
    fig.update_xaxes(title="Génération", dtick=1)
    fig.update_yaxes(title="Nombre moyen de couleurs", range=[0, 4.5])
    options = [{"label": f"{r.nom_fr} (n° {r.dex})", "value": r.dex} for r in c.sort_values("nom_fr").itertuples()]
    return t.question(
        "Les Pokémon sont-ils de plus en plus colorés ?",
        ["Oui. Un Pokémon de 1re génération a ", html.Strong(f"{t.fr(g.loc[1], 1)} couleurs"),
         f" importantes en moyenne, contre {t.fr(g.iloc[-1], 1)} en génération {g.index[-1]}. "
         "Les dessins récents sont plus chargés (et un peu plus sombres)."],
        html.Div(className="deux-colonnes", children=[
            t.graphe(fig, 340),
            html.Div([
                html.Div(className="controle", children=[
                    html.Label("Ouvre la palette d'un Pokémon 🎨", htmlFor="conc-choix"),
                    dcc.Dropdown(id="conc-choix", options=options, value=6, clearable=False),
                ]),
                html.Div(id="conc-fiche", className="fiche"),
            ]),
        ]),
        methode=html.Div([
            html.P(["Pour montrer chaque étape, on refait ici le calcul du notebook 03 en direct sur le Pokémon choisi "
                    "au-dessus (change-le pour voir ce que ça donne sur un autre)."], className="note"),
            dcc.Loading(html.Div(id="conc-methode"), color=t.ROUGE),
        ]),
    )


@callback(Output("conc-fiche", "children"), Input("conc-choix", "value"))
def fiche_palette(dex):
    c = couleurs().set_index("dex").loc[dex]
    nom = table_maitre().set_index("dex").loc[dex, "nom_fr"]
    return [
        t.image(dex, 140),
        html.H3(nom),
        barre_palette(_palette(c["palette"])),
        html.P(f"{int(c['nb_couleurs'])} couleur(s) importante(s) · la principale couvre {c['dom_part'] * 100:.0f} % du corps"),
    ]


@callback(Output("conc-methode", "children"), Input("conc-choix", "value"))
def methode_couleurs(dex):
    nom = table_maitre().set_index("dex").loc[dex, "nom_fr"]
    d = demo(dex)
    X = d["pixels"]
    f_pix = go.Figure(go.Scatter3d(
        x=X[:, 0], y=X[:, 1], z=X[:, 2], mode="markers",
        marker=dict(size=2, color=[f"rgb({r:.0f},{g:.0f},{b:.0f})" for r, g, b in X]), hoverinfo="skip"))
    f_pix.update_layout(scene=dict(xaxis_title="rouge", yaxis_title="vert", zaxis_title="bleu",
                                   bgcolor="rgba(0,0,0,0)"), margin=dict(l=0, r=0, t=0, b=0))
    f_k = go.Figure([
        go.Scatter(x=d["ks"], y=d["silhouettes"], mode="lines+markers", name="silhouette", line=dict(color=t.ROUGE),
                   hovertemplate="k = %{x} : silhouette %{y:.2f}<extra></extra>"),
    ])
    f_k.add_vline(x=8, line_dash="dot", line_color=t.GRIS_FONCE, annotation_text="k = 8 (notre choix)")
    f_k.update_xaxes(title="k (nombre de groupes)", dtick=1)
    f_k.update_yaxes(title="silhouette")
    f_i = go.Figure(go.Scatter(x=d["ks"], y=d["inerties"], mode="lines+markers", line=dict(color=t.GLACE),
                               hovertemplate="k = %{x} : inertie %{y:.3s}<extra></extra>"))
    f_i.update_xaxes(title="k", dtick=1)
    f_i.update_yaxes(title="inertie")
    k_best = d["ks"][max(range(len(d["ks"])), key=lambda i: d["silhouettes"][i])]
    f_contour = go.Figure(go.Image(z=d["image"], hoverinfo="skip"))
    f_contour.update_xaxes(visible=False)
    f_contour.update_yaxes(visible=False)
    f_contour.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    return t.etapes([
        ("On a enlevé le contour noir du dessin",
         [html.P("Tous les dessins officiels ont un trait noir autour du Pokémon et de ses détails : ce n'est pas une couleur "
                 "du Pokémon. Mais certaines zones noires en sont une (le bout des oreilles de Pikachu, des yeux…). Ce qui "
                 "les distingue, c'est la forme : le contour est un trait fin. On repère les pixels très sombres (L* < 15), "
                 "puis une ouverture morphologique (on érode puis on dilate ce masque) efface les traits fins et garde les "
                 f"taches pleines. On enlève aussi le bord adouci du trait. Pour {nom}, le contour couvre "
                 f"{d['part_contour'] * 100:.0f} % du corps, et le noir gardé {d['part_noir'] * 100:.0f} %."),
          t.mini(f_contour, 300, f"{nom} : en rouge le contour (enlevé), en noir le noir « plein » (gardé).")],
         "hors"),
        ("On a pris les pixels de l'image",
         [html.P(f"L'image de {nom} fait 475 × 475 pixels avec un fond transparent. On ne garde que les pixels opaques "
                 "(alpha ≥ 128) qui ne sont pas du contour, puis on en tire 3 000 au hasard. Chaque pixel devient un point "
                 "dans l'espace (rouge, vert, bleu) : c'est ce nuage qu'on va découper en groupes."),
          t.mini(f_pix, 320, f"Les 3 000 pixels de {nom}, chacun à sa place dans l'espace des couleurs (tu peux le tourner).")],
         "exploration"),
        ("On a cherché le bon k avec la silhouette et le coude",
         [html.P(f"Comme au TP clustering, on fait tourner le k-means pour k = 2 à 12. Pour {nom}, la meilleure silhouette "
                 f"est à k = {k_best}. Mais ça change d'un Pokémon à l'autre (2 pour Pikachu, 10 pour Dracaufeu) et "
                 "l'inertie n'a pas de vrai coude. Du coup on a pris k = 8 pour tout le monde, assez grand pour ne rater "
                 "aucune couleur, et on fusionne les nuances juste après."),
          html.Div(className="deux-colonnes", style={"gridTemplateColumns": "1fr 1fr"}, children=[
              t.mini(f_k, 200, "Silhouette selon k."), t.mini(f_i, 200, "Inertie selon k (méthode du coude)."),
          ])],
         "clustering"),
        ("Le k-means avec k = 8",
         [html.P("Chaque groupe donne une couleur (son centre) et une part du corps (sa taille). On voit souvent la même "
                 "couleur coupée en deux : la partie au soleil et la partie à l'ombre."),
          barre_palette(d["brut"], "Les 8 couleurs du k-means, de la plus grande à la plus petite.")],
         "clustering"),
        ("On a fusionné les nuances avec une CAH",
         [html.P("On regroupe les 8 centres avec une classification hiérarchique (lien moyen), coupée quand deux couleurs "
                 "sont à plus de 25 dans l'espace Lab. On passe par Lab parce que la distance y correspond à ce que voit "
                 "l'œil (on a testé 15, 25 et 35 sur des exemples)."),
          barre_palette(d["final"], f"La palette finale : {d['importantes']} couleur(s) importante(s) (au moins 5 % du corps)."),
          html.P("Le tirage au hasard des 3 000 pixels est le même que dans le notebook (chaque Pokémon a son propre "
                 "tirage) : la palette est exactement celle de la fiche au-dessus.",
                 className="note")],
         ["clustering", "hors"]),
        ("Et on a fait ça pour les 1 025 Pokémon",
         "On compte les couleurs qui couvrent au moins 5 % du corps (à 2 % on comptait les yeux et les reflets, à 10 % on "
         "perdait des couleurs bien visibles), puis on fait la moyenne par génération : c'est le graphique du haut.",
         "exploration"),
    ], attention="les seuils (Lab, contour, 5 %) sont choisis à l'œil sur des exemples, et les détails noirs très fins "
                 "(rayures, moustaches) partent avec le contour, puisqu'on ne peut pas les distinguer d'un trait.")


# ---------- 2. Design ou nostalgie ----------
def bloc_acp():
    d = pca().merge(table_maitre()[["dex", "generation", "nom_fr"]], on="dex")
    centres = d.groupby("generation")[["PC1", "PC2"]].mean()
    acp = pd.read_csv(PROCESSED / "methode_06_acp.csv")
    load = pd.read_csv(PROCESSED / "methode_06_loadings.csv")
    sp = pd.read_csv(PROCESSED / "methode_06_spearman.csv")
    reg = pd.read_csv(PROCESSED / "methode_06_regression.csv")
    r2 = pd.read_csv(PROCESSED / "methode_06_r2.csv").set_index(["source", "modele"])["r2_ajuste"]
    gardee = acp.loc[acp["valeur_propre"] > 1, "part_variance"].sum()

    fig = go.Figure()
    fig.add_trace(go.Scattergl(
        x=d["PC1"], y=d["PC2"], mode="markers", name="un Pokémon",
        marker=dict(size=5, color=t.GRIS, opacity=.6),
        text=d["nom_fr"], customdata=d["generation"],
        hovertemplate="<b>%{text}</b> (gén. %{customdata})<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=centres["PC1"], y=centres["PC2"], mode="lines+markers+text", name="centre de chaque génération",
        line=dict(color=t.ROUGE, width=2), text=[str(i) for i in centres.index], textposition="top center",
        textfont=dict(size=13, color=t.ENCRE),
        marker=dict(size=11, color=t.ROUGE, line=dict(color="#fffaf0", width=2)),
        hovertemplate="Génération %{text}<extra></extra>",
    ))
    fig.update_xaxes(title=f"Axe 1 : petit et faible → gros et fort ({t.pct(acp.part_variance[0])} %)", range=[-2.5, 2.5])
    fig.update_yaxes(title=f"Axe 2 : sobre → coloré ({t.pct(acp.part_variance[1])} %)", range=[-2.5, 2.5])

    # montrer : éboulis des valeurs propres
    f1 = go.Figure(go.Bar(x=acp["composante"], y=acp["valeur_propre"], marker_cornerradius=3,
                          marker_color=[t.SAPIN if v > 1 else t.GRIS for v in acp["valeur_propre"]],
                          customdata=acp["part_variance"] * 100,
                          hovertemplate="axe %{x} : valeur propre %{y:.2f} (%{customdata:.0f} %)<extra></extra>"))
    f1.add_hline(y=1, line_dash="dot", line_color=t.ROUGE, annotation_text="critère de Kaiser (1)")
    f1.update_xaxes(title="axe", dtick=1)
    f1.update_yaxes(title="valeur propre")

    # montrer : loadings des deux premiers axes
    f2 = go.Figure()
    for axe, coul in [("PC1", t.ROUGE), ("PC2", t.GLACE)]:
        f2.add_trace(go.Bar(y=load["variable"], x=load[axe], orientation="h", name=f"axe {axe[-1]}", marker_color=coul,
                            hovertemplate="%{y} : %{x:.2f}<extra>" + axe + "</extra>"))
    f2.update_layout(barmode="group", showlegend=True)
    f2.update_xaxes(title="corrélation de la variable avec l'axe", range=[-1, 1])

    # montrer : Spearman axes ↔ popularité
    f3 = go.Figure()
    for src, nom, coul in [("reddit", "Reddit", t.ROUGE), ("johto", "Johto Times", t.OR), ("trends", "Google", t.GLACE)]:
        s = sp[sp["source"] == src]
        f3.add_trace(go.Bar(x=s["axe"], y=s["rho"], name=nom, marker_color=coul, customdata=s["p_valeur"],
                            hovertemplate="%{x} : rho = %{y:.2f} (p = %{customdata:.3g})<extra>" + nom + "</extra>"))
    f3.update_layout(barmode="group", showlegend=True)
    f3.update_yaxes(title="rho de Spearman", range=[-.1, .45])

    # montrer : les coefficients des générations avec et sans les axes
    f4 = go.Figure()
    for src, nom, coul in [("reddit", "Reddit", t.ROUGE), ("trends", "Google", t.GLACE)]:
        s = reg[reg["source"] == src]
        f4.add_trace(go.Scatter(x=s["generation"], y=s["coef_sans_axes"] * 100, mode="lines+markers", name=f"{nom}, génération seule",
                                line=dict(color=coul, width=2), hovertemplate="gén. %{x} : %{y:+.0f}<extra></extra>"))
        f4.add_trace(go.Scatter(x=s["generation"], y=s["coef_avec_axes"] * 100, mode="lines+markers", name=f"{nom}, + design",
                                line=dict(color=coul, width=2, dash="dot"), hovertemplate="gén. %{x} : %{y:+.0f}<extra></extra>"))
    f4.update_layout(showlegend=True)
    f4.update_xaxes(title="génération (par rapport à la 1re)", dtick=1)
    f4.update_yaxes(title="effet sur le percentile (points)")
    sp_c = sp[sp["axe"] == "PC2"]["rho"].abs().max()
    sp_1 = sp[(sp["axe"] == "PC1") & (sp["source"] != "trends")]["rho"]

    return t.question(
        "Les générations récentes sont-elles moins aimées à cause de leur design ?",
        ["Non. Le design a bien bougé : génération après génération, le centre glisse vers ",
         html.Strong("« plus fort et plus coloré »"), ". Mais à génération égale, la couleur ne change rien "
         "à la popularité (seuls les Pokémon gros et forts sont un peu plus aimés), et ",
         html.Strong("ajouter le design au modèle ne réduit presque pas l'écart entre générations"),
         ". Ce n'est donc pas le design qu'on a mesuré qui explique le désamour : plutôt la nostalgie."],
        t.graphe(fig, 460),
        methode=t.etapes([
            ("On a choisi 12 variables de design",
             "Les 6 stats (séparées, pour que l'ACP voie les profils), la taille et le poids, et 4 variables de couleur "
             "du k-means (nombre de couleurs, saturation, luminosité, part de la couleur dominante). On a retiré la teinte : "
             "c'est un angle (0° et 359° sont presque la même couleur), l'ACP la lirait comme deux extrêmes.", "transfo"),
            ("On a transformé puis standardisé",
             "Taille et poids passent en log, à cause des géants comme Éthernatos (20 m). Puis on standardise chaque "
             "variable (moyenne 0, écart-type 1). Comme on l'a vu en cours, l'ACP est sensible à l'échelle : sans ça, les "
             "stats (des centaines) écraseraient la saturation (entre 0 et 1).", ["exploration", "transfo"]),
            ("On a fait l'ACP et gardé 4 axes",
             [html.P(f"L'ACP cherche les axes qui résument le plus de variance. On garde les axes dont la valeur propre "
                     f"dépasse 1 (critère de Kaiser : l'axe résume plus qu'une variable toute seule). Ça fait 4 axes et "
                     f"{t.pct(gardee)} % de la variance."),
              t.mini(f1, 220, "L'éboulis des valeurs propres : en vert les axes qu'on garde.")],
             "transfo"),
            ("On a donné un nom aux axes",
             [html.P("On regarde quelles variables sont liées à chaque axe (les loadings). Sur l'axe 1, toutes les stats, la "
                     "taille et le poids vont dans le même sens : c'est « gros et fort ». Sur l'axe 2, le nombre de couleurs "
                     "et la saturation s'opposent à la part de la couleur dominante : c'est « coloré ». On a vérifié avec "
                     "les Pokémon aux extrémités (Crèmy → Éthernatos ; Leveinard → Crocogril)."),
              t.mini(f2, 380, "Ce que chaque variable pèse sur les deux premiers axes.")],
             "transfo"),
            ("On a suivi le centre de chaque génération",
             "On fait la moyenne des coordonnées de chaque génération et on relie les points dans l'ordre : c'est la ligne "
             "rouge du graphique du haut, qui part vers « plus fort et plus coloré ».", "transfo"),
            ("On a testé le lien avec la popularité, à génération égale",
             [html.P(f"On prend les percentiles dans la génération (l'effet nostalgie est retiré par construction) et on "
                     f"calcule Spearman avec chaque axe. L'axe 1 est lié dans les sondages ({t.fr(sp_1.min())} à "
                     f"{t.fr(sp_1.max())}), l'axe « coloré » pas du tout (|rho| ≤ {t.fr(sp_c)})."),
              t.mini(f3, 240, "Corrélation de Spearman entre chaque axe et la popularité dans la génération.")],
             "exploration"),
            ("On a vu si le design « absorbe » l'effet génération",
             [html.P(f"Une régression popularité ~ génération, puis la même avec les 4 axes en plus. Le R² monte (Reddit "
                     f"{t.pct(r2[('reddit', 'génération seule')])} → {t.pct(r2[('reddit', 'génération + axes')])} %), donc "
                     "le design apporte de l'information. Mais les effets des générations ne bougent presque pas : les "
                     "lignes pleines et pointillées sont collées. L'écart entre générations ne passe pas par le design."),
              t.mini(f4, 280, "Effet de chaque génération, sans (plein) et avec (pointillé) les axes de design.")],
             "hors"),
        ], attention="les 6 stats font la moitié des variables, elles pèsent lourd dans l'axe 1. Et ça montre seulement "
                     "que ce n'est pas le design mesuré ici (taille, stats, couleurs) qui explique l'écart, pas que c'est "
                     "la nostalgie : le style de dessin ou l'anime ne sont pas mesurés."),
    )


# ---------- 3. Bonus festif ----------
def _est_noel(chaine):
    rouge = vert = 0.0
    for h, p in _palette(chaine):
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
        teinte, lum, sat = colorsys.rgb_to_hls(r, g, b)
        teinte *= 360
        if sat < .35 or not .2 < lum < .8:
            continue
        if teinte < 15 or teinte > 345:
            rouge += p
        elif 90 < teinte < 160:
            vert += p
    return min(rouge, vert)


def bloc_noel():
    c = couleurs().merge(table_maitre()[["dex", "nom_fr"]], on="dex")
    c["noel"] = c["palette"].map(_est_noel)
    top = c[c["noel"] >= .10].sort_values("noel", ascending=False).head(12)
    return t.question(
        "Bonus : quels Pokémon sont aux couleurs de Noël ?",
        ["Juste pour le plaisir : avec les palettes du k-means, on cherche les Pokémon qui ont ",
         html.Strong("au moins 10 % de rouge et 10 % de vert"), f". Ils sont {(c['noel'] >= .10).sum()} sur 1 025."],
        t.galerie(top["dex"], top["nom_fr"]),
        methode=t.etapes([
            ("On est repartis des palettes du k-means",
             [html.P("La palette de chaque Pokémon trouvée plus haut (k-means sur les pixels, nuances fusionnées, contour "
                     "retiré), avec la part du corps de chaque couleur. Par exemple :"),
              *[barre_palette(_palette(r.palette), r.nom_fr) for r in top.head(3).itertuples()]],
             "clustering"),
            ("On a donné un nom aux couleurs",
             "Chaque couleur est passée en teinte / saturation / luminosité. Rouge = teinte à moins de 15° du rouge pur, "
             "vert = teinte entre 90° et 160°, et on ignore les couleurs trop grises, trop sombres ou trop claires.", "hors"),
            ("On a gardé les Pokémon rouges ET verts",
             "Un Pokémon est « de Noël » s'il a au moins 10 % de rouge et 10 % de vert. C'est un jeu, pas une analyse : "
             "les seuils sont choisis à la main.", "hors"),
        ]),
    )


def layout():
    return html.Div([
        t.entete_page("Design ou nostalgie ?",
                      "Les Pokémon récents sont moins aimés. Est-ce leur design, ou juste qu'on a grandi avec les anciens ?",
                      "blizzaroi"),
        bloc_couleurs(),
        bloc_acp(),
        bloc_noel(),
    ])
