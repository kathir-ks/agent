"""Tests for LLM base classes."""

import pytest
from src.llm.base import LLMConfig, LLMResponse, ModelProvider


def test_llm_config_creation():
    """Test LLM config creation."""
    config = LLMConfig(
        provider=ModelProvider.GEMINI,
        model_name="gemini-pro",
        api_key="test-key",
        temperature=0.8,
        max_tokens=2048,
    )

    assert config.provider == ModelProvider.GEMINI
    assert config.model_name == "gemini-pro"
    assert config.api_key == "test-key"
    assert config.temperature == 0.8
    assert config.max_tokens == 2048


def test_llm_config_defaults():
    """Test LLM config defaults."""
    config = LLMConfig(
        provider=ModelProvider.GEMINI,
        model_name="gemini-pro",
        api_key="test-key",
    )

    assert config.temperature == 0.7
    assert config.max_tokens == 2048
    assert config.top_p == 1.0
    assert config.top_k is None


def test_llm_response_creation():
    """Test LLM response creation."""
    response = LLMResponse(
        content="Hello, world!",
        model="gemini-pro",
        provider=ModelProvider.GEMINI,
        usage={"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        finish_reason="stop",
    )

    assert response.content == "Hello, world!"
    assert response.model == "gemini-pro"
    assert response.provider == ModelProvider.GEMINI
    assert response.usage["total_tokens"] == 15
    assert response.finish_reason == "stop"


@pytest.mark.asyncio
async def test_mock_llm_generate(mock_llm):
    """Test mock LLM generation."""
    response = await mock_llm.generate("Test prompt")

    assert isinstance(response, LLMResponse)
    assert "Mock response" in response.content
    assert mock_llm.call_count == 1


@pytest.mark.asyncio
async def test_mock_llm_chat(mock_llm):
    """Test mock LLM chat."""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
    ]

    response = await mock_llm.chat(messages)

    assert isinstance(response, LLMResponse)
    assert response.content == "Mock chat response"
    assert mock_llm.call_count == 1


@pytest.mark.asyncio
async def test_mock_llm_stream(mock_llm):
    """Test mock LLM streaming."""
    chunks = []
    async for chunk in mock_llm.generate_stream("Test prompt"):
        chunks.append(chunk)

    assert len(chunks) == 3
    assert "".join(chunks) == "Mock streaming response"


@pytest.mark.asyncio
async def test_llm_context_manager(mock_llm_config):
    """Test LLM context manager."""
    from tests.conftest import MockLLM

    async with MockLLM(mock_llm_config) as llm:
        response = await llm.generate("Test")
        assert response.content is not None
