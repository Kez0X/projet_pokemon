"""Notebook 08 : la popularité dans le monde (Google Trends par pays, CAH, MDS, Moran et LISA)."""
import dash
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

import theme as t
from donnees import PROCESSED, nom_vers_dex, pays, popularite

dash.register_page(__name__, path="/carte", name="Le monde", order=7)

# Nom des groupes de la CAH, repérés par un pays qui en fait partie (les numéros changent si on relance)
GROUPES = [
    ("Mexico", "Amérique latine, Espagne, Italie", t.ROUGE),
    ("France", "France, Suisse, Autriche", t.OR),
    ("India", "Asie du Sud", t.SAPIN),
    (None, "Le reste du monde", t.GLACE),
]


def _pays():
    p = pays().copy()
    noms = {}
    for repere, nom, _ in GROUPES:
        if repere is not None:
            noms[int(p.loc[p["pays"] == repere, "groupe_cah"].iloc[0])] = nom
    p["groupe_nom"] = p["groupe_cah"].map(lambda g: noms.get(g, GROUPES[-1][1]))
    return p


def _ratio():
    return pd.read_csv(PROCESSED / "trends_ratio_gengar_pays.csv", index_col=0)


def _geo(fig):
    fig.update_geos(showframe=False, showcoastlines=False, showcountries=True, countrycolor="#fffaf0",
                    showland=True, landcolor="#e9e3d6", bgcolor="rgba(0,0,0,0)", projection_type="natural earth",
                    lataxis_range=[-58, 85])
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), legend=dict(y=-.02, yanchor="top"))
    return fig


