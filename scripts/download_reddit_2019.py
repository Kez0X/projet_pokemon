"""Télécharge les données du sondage Reddit r/pokemon 2019 (u/mamamia1001).

Source : dépôt GitHub d'arturomoncadatorres/favorite-pokemon, qui reprend les
données publiées par l'auteur du sondage (libres d'usage).
"""
from pathlib import Path

import requests

BASE = "https://raw.githubusercontent.com/arturomoncadatorres/favorite-pokemon/master/data/"
FICHIERS = ["df_ranked.csv", "responses.xlsx", "pokemon_stats.csv", "df_stats.csv"]
SORTIE = Path(__file__).resolve().parents[1] / "data" / "raw" / "reddit_2019"


def main():
    SORTIE.mkdir(parents=True, exist_ok=True)
    for nom in FICHIERS:
        r = requests.get(BASE + nom, timeout=60)
        r.raise_for_status()
        (SORTIE / nom).write_bytes(r.content)
        print(f"{nom} : {len(r.content) / 1024:.0f} Ko")


if __name__ == "__main__":
    main()
