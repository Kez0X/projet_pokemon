"""Refait, pour un seul Pokémon, les étapes du notebook 03 (k-means sur les pixels),
pour pouvoir les montrer dans le dashboard. Mêmes réglages que le notebook."""
from functools import lru_cache

import numpy as np
from PIL import Image
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import silhouette_score

from donnees import SPRITES

SEUIL_ALPHA = 128
N_PIXELS = 3000
SEED = 0
K = 8
FUSION_DELTA_E = 25
L_CONTOUR = 15
PART_CONTOUR = 0.15
SEUIL_IMPORTANTE = 0.05


def pixels(dex):
    arr = np.asarray(Image.open(SPRITES / f"{dex}.png").convert("RGBA")).reshape(-1, 4)
    vis = arr[arr[:, 3] >= SEUIL_ALPHA, :3]
    rng = np.random.default_rng(SEED)
    if len(vis) > N_PIXELS:
        vis = vis[rng.choice(len(vis), N_PIXELS, replace=False)]
    return vis.astype(float)


def rgb_vers_lab(rgb):
    c = np.asarray(rgb, dtype=float) / 255
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], axis=-1)


def hexa(c):
    return "#{:02x}{:02x}{:02x}".format(*np.clip(np.round(c), 0, 255).astype(int))


@lru_cache(maxsize=64)
def demo(dex):
    X = pixels(dex)
    # 1) coude et silhouette pour k = 2 à 12 (silhouette sur 1 000 pixels pour aller plus vite)
    sous = X[np.random.default_rng(SEED).choice(len(X), min(1000, len(X)), replace=False)]
    ks, inerties, silhouettes = list(range(2, 13)), [], []
    for k in ks:
        km = KMeans(n_clusters=k, n_init=3, random_state=SEED).fit(X)
        inerties.append(km.inertia_)
        silhouettes.append(silhouette_score(sous, km.predict(sous)))
    # 2) k-means avec k = 8
    km = KMeans(n_clusters=K, n_init=3, random_state=SEED).fit(X)
    centres, parts = km.cluster_centers_, np.bincount(km.labels_, minlength=K) / len(X)
    brut = sorted(zip(map(hexa, centres), parts), key=lambda x: -x[1])
    # 3) fusion des nuances (CAH, lien moyen, dans l'espace Lab)
    groupes = AgglomerativeClustering(n_clusters=None, distance_threshold=FUSION_DELTA_E,
                                      linkage="average").fit_predict(rgb_vers_lab(centres))
    fus = []
    for g in np.unique(groupes):
        m = groupes == g
        fus.append(((centres[m] * parts[m, None]).sum(0) / parts[m].sum(), parts[m].sum()))
    fus.sort(key=lambda x: -x[1])
    # 4) contour : la couleur la plus sombre, si L* < 15 et part <= 15 %
    L = rgb_vers_lab(np.array([c for c, _ in fus]))[:, 0]
    i = int(np.argmin(L))
    contour = bool(L[i] < L_CONTOUR and fus[i][1] <= PART_CONTOUR)
    sans = [f for j, f in enumerate(fus) if not (contour and j == i)]
    total = sum(p for _, p in sans)
    sans = [(c, p / total) for c, p in sans]
    return {
        "pixels": X, "ks": ks, "inerties": inerties, "silhouettes": silhouettes,
        "brut": brut,
        "fusion": [(hexa(c), p) for c, p in fus],
        "contour": contour, "contour_L": float(L[i]), "contour_part": float(fus[i][1]),
        "final": [(hexa(c), p) for c, p in sans],
        "importantes": sum(p >= SEUIL_IMPORTANTE for _, p in sans),
    }