# ---------- 1. Le plus cherché ----------
def bloc_plus_cherche():
    p = _pays()
    r = _ratio()
    noms = popularite().set_index("dex")["nom_fr"]
    gardes = list(p["pays"])
    med = r[gardes].median(axis=1).sort_values(ascending=False).head(10)
    fig = go.Figure(go.Bar(
        y=[noms[d] for d in med.index][::-1], x=med.values[::-1], orientation="h", marker_cornerradius=4,
        marker_color=[t.ROUGE if noms[d] == "Pikachu" else t.GRIS for d in med.index][::-1],
        hovertemplate="%{y} : %{x:.2f} fois les recherches d'Ectoplasma<extra></extra>"))
    fig.add_vline(x=1, line_dash="dot", line_color=t.GRIS_FONCE, annotation_text="Ectoplasma (= 1)", annotation_position="bottom right")
    fig.update_xaxes(title="recherches Google, en nombre de fois Ectoplasma (médiane sur les 67 pays)")
    n = p["plus_cherche"].value_counts()

    # montrer : les zéros par pays
    z = (r == 0).mean().sort_values()
    f1 = go.Figure(go.Histogram(x=z * 100, nbinsx=40, marker_color=t.GRIS,
                                hovertemplate="%{x} % de zéros : %{y} pays<extra></extra>"))
    f1.add_vline(x=25, line_color=t.ROUGE, annotation_text="seuil 25 %")
    f1.update_xaxes(title="part des Pokémon à 0 dans le pays (%)")
    f1.update_yaxes(title="pays")

    # montrer : les mots retirés
    amb = popularite()[popularite()["trends_nom_ambigu"]].sort_values("dex")

    # montrer : le plus cherché pays par pays
    f2 = go.Figure(go.Bar(x=n.index, y=n.values, marker_color=[t.ROUGE if x == "Pikachu" else t.GRIS for x in n.index],
                          marker_cornerradius=4, hovertemplate="%{x} : %{y} pays<extra></extra>"))
    f2.update_yaxes(title="nombre de pays")

    return t.question(
        "Quel Pokémon est le plus cherché dans le monde ?",
        ["Sans surprise, ", html.Strong(f"Pikachu : c'est le plus cherché dans {n.get('Pikachu', 0)} pays sur {len(p)}"),
         f", et il est cherché {t.fr(med.iloc[0], 0)} fois plus qu'Ectoplasma. Derrière, on trouve Arceus "
         f"(le plus cherché dans {n.get('Arceus', 0)} pays), Dracaufeu, Évoli et Mewtwo : les stars de la licence."],
        html.Div([
            t.galerie(list(med.index[:6]), [noms[d] for d in med.index[:6]], taille=72),
            t.graphe(fig, 340),
        ]),
        methode=t.etapes([
            ("On a collecté Google Trends avec un Pokémon de référence",
             "Google ne compare que 5 termes à la fois, et en valeurs relatives (dans chaque pays, les 5 se partagent 100). "
             "Du coup chaque requête contenait Ectoplasma (Gengar) plus 4 autres Pokémon : 256 requêtes pour couvrir les "
             "1 025. Ectoplasma sert de « mètre étalon » commun à toutes les requêtes.", "hors"),
            ("On a tout ramené sur l'échelle d'Ectoplasma",
             "Dans chaque pays, on divise la valeur de chaque Pokémon par celle d'Ectoplasma dans la même requête. Un "
             "ratio de 2 = deux fois plus cherché qu'Ectoplasma. C'est ce qu'on voit sur le graphique du haut.",
             "exploration"),
            ("On a contrôlé la qualité des données",
             [html.P("Comme en cours, on a d'abord exploré : un pays a soit des valeurs pour toute la requête, soit que des 0 "
                     "(171 pays utilisables). Et comme Ectoplasma prend 89 % de chaque requête, les autres Pokémon n'ont que "
                     "des petits entiers, avec beaucoup de 0 dans les petits pays. On garde les 67 pays qui ont moins de 25 % "
                     "de Pokémon à 0, sinon on ne peut plus les départager."),
              t.mini(f1, 220, "Les 171 pays selon leur part de Pokémon à 0, et notre seuil.")],
             "exploration"),
            ("On a retiré les noms qui sont aussi des mots",
             [html.P(f"En haut du classement, on trouvait Persian (« persan »), Durant (le basketteur), Ditto, Onix (une "
                     f"voiture Chevrolet)… On mesurait le mot, pas le Pokémon. On a fait une liste à la main, complétée avec le "
                     f"dictionnaire anglais (un nom est retiré s'il est un mot et qu'il est beaucoup plus cherché qu'aimé). "
                     f"Ces {len(amb)} Pokémon n'ont plus de valeur Google (ils restent dans les sondages) :"),
              t.galerie(amb["dex"], amb["nom_fr"], taille=48)],
             "exploration"),
            ("Le plus cherché, pays par pays",
             [html.P("Pour chaque pays, on prend le Pokémon qui a le plus grand ratio, et on compte les pays."),
              t.mini(f2, 200, "Combien de pays ont chaque Pokémon comme plus cherché.")],
             "exploration"),
        ], attention="on cherche les noms anglais partout : Google mesure l'attention (ce qu'on tape), pas forcément "
                     "l'affection, et les pays qui écrivent autrement (Japon, Corée…) sont mal mesurés."),
    )


