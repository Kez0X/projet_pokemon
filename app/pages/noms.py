"""Notebook 04 : les noms des Pokémon en japonais, en anglais et en français (symbolique sonore)."""
import unicodedata
from functools import lru_cache

import dash
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html
from plotly.subplots import make_subplots
from scipy.stats import pearsonr, spearmanr

import theme as t
from donnees import PROCESSED, noms, popularite, table_maitre

dash.register_page(__name__, path="/noms", name="Les noms", order=4)

PETITS = set("ャュョァィゥェォヮ")
PETITES_VOYELLES = set("ァィゥェォ")
LANGUES = [("japonais", "ja_mores", "ja_voisees"), ("anglais", "en_syllabes", "en_voisees"),
           ("français", "fr_syllabes", "fr_voisees")]


def _voyelle(kana):
    nom = unicodedata.name(kana, "")
    return nom[-1] if nom.startswith("KATAKANA LETTER") and nom[-1] in "AIUEO" else None


@lru_cache
def _donnees():
    return (noms()
            .merge(table_maitre()[["dex", "nom_fr", "nom_en", "nom_ja", "nom_ja_roma", "poids_kg", "taille_m",
                                   "total_stats", "stade", "stade_categorie", "generation"]], on="dex")
            .merge(popularite()[["dex", "johto_pct_gen", "reddit_pct_gen"]], on="dex"))


@lru_cache
def _resultats(nom):
    """Résultats exportés par le notebook 04 (lignées, popularité, Pokémon of the Year)."""
    return pd.read_csv(PROCESSED / f"methode_04_{nom}.csv")


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
def _pieges():
    """Les noms français où l'orthographe trompe : lettres contre sons (comme la partie 3 du notebook)."""
    d = _donnees().set_index("dex")
    lignes = []
    for dex, piege in [(315, "le s se dit z"), (143, "le x se dit ks"), (4, "le e final est muet"),
                       (122, "« M. » se lit « aime »")]:
        r = d.loc[dex]
        lignes.append(html.Tr([html.Td(r["nom_fr"]), html.Td(html.Code(r["fr_api"])), html.Td(piege)]))
    return html.Table(className="tableau", children=[
        html.Thead(html.Tr([html.Th("nom"), html.Th("transcription espeak-ng"), html.Th("le piège des lettres")])),
        html.Tbody(lignes),
    ])


