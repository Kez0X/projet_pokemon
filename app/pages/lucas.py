"""Pages préparées par Lucas : pour l'instant des cadeaux encore emballés."""
import dash

import theme as t

dash.register_page(
    "classement", path="/classement", name="Classement", order=1,
    layout=lambda: t.cadeau_ferme(
        "Le classement", "Lucas",
        ["Qui est aimé, qui ne l'est pas ? (distributions, top et flop)",
         "Les sondages sont-ils d'accord entre eux ? (Reddit, Pokémon of the Year 2020, Johto Times)",
         "Les effets attendus : génération, stade d'évolution, starter, légendaire, type"],
        "cerfrousse"),
)

dash.register_page(
    "biologie", path="/biologie", name="Biologie", order=5,
    layout=lambda: t.cadeau_ferme(
        "Biologie", "Lucas (notebook) et Luka (page)",
        ["Le Feu est-il rouge ? (types × couleurs)",
         "Les petits Pokémon « mignons » sont-ils plus aimés ?",
         "Une typologie des Pokémon (k-means, GMM, DBSCAN, CAH) et la popularité de chaque groupe"],
        "obalie"),
)

dash.register_page(
    "temps", path="/temps", name="Dans le temps", order=8,
    layout=lambda: t.cadeau_ferme(
        "Dans le temps", "Lucas",
        ["La popularité monte-t-elle à la sortie d'un jeu, d'un film ou d'un Community Day ?",
         "Attention : les vues Wikipedia ont été écartées le 17/11, il faut choisir une autre série."],
        "stalgamin"),
)
