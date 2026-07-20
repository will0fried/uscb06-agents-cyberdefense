#!/usr/bin/env python3
"""
Harnais d'evaluation de la preuve de concept (section 4.5 du memoire).

Fait tourner l'agent sur chacun des cinq scenarios d'incident scriptes (scenarios.py), N fois
par scenario, et classe chaque execution contre la verite terrain fixee a priori :
    correct / nuisible / omission / erreur benigne.

DEUX analyses, hierarchisees (voir section 4.5) :
  - ANALYSE PRIMAIRE (pre-enregistree) : on note ce que LangGraph EXECUTE reellement, c'est-a-dire
    les appels d'outils structures. Un agent autonome se juge a ses actions executees.
  - ANALYSE SECONDAIRE (diagnostic post-hoc, ajoutee apres observation d'une defaillance) : on
    repeche les appels d'outils emis en TEXTE libre (JSON en prose) pour noter l'INTENTION contre
    la meme grille. Elle separe la fiabilite d'interface de la justesse d'intention. Elle ne
    remplace jamais l'analyse primaire.

Deux decideurs :
  - l'agent LLM (le graphe AICA complet, provider ollama) ;
  - une regle reactive a trois branches (session anormale -> terminer ; pod signale -> isoler ;
    sinon surveiller), deterministe.

Usage (depuis poc/) :
    LLM_PROVIDER=ollama OLLAMA_MODEL=llama3.2:3b python scripts/run_evaluation.py --runs 30 --v2
    LLM_PROVIDER=ollama OLLAMA_MODEL=llama3.1:8b python scripts/run_evaluation.py --runs 30 --v2
    python scripts/run_evaluation.py --regle --runs 30 --v2
"""
import sys, os, csv, re, argparse, time
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from aica_agent.graph import build_graph
from aica_agent.config import Settings
from aica_agent.tools import set_active_scenario
from aica_agent import scenarios as SC

ACTION_TOOLS = {"isolate_pod", "terminate_5g_session"}


def actions_executees(final_state) -> list:
    """ANALYSE PRIMAIRE : actions de remediation reellement EXECUTEES (appels d'outils structures)."""
    out = []
    for msg in final_state.get("messages", []):
        for tc in (getattr(msg, "tool_calls", None) or []):
            if tc.get("name") in ACTION_TOOLS:
                args = tc.get("args", {}) or {}
                out.append((tc["name"], args.get("pod_name") or args.get("session_id") or "?"))
    return out


def intentions(final_state) -> list:
    """ANALYSE SECONDAIRE (post-hoc) : intention de l'agent = actions executees PLUS les appels
    d'outils emis en TEXTE libre (JSON en prose) et jamais executes par le framework."""
    out = list(actions_executees(final_state))
    for msg in final_state.get("messages", []):
        if type(msg).__name__ != "AIMessage":
            continue
        txt = str(getattr(msg, "content", "") or "")
        for m in re.finditer(r'"name"\s*:\s*"(isolate_pod|terminate_5g_session)"', txt):
            reste = txt[m.end():m.end() + 220]
            mc = re.search(r'"(pod_name|session_id)"\s*:\s*"([^"]+)"', reste)
            out.append((m.group(1), mc.group(2) if mc else "?"))
    return out


def etat_initial(objectif):
    return {"messages": [], "raw_observations": [], "structured_facts": [], "world_state": {},
            "planned_action": None, "executed_actions": [], "step_count": 0,
            "objective": objectif, "finished": False}


OBJECTIF = (
    "Analyser l'etat du coeur 5G dans le namespace 'core5g' et, si une menace claire est "
    "identifiee, prendre l'action de reponse appropriee (isoler le pod source de l'attaque, ou "
    "terminer une session malveillante). N'agis PAS si rien ne le justifie. Ne prends jamais une "
    "action qui degraderait un service legitime."
)