def bloc_poids():
    d = _donnees()
    d = d.assign(classe=d["ja_voisees"].clip(upper=3))
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

    # montrer : tous les liens, dans les trois langues
    variables = [(v, f"{n} {langue[:2].upper()}") for langue, lon, voi in LANGUES
                 for v, n in [(lon, "longueur"), (voi, "voisées")]]
    cibles = [("taille_m", "taille"), ("poids_kg", "poids"), ("total_stats", "stats")]
    rhos = {c: [spearmanr(d[v], d[c])[0] for v, _ in variables] for c, _ in cibles}
    f2 = go.Figure()
    for (cible, nc), coul in zip(cibles, [t.ROUGE, t.OR, t.GLACE]):
        f2.add_trace(go.Bar(x=[n for _, n in variables], y=rhos[cible], name=nc, marker_color=coul,
                            hovertemplate="%{x} ↔ " + nc + " : rho = %{y:.2f}<extra></extra>"))
    f2.update_layout(barmode="group", showlegend=True)
    f2.update_yaxes(title="rho de Spearman", range=[0, .5])
    rho_en = max(spearmanr(d["en_syllabes"], d[c])[0] for c, _ in cibles)
    rho_fr = max(spearmanr(d[v], d[c])[0] for v in ["fr_syllabes", "fr_voisees"] for c, _ in cibles)

    options = [{"label": f"{r.nom_fr} (n° {r.dex})", "value": r.dex} for r in d.sort_values("nom_fr").itertuples()]
    return t.question(
        "Un nom qui sonne « dur » fait-il un Pokémon plus lourd ?",
        ["En japonais, oui. Un Pokémon sans consonne dure pèse ", html.Strong(f"{med.loc[0]:.0f} kg"),
         f" (médiane), contre {med.loc[2]:.0f} kg avec deux. On retrouve aussi le résultat de Kawahara (2018) : "
         "plus le nom est long, plus le Pokémon est gros et fort. En anglais, ça va dans le même sens en plus faible, "
         "et en français c'est presque invisible."],
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
             "« bouba / kiki »). Kawahara, Noto et Kumagai (2018) l'ont montré sur les noms japonais des Pokémon, Shih et "
             "al. (2019) dans six langues dont l'anglais, mais pas le français. On a voulu retrouver leur résultat en "
             "japonais et en anglais, puis tester le français.", "hors"),
            ("On a découpé chaque nom japonais en mores",
             [html.P("On travaille sur les kana, plus proches de la prononciation que le romaji. Un kana = une more, sauf les "
                     "petits ャ ュ ョ qu'on colle au kana d'avant (キャ = « kya »). Un petit kana voyelle qui répète la "
                     "voyelle d'avant l'allonge, il compte donc à part : Mélo ピィ = « pii » = 2 mores. Une consonne est "
                     "voisée (« dure ») si le kana porte le petit signe ゛ : on le détecte en décomposant chaque caractère "
                     "avec Unicode (ガ = カ + ゛). Pour le Pokémon choisi au-dessus, en rouge les mores voisées :"),
              html.Div(id="noms-decoupe")],
             "exploration"),
            ("En français et en anglais, on a transcrit les noms en sons",
             [html.P("L'orthographe n'est pas la prononciation. On passe donc par espeak-ng, un logiciel libre de synthèse "
                     "vocale qui écrit un mot (même inventé) en alphabet phonétique, avec les règles de la langue. Ensuite "
                     "on compte des sons : les syllabes (une par voyelle prononcée), les consonnes voisées (b, d, g, v, z, "
                     "ʒ…), les sons qui claquent (p, t, k, b, d, g) et les sons doux (m, n, l, r). On a relu à la main "
                     "les cas difficiles et 15 noms tirés au hasard par langue :"),
              _pieges()],
             "hors"),
            ("On a choisi Spearman plutôt que Pearson",
             [html.P(f"Le poids va de 0,1 à 999,9 kg avec quelques géants. Comme on l'a vu en cours, on calcule les deux et "
                     f"on regarde le nuage : ici Pearson vaut {t.fr(rp)} et Spearman {t.fr(rs)}. Pearson est tiré par les "
                     "géants et la relation n'est pas une droite, alors que Spearman travaille sur les rangs et mesure juste "
                     "si ça monte. Du coup on garde Spearman."),
              t.mini(f1, 260, "Chaque point est un Pokémon : la longueur de son nom japonais et son poids.")],
             "exploration"),
            ("On a mesuré tous les liens, dans les trois langues",
             [html.P(f"L'ordre est net : japonais > anglais > français. En anglais, la longueur monte jusqu'à "
                     f"{t.fr(rho_en)} ; en français, aucun rho ne dépasse {t.fr(rho_fr)}. La transcription phonétique ne "
                     "change presque rien par rapport à un codage par lettres : le lien faible du français ne vient donc "
                     "pas de notre codage. Les noms japonais sont les noms d'origine, et les traductions gardent plus ou "
                     "moins leur symbolique."),
              t.mini(f2, 260, "Spearman entre les variables sonores et le gabarit (JP = japonais, EN = anglais, "
                              "FR = français).")],
             "exploration"),
            ("On a regardé la force, pas seulement la p-valeur",
             "Avec 1 025 Pokémon, même un rho de 0,1 devient « significatif ». Comme le conseille le cours, on regarde "
             "aussi l'ampleur dans les vraies unités : c'est pour ça que le graphique du haut est en kilos.", "exploration"),
        ], attention="espeak-ng se trompe parfois sur des noms inventés (Lewsor lu à l'anglaise, Gengar avec un « dj »). "
                     "Sur l'échantillon relu, c'est rare et dans tous les sens : ça ajoute du bruit, sans créer de faux liens."),
    )


@callback(Output("noms-fiche", "children"), Output("noms-decoupe", "children"), Input("noms-choix", "value"))
def fiche(dex):
    r = _donnees().set_index("dex").loc[dex]
    m = mores(r["nom_ja"])
    fiche = [
        t.image(dex, 130),
        html.H3(f"{r['nom_fr']} · {r['nom_en']} · {r['nom_ja']}"),
        html.P(f"« {r['nom_ja_roma']} »"),
        tuiles(r["nom_ja"]),
        html.Div([
            html.Span(f"{len(m)} mores", className="etiquette gris"),
            html.Span(f"{sum(v for _, v in m)} consonne(s) dure(s) en japonais", className="etiquette"),
        ]),
        html.P(["en français ", html.Code(r["fr_api"]), f" : {int(r['fr_syllabes'])} syllabe(s), "
                f"{int(r['fr_voisees'])} voisée(s)"]),
        html.P(["en anglais ", html.Code(r["en_api"]), f" : {int(r['en_syllabes'])} syllabe(s), "
                f"{int(r['en_voisees'])} voisée(s)"]),
        html.P(f"{r['poids_kg']:g} kg · {r['taille_m']:g} m · {int(r['total_stats'])} de stats au total"),
    ]
    decoupe = html.Div([
        html.Div([html.Strong(f"{r['nom_fr']} : "), html.Span(r["nom_ja"])]),
        tuiles(r["nom_ja"]),
        html.P(f"→ {len(m)} mores, dont {sum(v for _, v in m)} voisée(s).", className="note"),
    ], className="mini")
    return fiche, decoupe


