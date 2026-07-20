# Agents autonomes de cyberdéfense - code et résultats

Ce dépôt rassemble le code et les données de mon mémoire de Master 2 (CNAM, USCB06). J'y compare trois familles d'agents défensifs - des règles réactives, de l'apprentissage par renforcement (PPO) et un LLM - sur deux environnements de simulation CybORG : CAGE 2, un réseau d'entreprise, et DroneSwarm, un essaim de drones.

L'idée que je défends dans le mémoire : la performance d'un agent tient autant au terrain qu'à l'algorithme. Le même modèle qui domine tout sur CAGE 2 fait à peine mieux que le hasard sur DroneSwarm. Tout le code et tous les CSV qui montrent ça sont ici.

## Organisation

- `01_scripts/` : le code des agents et des campagnes de mesure
- `02_resultats_bruts/` : les résultats bruts en CSV, le modèle RL entraîné, un exemple d'échange avec le LLM
- `03_captures/` : les figures (boxplots, comparaison des deux terrains)
- `04_poc_evaluation/` : le barème, les CSV et les transcripts de l'évaluation du PoC (chapitre 4.5)
- `05_poc/` : le code de la preuve de concept (agent AICA en LangGraph et harnais d'évaluation)
- `journal.md` : mon journal de bord, une ligne par séance de travail
- `versions.md` et `resultats_*.md` : le relevé de l'environnement et les synthèses chiffrées
- les sous-dossiers `archives/` (dans `01_scripts/` et `02_resultats_bruts/`) : les scripts d'exploration et les mesures intermédiaires, gardés pour la transparence mais mis de côté

## Quel script pour quelle stratégie

Les campagnes finales (1 000 parties de 30 tours, graines 1-1000 appariées) tiennent en quatre scripts, et chacun écrit directement les fichiers `*_final.csv` cités dans le mémoire :

- `cage2_campagne.py` : sur CAGE 2, joue le hasard, l'action fixe, la règle réactive (façon AICA) et le RL
- `cage2_llm_1000.py` : sur CAGE 2, le LLM
- `drones_campagne.py` : sur DroneSwarm, les quatre mêmes stratégies
- `serie_llm_nuit.py` : sur DroneSwarm, le LLM

En amont : `cage2_entrainement_rl.py` et `entrainement_rl.py` entraînent les deux modèles PPO ; `cage2_action_fixe.py` et `experience_complete.py` sont les balayages qui ont servi à choisir l'action fixe de chaque terrain. Sur CAGE 2, #135 (Restore Enterprise2) est bien la meilleure : calibration sur les graines 1-50 (-57,29) puis test sur les graines neuves 51-100 (-57,43), les deux mesures concordent. Sur DroneSwarm, #12 n'est pas « la meilleure » et je ne le prétends pas : c'est la deuxième du balayage, retenue après l'effondrement de la première (#13, -115,5 au balayage, -157,3 sur échantillon neuf). Elle s'est effondrée aussi (-126,2 au balayage, -194,38 à mille parties) - c'est d'ailleurs un des artefacts que je raconte au chapitre 5. Sur ce terrain aucune action fixe ne se distingue, donc #12 vaut comme témoin, pas comme championne.

## Expériences complémentaires et contrôles

Au-delà des quatre campagnes principales, plusieurs scripts produisent des résultats cités dans le mémoire, chacun écrivant les CSV correspondants :

- `cage2_llm_145.py` : sur CAGE 2, le LLM avec le menu complet des 145 actions (au lieu du menu restreint) - produit `cage2_llm_145_final.csv` (-176,06).
- `cage2_campagne_meander.py` et `cage2_llm_meander.py` : les mêmes stratégies face à l'attaquant `Meander` au lieu de `B_line` - produisent les `cage2_*_meander.csv`.
- `entrainement_rl_normalise.py` : contrôle de représentation. Réentraîne le PPO de DroneSwarm avec une observation normalisée (VecNormalize), tout le reste égal par ailleurs (même réseau, même budget de 300 000 pas, même graine), puis l'évalue au même protocole apparié - produit `drones_rl_norm_final.csv` (-194,11, indistinguable du PPO brut : le plafond n'est pas un artefact d'échelle). Le script entraîne puis évalue en une seule exécution ; le modèle normalisé n'est pas versionné, il suffit de relancer le script depuis le dossier CybORG 3.1.
- `controle3_rl_graines_duree.py` : contrôle de robustesse du PPO (graines et durée d'épisode) - produit les `controle3_*.csv`. Les contrôles `controle4_politique_constante.py` et `controle5_observation_vivante.py` vérifient respectivement que la politique apprise n'est pas constante et que l'observation évolue bien au fil de la partie.
- `analyse_profondeur.py` : recalcule, à partir des CSV bruts, la décomposition de variance (stratégie vs graine) et les queues de distribution citées au chapitre 4.

## Ce que ça donne

Sur CAGE 2, les stratégies se classent nettement : le RL devant, puis la règle, puis l'action fixe, loin devant le hasard, et le LLM en dernier - plus mauvais que le hasard. Sur DroneSwarm, tout se tasse : les écarts existent encore statistiquement mais restent faibles, et aucune stratégie ne prend vraiment le dessus. Les chiffres exacts et leur interprétation sont dans le mémoire ; les données brutes sont dans `02_resultats_bruts/`.

## Refaire tourner le code

Il faut Python 3, `stable-baselines3`, `numpy`, et les deux environnements CybORG installés à part (CAGE 2 en CybORG 2.1, DroneSwarm en CybORG 3.1, récupérés depuis les dépôts CAGE). Le LLM tourne en local avec Ollama et le modèle `llama3.2:3b`.

Un piège qui m'a coûté du temps : la version de CybORG qui s'exécute dépend du dossier depuis lequel on lance le script, pas du venv. Du coup je lance les scripts CAGE 2 depuis le dossier `cage-challenge-2/CybORG` et ceux de DroneSwarm depuis le dossier CybORG 3.1. Pour vérifier laquelle est chargée :

 python3 -c "import CybORG; print(CybORG.__file__)"

Pour rejouer une campagne complète de bout en bout, copiez le script dans le dossier CybORG correspondant et lancez-le. Les quatre stratégies de CAGE 2 (hasard, action fixe, règle, RL), 1 000 parties de 30 tours :

 cp 01_scripts/cage2_campagne.py ~/cage-challenge-2/CybORG/
 cd ~/cage-challenge-2/CybORG
 caffeinate -i python cage2_campagne.py

Il vous faut `ppo_cage2.zip` dans le même dossier (il est dans `02_resultats_bruts/`), sinon relancez d'abord `cage2_entrainement_rl.py`. Le script écrit les quatre CSV `cage2_*_final.csv` cités dans le mémoire, et affiche en en-tête la version de CybORG chargée : c'est le garde-fou contre le piège ci-dessus. Même principe pour DroneSwarm avec `drones_campagne.py` depuis le dossier CybORG 3.1.

## À noter

C'est un travail universitaire. Toutes les données viennent de simulations CybORG : pas d'infrastructure réelle, pas de données sensibles. Le code est là pour que les résultats du mémoire soient reproductibles.

Wilfried Koussouri - Master 2, CNAM (2025-2026).
