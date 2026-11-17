"""Télécharge les images officielles (« official artwork ») des 1 025 Pokémon.

Source : dépôt PokeAPI/sprites (images reprises de The Pokémon Company).
On prend l'artwork officiel plutôt que les sprites de jeu : le style est le même
pour toutes les générations, ce qui rend les couleurs comparables. Fond transparent.
Reprend là où il s'est arrêté (les fichiers déjà présents sont sautés).
"""
import time
from pathlib import Path

import requests

URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{id}.png"
SORTIE = Path(__file__).resolve().parents[1] / "data" / "raw" / "sprites" / "official_artwork"
N = 1025


def main():
    SORTIE.mkdir(parents=True, exist_ok=True)
    manquants = []
    for i in range(1, N + 1):
        f = SORTIE / f"{i}.png"
        if f.exists():
            continue
        r = requests.get(URL.format(id=i), timeout=60)
        if r.status_code != 200:
            manquants.append(i)
            continue
        f.write_bytes(r.content)
        if i % 100 == 0:
            print(f"{i}/{N}", flush=True)
        time.sleep(0.05)
    print(f"terminé, manquants : {manquants}")


if __name__ == "__main__":
    main()
