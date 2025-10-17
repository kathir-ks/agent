"""Base classes for LLM abstraction."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum


class ModelProvider(str, Enum):
    """Supported LLM providers."""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    # Add more as needed


@dataclass
class LLMConfig:
    """Configuration for LLM models."""
    provider: ModelProvider
    model_name: str
    api_key: str
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0
    top_k: Optional[int] = None
    stop_sequences: Optional[List[str]] = None
    extra_params: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """Response from an LLM."""
    content: str
    model: str
    provider: ModelProvider
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    raw_response: Optional[Any] = None


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: LLMConfig):
        """Initialize the LLM with configuration.

        Args:
            config: LLM configuration
        """
        self.config = config
        self._client = None

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the LLM client (async setup)."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from the LLM.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse with the generated content
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        """Generate a streaming response from the LLM.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters

        Yields:
            Chunks of the generated content
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """Have a multi-turn conversation with the LLM.

        Args:
            messages: List of messages with 'role' and 'content'
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse with the generated content
        """
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Clean up resources (override if needed)."""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider={self.config.provider}, model={self.config.model_name})"