# ---------- 2. Des goûts différents selon les pays ? ----------
def bloc_groupes():
    p = _pays()
    fig = go.Figure()
    for _, nom, couleur in GROUPES:
        s = p[p["groupe_nom"] == nom]
        fig.add_trace(go.Choropleth(
            locations=s["iso3"], z=[1] * len(s), name=nom, showscale=False, showlegend=True,
            colorscale=[[0, couleur], [1, couleur]], marker_line_color="#fffaf0", marker_line_width=.6,
            text=s["pays"], customdata=s[["favori_surrep", "plus_cherche"]].values,
            hovertemplate="<b>%{text}</b><br>favori du pays : %{customdata[0]}<br>"
                          "le plus cherché : %{customdata[1]}<extra>" + nom + "</extra>",
        ))
    _geo(fig)
    sil = pd.read_csv(PROCESSED / "methode_08_silhouette.csv")
    stress = pd.read_csv(PROCESSED / "methode_08_mds.csv")["stress"].iloc[0]

    f1 = go.Figure([
        go.Scatter(x=sil["k"], y=sil["silhouette_kmeans"], mode="lines+markers", name="k-means", line=dict(color=t.GLACE)),
        go.Scatter(x=sil["k"], y=sil["silhouette_cah_ward"], mode="lines+markers", name="CAH Ward", line=dict(color=t.ROUGE)),
    ])
    f1.add_vline(x=4, line_dash="dot", line_color=t.GRIS_FONCE, annotation_text="k = 4")
    f1.update_layout(showlegend=True)
    f1.update_xaxes(title="k", dtick=1)
    f1.update_yaxes(title="silhouette", range=[0, .2])
    f2 = go.Figure(go.Scatter(x=sil["k"], y=sil["inertie_kmeans"], mode="lines+markers", line=dict(color=t.GLACE)))
    f2.update_xaxes(title="k", dtick=1)
    f2.update_yaxes(title="inertie (k-means)")

    f3 = go.Figure()
    for _, nom, couleur in GROUPES:
        s = p[p["groupe_nom"] == nom]
        f3.add_trace(go.Scatter(x=s["mds1"], y=s["mds2"], mode="markers+text", name=nom, text=s["iso3"],
                                textposition="top center", textfont=dict(size=9, color=t.ENCRE_2),
                                marker=dict(size=9, color=couleur), customdata=s["pays"],
                                hovertemplate="%{customdata}<extra>" + nom + "</extra>"))
    f3.update_layout(showlegend=True)
    f3.update_xaxes(title="axe MDS 1")
    f3.update_yaxes(title="axe MDS 2")

    options = [{"label": r.pays, "value": r.pays} for r in p.sort_values("pays").itertuples()]
    return t.question(
        "Chaque pays a-t-il son Pokémon préféré ?",
        ["Oui, et les goûts suivent la géographie. En regardant le Pokémon cherché ", html.Strong("plus là qu'ailleurs"),
         f", on trouve {p['favori_surrep'].nunique()} favoris différents dans les {len(p)} pays, et les pays se "
         "regroupent en ", html.Strong("4 familles : l'Amérique latine (avec l'Espagne et l'Italie), France-Suisse-"
                                       "Autriche, l'Asie du Sud, et le reste du monde"),
         ". Mais ces familles sont peu marquées : au fond, le monde aime à peu près les mêmes Pokémon."],
        html.Div(className="deux-colonnes", children=[
            t.graphe(fig, 440),
            html.Div([
                html.Div(className="controle", children=[
                    html.Label("Ouvre le cadeau d'un pays 🌍", htmlFor="carte-choix"),
                    dcc.Dropdown(id="carte-choix", options=options, value="France", clearable=False),
                ]),
                html.Div(id="carte-fiche", className="fiche"),
            ]),
        ]),
        methode=t.etapes([
            ("On a cherché le favori de chaque pays",
             "Comme TheToyZone : la part d'un Pokémon dans les recherches du pays, divisée par sa part moyenne dans le "
             "monde. Au début, les favoris étaient des Pokémon « fantômes », cherchés dans un seul pays, qui font exploser "
             "ce rapport. Du coup un favori doit être cherché dans au moins la moitié des pays.", "exploration"),
            ("On a retiré le goût commun avant de regrouper",
             "Les pays se ressemblent énormément (Spearman médian de 0,88 entre deux pays). Si on regroupait directement, "
             "on ne verrait que ce fond commun. On retire donc à chaque Pokémon son percentile moyen sur les pays : il "
             "reste « plus ou moins cherché ici qu'ailleurs ». Chaque pays devient un vecteur de près de 1 000 Pokémon.",
             "exploration"),
            ("On a testé k-means et CAH Ward",
             "Les deux méthodes du cours. La CAH fusionne pas à pas les groupes les plus proches ; avec le critère de Ward, "
             "elle vise le même but que le k-means (des groupes compacts), mais on voit sur le dendrogramme comment les "
             "groupes se forment.", "clustering"),
            ("On a choisi k avec la silhouette et le coude",
             [html.P("La silhouette est faible partout (autour de 0,1) et l'inertie n'a pas de coude net. Comme on l'a vu en "
                     "cours, quand les métriques ne tranchent pas, c'est qu'il n'y a pas de groupes très nets, et on choisit "
                     "selon l'usage. Ici k = 4 est quand même le meilleur score pour les deux méthodes."),
              html.Div(className="deux-colonnes", style={"gridTemplateColumns": "1fr 1fr"}, children=[
                  t.mini(f1, 220, "Silhouette selon k."), t.mini(f2, 220, "Inertie du k-means selon k (coude)."),
              ])],
             "clustering"),
            ("On a comparé les deux méthodes et gardé la CAH",
             "Le k-means et la CAH sont d'accord sur l'Amérique latine et sur France-Suisse-Autriche, mais coupent le reste "
             "autrement. On garde la CAH, plus facile à lire. Les groupes sont géographiques alors que le clustering ne "
             "connaît pas la position des pays : c'est rassurant.", "clustering"),
            ("On a dessiné la carte des goûts avec une MDS",
             [html.P(f"Distance entre deux pays = 1 − Spearman entre leurs profils. La MDS place les pays en 2D en essayant "
                     f"de respecter ces distances. Le stress vaut {t.fr(stress)} : la carte déforme pas mal, donc on lit "
                     "surtout le 1er axe, qui va du Japon et de l'Europe d'un côté à l'Amérique latine de l'autre."),
              t.mini(f3, 340, "Les 67 pays sur la carte MDS, colorés par groupe.")],
             "transfo"),
        ], attention="on n'est d'accord avec TheToyZone que pour environ 11 % des pays : ils ont des volumes de recherche "
                     "absolus (outil Ahrefs) et nous seulement du relatif, et certains de leurs favoris (Abra, Natu…) sont "
                     "des noms qu'on a retirés."),
    )


