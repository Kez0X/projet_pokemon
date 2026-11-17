"""Liste des Community Days de Pokémon GO (2018 → aujourd'hui) depuis Dittobase.

Source : https://www.dittobase.com/pokemon-go/community-days (tableau HTML).
Pour chaque événement : date, nom, Pokémon mis en avant (liens vers le Pokédex de
Dittobase, un événement peut en avoir plusieurs) et attaque(s) spéciale(s).
Le slug Dittobase est relié au numéro de Pokédex via les identifiants de PokéAPI
(les formes régionales « alolan-xxx », « galarian-xxx »… sont ramenées à l'espèce).
Les événements futurs sont gardés, avec a_venir = True.
"""
import html
import re
from pathlib import Path

import pandas as pd
import requests

URL = "https://www.dittobase.com/pokemon-go/community-days"
RACINE = Path(__file__).resolve().parents[1]
SORTIE = RACINE / "data" / "raw" / "evenements"
PREFIXES_REGION = ("alolan-", "galarian-", "hisuian-", "paldean-")


def vers_dex(slug, dex):
    """Slug Dittobase → n° de Pokédex. Les formes (« vulpix-alola », « flabebe-red »,
    « alolan-vulpix »…) sont ramenées à l'espèce en retirant préfixe ou suffixe."""
    if slug is None:
        return None
    for p in PREFIXES_REGION:
        if slug.startswith(p):
            slug = slug[len(p):]
    while slug not in dex and "-" in slug:
        slug = slug.rsplit("-", 1)[0]
    return dex.get(slug)


def main():
    SORTIE.mkdir(parents=True, exist_ok=True)
    page = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
    page.raise_for_status()
    esp = pd.read_csv(RACINE / "data/raw/pokeapi/pokemon_species.csv")
    dex = dict(zip(esp.identifier, esp.id))

    lignes = []
    for tr in re.findall(r"<tr.*?</tr>", page.text, re.S)[1:]:
        tds = re.findall(r"<td.*?</td>", tr, re.S)
        date = html.unescape(re.sub("<[^>]+>", " ", tds[1])).strip()
        titre = re.search(r'href="/pokemon-go/events/[^"]+"><img[^>]*alt="([^"]*)"', tr)
        evenement = html.unescape(titre.group(1)) if titre else ""
        slugs = list(dict.fromkeys(re.findall(r'href="/pokemon-go/pokedex/([^"]+)"', tr)))
        for slug in slugs or [None]:
            lignes.append({"date": pd.to_datetime(date, format="%b %d, %Y"),
                           "evenement": evenement, "pokemon_slug": slug,
                           "dex": vers_dex(slug, dex)})
    df = pd.DataFrame(lignes)
    df["dex"] = df.dex.astype("Int64")
    df["a_venir"] = df.date > pd.Timestamp.today()
    df.sort_values("date").to_csv(SORTIE / "community_days.csv", index=False)
    print(f"{df.evenement.nunique()} événements, {len(df)} lignes, "
          f"slugs sans n° de Pokédex : {sorted(df[df.dex.isna() & df.pokemon_slug.notna()].pokemon_slug.unique())}")


if __name__ == "__main__":
    main()
