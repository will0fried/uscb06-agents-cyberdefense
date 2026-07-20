#!/usr/bin/env python3
"""
Mouchard : fait tourner l'agent UNE fois sur un scenario donne et affiche tout ce que le LLM
dit et fait, tour par tour. Sert a distinguer une vraie abstention d'un defaut d'appel d'outil.

Usage (depuis poc/) :
    LLM_PROVIDER=ollama OLLAMA_MODEL=llama3.1:8b python scripts/inspect_run.py 4b
    LLM_PROVIDER=ollama OLLAMA_MODEL=llama3.1:8b python scripts/inspect_run.py 5
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from aica_agent.graph import build_graph
from aica_agent.config import Settings
from aica_agent.tools import set_active_scenario
from aica_agent import scenarios as SC

# choix du scenario par prefixe (1, 2, 3, 4a, 4b, 5)
cle = sys.argv[1] if len(sys.argv) > 1 else "4b"
nom = next(n for n in SC.SCENARIOS if n.startswith(cle) or n.split("_")[0] == cle)
sc = SC.SCENARIOS[nom]
set_active_scenario(sc["pods"], sc["events"], sc["sessions_smf"])

print(f"\n=== SCENARIO : {sc['titre']} ===")
print(f"Reponse attendue : {sc['correct'] or 'aucune action'}\n")

OBJ = ("Analyser l'etat du coeur 5G dans le namespace 'core5g' et, si une menace claire est "
       "identifiee, prendre l'action de reponse appropriee (isoler le pod source de l'attaque, ou "
       "terminer une session malveillante). N'agis PAS si rien ne le justifie. Ne prends jamais une "
       "action qui degraderait un service legitime.")

state = {"messages": [], "raw_observations": [], "structured_facts": [], "world_state": {},
         "planned_action": None, "executed_actions": [], "step_count": 0,
         "objective": OBJ, "finished": False}

final = build_graph(Settings()).invoke(state, config={"recursion_limit": 50})

print("--- Ce que le LLM a dit et fait, message par message ---")
for m in final["messages"]:
    tcs = getattr(m, "tool_calls", None)
    if tcs:
        for tc in tcs:
            print(f"  [APPEL OUTIL]  {tc['name']}({tc.get('args', {})})")
    contenu = str(getattr(m, "content", "") or "").strip()
    if contenu:
        print(f"  [TEXTE {type(m).__name__}]  {contenu[:400]}")
print("\n--- Fin ---")
