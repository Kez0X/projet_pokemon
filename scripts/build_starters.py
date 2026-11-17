"""Construit la liste des Pokémon de départ (starters) et de leurs évolutions.

Source : liste des starters de Bulbapedia,
https://bulbapedia.bulbagarden.net/wiki/Starter_Pok%C3%A9mon
Les 27 starters des jeux principaux (3 par génération, types Plante / Feu / Eau)
sont saisis à la main (numéros de Pokédex). Leurs évolutions sont retrouvées dans
PokéAPI (evolves_from_species_id), ce qui sert aussi de vérification.
Les partenaires de Pokémon Let's Go (Pikachu, Évoli) ne sont pas inclus.
"""
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
STARTERS = {  # génération : (Plante, Feu, Eau)
    1: (1, 4, 7), 2: (152, 155, 158), 3: (252, 255, 258),
    4: (387, 390, 393), 5: (495, 498, 501), 6: (650, 653, 656),
    7: (722, 725, 728), 8: (810, 813, 816), 9: (906, 909, 912),
}


def main():
    esp = pd.read_csv(RACINE / "data/raw/pokeapi/pokemon_species.csv").set_index("id")
    noms = pd.read_csv(RACINE / "data/raw/pokeapi/pokemon_species_names.csv")
    en = noms[noms.local_language_id == 9].set_index("pokemon_species_id").name
    fr = noms[noms.local_language_id == 5].set_index("pokemon_species_id").name
    enfants = esp.reset_index().groupby("evolves_from_species_id").id.apply(list)

    lignes = []
    for gen, trio in STARTERS.items():
        for type_, base in zip(("Plante", "Feu", "Eau"), trio):
            assert esp.loc[base, "generation_id"] == gen, base
            stade, courants = 1, [base]
            while courants:
                for d in courants:
                    lignes.append({"dex": d, "nom_en": en[d], "nom_fr": fr[d], "generation": gen,
                                   "type_starter": type_, "dex_starter": base, "stade": stade})
                courants = [e for d in courants for e in enfants.get(d, [])]
                stade += 1
    df = pd.DataFrame(lignes)
    sortie = RACINE / "data/raw/starters"
    sortie.mkdir(parents=True, exist_ok=True)
    df.to_csv(sortie / "starters.csv", index=False)
    print(f"{len(df)} Pokémon ({df.dex_starter.nunique()} lignées), stades : {df.stade.value_counts().to_dict()}")


if __name__ == "__main__":
    main()
