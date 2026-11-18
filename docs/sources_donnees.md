# Sources des données et méthode de récupération

Ce document liste les sources du projet et explique comment on a récupéré chaque jeu de données. Les données brutes ne sont pas versionnées (`data/raw/` est dans le `.gitignore`) : pour les obtenir, il suffit de relancer les scripts de `scripts/`.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/download_pokeapi.py           # à lancer en premier : noms et identifiants servent de clé
.venv/bin/python scripts/download_sprites.py           # ~130 Mo d'images
.venv/bin/python scripts/build_starters.py             # écrit data/raw/starters/starters.csv
.venv/bin/python scripts/download_reddit_2019.py
.venv/bin/python scripts/download_thetoyzone.py
.venv/bin/python scripts/download_google_trends.py     # très long (> 1 h), reprend où il s'est arrêté
.venv/bin/python scripts/download_community_days.py
.venv/bin/python scripts/download_sorties.py
.venv/bin/python scripts/download_naturalearth.py
```

Les données ont été récupérées les **16 et 17/11/2026**. Toutes les données sont dans `data/raw/<source>/`. Celles qu'on ne peut pas retélécharger (Johto Times, Pokémon of the Year 2020, starters) sont versionnées ; les autres sont ignorées par Git et se retéléchargent avec les scripts.

---

## 1. Noms et attributs des Pokémon : PokéAPI

- **Source** : PokéAPI, fichiers CSV du dépôt GitHub (base reprise de veekun/pokedex).
  - https://pokeapi.co/about
  - https://github.com/PokeAPI/pokeapi/tree/master/data/v2/csv
- **Comment** : téléchargement direct des CSV bruts (`raw.githubusercontent.com`) avec `scripts/download_pokeapi.py`.
- **Fichiers récupérés** (les tables sont reliées par des identifiants, la jointure se fera dans la préparation) :
  - **noms** : `pokemon_species_names.csv` (nom de chaque espèce dans 12 langues, dont anglais, français, japonais en kana et en romaji, coréen, chinois) et `languages.csv` ;
  - **espèces** : `pokemon_species.csv` (génération, espèce dont elle évolue, chaîne d'évolution, couleur officielle, forme du corps, légendaire, fabuleux, bébé, taux de capture…), avec `generations.csv`, `evolution_chains.csv`, `pokemon_colors.csv`, `pokemon_shapes.csv` ;
  - **Pokémon (formes)** : `pokemon.csv` (taille en décimètres, poids en hectogrammes, forme par défaut ou non), `pokemon_types.csv` + `types.csv`, `pokemon_stats.csv` + `stats.csv` (6 statistiques de base).
- **Contenu** : 1 025 espèces et 1 351 formes (dont 1 025 formes par défaut, une par espèce). Le nom anglais (`local_language_id = 9`) sert de clé pour interroger Google Trends. Les noms français et japonais serviront à l'axe Noms (Pokémonastics). Le stade d'évolution se déduit de `evolves_from_species_id`.
- **Sortie** : `data/raw/pokeapi/`

## 1 bis. Images officielles des Pokémon

- **Source** : dépôt PokeAPI/sprites, dossier `official-artwork` (illustrations officielles de The Pokémon Company), https://github.com/PokeAPI/sprites
- **Comment** : `scripts/download_sprites.py` télécharge `{numéro}.png` pour les 1 025 Pokémon (reprend là où il s'est arrêté).
- **Pourquoi l'artwork officiel** plutôt que les sprites de jeu : le style est le même pour toutes les générations, ce qui rend les couleurs comparables. Fond transparent.
- **Contenu** : 1 025 images PNG, environ 130 Mo. Elles serviront à calculer le nombre de couleurs et la couleur dominante (k-means sur les pixels).
- **Sortie** : `data/raw/sprites/official_artwork/`

## 1 ter. Pokémon de départ (starters)

- **Source** : liste des starters de Bulbapedia, https://bulbapedia.bulbagarden.net/wiki/Starter_Pok%C3%A9mon
- **Comment** : les 27 starters des jeux principaux (3 par génération : Plante, Feu, Eau) sont saisis à la main par leur numéro de Pokédex dans `scripts/build_starters.py`. Leurs évolutions sont retrouvées dans PokéAPI (`evolves_from_species_id`), ce qui vérifie aussi la saisie (le script contrôle la génération de chaque starter).
- **Contenu** : 81 Pokémon (27 lignées × 3 stades), avec le type de starter, le starter de la lignée et le stade. Les partenaires de Pokémon Let's Go (Pikachu, Évoli) ne sont pas inclus.
- **Sortie** : `data/raw/starters/starters.csv` (versionné)

## 2. Sondage Reddit r/pokemon 2019

- **Source** : sondage « Favourite Pokémon » lancé en juin 2019 sur r/pokemon par l'utilisateur u/mamamia1001. L'auteur a publié les résultats et autorisé leur réutilisation (« Please feel free to use this data however you wish »).
  - Fil des résultats : https://www.reddit.com/r/pokemon/comments/c0w4s0/
  - Données reprises et nettoyées par Arturo Moncada-Torres : https://github.com/arturomoncadatorres/favorite-pokemon (dossier `data/`)
  - Couverture presse : [Nintendo Life](https://www.nintendolife.com/news/2019/06/more_than_52000_people_voted_for_their_favourite_pokemon_here_are_the_results), [GameSpot](https://www.gamespot.com/articles/the-most-and-least-popular-pokemon-according-to-a-/1100-6467995/)
- **Comment** : téléchargement direct des fichiers du dépôt GitHub avec `scripts/download_reddit_2019.py`.
- **Fichiers récupérés** :
  - `df_ranked.csv` : 809 Pokémon (générations 1 à 7), avec le nombre de votes, les types, la génération, la famille d'évolution et le rang (global et dans la génération) ;
  - `responses.xlsx` : les 52 836 réponses individuelles, avec l'horodatage et le Pokémon choisi ;
  - `pokemon_stats.csv`, `df_stats.csv` : statistiques de jeu utilisées par le dépôt.
- **Limites** :
  - public de Reddit, surtout anglophone. **Le pays des votants n'est pas connu** ;
  - un seul vote par personne, sans pondération ;
  - les générations 8 et 9 ne sont pas couvertes.
- **Sortie** : `data/raw/reddit_2019/`

## 3. TheToyZone : Pokémon le plus « uniquement populaire » par pays

- **Source** : étude de TheToyZone, « The Most Popular Pokémon Around the World » (mise à jour du 30/01/2024).
  - Article : https://thetoyzone.com/the-most-popular-pokemon-around-the-world
  - Tableau interactif intégré à l'article : https://embed.neomam.com/popular-pokemon-around-the-world/
  - Première version (2021) : https://thetoyzone.com/pokemon-25-anniversary-fan-favorites
- **Leur méthode** : volumes de recherche Google de chacun des 1 016 Pokémon dans chaque pays, mesurés avec l'outil Ahrefs. Le Pokémon « uniquement populaire » d'un pays est celui dont la part dans les recherches du pays dépasse le plus sa part dans les recherches mondiales. **Ce n'est donc pas le Pokémon le plus cherché** (ce serait Pikachu presque partout), mais le plus surreprésenté par rapport au reste du monde.
- **Comment on l'a récupéré** : l'étude ne publie pas de fichier de données. Les données sont écrites en dur dans le JavaScript du tableau interactif. Le script `scripts/download_thetoyzone.py` télécharge la page du tableau, trouve le fichier JavaScript, puis extrait les entrées `{country, generation, pokemon}` avec une expression régulière. Les accents encodés (`\xE9` → é) sont décodés.
- **Contenu** : 853 lignes (pays × génération → Pokémon), 114 pays, générations 1 à 9. Tous les pays n'ont pas les 9 générations.
- **Limites** :
  - il n'y a qu'un Pokémon par pays et par génération, et **pas de favori toutes générations confondues** (celui-ci n'apparaît que sur les cartes en image de l'article) ;
  - les noms recherchés sont probablement les noms anglais : les pays qui cherchent dans une autre langue ou une autre écriture (Japon, Corée…) sont mal mesurés ;
  - la méthode et les volumes bruts ne sont pas publiés, on ne peut pas la reproduire.
- **Sortie** : `data/raw/thetoyzone/favori_par_pays_et_generation.csv`

## 4. Google Trends : intérêt par pays

- **Source** : Google Trends, https://trends.google.com/, interrogé avec la bibliothèque **pytrends** (non officielle, archivée en 2024, mais encore fonctionnelle au 16/11/2026) : https://github.com/GeneralMills/pytrends
- **Comment** (`scripts/download_google_trends.py`) :
  1. Google Trends compare **au plus 5 termes à la fois**, et ses valeurs sont **relatives** : dans chaque pays, les 5 termes se partagent 100 ;
  2. pour pouvoir comparer les lots entre eux, chaque requête contient un même Pokémon de référence (**l'ancre, Gengar**) et 4 autres Pokémon. On obtient 256 lots qui couvrent les 1 025 Pokémon ;
  3. pour chaque lot, on récupère l'intérêt par pays (`interest_by_region`, résolution pays, petits volumes inclus) sur la période du **01/11/2021 au 31/10/2026** (5 années complètes) ;
  4. dans l'analyse, on divisera chaque valeur par celle de Gengar dans le même pays, pour ramener tous les Pokémon sur une même échelle ;
  5. Google limite fortement le nombre de requêtes : le script fait une pause de 12 s entre deux lots, attend plus longtemps en cas de refus, et enregistre chaque lot dans un fichier à part. On peut donc le relancer, il reprend où il s'est arrêté ;
  6. **correction du 17/11** : 4 Pokémon valaient 0 dans tous les pays à cause de leur orthographe PokéAPI, que Google ne reconnaît pas. On cherche à la place : `Farfetch'd` et `Sirfetch'd` (apostrophe droite au lieu de ’), `Mime Jr` et `Mr Rime` (sans point). Les 4 lots concernés (20, 109, 215, 216) ont été refaits le 17/11, les autres datent du 16/11. Dans `interet_par_pays.csv`, la colonne `terme` contient donc le terme recherché, qui diffère du nom PokéAPI pour ces 4 Pokémon.
- **Fichiers** : `lots/lot_XXX.csv` (un fichier par requête), puis `interet_par_pays.csv` (tous les lots : pays, terme, valeur, lot).
- **Limites** :
  - les termes sont les **noms anglais**. Les noms ambigus (Ditto, Onix, Golem…) récupèrent d'autres recherches, et les pays qui cherchent dans une autre écriture (Japon, Corée, Chine…) sont sous-représentés. Les « sujets » Google (identifiants d'entité) régleraient ce problème, mais Google ne les reconnaît pas de façon fiable pour chaque Pokémon ;
  - les valeurs sont entières : un Pokémon peu cherché tombe souvent à 0 dans les petits pays ;
  - les données sont échantillonnées par Google : deux collectes peuvent donner des valeurs un peu différentes.
- **Sortie** : `data/raw/google_trends/`

## 5. Pokémon of the Year 2020 (vote officiel)

- **Source** : vote officiel organisé par The Pokémon Company avec Google, du 5 au 14 février 2020, environ 6,6 millions de votes, ouvert au monde entier.
  - Site officiel des résultats : https://pokemon2020.pokemon.com/en-us/
  - Fichier repris : dépôt `games_night_viz` de Will Sutton, https://github.com/wjsutton/games_night_viz/blob/main/challenges/1_player_select/pokemon_of_the_year_2020.xlsx
  - Présentation : https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_of_the_Year
- **Comment** : fichier Excel téléchargé depuis le dépôt GitHub et ajouté tel quel au dépôt.
- **Contenu** (`data/raw/pokemon_of_the_year_2020/pokemon_of_the_year_2020.xlsx`) :
  - feuille `pokemon_of_the_year_2020` : 270 lignes, soit le top 30 de chacune des 8 régions de jeu (Kanto → Galar) et le top 30 général (`All`), avec les votes et le rang ;
  - feuille `pokemon_stats` : 1 032 Pokémon et formes avec leurs statistiques de jeu, repris du jeu de données Kaggle « All Pokémon dataset » (https://www.kaggle.com/maca11/all-pokemon-dataset).
- **Limites** :
  - seuls les 30 premiers de chaque région sont publiés, donc uniquement des Pokémon déjà populaires ;
  - les régions sont celles des jeux (où le Pokémon apparaît), pas le pays des votants ;
  - Galar (génération 8) n'est pas dans le sondage Reddit 2019 : au plus 210 Pokémon en commun avec Reddit.

## 6. Johto Times / Dragonfly Cave 2025 (résultats préliminaires)

- **Source** : sondage « Favourite Pokémon Poll 2025 » du forum The Cave of Dragonflies (forum anglophone), étape par génération. Votes détaillés extraits de la vidéo de présentation des résultats.
  - Fil du forum : https://forums.dragonflycave.com/threads/johto-times-favourite-pokemon-poll-2025.19145/
  - Vidéo des résultats : https://www.youtube.com/watch?v=QlXgDUBE3d4
- **Comment** : les votes ont été relevés dans la vidéo, surtout par **OCR** (reconnaissance de texte sur les images). On a vérifié que chaque nombre de votes est cohérent avec le pourcentage affiché. Quand l'OCR échouait, la valeur a été lue à l'œil. La colonne `methode` indique la méthode utilisée pour chaque Pokémon :
  - OCR, votes cohérents avec le pourcentage : 1 014 Pokémon ;
  - lecture visuelle (dont texte retourné et animation) : 10 Pokémon ;
  - image officielle du Johto Times et différence avec le total : 1 Pokémon.
- **Contenu** (`data/raw/johto_times_2025/johto_times_2025_preliminaire.csv`) : 1 025 Pokémon, avec le numéro de Pokédex, la génération, le nom anglais et français, les votes, le pourcentage et le rang dans la génération, le total des votes et le nombre de participants de la génération (de 14 478 pour la génération 1 à 9 254 pour la génération 9).
- **Limites** :
  - **les votes sont comparés à l'intérieur d'une génération** : chaque participant vote dans chaque génération. Pour comparer deux Pokémon de générations différentes, il faut utiliser le pourcentage dans la génération, pas les votes bruts ;
  - ce sont des résultats préliminaires (étape par génération), pas le classement final ;
  - public d'un forum anglophone de fans, pays des votants inconnu.

---

## 7. Événements : Community Days de Pokémon GO

- **Source** : Dittobase, https://www.dittobase.com/pokemon-go/community-days (tableau HTML de tous les Community Days depuis janvier 2018).
- **Comment** (`scripts/download_community_days.py`) : on lit chaque ligne du tableau : date, nom de l'événement (texte alternatif de l'image), Pokémon mis en avant (liens vers le Pokédex de Dittobase, parfois plusieurs par événement). Le nom du Pokémon est relié au numéro de Pokédex via les identifiants de PokéAPI ; les formes régionales (`vulpix-alola`, `ponyta-galarian`, `flabebe-red`…) sont ramenées à l'espèce.
- **Contenu** : 129 événements, 159 lignes (une par événement × Pokémon), de janvier 2018 à février 2027. Les événements futurs sont gardés avec `a_venir = True` (leur Pokémon n'est souvent pas encore annoncé).
- **Sortie** : `data/raw/evenements/community_days.csv`

## 8. Événements : sorties des jeux, des films et des saisons de l'anime

- **Sources** : Wikipedia anglais, lu via l'API MediaWiki (`action=parse`, une requête par page) :
  - jeux : https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon_video_games
  - films : https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon_films
  - anime : https://en.wikipedia.org/wiki/Pok%C3%A9mon_(TV_series)
- **Comment** (`scripts/download_sorties.py`) : lecture des tableaux de chaque page avec `pandas.read_html`.
  - **jeux** : pour chaque jeu, la première date de sortie (Japon, ou monde quand la sortie est mondiale) et la rubrique de la page (jeux principaux et remakes, spin-off, Mystery Dungeon…). Les jeux mobiles ne sont décrits qu'en texte dans la page : **Pokémon GO (6 juillet 2016) est ajouté à la main** ;
  - **films** : films de cinéma (animation et Détective Pikachu) et courts-métrages, repérés à part, avec la date de sortie au Japon et en Amérique du Nord. Les téléfilms et épisodes spéciaux sont écartés ;
  - **anime** : début et fin de chaque saison (diffusion au Japon).
- **Contenu** : 106 jeux (dont 24 jeux principaux), 25 films d'animation au cinéma, 1 film live-action, 27 courts-métrages, 29 saisons de l'anime. 4 titres n'ont pas encore de date (sorties à venir : Pokémon Winds and Waves, Pokémon Champions, Pokémon: Wild Card ; et Pokémon Play It!, sans date dans le tableau).
- **Remarque** : contrairement à l'API Pageviews (écartée, voir plus bas), l'API MediaWiki a répondu normalement le 17/11.
- **Sortie** : `data/raw/evenements/sorties.csv`

## 9. Contours des pays : Natural Earth

- **Source** : Natural Earth, couche « Admin 0 – Countries » à l'échelle 1:50 m, domaine public.
  - https://www.naturalearthdata.com/downloads/50m-cultural-vectors/50m-admin-0-countries-2/
  - fichier GeoJSON du dépôt officiel : https://github.com/nvkelso/natural-earth-vector
- **Comment** : téléchargement direct du GeoJSON avec `scripts/download_naturalearth.py`.
- **Pourquoi l'échelle 1:50 m** : l'échelle 1:110 m n'a pas les petits pays (Singapour, Hong Kong…) qui sont dans Google Trends.
- **Contenu** : 242 pays et territoires, avec leurs contours et leurs codes ISO. Certains pays ont `ISO_A3 = -99` (la France, la Norvège…) : dans ce cas, on prend la colonne `ADM0_A3`.
- **Utilisation** : poids spatiaux (k plus proches voisins entre les centres des pays) pour l'indice de Moran et le LISA du notebook 08.
- **Sortie** : `data/raw/naturalearth/ne_50m_admin_0_countries.geojson`

## Source écartée

- **Vues des pages Wikipedia anglaises** (API Pageviews de Wikimedia, https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/reference/page-views.html). L'idée : la plupart des Pokémon ont une redirection à leur nom sur Wikipedia EN, et les vues d'une redirection sont comptées à part, ce qui donne une série mensuelle par Pokémon depuis 2015. On a trouvé un titre valide pour 1 024 Pokémon sur 1 025. Mais l'API a refusé nos requêtes en continu (erreurs 429, « trop de requêtes ») et la collecte n'a pas abouti après plus de 4 h. **On a écarté cette source le 17/11/2026.**

## Travaux scientifiques et état de l'art

- Le Vaillant, J. (2020). *What's your favourite Pokémon? Pocket monster popularity reflects interest in real-world Biology*. Journal of Geek Studies, 7(1), 35–52. https://jgeekstudies.org/wp-content/uploads/2020/06/le-vaillant_2020_pokefaves.pdf
- Kawahara, S., Noto, A., & Kumagai, G. (2018). *Sound symbolic patterns in Pokémon names*. Phonetica, 75(3). https://pmc.ncbi.nlm.nih.gov/articles/PMC6159826
- Shih, S. S., Ackerman, J., Hermalin, N., Inkelas, S., Jang, H., Johnson, J., Kavitskaya, D., Kawahara, S., Oh, M., Starr, R. L., & Yu, A. (2019). *Cross-linguistic and language-specific sound symbolism: Pokémonastics*. https://websites.umass.edu/phonolist/2019/10/08/shih-ackerman-hermalin-inkelas-jang-johnson-kavitskaya-kawahara-oh-starr-yu-2019-cross-linguistic-and-language-specific-sound-symbolism-pokemonastics
- Moncada-Torres, A. *Visualization of the favorite Pokémon survey results* (notebook). https://nbviewer.org/github/arturomoncadatorres/favorite-pokemon/blob/master/README.md
