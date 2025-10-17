"""User profile and preferences management."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path


@dataclass
class UserPreferences:
    """User preferences for content discovery."""
    interests: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=lambda: ["en"])
    content_types: List[str] = field(default_factory=lambda: ["article", "video", "paper"])
    excluded_keywords: List[str] = field(default_factory=list)
    time_of_day_preferences: Dict[str, Any] = field(default_factory=dict)
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserProfile:
    """User profile with learning history and preferences."""
    user_id: str
    name: str
    preferences: UserPreferences
    interaction_history: List[Dict[str, Any]] = field(default_factory=list)
    learned_patterns: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_interaction(self, interaction_type: str, content: Dict[str, Any]) -> None:
        """Record a user interaction.

        Args:
            interaction_type: Type of interaction (e.g., 'query', 'feedback', 'click')
            content: Interaction details
        """
        self.interaction_history.append({
            "type": interaction_type,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        self.updated_at = datetime.now()

    def update_preference(self, key: str, value: Any) -> None:
        """Update a user preference.

        Args:
            key: Preference key
            value: New value
        """
        if hasattr(self.preferences, key):
            setattr(self.preferences, key, value)
        else:
            self.preferences.custom_settings[key] = value
        self.updated_at = datetime.now()

    def add_interest(self, interest: str) -> None:
        """Add a new interest.

        Args:
            interest: Interest to add
        """
        if interest not in self.preferences.interests:
            self.preferences.interests.append(interest)
            self.updated_at = datetime.now()

    def remove_interest(self, interest: str) -> None:
        """Remove an interest.

        Args:
            interest: Interest to remove
        """
        if interest in self.preferences.interests:
            self.preferences.interests.remove(interest)
            self.updated_at = datetime.now()

    def save(self, file_path: Path) -> None:
        """Save profile to a JSON file.

        Args:
            file_path: Path to save the profile
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "user_id": self.user_id,
            "name": self.name,
            "preferences": {
                "interests": self.preferences.interests,
                "topics": self.preferences.topics,
                "languages": self.preferences.languages,
                "content_types": self.preferences.content_types,
                "excluded_keywords": self.preferences.excluded_keywords,
                "time_of_day_preferences": self.preferences.time_of_day_preferences,
                "custom_settings": self.preferences.custom_settings,
            },
            "interaction_history": self.interaction_history,
            "learned_patterns": self.learned_patterns,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, file_path: Path) -> "UserProfile":
        """Load profile from a JSON file.

        Args:
            file_path: Path to load the profile from

        Returns:
            UserProfile instance
        """
        with open(file_path, "r") as f:
            data = json.load(f)

        preferences = UserPreferences(**data["preferences"])

        return cls(
            user_id=data["user_id"],
            name=data["name"],
            preferences=preferences,
            interaction_history=data.get("interaction_history", []),
            learned_patterns=data.get("learned_patterns", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    @classmethod
    def create_default(cls, user_id: str = "default", name: str = "User") -> "UserProfile":
        """Create a default user profile.

        Args:
            user_id: User ID
            name: User name

        Returns:
            UserProfile with default settings
        """
        return cls(
            user_id=user_id,
            name=name,
            preferences=UserPreferences(),
        )
