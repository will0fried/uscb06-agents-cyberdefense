#!/usr/bin/env python3
"""
Test de sante de l'appel d'outils, HORS du harnais et du graphe AICA.

But : localiser la defaillance observee avec llama3.1:8b. On soumet au modele UN outil trivial
avec une invite courte, via exactement la meme pile (langchain-ollama, ChatOllama.bind_tools),
et on regarde s'il emet un appel d'outil STRUCTURE (champ tool_calls) ou s'il l'ecrit en texte.

  - S'il reussit ce cas minimal mais echoue dans le harnais -> la defaillance tient a
    l'interaction (longueur d'invite, complexite du contexte), pas a la pile.
  - S'il echoue meme ici -> c'est la pile (modele + Ollama + binding) qui ne supporte pas
    l'appel d'outils dans ce montage.

Usage (depuis poc/) :
    OLLAMA_MODEL=llama3.2:3b python scripts/health_check.py
    OLLAMA_MODEL=llama3.1:8b python scripts/health_check.py
"""
import os
from langchain_ollama import ChatOllama
from langchain_core.tools import tool


@tool
def additionner(a: int, b: int) -> int:
    """Additionne deux entiers a et b et renvoie le resultat."""
    return a + b


def main():
    modele = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    llm = ChatOllama(model=modele, temperature=0).bind_tools([additionner])
    resp = llm.invoke("Utilise l'outil disponible pour additionner 21 et 21.")

    print(f"\nModele teste : {modele}")
    print(f"Appels d'outils STRUCTURES (champ tool_calls) : {resp.tool_calls}")
    print(f"Texte libre du modele : {str(resp.content)[:300]!r}\n")

    if resp.tool_calls:
        print(">>> SAIN : sur le cas minimal, le modele emet un appel d'outil structure.")
        print("    Si le harnais echoue malgre tout, la defaillance tient a l'interaction")
        print("    (longueur d'invite / complexite du contexte), pas a la pile.")
    else:
        print(">>> ECHEC MEME MINIMAL : le modele n'emet pas d'appel structure sur un cas trivial.")
        print("    La defaillance tient a la pile (modele + Ollama + binding) dans ce montage.")
    print()


if __name__ == "__main__":
    main()
