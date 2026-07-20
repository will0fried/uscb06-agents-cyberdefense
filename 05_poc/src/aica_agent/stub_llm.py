"""
Provider LLM "stub" déterministe pour les tests et la CI.

Pourquoi ? Parce que :
- Ollama exige un binaire local + ~2 Go de RAM, pas pratique en CI ;
- les modèles 3B sont parfois aléatoires sur le tool calling, ce qui rend
  les tests d'intégration flakey ;
- pour le mémoire, on veut pouvoir reproduire un run exactement (même
  séquence d'actions, même conclusion) pour les chiffres de la section 3.5.

Le stub implémente le sous-ensemble de l'interface ChatModel utilisé par
nos nœuds : `bind_tools(tools)` retourne un objet avec `.invoke(messages)`
qui renvoie un AIMessage avec d'éventuels tool_calls.

Comportement scripté :
1. Premier appel    -> tool_call(isolate_pod, pod="open5gs-smf-0", ns="core5g")
2. Deuxième appel   -> tool_call(terminate_5g_session, session=0x7a8b9c)
3. Troisième appel  -> réponse texte "MISSION_TERMINEE …"
4. Appels suivants  -> idem #3 (idempotent)

Ce script reflète une décision plausible qu'un vrai agent prendrait face
au scénario mock (alertes Warning sur smf-0 + sessions PDU suspectes).
"""
from typing import Any, Dict, List, Optional, Sequence
from uuid import uuid4

from langchain_core.messages import AIMessage, BaseMessage


class StubChatModel:
    """LLM factice qui rejoue un script déterministe.

    Args:
        scripted_steps: liste de "tours". Chaque tour est soit un dict
            décrivant un tool call ({'tool': 'name', 'args': {...}}),
            soit une string (réponse texte du LLM).
            Si None, utilise le scénario par défaut (isolate -> terminate -> fin).
    """

    DEFAULT_SCRIPT: List[Any] = [
        {"tool": "isolate_pod", "args": {"pod_name": "open5gs-smf-0", "namespace": "core5g"}},
        {"tool": "terminate_5g_session", "args": {"session_id": "0x7a8b9c", "reason": "comportement anormal de session PDU détecté"}},
        "MISSION_TERMINEE - Le pod open5gs-smf-0 a été isolé et la session PDU suspecte 0x7a8b9c terminée. La menace est contenue.",
    ]

    def __init__(self, scripted_steps: Optional[List[Any]] = None):
        self._script = scripted_steps if scripted_steps is not None else list(self.DEFAULT_SCRIPT)
        self._step_index = 0
        # bind_tools garde une trace des outils mais ne s'en sert pas
        self._bound_tools: List[Any] = []

    def bind_tools(self, tools: Sequence[Any]) -> "StubChatModel":
        """Compatibilité interface LangChain. On retourne self avec les outils stockés."""
        self._bound_tools = list(tools)
        return self

    def invoke(self, messages: Sequence[BaseMessage], **_kwargs: Any) -> AIMessage:
        """Retourne le tour scripté courant et avance le curseur.

        Si on dépasse la fin du script, on retourne la dernière étape
        (idempotent) - utile si LangGraph rappelle le LLM après une action.
        """
        idx = min(self._step_index, len(self._script) - 1)
        self._step_index += 1

        step = self._script[idx]

        if isinstance(step, dict) and "tool" in step:
            return AIMessage(
                content="",
                tool_calls=[{
                    "name": step["tool"],
                    "args": step.get("args", {}),
                    "id": f"call_{uuid4().hex[:8]}",
                }],
            )

        # Sinon : réponse texte
        return AIMessage(content=str(step))

    def reset(self) -> None:
        """Remet le curseur du script à zéro (utile pour les tests)."""
        self._step_index = 0
