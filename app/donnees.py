"""Chargement des résultats des notebooks (data/processed/).

L'app ne lit que les petits fichiers exportés par les notebooks 01 à 08,
jamais les données brutes (sauf les images officielles, servies telles quelles).
"""
from functools import lru_cache
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
PROCESSED = RACINE / "data" / "processed"
SPRITES = RACINE / "data" / "raw" / "sprites" / "official_artwork"


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
    """URL de l'image officielle d'un Pokémon (servie par app.py)."""
    return f"/sprite/{int(dex)}.png"
