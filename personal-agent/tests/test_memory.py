"""Tests for memory management."""

import pytest
from datetime import datetime
from pathlib import Path

from src.agent.memory import MemoryManager, Interaction


def test_interaction_creation():
    """Test creating an interaction."""
    interaction = Interaction(
        user_input="Hello",
        agent_response="Hi there!",
        metadata={"source": "test"},
    )

    assert interaction.user_input == "Hello"
    assert interaction.agent_response == "Hi there!"
    assert interaction.metadata["source"] == "test"
    assert isinstance(interaction.timestamp, datetime)


def test_interaction_to_dict():
    """Test converting interaction to dictionary."""
    interaction = Interaction(
        user_input="Test input",
        agent_response="Test response",
    )

    data = interaction.to_dict()

    assert data["user_input"] == "Test input"
    assert data["agent_response"] == "Test response"
    assert "timestamp" in data


def test_memory_manager_creation():
    """Test creating a memory manager."""
    memory = MemoryManager(max_history=10)

    assert memory.max_history == 10
    assert len(memory.interactions) == 0
    assert len(memory.context) == 0


def test_add_interaction():
    """Test adding interactions."""
    memory = MemoryManager()

    memory.add_interaction("Hello", "Hi there!")
    memory.add_interaction("How are you?", "I'm good!")

    assert len(memory.interactions) == 2
    assert memory.interactions[0].user_input == "Hello"
    assert memory.interactions[1].user_input == "How are you?"


def test_max_history_limit():
    """Test that history is limited to max_history."""
    memory = MemoryManager(max_history=3)

    for i in range(5):
        memory.add_interaction(f"Input {i}", f"Response {i}")

    # Should only keep last 3
    assert len(memory.interactions) == 3
    assert memory.interactions[0].user_input == "Input 2"
    assert memory.interactions[-1].user_input == "Input 4"


def test_get_recent_context():
    """Test getting recent context."""
    memory = MemoryManager()

    memory.add_interaction("What is AI?", "AI is artificial intelligence")
    memory.add_interaction("Tell me more", "AI involves machine learning...")

    context = memory.get_recent_context(num_interactions=2)

    assert "What is AI?" in context
    assert "AI is artificial intelligence" in context
    assert "Tell me more" in context


def test_get_messages_for_llm():
    """Test getting messages formatted for LLM."""
    memory = MemoryManager()

    memory.add_interaction("Hello", "Hi!")
    memory.add_interaction("How are you?", "I'm good!")

    messages = memory.get_messages_for_llm(num_interactions=2)

    assert len(messages) == 4  # 2 interactions = 4 messages (user + model)
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello"
    assert messages[1]["role"] == "model"
    assert messages[1]["content"] == "Hi!"


def test_update_and_get_context():
    """Test context variables."""
    memory = MemoryManager()

    memory.update_context("user_name", "Alice")
    memory.update_context("session_id", "123")

    assert memory.get_context("user_name") == "Alice"
    assert memory.get_context("session_id") == "123"
    assert memory.get_context("nonexistent", "default") == "default"


def test_clear_history():
    """Test clearing history."""
    memory = MemoryManager()

    memory.add_interaction("Test 1", "Response 1")
    memory.add_interaction("Test 2", "Response 2")

    assert len(memory.interactions) == 2

    memory.clear_history()

    assert len(memory.interactions) == 0


def test_search_interactions():
    """Test searching through interactions."""
    memory = MemoryManager()

    memory.add_interaction("What is AI?", "AI is artificial intelligence")
    memory.add_interaction("Tell me about ML", "ML is machine learning")
    memory.add_interaction("How does it work?", "Through algorithms and data")

    # Search for "AI"
    results = memory.search_interactions("AI")
    assert len(results) == 1
    assert "What is AI?" in results[0].user_input

    # Search for "machine"
    results = memory.search_interactions("machine")
    assert len(results) == 1
    assert "ML" in results[0].user_input


def test_get_summary():
    """Test getting memory summary."""
    memory = MemoryManager()

    memory.add_interaction("Test 1", "Response 1")
    memory.add_interaction("Test 2", "Response 2")
    memory.update_context("key1", "value1")

    summary = memory.get_summary()

    assert summary["total_interactions"] == 2
    assert "key1" in summary["context_keys"]
    assert summary["oldest_interaction"] is not None
    assert summary["newest_interaction"] is not None


def test_save_and_load_memory(temp_dir):
    """Test saving and loading memory."""
    memory = MemoryManager()

    memory.add_interaction("Hello", "Hi!")
    memory.add_interaction("Test", "Response")
    memory.update_context("key", "value")

    # Save
    save_path = temp_dir / "memory.json"
    memory.save(save_path)

    assert save_path.exists()

    # Load
    new_memory = MemoryManager()
    new_memory.load(save_path)

    assert len(new_memory.interactions) == 2
    assert new_memory.interactions[0].user_input == "Hello"
    assert new_memory.get_context("key") == "value"


def test_load_nonexistent_file(temp_dir):
    """Test loading from nonexistent file."""
    memory = MemoryManager()

    # Should not raise an error
    memory.load(temp_dir / "nonexistent.json")

    assert len(memory.interactions) == 0
