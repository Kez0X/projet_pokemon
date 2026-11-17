"""Télécharge les noms des espèces depuis les CSV de PokéAPI (toutes langues).

Ces noms servent de clé pour les autres sources (Wikipedia, Google Trends…).
"""
from pathlib import Path

import requests

BASE = "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/"
FICHIERS = ["pokemon_species_names.csv", "languages.csv"]
SORTIE = Path(__file__).resolve().parents[1] / "data" / "raw" / "pokeapi"


def main():
    SORTIE.mkdir(parents=True, exist_ok=True)
    for nom in FICHIERS:
        r = requests.get(BASE + nom, timeout=60)
        r.raise_for_status()
        (SORTIE / nom).write_bytes(r.content)
        print(f"{nom} : {len(r.content) / 1024:.0f} Ko")


if __name__ == "__main__":
    main()