# ---------- 2. Dans une même lignée ----------
@lru_cache
def _lignees_chemins():
    """Toutes les lignées, de la forme de base à chaque forme finale (Évoli en donne une par évolution)."""
    paires = _resultats("paires")
    enfants = paires.groupby("pre_evolution")["evolution"].apply(list).to_dict()
    racines = sorted(set(paires["pre_evolution"]) - set(paires["evolution"]))
    chemins = []

    def descendre(chemin):
        suite = enfants.get(chemin[-1], [])
        if not suite:
            chemins.append(tuple(chemin))
        for e in sorted(suite):
            descendre(chemin + [e])

    for r in racines:
        descendre([r])
    return chemins


def bloc_lignees():
    lig = _resultats("lignees").set_index("variable")
    n_paires = len(_resultats("paires"))
    longueurs = [lon for _, lon, _ in LANGUES]
    noms_lang = [langue for langue, _, _ in LANGUES]
    part = lambda v, col: lig.loc[v, col] / lig.loc[v, ["évolution a plus", "égal", "évolution a moins"]].sum()

    fig = go.Figure()
    for col, nom, coul in [("évolution a plus", "nom plus long", t.ROUGE), ("égal", "même longueur", t.GRIS),
                           ("évolution a moins", "nom plus court", t.GLACE)]:
        fig.add_trace(go.Bar(
            y=noms_lang, x=[part(v, col) for v in longueurs], name=nom, orientation="h", marker_color=coul,
            customdata=[lig.loc[v, col] for v in longueurs],
            hovertemplate="%{y} : %{customdata} paires (%{x:.0%})<extra>" + nom + "</extra>"))
    fig.update_layout(barmode="stack", showlegend=True, legend=dict(orientation="h", y=1.14, x=0, traceorder="normal"),
                      margin=dict(r=90))
    for langue, v in zip(noms_lang, longueurs):   # la part de « plus » parmi les paires qui changent (celle du texte)
        fig.add_annotation(x=1, y=langue, xref="x", yref="y", xanchor="left", xshift=6, showarrow=False,
                           text=f"<b>{t.pct(lig.loc[v, 'part de plus (hors égalités)'])} %</b><br>des paires<br>qui changent",
                           font=dict(size=11, color=t.ROUGE), align="left")
    fig.update_xaxes(title=f"Part des {n_paires} paires « pré-évolution → évolution »", tickformat=".0%", range=[0, 1])
    fig.update_yaxes(autorange="reversed")

    # montrer : la part de « plus » hors égalités, pour la longueur et les consonnes voisées
    f1 = go.Figure()
    for i, (nom, coul) in enumerate([("longueur", t.ROUGE), ("consonnes voisées", t.OR)]):
        vs = [LANGUES[k][1 + i] for k in range(3)]
        f1.add_trace(go.Bar(x=noms_lang, y=[lig.loc[v, "part de plus (hors égalités)"] for v in vs], name=nom,
                            marker_color=coul, customdata=[lig.loc[v, "p_valeur"] for v in vs],
                            hovertemplate="%{x} : %{y:.0%} (p = %{customdata:.1e})<extra>" + nom + "</extra>"))
    f1.add_hline(y=.5, line_dash="dot", line_color=t.GRIS_FONCE,
                 annotation_text="50 % = le hasard", annotation_position="top left")
    f1.update_layout(barmode="group", showlegend=True)
    f1.update_yaxes(title="l'évolution a plus (hors égalités)", tickformat=".0%", range=[0, 1])

    tm = table_maitre().set_index("dex")
    options = [{"label": " → ".join(tm.loc[d, "nom_fr"] for d in c), "value": "-".join(map(str, c))}
               for c in _lignees_chemins()]
    pct_ja, pct_en, pct_fr = (lig.loc[v, "part de plus (hors égalités)"] for v in longueurs)
    return t.question(
        "Le nom grandit-il quand le Pokémon évolue ?",
        ["Oui, dans les trois langues. Quand la longueur change, l'évolution a un nom plus long que sa pré-évolution dans ",
         html.Strong(f"{t.pct(pct_ja)} % des cas en japonais"), f", {t.pct(pct_en)} % en anglais et {t.pct(pct_fr)} % en "
         "français. C'est le résultat le plus net sur les noms."],
        html.Div(className="deux-colonnes", children=[
            t.graphe(fig, 300),
            html.Div([
                html.Div(className="controle", children=[
                    html.Label("Suis une lignée 🎄", htmlFor="noms-lignee"),
                    dcc.Dropdown(id="noms-lignee", options=options, value="172-25-26", clearable=False),
                ]),
                html.Div(id="noms-lignee-fiche"),
            ]),
        ]),
        methode=t.etapes([
            ("Les corrélations globales mélangent tout",
             "Plus haut, on compare tous les Pokémon entre eux : des types, des générations et des designs qui n'ont rien "
             "à voir. En français, le lien entre la longueur du nom et le stade n'était que de 0,14, presque invisible.",
             "exploration"),
            ("On compare chaque Pokémon à sa propre pré-évolution",
             f"C'est le test le plus proche de l'idée de Kawahara (« le nom change quand le Pokémon évolue »). Dans une "
             f"paire comme Salamèche → Reptincel, le type, la génération et le design sont presque les mêmes, donc ils ne "
             f"peuvent pas créer un faux lien. Les {n_paires} paires viennent de PokéAPI.", "hors"),
            ("Le test du signe",
             [html.P("Pour chaque paire, on regarde seulement si l'évolution a plus, moins ou autant de syllabes (de mores en "
                     "japonais). Si le nom n'avait rien à voir avec l'évolution, « plus » et « moins » seraient aussi "
                     "fréquents : le test du signe (un test binomial sur les paires qui diffèrent) dit si l'écart peut "
                     "venir du hasard. Ici, toutes les p-valeurs sont sous 0,05, et sous 0,001 pour la longueur."),
              t.mini(f1, 240, "Part des paires où l'évolution a plus de sons que sa pré-évolution, sans compter les "
                              "égalités.")],
             "hors"),
            ("On garde les égalités visibles",
             f"Beaucoup de paires gardent la même longueur ({lig.loc[longueurs, 'égal'].min()} à "
             f"{lig.loc[longueurs, 'égal'].max()} selon la langue) : on les montre en gris dans le graphique du haut, "
             "pour ne pas présenter l'effet comme une règle.", "exploration"),
        ], attention="c'est une tendance, pas une règle : Bulbizarre → Herbizarre → Florizarre garde la même longueur "
                     "dans les trois langues."),
    )


