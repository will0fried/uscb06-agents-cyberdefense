"""
Outils que l'agent peut invoquer pour percevoir et agir sur son environnement.

Phase 1 (actuelle) : tous les outils sont en mode mock - ils retournent des
données fictives mais réalistes. Cela permet de valider la logique de l'agent
sans dépendre d'un cluster Kubernetes ou d'un cœur 5G déployé.

Phase 2 : les fonctions mock_* seront remplacées par de vrais appels (client
kubernetes Python, requêtes SBI vers AMF/SMF/UPF, etc.).
"""
from typing import List, Dict, Any
from langchain_core.tools import tool


# ---------- Mocks Kubernetes ----------

_MOCK_PODS = [
    {"name": "open5gs-amf-0", "namespace": "core5g", "status": "Running", "restarts": 0, "node": "worker-1"},
    {"name": "open5gs-smf-0", "namespace": "core5g", "status": "Running", "restarts": 2, "node": "worker-1"},
    {"name": "open5gs-upf-0", "namespace": "core5g", "status": "Running", "restarts": 0, "node": "worker-2"},
    {"name": "open5gs-nrf-0", "namespace": "core5g", "status": "Running", "restarts": 0, "node": "worker-1"},
    {"name": "attacker-pod",  "namespace": "core5g", "status": "Running", "restarts": 0, "node": "worker-2"},
]

_MOCK_EVENTS = [
    {"timestamp": "2026-05-10T14:23:01Z", "type": "Warning", "reason": "UnauthorizedAccess",
     "object": "pod/open5gs-smf-0", "message": "Tentative d'accès non autorisée sur l'interface N4 depuis 10.244.2.17"},
    {"timestamp": "2026-05-10T14:23:45Z", "type": "Warning", "reason": "AbnormalSessionRate",
     "object": "pod/open5gs-smf-0", "message": "Pic de créations de sessions PDU : 450/s (normal : 20/s)"},
    {"timestamp": "2026-05-10T14:24:12Z", "type": "Normal", "reason": "Pulling",
     "object": "pod/attacker-pod", "message": "Pulling image suspicious-registry/n4-exploit:latest"},
]

_MOCK_SESSIONS_SMF = [
    {"session_id": "0x1a2b3c", "supi": "imsi-208930000000001", "dnn": "internet", "state": "ACTIVE", "duration_s": 1247},
    {"session_id": "0x4d5e6f", "supi": "imsi-208930000000002", "dnn": "ims",      "state": "ACTIVE", "duration_s": 89},
    {"session_id": "0x7a8b9c", "supi": "imsi-999999999999999", "dnn": "internet", "state": "ESTABLISHING", "duration_s": 2},
    {"session_id": "0xdeadbe", "supi": "imsi-999999999999998", "dnn": "internet", "state": "ESTABLISHING", "duration_s": 1},
]

# --- Scenario actif ---------------------------------------------------------------------------
# Par defaut, l'agent voit le scenario historique de la demo (retro-compatibilite : demo.py et
# les tests ne changent pas). Le harnais d'evaluation appelle set_active_scenario() pour servir
# tour a tour chacun des cinq scenarios d'incident (voir scenarios.py).
_ACTIVE = {"pods": _MOCK_PODS, "events": _MOCK_EVENTS, "sessions_smf": _MOCK_SESSIONS_SMF}


def set_active_scenario(pods, events, sessions_smf):
    """Definit les donnees que les outils d'observation renverront jusqu'au prochain appel."""
    _ACTIVE["pods"] = pods
    _ACTIVE["events"] = events
    _ACTIVE["sessions_smf"] = sessions_smf


def reset_active_scenario():
    """Restaure le scenario historique de la demo."""
    _ACTIVE["pods"] = _MOCK_PODS
    _ACTIVE["events"] = _MOCK_EVENTS
    _ACTIVE["sessions_smf"] = _MOCK_SESSIONS_SMF


@tool
def list_pods(namespace: str = "default") -> List[Dict[str, Any]]:
    """Liste les pods d'un namespace Kubernetes donné.

    Args:
        namespace: namespace Kubernetes à inspecter (ex: 'core5g', 'default')

    Returns:
        Liste de pods avec leur statut, nombre de redémarrages, et nœud d'hébergement.
    """
    return [p for p in _ACTIVE["pods"] if p["namespace"] == namespace]


@tool
def get_recent_events(namespace: str = "default", limit: int = 20) -> List[Dict[str, Any]]:
    """Récupère les événements Kubernetes récents pour un namespace.

    Args:
        namespace: namespace à observer
        limit: nombre max d'événements à retourner

    Returns:
        Liste d'événements avec timestamp, type, raison et message.
    """
    # En mock on ignore le filtre namespace pour simplifier la démo
    return _ACTIVE["events"][:limit]


@tool
def isolate_pod(pod_name: str, namespace: str) -> Dict[str, Any]:
    """Isole un pod en appliquant une NetworkPolicy qui bloque tout son trafic.

    ACTION DE RÉPONSE - à utiliser uniquement quand un pod est identifié comme compromis.

    Args:
        pod_name: nom du pod à isoler
        namespace: son namespace

    Returns:
        Résultat de l'isolation : succès, NetworkPolicy créée.
    """
    return {
        "success": True,
        "action": "isolate_pod",
        "pod": f"{namespace}/{pod_name}",
        "network_policy": f"isolate-{pod_name}",
        "message": f"Pod {pod_name} isolé via NetworkPolicy (mock)"
    }


# ---------- Mocks 5G ----------

@tool
def list_5g_sessions(nf: str = "smf") -> List[Dict[str, Any]]:
    """Liste les sessions PDU actives sur une fonction réseau 5G.

    Args:
        nf: fonction réseau ciblée - 'smf' pour Session Management Function, 'upf' pour User Plane Function

    Returns:
        Liste des sessions actives avec ID, supi (identifiant abonné), DNN, état.
    """
    if nf.lower() == "smf":
        return list(_ACTIVE["sessions_smf"])
    return []


@tool
def terminate_5g_session(session_id: str, reason: str) -> Dict[str, Any]:
    """Termine une session PDU 5G.

    ACTION DE RÉPONSE - utile pour couper une session manifestement malveillante.

    Args:
        session_id: identifiant de la session à terminer
        reason: raison de la terminaison (auditée)

    Returns:
        Confirmation de la terminaison.
    """
    return {
        "success": True,
        "action": "terminate_5g_session",
        "session_id": session_id,
        "reason": reason,
        "message": f"Session {session_id} terminée (mock) - raison : {reason}"
    }


# ---------- Liste des outils exposés à l'agent ----------

ALL_TOOLS = [
    list_pods,
    get_recent_events,
    isolate_pod,
    list_5g_sessions,
    terminate_5g_session,
]
