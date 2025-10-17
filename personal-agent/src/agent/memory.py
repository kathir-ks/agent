"""Memory and context management for the agent."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path


@dataclass
class Interaction:
    """A single interaction with the agent."""
    user_input: str
    agent_response: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_input": self.user_input,
            "agent_response": self.agent_response,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class MemoryManager:
    """Manages conversation history and context."""

    def __init__(self, max_history: int = 50):
        """Initialize memory manager.

        Args:
            max_history: Maximum number of interactions to keep
        """
        self.max_history = max_history
        self.interactions: List[Interaction] = []
        self.context: Dict[str, Any] = {}

    def add_interaction(
        self,
        user_input: str,
        agent_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a new interaction to memory.

        Args:
            user_input: User's input
            agent_response: Agent's response
            metadata: Optional metadata
        """
        interaction = Interaction(
            user_input=user_input,
            agent_response=agent_response,
            metadata=metadata or {}
        )
        self.interactions.append(interaction)

        # Trim history if needed
        if len(self.interactions) > self.max_history:
            self.interactions = self.interactions[-self.max_history:]

    def get_recent_context(self, num_interactions: int = 5) -> str:
        """Get recent conversation context as a formatted string.

        Args:
            num_interactions: Number of recent interactions to include

        Returns:
            Formatted context string
        """
        recent = self.interactions[-num_interactions:]
        if not recent:
            return "No previous context."

        lines = ["Recent conversation:"]
        for i, interaction in enumerate(recent, 1):
            lines.append(f"\n{i}. User: {interaction.user_input}")
            lines.append(f"   Agent: {interaction.agent_response}")

        return "\n".join(lines)

    def get_messages_for_llm(self, num_interactions: int = 5) -> List[Dict[str, str]]:
        """Get recent interactions formatted for LLM chat.

        Args:
            num_interactions: Number of recent interactions to include

        Returns:
            List of message dictionaries
        """
        recent = self.interactions[-num_interactions:]
        messages = []

        for interaction in recent:
            messages.append({"role": "user", "content": interaction.user_input})
            messages.append({"role": "model", "content": interaction.agent_response})

        return messages

    def update_context(self, key: str, value: Any) -> None:
        """Update a context variable.

        Args:
            key: Context key
            value: Context value
        """
        self.context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a context variable.

        Args:
            key: Context key
            default: Default value if key not found

        Returns:
            Context value or default
        """
        return self.context.get(key, default)

    def clear_history(self) -> None:
        """Clear all interaction history."""
        self.interactions.clear()

    def save(self, file_path: Path) -> None:
        """Save memory to a file.

        Args:
            file_path: Path to save memory
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "interactions": [i.to_dict() for i in self.interactions],
            "context": self.context,
        }

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, file_path: Path) -> None:
        """Load memory from a file.

        Args:
            file_path: Path to load memory from
        """
        if not file_path.exists():
            return

        with open(file_path, "r") as f:
            data = json.load(f)

        self.interactions = [
            Interaction(
                user_input=i["user_input"],
                agent_response=i["agent_response"],
                timestamp=datetime.fromisoformat(i["timestamp"]),
                metadata=i.get("metadata", {}),
            )
            for i in data.get("interactions", [])
        ]

        self.context = data.get("context", {})

    def search_interactions(self, query: str) -> List[Interaction]:
        """Search through interaction history.

        Args:
            query: Search query

        Returns:
            List of matching interactions
        """
        query_lower = query.lower()
        return [
            i for i in self.interactions
            if query_lower in i.user_input.lower() or query_lower in i.agent_response.lower()
        ]

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the memory state.

        Returns:
            Dictionary with memory statistics
        """
        return {
            "total_interactions": len(self.interactions),
            "context_keys": list(self.context.keys()),
            "oldest_interaction": self.interactions[0].timestamp.isoformat() if self.interactions else None,
            "newest_interaction": self.interactions[-1].timestamp.isoformat() if self.interactions else None,
        }
