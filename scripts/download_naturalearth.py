"""Contours des pays (Natural Earth, échelle 1:50 m) pour la carte et l'analyse spatiale.

Source : Natural Earth, « Admin 0 – Countries », domaine public.
- https://www.naturalearthdata.com/downloads/50m-cultural-vectors/50m-admin-0-countries-2/
- fichier GeoJSON repris du dépôt officiel : https://github.com/nvkelso/natural-earth-vector

On prend l'échelle 1:50 m plutôt que 1:110 m parce que la 1:110 m n'a pas les petits
pays (Singapour, Hong Kong…) qui sont dans Google Trends.
"""
from pathlib import Path

import requests

URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson"
SORTIE = Path(__file__).resolve().parents[1] / "data" / "raw" / "naturalearth"


def main():
    SORTIE.mkdir(parents=True, exist_ok=True)
    r = requests.get(URL, timeout=120)
    r.raise_for_status()
    chemin = SORTIE / "ne_50m_admin_0_countries.geojson"
    chemin.write_bytes(r.content)
    print(f"écrit : {chemin} ({len(r.content) / 1e6:.1f} Mo)")


if __name__ == "__main__":
    main()
