"""Récupère les données de l'étude TheToyZone (2024) : Pokémon le plus « uniquement
populaire » par pays et par génération.

Méthode de TheToyZone : volumes de recherche Google (outil Ahrefs) de chaque Pokémon
par pays ; le favori d'un pays est celui dont la part locale des recherches dépasse le
plus sa part mondiale. Ce n'est donc PAS le Pokémon le plus cherché du pays.

Les données ne sont pas publiées en CSV : elles sont écrites en dur dans le
JavaScript du tableau interactif intégré à l'article (embed.neomam.com).
"""
import re
from pathlib import Path

import pandas as pd
import requests

PAGE = "https://embed.neomam.com/popular-pokemon-around-the-world/"
UA = {"User-Agent": "Mozilla/5.0"}
SORTIE = Path(__file__).resolve().parents[1] / "data" / "raw" / "thetoyzone"
MOTIF = re.compile(r'\{country:"([^"]+)",generation:(\d+),pokemon:"([^"]+)"\}')


def main():
    SORTIE.mkdir(parents=True, exist_ok=True)
    html = requests.get(PAGE, headers=UA, timeout=60).text
    js_url = re.search(r'src="([^"]+/assets/index\.[^"]+\.js)"', html).group(1)
    js = requests.get(requests.compat.urljoin(PAGE, js_url), headers=UA, timeout=60)
    js.raise_for_status()
    texte = js.content.decode("utf-8")
    # le bundle échappe les accents (\xE9 pour é)
    texte = re.sub(r"\\x([0-9A-Fa-f]{2})", lambda m: chr(int(m.group(1), 16)), texte)
    lignes = [{"pays": p, "generation": int(g), "pokemon": n} for p, g, n in MOTIF.findall(texte)]
    df = pd.DataFrame(lignes).drop_duplicates().sort_values(["pays", "generation"])
    df.to_csv(SORTIE / "favori_par_pays_et_generation.csv", index=False)
    print(f"{len(df)} lignes, {df.pays.nunique()} pays, générations {sorted(df.generation.unique())}")


if __name__ == "__main__":
    main()
