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

Sur CAGE 2 : `cage2_regles.py` pour la règle réactive (façon AICA), `cage2_hasard_et_rl.py` pour le hasard et le RL, `cage2_action_fixe.py` pour le balayage des actions fixes, `cage2_llm_nuit.py` pour le LLM. Sur DroneSwarm : `entrainement_rl.py` et `eval_rl_v2.py` pour le RL, `experience_complete.py` pour les actions fixes, `serie_llm_nuit.py` pour le LLM. Les résultats finaux, sur 1 000 parties, sont les fichiers dont le nom finit par `_final.csv`.

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
