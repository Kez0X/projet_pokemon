"""Dates de sortie des jeux, des films et des saisons de l'anime Pokémon (Wikipedia EN).

Sources (pages lues via l'API MediaWiki, action=parse) :
- jeux   : https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon_video_games
- films  : https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon_films
- anime  : https://en.wikipedia.org/wiki/Pok%C3%A9mon_(TV_series)

Pour les jeux, on garde la première date de sortie (Japon ou monde) et la rubrique
de la page (jeux principaux, spin-off, mobile…). Pour les films : films de cinéma
(animés et Détective Pikachu), date de sortie au Japon et en Amérique du Nord.
Pour l'anime : début et fin de chaque saison (diffusion au Japon).
Les jeux mobiles sont décrits en texte, sans tableau : Pokémon GO (6 juillet 2016)
est ajouté à la main. Les courts-métrages sont gardés mais repérés à part.
"""
import io
import re
from pathlib import Path

import pandas as pd
import requests

API = "https://en.wikipedia.org/w/api.php"
UA = {"User-Agent": "pokemon-popularity-student-project/0.1 (cours DAD, M2)"}
SORTIE = Path(__file__).resolve().parents[1] / "data" / "raw" / "evenements"
DATE = r"([A-Z][a-z]+ \d{1,2}, \d{4})"


def html_page(titre):
    r = requests.get(API, headers=UA, timeout=60, params={
        "action": "parse", "page": titre, "prop": "text", "format": "json", "formatversion": 2})
    r.raise_for_status()
    return r.json()["parse"]["text"]


def date(texte):
    m = re.search(DATE, str(texte).replace("\xa0", " "))
    return pd.to_datetime(m.group(1), format="%B %d, %Y") if m else pd.NaT


def jeux():
    h = html_page("List_of_Pokémon_video_games")
    # on découpe la page par titre de section pour savoir dans quelle rubrique est chaque tableau
    morceaux = re.split(r'<h[23][^>]*>(.*?)</h[23]>', h)
    lignes = []
    for titre, contenu in zip(morceaux[1::2], morceaux[2::2]):
        rubrique = re.sub("<[^>]+>", "", titre).strip()
        if "<table" not in contenu:
            continue
        for t in pd.read_html(io.StringIO(contenu)):
            if "Game" not in t.columns:
                continue
            for cellule in t.Game.dropna().unique():
                nom = re.split(r" Original release dates?:?", cellule)[0].strip()
                jp = re.search(r"(?:JP|WW): " + DATE, cellule)
                lignes.append({"type": "jeu", "rubrique": rubrique, "titre": nom,
                               "date": pd.to_datetime(jp.group(1), format="%B %d, %Y") if jp else date(cellule)})
    return pd.DataFrame(lignes)


def films():
    tables = pd.read_html(io.StringIO(html_page("List_of_Pokémon_films")))
    lignes, grands = [], 0
    for t in tables:
        if "English title" not in t.columns or "Japanese release date" not in t.columns:
            continue
        if "No." not in t.columns:  # téléfilms / épisodes spéciaux : écartés
            continue
        # une ligne sur deux est le résumé du film (toutes les cellules identiques)
        t = t[t["English title"] != t["Japanese title"]]
        if len(t) <= 3:
            rubrique = "cinéma (live-action)"
        else:  # dans la page : d'abord les films de cinéma, puis les courts-métrages
            rubrique = "cinéma (animation)" if grands == 0 else "court-métrage"
            grands += 1
        for _, r in t.iterrows():
            lignes.append({"type": "film", "rubrique": rubrique,
                           "titre": r["English title"], "date": date(r["Japanese release date"]),
                           "date_amerique_nord": date(r["North American release date"])})
    return pd.DataFrame(lignes)


def anime():
    tables = pd.read_html(io.StringIO(html_page("Pokémon_(TV_series)")))
    t = next(t for t in tables if any("Season name" in str(c) for c in t.columns))
    t.columns = ["saison", "titre", "episodes", "episodes_2", "debut", "fin"]
    return pd.DataFrame({"type": "anime", "rubrique": "saison", "titre": t.titre,
                         "date": t.debut.map(date), "date_fin": t.fin.map(date)})


def main():
    SORTIE.mkdir(parents=True, exist_ok=True)
    # Pokémon GO n'est décrit qu'en texte dans la page (pas de tableau) : saisi à la main
    go = pd.DataFrame([{"type": "jeu", "rubrique": "Mobile games", "titre": "Pokémon Go",
                        "date": pd.Timestamp("2016-07-06")}])
    df = pd.concat([jeux(), go, films(), anime()], ignore_index=True)
    df = df.drop_duplicates(["type", "titre"]).sort_values("date")
    df.to_csv(SORTIE / "sorties.csv", index=False)
    print(df.groupby(["type", "rubrique"]).size().to_string())
    print("sans date :", df.date.isna().sum())


if __name__ == "__main__":
    main()
