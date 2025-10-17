"""Factory for creating LLM instances."""

import logging
from typing import Optional
from .base import BaseLLM, LLMConfig, ModelProvider
from .gemini import GeminiLLM

logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory for creating LLM instances based on provider."""

    _providers = {
        ModelProvider.GEMINI: GeminiLLM,
        # Add more providers here as they're implemented
        # ModelProvider.OPENAI: OpenAILLM,
        # ModelProvider.ANTHROPIC: AnthropicLLM,
    }

    @classmethod
    def create(cls, config: LLMConfig) -> BaseLLM:
        """Create an LLM instance based on the configuration.

        Args:
            config: LLM configuration

        Returns:
            An instance of the appropriate LLM class

        Raises:
            ValueError: If the provider is not supported
        """
        provider_class = cls._providers.get(config.provider)

        if provider_class is None:
            supported = ", ".join([p.value for p in cls._providers.keys()])
            raise ValueError(
                f"Unsupported provider: {config.provider}. "
                f"Supported providers: {supported}"
            )

        logger.info(f"Creating LLM instance for provider: {config.provider}")
        return provider_class(config)

    @classmethod
    def register_provider(cls, provider: ModelProvider, provider_class: type[BaseLLM]) -> None:
        """Register a new LLM provider.

        Args:
            provider: The provider enum value
            provider_class: The LLM implementation class
        """
        cls._providers[provider] = provider_class
        logger.info(f"Registered new provider: {provider}")

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered providers.

        Returns:
            List of provider names
        """
        return [p.value for p in cls._providers.keys()]
