"""
Test d'intégration : on fait tourner le graphe entier avec le stub LLM.

C'est le test le plus important du PoC : il valide que la chaîne complète
sensing -> perception -> world_model -> decision -> action -> decision -> END
fonctionne, et qu'au moins une action de défense est exécutée.
"""
import os

import pytest

from aica_agent.config import Settings
from aica_agent.graph import build_graph


@pytest.fixture
def stub_settings(monkeypatch):
    """Force le provider à 'stub' pour ce test, sans toucher au .env de l'utilisateur."""
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    return Settings()


def test_graph_runs_end_to_end_and_executes_actions(stub_settings):
    graph = build_graph(stub_settings)

    initial_state = {
        "messages": [],
        "raw_observations": [],
        "structured_facts": [],
        "world_state": {},
        "planned_action": None,
        "executed_actions": [],
        "step_count": 0,
        "objective": "test e2e",
        "finished": False,
    }

    visited_nodes: list[str] = []
    final_state = None
    for step in graph.stream(initial_state, config={"recursion_limit": 50}):
        for node, update in step.items():
            visited_nodes.append(node)
            final_state = update

    # Tous les modules AICA doivent avoir été visités
    assert "sensing" in visited_nodes
    assert "perception" in visited_nodes
    assert "world_model" in visited_nodes
    assert "decision" in visited_nodes
    # Le stub script appelle deux outils -> au moins un passage par 'action'
    assert "action" in visited_nodes


def test_graph_finishes_with_mission_terminee(stub_settings):
    """Le stub doit conclure par 'MISSION_TERMINEE' dans le dernier message."""
    graph = build_graph(stub_settings)

    initial_state = {
        "messages": [],
        "raw_observations": [],
        "structured_facts": [],
        "world_state": {},
        "planned_action": None,
        "executed_actions": [],
        "step_count": 0,
        "objective": "test",
        "finished": False,
    }

    final_full_state = graph.invoke(initial_state, config={"recursion_limit": 50})

    # Le dernier message du LLM doit contenir le mot clé de fin
    last_msg = final_full_state["messages"][-1]
    # Le dernier message peut être un ToolMessage si la conv s'est arrêtée juste
    # après une action, donc on remonte au dernier AIMessage texte
    last_ai_text = next(
        (m.content for m in reversed(final_full_state["messages"])
         if getattr(m, "content", None) and "MISSION_TERMINEE" in str(m.content)),
        None,
    )
    assert last_ai_text is not None, "MISSION_TERMINEE attendu dans la conversation"
