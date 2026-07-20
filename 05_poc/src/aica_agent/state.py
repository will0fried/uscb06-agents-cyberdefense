"""
État partagé entre les nœuds du graphe AICA.

LangGraph nous demande un TypedDict qui décrit toutes les valeurs que les
nœuds vont produire et consommer. Cette structure reflète les modules AICA :
- raw_observations  ← sensing
- structured_facts  ← perception
- world_state       ← world_model
- planned_action    ← decision
- executed_actions  ← action
- messages          ← historique LLM (pour le tool calling)
"""
from typing import Annotated, Any, Dict, List, Optional, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """État global de l'agent, lu et écrit par les nœuds du graphe."""

    # Historique des messages (LLM + outils). add_messages = append automatique.
    messages: Annotated[List[BaseMessage], add_messages]

    # Couche AICA : sensing -> perception -> world_model -> decision -> action
    raw_observations: List[Dict[str, Any]]
    structured_facts: List[Dict[str, Any]]
    world_state: Dict[str, Any]
    planned_action: Optional[Dict[str, Any]]
    executed_actions: List[Dict[str, Any]]

    # Suivi de progression
    step_count: int
    objective: str
    finished: bool
