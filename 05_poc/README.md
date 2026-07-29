# Preuve de concept : agent AICA en LangGraph

Code de la preuve de concept du chapitre 4.5. Un agent de cyberdefense autonome inspire de
l'architecture de reference AICA (groupe OTAN IST-152), implemente comme un graphe LangGraph
de cinq noeuds (sensing, perception, world_model, decision, action), avec un modele de langage
local (Ollama) au seul etage de decision. Ces cinq noeuds couvrent trois des cinq fonctions
AICA de reference : identification de l'etat du monde, planification et selection d'action,
execution de l'action. Les deux autres - collaboration entre agents et apprentissage - ne sont
pas implementees, et le chapitre 4.5 le dit. Cible : un coeur de reseau 5G Open5GS deploye sur
Kubernetes. Donnees simulees.

## Organisation

- `src/aica_agent/` : le code de l'agent
  - `graph.py` : assemblage du graphe AICA
  - `nodes.py` : les cinq noeuds du graphe (sensing, perception, world_model, decision, action)
  - `tools.py` : les cinq outils (observation et action), en mock
  - `scenarios.py` : les cinq scenarios d'incident et le bareme de notation mecanique
  - `stub_llm.py` : un faux LLM deterministe (pour la reproductibilite et les tests)
  - `config.py`, `state.py` : configuration et etat partage
- `scripts/`
  - `demo.py` : lance l'agent une fois sur le scenario historique
  - `run_evaluation.py` : le harnais d'evaluation (5 scenarios, notation, double analyse)
  - `health_check.py` : test de sante de l'appel d'outils, hors harnais
  - `inspect_run.py` : affiche tout ce que l'agent dit et fait sur un scenario
- `tests/` : tests unitaires et d'integration

## Reproduire l'evaluation

Pre-requis : Python 3, Ollama avec un modele local, et les dependances de `requirements.txt`
(versions figees dans `requirements-lock.txt`).

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# table de bareme (fixee a priori)
cd src && python -m aica_agent.scenarios && cd ..

# test de sante de l'appel d'outils
OLLAMA_MODEL=llama3.2:3b python scripts/health_check.py

# evaluation complete : les 5 scenarios de base + la variante 4b ajoutee par --v2,
# soit 6 configurations x 30 executions = 180 lignes de resultats
LLM_PROVIDER=ollama OLLAMA_MODEL=llama3.2:3b python scripts/run_evaluation.py --runs 30 --v2

# meme protocole avec le modele 8B, pour comparer deux tailles de modele
LLM_PROVIDER=ollama OLLAMA_MODEL=llama3.1:8b python scripts/run_evaluation.py --runs 30 --v2

# la regle reactive (deterministe)
python scripts/run_evaluation.py --regle --runs 30 --v2
```

Les resultats produits (CSV, table de bareme, transcripts) sont dans `../04_poc_evaluation/`.
