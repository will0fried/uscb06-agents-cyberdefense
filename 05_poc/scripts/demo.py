#!/usr/bin/env python3
"""
Démo principale : lance l'agent AICA-en-LangGraph sur un scénario fictif.

Usage :
    python scripts/demo.py
"""
import sys
import os
from pathlib import Path

# Ajoute src/ au PYTHONPATH pour pouvoir importer aica_agent sans installer le package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.json import JSON

from aica_agent.graph import build_graph
from aica_agent.config import Settings

console = Console()


def main():
    settings = Settings()

    console.print(Panel(
        f"[bold cyan]AICA-en-LangGraph - Démo[/bold cyan]\n\n"
        f"Provider LLM : [yellow]{settings.llm_provider}[/yellow]\n"
        f"Modèle : [yellow]{settings.ollama_model if settings.llm_provider == 'ollama' else 'cloud'}[/yellow]\n"
        f"Pas max : [yellow]{settings.agent_max_steps}[/yellow]",
        title="Configuration",
    ))

    objective = (
        "Détecter une éventuelle compromission dans le cœur 5G déployé "
        "dans le namespace 'core5g'. Si tu identifies une menace claire, "
        "prends une action de réponse appropriée (isolation de pod ou "
        "terminaison de session). Justifie chaque action."
    )

    initial_state = {
        "messages": [],
        "raw_observations": [],
        "structured_facts": [],
        "world_state": {},
        "planned_action": None,
        "executed_actions": [],
        "step_count": 0,
        "objective": objective,
        "finished": False,
    }

    graph = build_graph(settings)

    console.print("\n[bold green]Démarrage du graphe…[/bold green]\n")

    final_state = None
    for step in graph.stream(initial_state, config={"recursion_limit": 50}):
        for node, update in step.items():
            console.print(Panel(
                _format_update(update),
                title=f"[bold]Nœud : {node}[/bold]",
                border_style="blue",
            ))
            final_state = step

    console.print("\n[bold green]Mission terminée.[/bold green]\n")

    if final_state:
        # Récupère le dernier message du LLM (synthèse)
        last_messages = []
        for v in final_state.values():
            if isinstance(v, dict) and "messages" in v:
                last_messages = v["messages"]
        if last_messages:
            console.print(Panel(
                str(last_messages[-1].content),
                title="[bold]Synthèse finale du LLM[/bold]",
                border_style="green",
            ))


def _format_update(update):
    """Formatage lisible d'une mise à jour d'état."""
    if not isinstance(update, dict):
        return str(update)
    lines = []
    for k, v in update.items():
        if k == "messages":
            if v:
                last = v[-1]
                tool_calls = getattr(last, "tool_calls", None)
                if tool_calls:
                    lines.append(f"[yellow]LLM -> appel(s) outil :[/yellow] {[tc['name'] for tc in tool_calls]}")
                else:
                    content = str(last.content)[:300]
                    lines.append(f"[yellow]LLM :[/yellow] {content}")
        elif k == "raw_observations":
            lines.append(f"[cyan]raw_observations :[/cyan] {len(v)} sources collectées")
        elif k == "structured_facts":
            lines.append(f"[cyan]structured_facts :[/cyan] {len(v)} faits identifiés")
            for f in v[:5]:
                lines.append(f"    - [{f['kind']}] {f['subject']} : {f['detail']}")
        elif k == "world_state":
            lines.append(f"[cyan]world_state :[/cyan] suspects = {v.get('suspects', [])}")
        else:
            lines.append(f"[cyan]{k} :[/cyan] {v}")
    return "\n".join(lines) if lines else "(pas de changement)"


if __name__ == "__main__":
    main()
