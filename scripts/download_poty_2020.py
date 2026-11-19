"""Récupère les résultats publiés de Pokémon of the Year 2020 sur le site officiel.

Le site officiel (pokemon2020.pokemon.com) ne publie que le top 30 général et le top 30
de chacune des 8 régions de jeu. Ces résultats ne sont pas proposés en fichier : ils sont
écrits en dur dans le JavaScript du site (`bundle.js`), dans un objet de la forme
`{All: [[n° Pokédex, région, nom EN, nom JA, votes, nom EN, nom EN, nom FR, nom DE], ...], Kanto: [...], ...}`.

On s'en sert pour avoir le numéro de Pokédex (absent du fichier Excel repris de Will
Sutton) et pour vérifier les votes de ce fichier.

Le dossier de sortie est versionné : si le site disparaît, on ne pourra plus le retélécharger.
"""
import json
import re
from pathlib import Path

import pandas as pd
import requests

JS = "https://pokemon2020.pokemon.com/assets/javascript/bundle.js"
UA = {"User-Agent": "Mozilla/5.0"}
SORTIE = Path(__file__).resolve().parents[1] / "data" / "raw" / "pokemon_of_the_year_2020"


def extraire_objet(texte, debut):
    """Renvoie le texte de l'objet {...} qui commence à `debut` (accolades équilibrées)."""
    profondeur = 0
    for i in range(debut, len(texte)):
        if texte[i] == "{":
            profondeur += 1
        elif texte[i] == "}":
            profondeur -= 1
            if profondeur == 0:
                return texte[debut:i + 1]
    raise ValueError("objet non fermé")


def main():
    SORTIE.mkdir(parents=True, exist_ok=True)
    r = requests.get(JS, headers=UA, timeout=60)
    r.raise_for_status()
    texte = r.content.decode("utf-8")
    objet = extraire_objet(texte, texte.index("{All:"))
    # les clés ne sont pas entre guillemets en JavaScript : on les ajoute pour lire en JSON
    listes = json.loads(re.sub(r"([{,])([A-Za-z]+):", r'\1"\2":', objet))

    lignes = []
    for liste, entrees in listes.items():
        for rang, e in enumerate(entrees, start=1):
            lignes.append({
                "liste": liste, "rang": rang, "dex": int(e[0]), "region_site": e[1],
                "nom_en": e[2], "nom_ja": e[3], "nom_fr": e[7], "nom_de": e[8], "votes": int(e[4]),
            })
    df = pd.DataFrame(lignes)
    df.to_csv(SORTIE / "poty_2020_officiel.csv", index=False)
    print(f"{len(df)} lignes, {df.liste.nunique()} listes, {df.dex.nunique()} Pokémon différents")


if __name__ == "__main__":
    main()
