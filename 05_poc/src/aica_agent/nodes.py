"""
Nœuds du graphe AICA-en-LangGraph.

Chaque fonction ici implémente un module AICA. Toutes prennent l'état courant
en entrée et retournent un dictionnaire de mises à jour partielles. LangGraph
se charge de fusionner ces mises à jour dans l'état global.
"""
from typing import Any, Dict
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.prebuilt import ToolNode

from .state import AgentState
from .tools import ALL_TOOLS, get_recent_events, list_pods


# --------- Sensing ---------

def sensing_node(state: AgentState) -> Dict[str, Any]:
    """Couche capteurs : récolte les observations brutes de l'environnement.

    Dans cette première version, sensing appelle directement les outils de
    perception passive (list_pods, get_recent_events). En phase 2, sensing
    pourra s'abonner à Falco, à un flux Kubernetes Watch, etc.
    """
    raw = []
    # On invoque deux outils en passif pour avoir une vue de base
    raw.append({
        "source": "k8s.pods",
        "data": list_pods.invoke({"namespace": "core5g"}),
    })
    raw.append({
        "source": "k8s.events",
        "data": get_recent_events.invoke({"namespace": "core5g", "limit": 10}),
    })
    return {"raw_observations": raw}


# --------- Perception ---------

def perception_node(state: AgentState) -> Dict[str, Any]:
    """Couche perception : filtre les observations brutes en faits structurés.

    Règles simples pour démarrer (à enrichir avec un LLM en phase 2) :
    - tout pod avec restarts > 0 est un fait "instabilité"
    - tout événement de type Warning est un fait "alerte"
    """
    facts = []
    for obs in state.get("raw_observations", []):
        if obs["source"] == "k8s.pods":
            for pod in obs["data"]:
                if pod.get("restarts", 0) > 0:
                    facts.append({
                        "kind": "instability",
                        "subject": pod["name"],
                        "detail": f"{pod['restarts']} redémarrage(s)",
                    })
        elif obs["source"] == "k8s.events":
            for ev in obs["data"]:
                if ev.get("type") == "Warning":
                    facts.append({
                        "kind": "alert",
                        "subject": ev["object"],
                        "detail": ev["message"],
                        "reason": ev["reason"],
                    })
    return {"structured_facts": facts}


# --------- World Model ---------

def world_model_node(state: AgentState) -> Dict[str, Any]:
    """Couche modèle du monde : maintient une représentation synthétique.

    Pour l'instant : on agrège les faits par sujet et on note le nombre
    d'alertes par pod. En phase 2, on pourra modéliser des chaînes causales
    et des hypothèses (raisonnement abductif).
    """
    alerts_by_subject: Dict[str, int] = {}
    suspects = set()
    for fact in state.get("structured_facts", []):
        subj = fact["subject"]
        if fact["kind"] == "alert":
            alerts_by_subject[subj] = alerts_by_subject.get(subj, 0) + 1
            if alerts_by_subject[subj] >= 2:
                suspects.add(subj)

    world = {
        "alerts_by_subject": alerts_by_subject,
        "suspects": sorted(suspects),
        "total_facts": len(state.get("structured_facts", [])),
    }
    return {"world_state": world}


# --------- Decision (cœur LLM) ---------

def make_decision_node(llm_with_tools):
    """Construit le nœud de décision avec un LLM lié aux outils.

    Retourne une fonction de nœud que LangGraph peut invoquer.
    """
    def decision_node(state: AgentState) -> Dict[str, Any]:
        # On construit le contexte pour le LLM à partir de l'état AICA
        system = SystemMessage(content=(
            "Tu es un agent de cyberdéfense déployé dans un cluster Kubernetes "
            "qui héberge un cœur 5G open-source (Open5GS). Ton objectif est "
            "fourni dans le message utilisateur. Tu disposes d'outils pour "
            "observer le cluster, observer les sessions 5G, et agir (isoler "
            "un pod, terminer une session). Raisonne en français, étape par "
            "étape. Quand tu as identifié une action de défense pertinente, "
            "invoque l'outil correspondant. Quand tu juges la mission terminée, "
            "réponds simplement 'MISSION_TERMINEE' suivi d'un résumé."
        ))

        # Si c'est le premier appel, on injecte aussi l'objectif et le contexte AICA.
        # IMPORTANT : le briefing doit être ajouté à state.messages (pas seulement
        # passé au LLM) pour rester accessible aux pas suivants - sinon l'agent
        # perd l'objectif dès le pas 2.
        if state.get("step_count", 0) == 0:
            world = state.get("world_state", {})
            facts = state.get("structured_facts", [])
            briefing = (
                f"Objectif : {state['objective']}\n\n"
                f"Faits structurés observés ({len(facts)}) :\n"
                + "\n".join(f"  - [{f['kind']}] {f['subject']} : {f['detail']}" for f in facts)
                + f"\n\nSuspects identifiés par le modèle du monde : "
                + (", ".join(world.get("suspects", [])) or "aucun pour l'instant")
            )
            initial_msg = HumanMessage(content=briefing)
            messages_in = [system, initial_msg]
            new_messages = [initial_msg]  # on persiste le briefing dans l'historique
        else:
            # Étapes suivantes : on s'appuie sur l'historique
            messages_in = [system] + state["messages"]
            new_messages = []

        response = llm_with_tools.invoke(messages_in)
        new_messages.append(response)

        # Détection de la fin de mission
        text = (response.content or "").upper()
        finished = "MISSION_TERMINEE" in text or "MISSION TERMINEE" in text

        return {
            "messages": new_messages,
            "step_count": state.get("step_count", 0) + 1,
            "finished": finished,
        }

    return decision_node


# --------- Action ---------

# LangGraph fournit un ToolNode prêt à l'emploi qui exécute les tool calls
# émis par le LLM et renvoie un ToolMessage. C'est notre couche "action".
action_node = ToolNode(ALL_TOOLS)


# --------- Routage ---------

def should_continue(state: AgentState) -> str:
    """Aiguillage après le nœud décision.

    - Si le LLM a émis des tool calls -> on exécute (nœud action)
    - Si le LLM a déclaré MISSION_TERMINEE -> on s'arrête
    - Si on a dépassé le budget de pas -> on s'arrête
    - Sinon -> on retourne au sensing pour ré-observer
    """
    if state.get("finished"):
        return "end"
    if state.get("step_count", 0) >= 10:
        return "end"
    last = state["messages"][-1] if state["messages"] else None
    if last and getattr(last, "tool_calls", None):
        return "act"
    return "end"
