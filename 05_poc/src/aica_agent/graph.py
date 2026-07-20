"""
Assemblage du graphe LangGraph qui implémente l'architecture AICA.

Schéma :

  START
    |
  sensing  ->  perception  ->  world_model  ->  decision
                                                |
                                          should_continue ?
                                            ↙          ↘
                                         act           END
                                          |
                                       decision  (boucle)
"""
from langgraph.graph import StateGraph, START, END

from .state import AgentState
from .nodes import (
    sensing_node,
    perception_node,
    world_model_node,
    make_decision_node,
    action_node,
    should_continue,
)
from .tools import ALL_TOOLS
from .config import get_llm, Settings


def build_graph(settings: Settings = None):
    """Construit et compile le graphe AICA-en-LangGraph.

    Args:
        settings: configuration. Si None, charge depuis .env

    Returns:
        Graphe compilé prêt à invoquer.
    """
    if settings is None:
        settings = Settings()

    llm = get_llm(settings)
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    decision_node = make_decision_node(llm_with_tools)

    workflow = StateGraph(AgentState)

    # Modules AICA
    workflow.add_node("sensing", sensing_node)
    workflow.add_node("perception", perception_node)
    workflow.add_node("world_model", world_model_node)
    workflow.add_node("decision", decision_node)
    workflow.add_node("action", action_node)

    # Chaîne linéaire perception -> décision
    workflow.add_edge(START, "sensing")
    workflow.add_edge("sensing", "perception")
    workflow.add_edge("perception", "world_model")
    workflow.add_edge("world_model", "decision")

    # Boucle décision / action
    workflow.add_conditional_edges(
        "decision",
        should_continue,
        {"act": "action", "end": END},
    )
    workflow.add_edge("action", "decision")

    return workflow.compile()
