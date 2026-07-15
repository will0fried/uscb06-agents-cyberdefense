# Agents autonomes de cyberdéfense - code et résultats

Ce dépôt rassemble le code et les données de mon mémoire de Master 2 (CNAM, USCB06). J'y compare trois familles d'agents défensifs - des règles réactives, de l'apprentissage par renforcement (PPO) et un LLM - sur deux environnements de simulation CybORG : CAGE 2, un réseau d'entreprise, et DroneSwarm, un essaim de drones.

L'idée que je défends dans le mémoire : la performance d'un agent tient autant au terrain qu'à l'algorithme. Le même modèle qui domine tout sur CAGE 2 fait à peine mieux que le hasard sur DroneSwarm. Tout le code et tous les CSV qui montrent ça sont ici.

## Organisation

- `01_scripts/` : le code des agents et des campagnes de mesure
- `02_resultats_bruts/` : les résultats bruts en CSV, le modèle RL entraîné, un exemple d'échange avec le LLM
- `03_captures/` : les figures (boxplots, comparaison des deux terrains)
- `journal.md` : mon journal de bord, une ligne par séance de travail
- `versions.md` et `resultats_*.md` : le relevé de l'environnement et les synthèses chiffrées
- les sous-dossiers `archives/` (dans `01_scripts/` et `02_resultats_bruts/`) : les scripts d'exploration et les mesures intermédiaires, gardés pour la transparence mais mis de côté

## Quel script pour quelle stratégie

Les campagnes finales (1 000 parties de 30 tours, graines 1-1000 appariées) tiennent en quatre scripts, et chacun écrit directement les fichiers `*_final.csv` cités dans le mémoire :

- `cage2_campagne.py` : sur CAGE 2, joue le hasard, l'action fixe, la règle réactive (façon AICA) et le RL
- `cage2_llm_1000.py` : sur CAGE 2, le LLM
- `drones_campagne.py` : sur DroneSwarm, les quatre mêmes stratégies
- `serie_llm_nuit.py` : sur DroneSwarm, le LLM

En amont : `cage2_entrainement_rl.py` et `entrainement_rl.py` entraînent les deux modèles PPO ; `cage2_action_fixe.py` et `experience_complete.py` sont les balayages qui ont servi à identifier la meilleure action fixe de chaque terrain (#135 sur CAGE 2, #12 sur DroneSwarm).

## Ce que ça donne

Sur CAGE 2, les stratégies se classent nettement : le RL devant, puis la règle, puis l'action fixe, loin devant le hasard, et le LLM en dernier - plus mauvais que le hasard. Sur DroneSwarm, tout se tasse : les écarts existent encore statistiquement mais restent faibles, et aucune stratégie ne prend vraiment le dessus. Les chiffres exacts et leur interprétation sont dans le mémoire ; les données brutes sont dans `02_resultats_bruts/`.

## Refaire tourner le code

Il faut Python 3, `stable-baselines3`, `numpy`, et les deux environnements CybORG installés à part (CAGE 2 en CybORG 2.1, DroneSwarm en CybORG 3.1, récupérés depuis les dépôts CAGE). Le LLM tourne en local avec Ollama et le modèle `llama3.2:3b`.

Un piège qui m'a coûté du temps : la version de CybORG qui s'exécute dépend du dossier depuis lequel on lance le script, pas du venv. Du coup je lance les scripts CAGE 2 depuis le dossier `cage-challenge-2/CybORG` et ceux de DroneSwarm depuis le dossier CybORG 3.1. Pour vérifier laquelle est chargée :

 python3 -c "import CybORG; print(CybORG.__file__)"

Par exemple :

 python3 01_scripts/cage2_regles.py
 python3 01_scripts/cage2_hasard_et_rl.py

## À noter

C'est un travail universitaire. Toutes les données viennent de simulations CybORG : pas d'infrastructure réelle, pas de données sensibles. Le code est là pour que les résultats du mémoire soient reproductibles.

Wilfried Koussouri - Master 2, CNAM (2025-2026).
