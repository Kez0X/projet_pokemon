"""Chargement des résultats des notebooks pour le dashboard.

L'app ne lit que les petits fichiers exportés par les notebooks 01 à 08, copiés dans app/data/
par scripts/exporter_dashboard.py (app/data/ est versionné, pour pouvoir déployer l'app sur Vercel).
Les images officielles sont chargées depuis le dépôt GitHub de PokéAPI (comme scripts/download_sprites.py).
"""
import io
import urllib.request
from functools import lru_cache
from pathlib import Path

import pandas as pd
from PIL import Image

ICI = Path(__file__).resolve().parent
PROCESSED = ICI / "data"
SPRITES_LOCAUX = ICI.parent / "data" / "raw" / "sprites" / "official_artwork"
URL_SPRITE = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{dex}.png"


def _lire(nom):
    return pd.read_csv(PROCESSED / nom)


@lru_cache
def table_maitre():
    return _lire("table_maitre.csv")


@lru_cache
def popularite():
    return _lire("popularite_sources.csv")


@lru_cache
def sur_sous_cotes():
    return _lire("sur_sous_cotes.csv")


@lru_cache
def couleurs():
    return _lire("couleurs_sprites.csv")


@lru_cache
def noms():
    return _lire("noms_variables.csv")


@lru_cache
def pca():
    return _lire("pca_conception.csv")


@lru_cache
def reseau_noeuds():
    return _lire("reseau_noeuds.csv")


@lru_cache
def reseau_aretes():
    return _lire("reseau_aretes.csv")


@lru_cache
def pays():
    return _lire("pays_profils.csv")


@lru_cache
def nom_vers_dex():
    """Nom français -> numéro de Pokédex (les favoris par pays sont en français)."""
    t = table_maitre()
    return dict(zip(t["nom_fr"], t["dex"]))


@lru_cache
def dex_vers_nom():
    t = table_maitre()
    return dict(zip(t["dex"], t["nom_fr"]))


def sprite(dex):
    """URL de l'image officielle d'un Pokémon."""
    return URL_SPRITE.format(dex=int(dex))


@lru_cache(maxsize=128)
def image_rgba(dex):
    """L'image d'un Pokémon pour la démo du k-means : le fichier local s'il existe, sinon on la télécharge."""
    local = SPRITES_LOCAUX / f"{int(dex)}.png"
    if local.exists():
        return Image.open(local).convert("RGBA")
    with urllib.request.urlopen(URL_SPRITE.format(dex=int(dex)), timeout=20) as r:
        return Image.open(io.BytesIO(r.read())).convert("RGBA")
