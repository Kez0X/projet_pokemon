"""Refait, pour un seul Pokémon, les étapes du notebook 03 (k-means sur les pixels),
pour pouvoir les montrer dans le dashboard. Mêmes réglages que le notebook."""
from functools import lru_cache

import numpy as np
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import silhouette_score
from scipy import ndimage

from donnees import image_rgba

SEUIL_ALPHA = 128
N_PIXELS = 3000
SEED = 0
K = 8
FUSION_DELTA_E = 25
L_CONTOUR = 15          # pixel très sombre
RAYON_OUVERTURE = 3     # ouverture morphologique : les traits plus fins disparaissent
L_FRANGE = 30           # bord adouci du trait
SEUIL_IMPORTANTE = 0.05


def masques(dex):
    """Comme le notebook 03 : le contour (trait fin + bord adouci) et le noir « plein » (gardé)."""
    arr = np.asarray(image_rgba(dex))
    vis = arr[..., 3] >= SEUIL_ALPHA
    L = rgb_vers_lab(arr[..., :3])[..., 0]
    sombre = vis & (L < L_CONTOUR)
    st = ndimage.iterate_structure(ndimage.generate_binary_structure(2, 1), RAYON_OUVERTURE)
    plein = ndimage.binary_opening(sombre, structure=st)
    trait = sombre & ~plein
    trait = trait | (ndimage.binary_dilation(trait) & vis & (L < L_FRANGE) & ~plein)
    return arr, vis, trait, plein


def pixels(dex):
    """Les pixels visibles sans le contour, 3 000 tirés au hasard (même tirage que le notebook 03)."""
    arr, vis, trait, _ = masques(dex)
    X = arr[..., :3][vis & ~trait].astype(float)
    if len(X) > N_PIXELS:
        X = X[np.random.default_rng([SEED, dex]).choice(len(X), N_PIXELS, replace=False)]
    return X


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
    # 0) le contour, enlevé de l'image avant le k-means
    arr, vis, trait, plein = masques(dex)
    image = np.full(vis.shape + (3,), 255, np.uint8)
    image[vis] = (225, 225, 225)
    image[trait] = (230, 90, 90)
    image[plein] = (0, 0, 0)
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
    final = [(hexa(c), p) for c, p in fus]
    return {
        "image": image[::2, ::2], "part_contour": float(trait.sum() / vis.sum()), "part_noir": float(plein.sum() / vis.sum()),
        "pixels": X, "ks": ks, "inerties": inerties, "silhouettes": silhouettes,
        "brut": brut, "fusion": final, "final": final,
        "importantes": sum(p >= SEUIL_IMPORTANTE for _, p in final),
    }
