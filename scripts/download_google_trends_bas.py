"""Deuxième collecte Google Trends : le bas du classement, avec une ancre faible.

Dans la première collecte (download_google_trends.py), Gengar prend ~89 % de chaque lot :
les Pokémon peu cherchés tombent à 0 ou à 1-2 points. Ici (voir la partie 10 du notebook 02) :
- chaque lot = Chuchmur (Whismur, ~0,023 × Gengar) + 4 Pokémon du bas ;
- la liste des Pokémon vient de data/processed/trends_a_recollecter.csv (notebook 02) ;
- 3 lots de liaison pour revenir à l'échelle de Gengar :
  Gengar + Goupix (Vulpix), Goupix + Chuchmur, et Gengar + Chuchmur (contrôle).
Les lots de liaison sont collectés en premier, dans la même collecte que les autres,
parce que Google Trends travaille sur un échantillon qui change d'un jour à l'autre.
"""
import pandas as pd
from pytrends.request import TrendReq

from download_google_trends import ANCRE, RACINE, TERMES_CORRIGES, collecter

SORTIE = RACINE / "data" / "raw" / "google_trends_bas"
LOTS = SORTIE / "lots"
ANCRE_FAIBLE = "Whismur"   # Chuchmur
ANCRE_INTER = "Vulpix"     # Goupix


def main():
    liste = pd.read_csv(RACINE / "data" / "processed" / "trends_a_recollecter.csv")
    termes = [TERMES_CORRIGES.get(n, n) for n in liste.nom_en if n != ANCRE_FAIBLE]
    lots = {
        "liaison_gengar_goupix": [ANCRE, ANCRE_INTER],
        "liaison_goupix_chuchmur": [ANCRE_INTER, ANCRE_FAIBLE],
        "controle_gengar_chuchmur": [ANCRE, ANCRE_FAIBLE],
    }
    lots.update({f"{i:03d}": [ANCRE_FAIBLE] + termes[k:k + 4]
                 for i, k in enumerate(range(0, len(termes), 4))})
    print(f"{len(termes)} Pokémon, {len(lots)} lots (dont 3 de liaison)", flush=True)
    collecter(lots, LOTS, TrendReq(hl="en-US", tz=0))

    tout = pd.concat(pd.read_csv(f) for f in sorted(LOTS.glob("lot_*.csv")))
    tout.to_csv(SORTIE / "interet_par_pays.csv", index=False)
    print(f"{len(tout)} lignes → interet_par_pays.csv")


if __name__ == "__main__":
    main()