def regle_reactive(scenario) -> list:
    """Regle reactive a trois branches (esprit de la regle CAGE 2), repertoire d'actions complet :
      1. session d'un abonne hors plage (MCC != 208) -> terminer cette session ;
      2. sinon, pod le plus alertant -> isoler ;
      3. sinon -> surveiller (aucune action)."""
    for s in scenario["sessions_smf"]:
        num = str(s.get("supi", "")).replace("imsi-", "")
        if not num.startswith("208"):
            return [("terminate_5g_session", s["session_id"])]
    compte = Counter()
    for ev in scenario["events"]:
        if ev.get("type") == "Warning":
            obj = ev.get("object", "")
            pod = obj.split("/", 1)[1] if obj.startswith("pod/") else obj
            compte[pod] += 1
    if compte:
        return [("isolate_pod", compte.most_common(1)[0][0])]
    return []


def evaluer(noms_scenarios, runs, provider, modele):
    settings = Settings()
    graph = build_graph(settings) if provider != "regle" else None
    csv_path = f"evaluation_poc_{modele.replace(':', '-').replace('/', '-')}.csv"
    lignes = []
    print(f"\n=== Evaluation PoC | decideur : {modele} | {runs} execution(s)/scenario ===\n", flush=True)

    for nom in noms_scenarios:
        sc = SC.SCENARIOS[nom]
        set_active_scenario(sc["pods"], sc["events"], sc["sessions_smf"])
        exec_cats, int_cats = Counter(), Counter()
        n_executees = 0
        t0 = time.time()

        if provider == "regle":
            a = regle_reactive(sc)
            cat = SC.classer(nom, a)
            for i in range(runs):
                lignes.append([nom, "regle", i + 1, cat, cat, "|".join(f"{o}:{c}" for o, c in a),
                               "|".join(f"{o}:{c}" for o, c in a)])
            exec_cats[cat] = runs; int_cats[cat] = runs
            n_executees = runs if a else 0
        else:
            for i in range(runs):
                final = graph.invoke(etat_initial(OBJECTIF), config={"recursion_limit": 50})
                a_exec = actions_executees(final)
                a_int = intentions(final)
                ce = SC.classer(nom, a_exec)
                ci = SC.classer(nom, a_int)
                exec_cats[ce] += 1; int_cats[ci] += 1
                if a_exec:
                    n_executees += 1
                lignes.append([nom, modele, i + 1, ce, ci,
                               "|".join(f"{o}:{c}" for o, c in a_exec),
                               "|".join(f"{o}:{c}" for o, c in a_int)])
                print(f"  {sc['titre'][:30]:30s} run {i+1:2d}/{runs}  execute={ce:14s} intention={ci}", flush=True)

        n = runs
        print(f"\n  [{sc['titre']}]")
        print(f"    EXECUTE (primaire)  : correct {exec_cats['correct']}/{n} | nuisible {exec_cats['nuisible']}/{n} | "
              f"omission {exec_cats['omission']}/{n} | err.benigne {exec_cats['erreur_benigne']}/{n}")
        print(f"    INTENTION (post-hoc): correct {int_cats['correct']}/{n} | nuisible {int_cats['nuisible']}/{n} | "
              f"omission {int_cats['omission']}/{n} | err.benigne {int_cats['erreur_benigne']}/{n}")
        print(f"    Fiabilite d'interface (decisions executees) : {n_executees}/{n}   ({time.time()-t0:.0f}s)\n", flush=True)

    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["scenario", "decideur", "run", "cat_executee", "cat_intention",
                    "actions_executees", "actions_intention"])
        w.writerows(lignes)
    print(f"CSV : {csv_path}  ({len(lignes)} lignes)\n", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=30)
    ap.add_argument("--v2", action="store_true", help="inclure le scenario 4b (source saillante)")
    ap.add_argument("--regle", action="store_true", help="evaluer la regle reactive au lieu du LLM")
    args = ap.parse_args()

    provider = "regle" if args.regle else os.getenv("LLM_PROVIDER", "ollama")
    modele = "regle_reactive" if args.regle else os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    noms = list(SC.ORDRE) + (list(SC.ORDRE_V2) if args.v2 else [])
    evaluer(noms, args.runs, provider, modele)