@callback(Output("carte-fiche", "children"), Input("carte-choix", "value"))
def fiche(nom_pays):
    r = _pays().set_index("pays").loc[nom_pays]
    d = nom_vers_dex()
    vois = pd.read_csv(PROCESSED / "methode_08_voisins.csv").set_index("pays")["voisins"].get(nom_pays, "")
    return [
        html.H3(nom_pays),
        html.P(r["groupe_nom"], className="note"),
        html.Div(className="galerie", style={"justifyContent": "center", "marginTop": "8px"}, children=[
            html.Div(className="galerie-item", children=[
                t.image(d[r["favori_surrep"]], 90), html.Div(r["favori_surrep"], className="galerie-nom"),
                html.Div(f"son favori (×{t.fr(r['surrep'], 0)})", className="galerie-legende")]),
            html.Div(className="galerie-item", children=[
                t.image(d[r["plus_cherche"]], 90), html.Div(r["plus_cherche"], className="galerie-nom"),
                html.Div("le plus cherché", className="galerie-legende")]),
        ]),
        html.P(f"Ses 4 voisins pour Moran : {vois.replace(';', ',')}.", className="note"),
    ]


# ---------- 3. Les voisins ----------
def bloc_voisins():
    p = _pays()
    zones = {"HH": ("Noyau Amérique latine et Asie du Sud", t.ROUGE), "LL": ("Noyau Europe et Asie de l'Est", t.GLACE),
             "HL": ("Exception dans son voisinage", t.OR), "LH": ("Exception dans son voisinage", t.OR),
             "non significatif": ("Pas de tendance locale", t.GRIS)}
    p["zone"] = p["lisa_mds1"].map(lambda z: zones[z][0])
    fig = go.Figure()
    for nom, couleur in dict(zones.values()).items():
        s = p[p["zone"] == nom]
        if s.empty:
            continue
        fig.add_trace(go.Choropleth(
            locations=s["iso3"], z=[1] * len(s), name=nom, showscale=False, showlegend=True,
            colorscale=[[0, couleur], [1, couleur]], marker_line_color="#fffaf0", marker_line_width=.6,
            text=s["pays"], hovertemplate="<b>%{text}</b><extra>" + nom + "</extra>",
        ))
    _geo(fig)
    glob = pd.read_csv(PROCESSED / "methode_08_moran_global.csv").set_index("variable")
    mor = pd.read_csv(PROCESSED / "methode_08_moran.csv")

    def diagramme(variable):
        m = mor[mor["variable"] == variable]
        coul = m["lisa"].map(lambda z: zones[z][1])
        f = go.Figure(go.Scatter(x=m["z"], y=m["lag"], mode="markers", marker=dict(size=8, color=coul),
                                 text=m["pays"], hovertemplate="<b>%{text}</b><br>pays %{x:.2f} · voisins %{y:.2f}<extra></extra>"))
        xs = np.linspace(m["z"].min(), m["z"].max(), 2)
        f.add_trace(go.Scatter(x=xs, y=glob.loc[variable, "I"] * xs, mode="lines", line=dict(color=t.ENCRE, dash="dot"),
                               hoverinfo="skip"))
        f.add_hline(y=0, line_color="#d8d0bf")
        f.add_vline(x=0, line_color="#d8d0bf")
        f.update_xaxes(title="valeur du pays (standardisée)")
        f.update_yaxes(title="moyenne de ses 4 voisins")
        return f

    i_mds, p_mds = glob.loc["mds1", "I"], glob.loc["mds1", "p_valeur"]
    i_g1, p_g1 = glob.loc["part_gen1", "I"], glob.loc["part_gen1", "p_valeur"]
    return t.question(
        "Les pays voisins aiment-ils les mêmes Pokémon ?",
        ["Oui, nettement : ", html.Strong(f"l'indice de Moran vaut {t.fr(i_mds)}"),
         ". Deux blocs se détachent : l'Amérique latine (avec l'Asie du Sud) d'un côté, l'Europe et l'Asie de l'Est de "
         "l'autre. Par contre, il n'y a ", html.Strong("pas de « nostalgie régionale »"),
         " : la part des recherches qui vont à la 1re génération ne se ressemble pas entre voisins."],
        t.graphe(fig, 420),
        methode=t.etapes([
            ("On a résumé chaque pays en un nombre",
             "Moran a besoin d'une seule valeur par pays. On en a pris deux : la coordonnée du pays sur le 1er axe de la "
             "MDS (elle résume tout son profil de goûts) et la part de ses recherches qui vont à la génération 1 (pour "
             "tester la nostalgie).", "transfo"),
            ("On a défini les voisins",
             "Beaucoup de nos pays n'ont pas de frontière avec un autre pays gardé (Japon, Australie, Royaume-Uni…). Du "
             "coup on a pris les 4 pays les plus proches (distance entre les centres, contours Natural Earth). Par exemple "
             "France → Belgique, Suisse, Pays-Bas, Royaume-Uni (choisis un pays dans le bloc d'au-dessus pour voir ses voisins).",
             "transfo"),
            ("On a tracé le diagramme de Moran",
             [html.P(f"Chaque point est un pays : sa valeur en x, la moyenne de ses 4 voisins en y (le « lag spatial »). "
                     f"L'indice de Moran, c'est la pente de la droite en pointillé : {t.fr(i_mds)} (p = {t.fr(p_mds, 3)}). "
                     "Les points en haut à droite (HH) et en bas à gauche (LL) sont des pays qui ressemblent à leurs voisins."),
              t.mini(diagramme("mds1"), 300, "Axe MDS 1 : les voisins se ressemblent beaucoup.")],
             "transfo"),
            ("On a localisé avec LISA",
             "Le Moran global dit s'il y a un regroupement, LISA dit où. Chaque pays est classé HH, LL ou exception (HL, LH), "
             "et on ne colore sur la carte que les pays significatifs (test par permutations).", "transfo"),
            ("Et pour la nostalgie ?",
             [html.P(f"Pour la part de la génération 1, la pente est presque plate : I = {t.fr(i_g1)} (p = {t.fr(p_g1)}), "
                     "pas significatif. Dans notre première version on trouvait 0,39, mais c'était un effet des mots : "
                     "Onix (la voiture) gonflait la génération 1 dans toute l'Amérique du Sud. Une fois les mots retirés, "
                     "ça disparaît."),
              t.mini(diagramme("part_gen1"), 260, "Part de la génération 1 : pas de lien entre voisins.")],
             "transfo"),
        ], attention="avec les 4 plus proches voisins, un pays isolé peut avoir des voisins lointains (Mexique → "
                     "États-Unis, Inde → Émirats). Et la MDS déforme les distances, donc on lit le résultat comme deux "
                     "grands blocs, pas pays par pays."),
    )


def layout():
    return html.Div([
        t.entete_page("Le tour du monde de Cadoizo",
                      "Une nuit, 67 pays : quel Pokémon met-on sous le sapin selon l'endroit où on vit ?",
                      "cadoizo"),
        bloc_plus_cherche(),
        bloc_groupes(),
        bloc_voisins(),
    ])
