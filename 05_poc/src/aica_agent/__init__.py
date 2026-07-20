"""
AICA-en-LangGraph - Agent autonome de cyberdéfense pour cluster Kubernetes + 5G.

Architecture inspirée du modèle AICA (Argonne National Laboratory, IST-152 OTAN) :
- sensing : collecte d'observations brutes
- perception : filtrage et structuration des observations
- world_model : maintien d'une représentation de l'environnement
- decision : raisonnement et choix d'action (LLM via LangGraph)
- action : exécution effective de l'action choisie

Cette implémentation utilise LangGraph comme moteur, ce qui permet de garder la
souplesse de l'écosystème LangChain tout en respectant la décomposition AICA.
"""

__version__ = "0.1.0"
