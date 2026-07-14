# Versions de l'environnement - relevé du 9 juillet 2026

Relevé par diagnostic direct sur la machine (aucune valeur écrite de mémoire).
Toute mise à jour ultérieure sera datée et ajoutée en nouveau bloc, sans écraser
l'ancien.

## Machine

- macOS : 26.5.2 (Apple Silicon)
- Python : 3.12.13 (identique dans les deux environnements virtuels)

## Point critique : quelle version de CybORG s'exécute réellement ?

Les deux terrains utilisent des versions différentes de CybORG, mais celle qui
s'exécute ne dépend pas de l'environnement virtuel activé : elle dépend du
répertoire depuis lequel le script est lancé.

Python place le répertoire courant en tête de son chemin de recherche des modules.
Un script lancé depuis `~/cage-challenge-2/CybORG/` importe donc le code local
(CybORG 2.1) et masque le paquet installé dans le venv (CybORG 3.1, installé
en mode éditable depuis `~/CybORG`). C'est le mécanisme dit de *shadowing*.

Conséquence : `pip show CybORG` répond 3.1 dans les deux venv, alors que le
module réellement chargé peut être le 2.1. Vérification à faire avant chaque
campagne :

```bash
python3 -c "import CybORG; print(CybORG.__file__)"
```

Le chemin affiché fait foi, pas `pip show`.

## Terrain A - DroneSwarm (CAGE 3)

- CybORG : 3.1 (`~/CybORG/CybORG/version.txt`)
- Source : `~/CybORG`, dépôt Git au commit `2742b5e` (2024-02-20)
- Scénario : DroneSwarm, mode simulation
- Wrappers : `OpenAIGymWrapper` + `FixedFlatWrapper`
- Agent étudié : `blue_agent_0` (défenseur), 56 actions discrètes
- Observation : vecteur de 11 293 nombres

## Terrain B - CAGE 2 (réseau d'entreprise)

- CybORG : 2.1 (`~/cage-challenge-2/CybORG/CybORG/version.txt`)
- Source : `~/cage-challenge-2`, dépôt Git au commit `26ce1c1` (2024-05-24)
- Scénario : `Scenario2.yaml`, mode simulation, attaquant `B_lineAgent`
- Wrapper : `ChallengeWrapper` (agent `Blue`)
- Observation : 52 bits (13 serveurs × 4 bits) - 145 actions

## Environnements virtuels

| Venv | Chemin | Contenu notable | Usage |
|---|---|---|---|
| `cyborg-env` | `~/cyborg-env` | CybORG 3.1 (éditable), gym 0.23.1, gymnasium 1.3.0 | Premières mesures (hasard, action fixe) - pas de stable-baselines3 |
| `.venv` | `~/CybORG/.venv` | idem + stable_baselines3 2.9.0, torch 2.12.1, ollama 0.6.2 | Tous les runs RL (PPO) et LLM, sur les deux terrains |

Bibliothèques communes : `gym 0.23.1`, `gym-notices 0.1.0`, `gymnasium 1.3.0`.

## Modèle de langage

- Modèle Ollama : `llama3.2:3b` - empreinte `a80c4f17acd5` - 2,0 Go
- Température : 0 pour toutes les séries officielles
- Client Python : `ollama 0.6.2`

## Graines aléatoires

- Campagne v1 (DroneSwarm) : graine fixée à 42
- Campagne v2 (deux terrains, 100 parties appariées) : graines 1 à 100,
 appliquées à `random.seed`, `np.random.seed` et `env.action_space.seed`

## Longueur des épisodes

- Campagne v1 : 25 tours - Campagne v2 : 30 tours
- Écart assumé au protocole officiel de CAGE 3 (500 pas) ; conforme en revanche à
 la pratique de CAGE 1 et 2 (évaluations à 30, 50 et 100 pas).