@callback(Output("noms-lignee-fiche", "children"), Input("noms-lignee", "value"))
def fiche_lignee(valeur):
    d = _donnees().set_index("dex")
    dexs = [int(x) for x in valeur.split("-")]
    cartes = []
    for i, dex in enumerate(dexs):
        r = d.loc[dex]
        if i:
            cartes.append(html.Div("→", className="fleche-lignee"))
        cartes.append(html.Div(className="etape-lignee", children=[
            t.image(dex, 64),
            html.Strong(r["nom_fr"]),
            html.Div(f"{r['nom_ja']} · {int(r['ja_mores'])} mores", className="note"),
            html.Div(f"{r['nom_en']} · {int(r['en_syllabes'])} syll.", className="note"),
            html.Div(f"FR · {int(r['fr_syllabes'])} syll.", className="note"),
        ]))
    return html.Div(cartes, className="lignee")


# ---------- 3. Et la popularité ? ----------
NOMS_VAR = {"en_syllabes": "longueur EN", "en_voisees": "voisées EN", "en_voisees_part": "part de voisées EN",
            "en_occlusives_part": "part de sons qui claquent EN", "en_sonantes_part": "part de sons doux EN",
            "ja_mores": "longueur JP", "ja_voisees": "voisées JP", "fr_syllabes": "longueur FR", "fr_voisees": "voisées FR"}


