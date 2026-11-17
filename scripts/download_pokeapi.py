"""Télécharge les tables de PokéAPI utiles au projet (CSV du dépôt GitHub).

- noms des espèces dans toutes les langues (clé pour Google Trends, axe Noms) ;
- attributs : taille, poids, types, stats, génération, couleur, forme,
  légendaire / fabuleux / bébé, évolutions.

Les CSV de PokéAPI sont « normalisés » : une table par notion, reliées par des
identifiants (species_id, type_id…). La jointure se fera dans la préparation.
"""
from pathlib import Path

import requests

BASE = "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/"
FICHIERS = [
    # noms
    "pokemon_species_names.csv", "languages.csv",
    # espèces : génération, couleur, forme, légendaire, évolutions…
    "pokemon_species.csv", "generations.csv", "evolution_chains.csv",
    "pokemon_colors.csv", "pokemon_shapes.csv",
    # Pokémon (formes) : taille, poids, types, stats
    "pokemon.csv", "pokemon_types.csv", "types.csv", "pokemon_stats.csv", "stats.csv",
]
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
