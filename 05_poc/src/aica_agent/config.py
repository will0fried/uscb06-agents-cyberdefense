"""
Configuration centrale : chargement des variables d'environnement et instanciation
du provider LLM (Ollama par défaut, ou cloud si une clé API est fournie).
"""
import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """Configuration de l'agent, chargée depuis .env."""
    llm_provider: str = os.getenv("LLM_PROVIDER", "ollama")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")

    mistral_api_key: Optional[str] = os.getenv("MISTRAL_API_KEY")
    mistral_model: str = os.getenv("MISTRAL_MODEL", "mistral-small-latest")

    agent_max_steps: int = int(os.getenv("AGENT_MAX_STEPS", "10"))
    agent_verbose: bool = os.getenv("AGENT_VERBOSE", "true").lower() == "true"

    kubeconfig_path: Optional[str] = os.getenv("KUBECONFIG_PATH") or None
    target_namespace: str = os.getenv("TARGET_NAMESPACE", "default")


def get_llm(settings: Optional[Settings] = None):
    """Instancie le LLM selon le provider configuré.

    Cette fonction est volontairement isolée pour que le reste du code n'ait
    aucune dépendance directe au provider - on peut basculer Ollama -> OpenAI
    sans toucher au graphe.
    """
    if settings is None:
        settings = Settings()

    provider = settings.llm_provider.lower()

    if provider == "stub":
        # Provider déterministe pour tests / CI / reproductibilité mémoire.
        # Aucune dépendance externe : pas d'Ollama, pas de clé API.
        from .stub_llm import StubChatModel
        return StubChatModel()

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.0,   # aligne le PoC sur les campagnes CybORG (T=0) - un seul facteur change
        )

    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY non défini dans .env")
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=settings.openai_model, temperature=0.1)

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY non défini dans .env")
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=settings.anthropic_model, temperature=0.1)

    if provider == "mistral":
        if not settings.mistral_api_key:
            raise ValueError("MISTRAL_API_KEY non défini dans .env")
        from langchain_mistralai import ChatMistralAI
        return ChatMistralAI(model=settings.mistral_model, temperature=0.1)

    raise ValueError(f"Provider LLM inconnu : {provider}")
