"""Pytest configuration and fixtures."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from src.llm.base import LLMConfig, LLMResponse, ModelProvider, BaseLLM


class MockLLM(BaseLLM):
    """Mock LLM for testing."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.call_count = 0
        self.messages = []

    async def initialize(self):
        """Mock initialization."""
        self._client = Mock()

    async def generate(self, prompt: str, system_prompt=None, **kwargs):
        """Mock generation."""
        self.call_count += 1
        self.messages.append({"prompt": prompt, "system_prompt": system_prompt})

        return LLMResponse(
            content=f"Mock response to: {prompt[:50]}",
            model=self.config.model_name,
            provider=self.config.provider,
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        )

    async def generate_stream(self, prompt: str, system_prompt=None, **kwargs):
        """Mock streaming."""
        for chunk in ["Mock ", "streaming ", "response"]:
            yield chunk

    async def chat(self, messages: list, **kwargs):
        """Mock chat."""
        self.call_count += 1
        self.messages.extend(messages)

        return LLMResponse(
            content="Mock chat response",
            model=self.config.model_name,
            provider=self.config.provider,
        )


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_llm_config():
    """Create a mock LLM config."""
    return LLMConfig(
        provider=ModelProvider.GEMINI,
        model_name="gemini-pro-test",
        api_key="test-key",
        temperature=0.7,
        max_tokens=1024,
    )


@pytest.fixture
def mock_llm(mock_llm_config):
    """Create a mock LLM instance."""
    llm = MockLLM(mock_llm_config)
    # Don't await here - let the test handle async operations
    return llm
