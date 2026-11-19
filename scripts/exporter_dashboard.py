"""Copie dans app/data/ les fichiers de data/processed/ dont le dashboard a besoin.

À relancer après avoir réexécuté les notebooks. app/data/ est versionné (contrairement à
data/processed/), pour que l'app déployée sur Vercel ait toutes les analyses.
"""
import shutil
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
SOURCE = RACINE / "data" / "processed"
CIBLE = RACINE / "app" / "data"

FICHIERS = [
    "table_maitre.csv", "popularite_sources.csv", "sur_sous_cotes.csv", "couleurs_sprites.csv",
    "noms_variables.csv", "pca_conception.csv", "reseau_noeuds.csv", "reseau_aretes.csv",
    "pays_profils.csv", "trends_ratio_gengar_pays.csv",
]


def main():
    CIBLE.mkdir(parents=True, exist_ok=True)
    a_copier = FICHIERS + sorted(p.name for p in SOURCE.glob("methode_*.csv"))
    manquants = [f for f in a_copier if not (SOURCE / f).exists()]
    if manquants:
        raise SystemExit(f"Fichiers absents de data/processed (relancer les notebooks) : {manquants}")
    for f in a_copier:
        shutil.copy2(SOURCE / f, CIBLE / f)
    taille = sum((CIBLE / f).stat().st_size for f in a_copier) / 1e6
    print(f"{len(a_copier)} fichiers copiés dans {CIBLE} ({taille:.1f} Mo)")


if __name__ == "__main__":
    main()
