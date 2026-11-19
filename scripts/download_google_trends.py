"""Intérêt Google Trends par pays pour chaque Pokémon (via pytrends, non officiel).

Google Trends ne compare que 5 termes à la fois, et ses valeurs sont relatives :
dans chaque pays, les 5 termes se partagent 100. Pour rendre les lots comparables,
chaque lot contient un même Pokémon « ancre » + 4 autres Pokémon. On pourra ensuite
diviser chaque valeur par celle de l'ancre dans le même pays.

Limites (à garder en tête pour l'analyse) :
- les termes sont les noms anglais : les noms ambigus (Ditto, Onix, Golem…) captent
  d'autres recherches, et les pays qui cherchent dans une autre écriture (Japon,
  Corée, Chine…) sont sous-représentés ;
- valeurs entières : les Pokémon rares tombent souvent à 0 dans les petits pays ;
- Google limite fortement le nombre de requêtes : le script fait des pauses et
  reprend là où il s'est arrêté (un fichier par lot dans data/raw/google_trends/lots/).
"""
import time
from pathlib import Path

import pandas as pd
from pytrends.request import TrendReq

RACINE = Path(__file__).resolve().parents[1]
SORTIE = RACINE / "data" / "raw" / "google_trends"
LOTS = SORTIE / "lots"
ANCRE = "Gengar"
PERIODE = "2021-11-01 2026-10-31"  # 5 années complètes
PAUSE = 12  # secondes entre deux requêtes
# Orthographes de PokéAPI que Google ne reconnaît pas (0 partout) → terme recherché
TERMES_CORRIGES = {
    "Farfetch’d": "Farfetch'd",  # apostrophe typographique → droite
    "Sirfetch’d": "Sirfetch'd",
    "Mime Jr.": "Mime Jr",  # point final
    "Mr. Rime": "Mr Rime",
}


def noms_anglais():
    noms = pd.read_csv(RACINE / "data" / "raw" / "pokeapi" / "pokemon_species_names.csv")
    en = noms[noms.local_language_id == 9].sort_values("pokemon_species_id").name
    return [TERMES_CORRIGES.get(n, n) for n in en]


def collecter(lots, dossier, trends):
    """Collecte chaque lot (liste de termes) dans dossier/lot_<nom>.csv, en reprenant là où on s'est arrêté.
    lots : dict {nom du lot: liste de termes}."""
    dossier.mkdir(parents=True, exist_ok=True)
    for k, (nom, termes) in enumerate(lots.items()):
        fichier = dossier / f"lot_{nom}.csv"
        if fichier.exists():
            continue
        for essai in range(6):
            try:
                trends.build_payload(termes, timeframe=PERIODE)
                df = trends.interest_by_region(resolution="COUNTRY", inc_low_vol=True)
                break
            except Exception as e:  # 429 (TooManyRequestsError) le plus souvent
                attente = 60 * 2 ** essai
                print(f"lot {nom} : {type(e).__name__}, pause de {attente} s", flush=True)
                time.sleep(attente)
        else:
            raise SystemExit(f"lot {nom} : abandon après 6 essais, relancer plus tard")
        long = (df.reset_index().melt(id_vars="geoName", var_name="terme", value_name="valeur")
                  .rename(columns={"geoName": "pays"}))
        long["lot"] = nom
        long.to_csv(fichier, index=False)
        print(f"lot {k + 1}/{len(lots)} ok ({nom})", flush=True)
        time.sleep(PAUSE)


def main():
    autres = [n for n in noms_anglais() if n != ANCRE]
    lots = {f"{i:03d}": [ANCRE] + autres[k:k + 4] for i, k in enumerate(range(0, len(autres), 4))}
    collecter(lots, LOTS, TrendReq(hl="en-US", tz=0))

    tout = pd.concat(pd.read_csv(f) for f in sorted(LOTS.glob("lot_*.csv")))
    tout.to_csv(SORTIE / "interet_par_pays.csv", index=False)
    print(f"{len(tout)} lignes → interet_par_pays.csv")


if __name__ == "__main__":
    main()
