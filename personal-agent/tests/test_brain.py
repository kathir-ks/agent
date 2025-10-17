"""Tests for agent brain."""

import pytest
from pathlib import Path

from src.agent.brain import AgentBrain
from src.agent.profile import UserProfile


@pytest.mark.asyncio
async def test_brain_initialization(mock_llm, temp_dir):
    """Test initializing the agent brain."""
    profile = UserProfile.create_default("test_user", "Test User")

    brain = AgentBrain(llm=mock_llm, user_profile=profile, data_dir=temp_dir)

    assert brain.llm == mock_llm
    assert brain.user_profile == profile
    assert brain.data_dir == temp_dir
    assert brain.memory is not None
    assert brain.content_discovery is not None


@pytest.mark.asyncio
async def test_brain_default_profile(mock_llm, temp_dir):
    """Test brain with default profile."""
    brain = AgentBrain(llm=mock_llm, data_dir=temp_dir)

    assert brain.user_profile is not None
    assert brain.user_profile.user_id == "default"


@pytest.mark.asyncio
async def test_process_message(mock_llm, temp_dir):
    """Test processing a message."""
    brain = AgentBrain(llm=mock_llm, data_dir=temp_dir)

    response = await brain.process_message("Hello, how are you?")

    assert isinstance(response, str)
    assert len(response) > 0
    # Check that interaction was recorded
    assert len(brain.memory.interactions) == 1
    assert brain.memory.interactions[0].user_input == "Hello, how are you?"


@pytest.mark.asyncio
async def test_process_multiple_messages(mock_llm, temp_dir):
    """Test processing multiple messages."""
    brain = AgentBrain(llm=mock_llm, data_dir=temp_dir)

    response1 = await brain.process_message("First message")
    response2 = await brain.process_message("Second message")

    assert len(brain.memory.interactions) == 2
    assert mock_llm.call_count >= 2


@pytest.mark.asyncio
async def test_discover_content(mock_llm, temp_dir):
    """Test discovering content."""
    profile = UserProfile.create_default()
    profile.add_interest("AI")

    brain = AgentBrain(llm=mock_llm, user_profile=profile, data_dir=temp_dir)

    items = await brain.discover_content(limit=5)

    assert isinstance(items, list)
    # Check that interaction was recorded
    assert any(
        i["type"] == "content_discovery"
        for i in brain.user_profile.interaction_history
    )


@pytest.mark.asyncio
async def test_understand_user(mock_llm, temp_dir):
    """Test understanding user."""
    brain = AgentBrain(llm=mock_llm, data_dir=temp_dir)

    # Add some interactions first
    await brain.process_message("I love AI")
    await brain.process_message("Tell me about machine learning")

    understanding = await brain.understand_user()

    assert isinstance(understanding, str)
    assert len(understanding) > 0
    assert mock_llm.call_count >= 3


@pytest.mark.asyncio
async def test_understand_user_no_history(mock_llm, temp_dir):
    """Test understanding user with no history."""
    brain = AgentBrain(llm=mock_llm, data_dir=temp_dir)

    understanding = await brain.understand_user()

    assert "Not enough interaction history" in understanding


def test_add_interest(mock_llm, temp_dir):
    """Test adding an interest."""
    brain = AgentBrain(llm=mock_llm, data_dir=temp_dir)

    brain.add_interest("Quantum Computing")

    assert "Quantum Computing" in brain.user_profile.preferences.interests


def test_remove_interest(mock_llm, temp_dir):
    """Test removing an interest."""
    brain = AgentBrain(llm=mock_llm, data_dir=temp_dir)

    brain.add_interest("AI")
    brain.add_interest("ML")
    brain.remove_interest("AI")

    assert "AI" not in brain.user_profile.preferences.interests
    assert "ML" in brain.user_profile.preferences.interests


def test_get_status(mock_llm, temp_dir):
    """Test getting agent status."""
    profile = UserProfile.create_default("test", "Test User")
    profile.add_interest("AI")

    brain = AgentBrain(llm=mock_llm, user_profile=profile, data_dir=temp_dir)

    status = brain.get_status()

    assert status["user"] == "Test User"
    assert "AI" in status["interests"]
    assert "memory" in status
    assert status["discovered_content_count"] == 0


@pytest.mark.asyncio
async def test_state_persistence(mock_llm, temp_dir):
    """Test that state is saved and can be loaded."""
    # Create brain and add some data
    profile = UserProfile.create_default("persist_test", "Test User")
    brain1 = AgentBrain(llm=mock_llm, user_profile=profile, data_dir=temp_dir)

    brain1.add_interest("AI")
    await brain1.process_message("Test message")

    # Manually save state
    brain1._save_state()

    # Create new brain with same user_id
    profile2 = UserProfile.create_default("persist_test", "Test User")
    brain2 = AgentBrain(llm=mock_llm, user_profile=profile2, data_dir=temp_dir)

    # Should load the saved state
    assert "AI" in brain2.user_profile.preferences.interests
    assert len(brain2.memory.interactions) > 0


@pytest.mark.asyncio
async def test_close(mock_llm, temp_dir):
    """Test closing the brain."""
    brain = AgentBrain(llm=mock_llm, data_dir=temp_dir)

    await brain.process_message("Test")

    # Close should save state and close LLM
    await brain.close()

    # State should be saved
    profile_path = temp_dir / f"profile_{brain.user_profile.user_id}.json"
    assert profile_path.exists()


@pytest.mark.asyncio
async def test_error_handling(mock_llm, temp_dir):
    """Test error handling in process_message."""
    brain = AgentBrain(llm=mock_llm, data_dir=temp_dir)

    # Make the mock LLM raise an error
    original_chat = mock_llm.chat

    async def error_chat(*args, **kwargs):
        raise Exception("Test error")

    mock_llm.chat = error_chat

    response = await brain.process_message("Test")

    # Should return error message
    assert "error" in response.lower() or "apologize" in response.lower()

    # Restore original
    mock_llm.chat = original_chat


def test_build_system_prompt(mock_llm, temp_dir):
    """Test building system prompt."""
    profile = UserProfile.create_default("test", "Alice")
    profile.add_interest("AI")
    profile.add_interest("Python")

    brain = AgentBrain(llm=mock_llm, user_profile=profile, data_dir=temp_dir)

    prompt = brain._build_system_prompt()

    assert "Alice" in prompt
    assert "AI" in prompt
    assert "Python" in prompt
    assert "personal ai assistant" in prompt.lower()
