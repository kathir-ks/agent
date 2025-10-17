"""Tests for user profile and preferences."""

import pytest
from datetime import datetime
from pathlib import Path

from src.agent.profile import UserProfile, UserPreferences


def test_user_preferences_creation():
    """Test creating user preferences."""
    prefs = UserPreferences(
        interests=["AI", "Programming"],
        topics=["Machine Learning", "Python"],
        languages=["en", "es"],
    )

    assert "AI" in prefs.interests
    assert "Programming" in prefs.interests
    assert "Machine Learning" in prefs.topics
    assert "en" in prefs.languages


def test_user_preferences_defaults():
    """Test default user preferences."""
    prefs = UserPreferences()

    assert prefs.interests == []
    assert prefs.topics == []
    assert prefs.languages == ["en"]
    assert prefs.content_types == ["article", "video", "paper"]


def test_user_profile_creation():
    """Test creating a user profile."""
    prefs = UserPreferences(interests=["AI"])
    profile = UserProfile(
        user_id="test123",
        name="Test User",
        preferences=prefs,
    )

    assert profile.user_id == "test123"
    assert profile.name == "Test User"
    assert profile.preferences == prefs
    assert len(profile.interaction_history) == 0


def test_user_profile_default_creation():
    """Test creating a default profile."""
    profile = UserProfile.create_default("test_user", "Test Name")

    assert profile.user_id == "test_user"
    assert profile.name == "Test Name"
    assert isinstance(profile.preferences, UserPreferences)


def test_add_interest():
    """Test adding an interest."""
    profile = UserProfile.create_default()

    profile.add_interest("Quantum Computing")
    assert "Quantum Computing" in profile.preferences.interests

    # Adding duplicate should not create duplicates
    profile.add_interest("Quantum Computing")
    assert profile.preferences.interests.count("Quantum Computing") == 1


def test_remove_interest():
    """Test removing an interest."""
    profile = UserProfile.create_default()
    profile.add_interest("AI")
    profile.add_interest("ML")

    profile.remove_interest("AI")
    assert "AI" not in profile.preferences.interests
    assert "ML" in profile.preferences.interests


def test_add_interaction():
    """Test adding an interaction."""
    profile = UserProfile.create_default()

    profile.add_interaction("query", {"text": "What is AI?"})

    assert len(profile.interaction_history) == 1
    assert profile.interaction_history[0]["type"] == "query"
    assert profile.interaction_history[0]["content"]["text"] == "What is AI?"
    assert "timestamp" in profile.interaction_history[0]


def test_update_preference():
    """Test updating preferences."""
    profile = UserProfile.create_default()

    profile.update_preference("languages", ["en", "fr"])
    assert profile.preferences.languages == ["en", "fr"]

    # Custom settings
    profile.update_preference("custom_key", "custom_value")
    assert profile.preferences.custom_settings["custom_key"] == "custom_value"


def test_save_and_load_profile(temp_dir):
    """Test saving and loading a profile."""
    profile = UserProfile.create_default("test123", "Test User")
    profile.add_interest("AI")
    profile.add_interest("ML")
    profile.add_interaction("query", {"text": "Hello"})

    # Save
    save_path = temp_dir / "profile.json"
    profile.save(save_path)

    assert save_path.exists()

    # Load
    loaded_profile = UserProfile.load(save_path)

    assert loaded_profile.user_id == profile.user_id
    assert loaded_profile.name == profile.name
    assert loaded_profile.preferences.interests == profile.preferences.interests
    assert len(loaded_profile.interaction_history) == len(profile.interaction_history)


def test_profile_timestamps():
    """Test profile timestamps."""
    profile = UserProfile.create_default()

    created_at = profile.created_at
    updated_at = profile.updated_at

    assert isinstance(created_at, datetime)
    assert isinstance(updated_at, datetime)

    # After update, updated_at should change
    import time
    time.sleep(0.01)
    profile.add_interest("New Interest")

    assert profile.updated_at > updated_at
    assert profile.created_at == created_at  # Should not change


def test_learned_patterns():
    """Test learned patterns storage."""
    profile = UserProfile.create_default()

    profile.learned_patterns["preference_1"] = "value_1"
    profile.learned_patterns["preference_2"] = "value_2"

    assert len(profile.learned_patterns) == 2
    assert profile.learned_patterns["preference_1"] == "value_1"