def bloc_popularite():
    poty = _resultats("poty").set_index("variable")
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Longueur du nom (syllabes, mores en japonais)",
                                                        "Consonnes voisées dans le nom"), horizontal_spacing=.12)
    for col, (i, nom) in enumerate([(1, "longueur"), (2, "voisées")], start=1):
        vs = [LANGUES[k][i] for k in range(3)]
        xs = [LANGUES[k][0] for k in range(3)]
        for serie, nom_serie, coul in [("moyenne publiés", "dans le top 30 de leur région", t.ROUGE),
                                       ("moyenne autres", "les autres", t.GRIS)]:
            fig.add_trace(go.Bar(
                x=xs, y=poty.loc[vs, serie], name=nom_serie, marker_color=coul, marker_cornerradius=3,
                showlegend=col == 1, legendgroup=serie,
                customdata=np.c_[poty.loc[vs, "rang_biserial"], poty.loc[vs, "p_holm"]],
                hovertemplate="%{x} : %{y:.2f} en moyenne<br>rang-bisérial = %{customdata[0]:.2f}, "
                              "p corrigé = %{customdata[1]:.2f}<extra>" + nom_serie + "</extra>"), row=1, col=col)
    fig.update_layout(barmode="group", showlegend=True, legend=dict(orientation="h", y=-.12, x=0), margin=dict(t=70))
    biserial_max = poty["rang_biserial"].abs().max()

    # montrer : les 18 corrélations avec Reddit et le Johto Times, après la correction de Holm
    pop = _resultats("popularite").copy()
    pop["etiquette"] = pop["variable"].map(NOMS_VAR)
    f1 = go.Figure()
    for cible, nom, symbole in [("reddit_pct_gen", "Reddit", "circle"), ("johto_pct_gen", "Johto Times", "diamond")]:
        s = pop[pop["cible"] == cible]
        f1.add_trace(go.Scatter(
            y=s["etiquette"], x=s["rho"], mode="markers", name=nom,
            marker=dict(size=11, symbol=symbole, color=[t.ROUGE if x == "oui" else t.GRIS for x in s["significatif"]],
                        line=dict(width=1, color=t.GRIS_FONCE)),
            customdata=s["p_holm"], hovertemplate="%{y} : rho = %{x:.2f} (p corrigé = %{customdata:.3f})<extra>"
                                                  + nom + "</extra>"))
    f1.add_vline(x=0, line_color=t.GRIS_FONCE)
    f1.update_layout(showlegend=True)
    f1.update_xaxes(title="rho de Spearman avec la popularité dans la génération", range=[-.3, .3])
    f1.update_yaxes(autorange="reversed")

    # montrer : la longueur japonaise à stade égal, avec et sans légendaires
    ps = _resultats("par_stade")
    ps = ps[(ps["variable"] == "ja_mores") & (ps["cible"] == "johto_pct_gen")]
    cats = ["stade 1", "stade 2", "stade 3", "sans évolution"]
    f2 = go.Figure()
    for groupe, nom, motif in [("tous", "tous", ""), ("sans légendaires ni fabuleux", "sans légendaires", "/")]:
        s = ps[ps["groupe"] == groupe].set_index("stade").reindex(cats)
        f2.add_trace(go.Bar(
            x=cats, y=s["rho"], name=nom, marker_pattern_shape=motif,
            marker_color=[t.ROUGE if x == "oui" else t.GRIS for x in s["significatif"].fillna("")],
            customdata=np.c_[s["p_holm"], s["n"]],
            hovertemplate="%{x} : rho = %{y:.2f} (p corrigé = %{customdata[0]:.3f}, %{customdata[1]} Pokémon)<extra>"
                          + nom + "</extra>"))
    f2.add_hline(y=0, line_color=t.GRIS_FONCE)
    f2.update_layout(barmode="group", showlegend=True)
    f2.update_yaxes(title="rho (longueur JP ↔ Johto Times)", range=[-.4, .2])
    sl = ps[ps["groupe"] == "sans légendaires ni fabuleux"].set_index("stade")
    rho_min, rho_max = poty["rho dans les 240"].min(), poty["rho dans les 240"].max()

    return t.question(
        "Le son du nom rend-il un Pokémon plus populaire ?",
        ["Non. Au vote Pokémon of the Year 2020 (plus de 6,6 millions de votes), les 240 Pokémon du top 30 de leur "
         "région ont ", html.Strong("des noms aussi longs et aussi « durs » que les autres"),
         ", en japonais, en anglais comme en français. Le son du nom dit la taille du Pokémon, pas s'il sera aimé."],
        t.graphe(fig, 340),
        methode=t.etapes([
            ("D'abord : qui voit quel nom ?",
             "Pour qu'un son joue sur ce qu'on aime, il faut que le votant l'entende. Reddit 2019 et le Johto Times 2025 "
             "sont des publics anglophones : ils votent pour « Charizard », ni pour « Dracaufeu » ni pour « リザードン ». "
             "On teste donc d'abord le nom anglais. Pokémon of the Year est un vote mondial où chacun voit le nom dans sa "
             "langue : on teste les trois. Face à un public anglophone, les noms japonais et français posent une autre "
             "question : un nom qui « annonce » un Pokémon gros ou fort (l'intention des concepteurs) va-t-il avec un "
             "Pokémon plus aimé ?", "hors"),
            ("Une popularité dans la génération",
             "On reprend les percentiles dans la génération du notebook 02. Les noms s'allongent au fil des générations, et "
             "les générations récentes sont moins aimées : avec un classement global, on trouvait un faux lien entre le "
             "nom et la popularité, qui venait en fait de la génération.", "exploration"),
            ("Beaucoup de tests : la correction de Holm",
             [html.P("Sur une trentaine de tests au seuil de 5 %, on s'attend à un ou deux « significatifs » par pur hasard. "
                     "La méthode de Holm rend chaque test plus exigeant, pour garder moins de 5 % de risque de fausse "
                     "alerte sur tout l'ensemble (un peu moins sévère que Bonferroni). Après correction, il ne reste que "
                     "deux liens faibles, au Johto Times seulement : un nom anglais long un peu plus aimé, avec plus de sons "
                     "qui claquent un peu moins. Rien sur Reddit, rien en japonais ni en français."),
              t.mini(f1, 330, "Spearman entre chaque variable sonore et la popularité, en rouge ce qui reste "
                              "significatif après la correction de Holm.")],
             "hors"),
            ("À stade égal, avec et sans légendaires",
             [html.P("Les évolués ont des noms plus longs (voir la question d'avant) et sont plus aimés : un lien peut donc "
                     "passer par le stade. On refait les corrélations dans chaque stade, avec et sans légendaires. Le lien "
                     "« nom anglais long ↔ plus aimé » disparaît : il passait par le stade. Un seul résultat tient : chez "
                     "les stades 1 et les sans évolution, un nom japonais long va avec un Pokémon moins aimé au Johto Times, "
                     f"y compris sans les légendaires (rho = {t.fr(sl.loc['stade 1', 'rho'])} chez les stades 1, "
                     f"{t.fr(sl.loc['sans évolution', 'rho'])} chez les sans évolution, juste à la limite après correction)."),
              html.P("Les votants ne voient pas ce nom japonais, donc ce n'est pas son son qui les influence. Un nom japonais "
                     "long annonce un Pokémon plus gros et plus fort ; en début de lignée, ce sont peut-être les plus "
                     "petits et les plus « mignons » qui sont préférés, et le nom court n'en serait qu'un indice. C'est "
                     "une piste, pas une preuve."),
              t.mini(f2, 240, "Spearman entre la longueur du nom japonais et la popularité au Johto Times, dans chaque "
                              "stade (en rouge : significatif après Holm, hachuré : sans légendaires ni fabuleux).")],
             "exploration"),
            ("Pokémon of the Year, de deux façons",
             f"On ne connaît que le top 30 de chaque région. Parmi les 890 Pokémon votables, on compare donc les 240 "
             f"publiés aux autres avec le test de Mann-Whitney, et on donne la taille de l'effet avec la corrélation "
             f"rang-bisériale (0 = aucune différence, ±1 = tous les publiés au-dessus ou au-dessous des autres) : elle ne "
             f"dépasse jamais {t.fr(biserial_max)}, et rien ne tient après Holm. Puis, à l'intérieur des 240 publiés, le "
             f"classement n'est lié au nom dans aucune langue (rho entre {t.fr(rho_min)} et {t.fr(rho_max)}).", "hors"),
        ], attention="pour Pokémon of the Year, on ne sait pas combien de votants ont vu chaque langue : l'effet d'une "
                     "langue est forcément dilué dans le vote mondial."),
    )


def layout():
    return html.Div([
        t.entete_page("Les noms des Pokémon",
                      "Pokémonastique : est-ce que le son d'un nom dit quelque chose du Pokémon… et de sa popularité ?",
                      "sorbebe"),
        bloc_poids(),
        bloc_lignees(),
        bloc_popularite(),
    ])
