"""Core agent brain - orchestrates all agent functionality."""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from .profile import UserProfile
from .content import ContentDiscovery
from .memory import MemoryManager
from ..llm import BaseLLM

logger = logging.getLogger(__name__)


class AgentBrain:
    """Main agent orchestrator that ties everything together."""

    def __init__(
        self,
        llm: BaseLLM,
        user_profile: Optional[UserProfile] = None,
        data_dir: Optional[Path] = None
    ):
        """Initialize the agent brain.

        Args:
            llm: LLM instance
            user_profile: User profile (creates default if None)
            data_dir: Directory for storing data
        """
        self.llm = llm
        self.user_profile = user_profile or UserProfile.create_default()
        self.data_dir = data_dir or Path("./data")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.memory = MemoryManager()
        self.content_discovery = ContentDiscovery(llm=llm)

        # Load saved data if available
        self._load_state()

        logger.info(f"Agent brain initialized for user: {self.user_profile.name}")

    def _load_state(self) -> None:
        """Load saved state from disk."""
        profile_path = self.data_dir / f"profile_{self.user_profile.user_id}.json"
        memory_path = self.data_dir / f"memory_{self.user_profile.user_id}.json"

        if profile_path.exists():
            try:
                self.user_profile = UserProfile.load(profile_path)
                logger.info("Loaded user profile from disk")
            except Exception as e:
                logger.warning(f"Failed to load profile: {e}")

        if memory_path.exists():
            try:
                self.memory.load(memory_path)
                logger.info("Loaded memory from disk")
            except Exception as e:
                logger.warning(f"Failed to load memory: {e}")

    def _save_state(self) -> None:
        """Save current state to disk."""
        profile_path = self.data_dir / f"profile_{self.user_profile.user_id}.json"
        memory_path = self.data_dir / f"memory_{self.user_profile.user_id}.json"

        try:
            self.user_profile.save(profile_path)
            self.memory.save(memory_path)
            logger.debug("Saved state to disk")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    async def process_message(self, user_message: str) -> str:
        """Process a user message and generate a response.

        Args:
            user_message: User's input message

        Returns:
            Agent's response
        """
        logger.info(f"Processing message: {user_message[:50]}...")

        # Build context from memory
        recent_context = self.memory.get_recent_context(num_interactions=5)

        # Build system prompt with user context
        system_prompt = self._build_system_prompt()

        # Get messages for context
        messages = self.memory.get_messages_for_llm(num_interactions=5)
        messages.append({"role": "user", "content": user_message})

        try:
            # Generate response using LLM
            response = await self.llm.chat(messages)

            # Record interaction
            self.memory.add_interaction(user_message, response.content)
            self.user_profile.add_interaction("message", {
                "input": user_message,
                "output": response.content
            })

            # Save state
            self._save_state()

            return response.content

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_msg = "I apologize, but I encountered an error processing your message. Please try again."
            self.memory.add_interaction(user_message, error_msg)
            return error_msg

    async def discover_content(self, limit: int = 10) -> list:
        """Discover interesting content for the user.

        Args:
            limit: Maximum number of items to discover

        Returns:
            List of content items
        """
        logger.info(f"Discovering content for user (limit={limit})")

        try:
            items = await self.content_discovery.discover_for_user(
                self.user_profile,
                limit=limit
            )

            # Rank items
            ranked_items = self.content_discovery.rank_content(items, self.user_profile)

            # Record discovery
            self.user_profile.add_interaction("content_discovery", {
                "count": len(ranked_items),
                "top_item": ranked_items[0].title if ranked_items else None
            })

            self._save_state()

            return ranked_items

        except Exception as e:
            logger.error(f"Error discovering content: {e}")
            return []

    async def understand_user(self) -> str:
        """Analyze user interactions to better understand them.

        Returns:
            Understanding summary
        """
        logger.info("Analyzing user to improve understanding")

        if not self.memory.interactions:
            return "Not enough interaction history to analyze yet."

        # Build a summary of interactions
        interaction_summary = "\n".join([
            f"User: {i.user_input}\nAgent: {i.agent_response}"
            for i in self.memory.interactions[-10:]
        ])

        prompt = f"""Analyze these recent interactions with the user and provide insights:

{interaction_summary}

Current interests: {', '.join(self.user_profile.preferences.interests)}
Current topics: {', '.join(self.user_profile.preferences.topics)}

Provide:
1. What the user seems interested in
2. Patterns in their questions/interactions
3. Suggested interests to add
4. How to better assist them
"""

        try:
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt="You are an AI analyzing user behavior to provide better personalized assistance."
            )

            return response.content

        except Exception as e:
            logger.error(f"Error understanding user: {e}")
            return "Unable to analyze user at this time."

    def _build_system_prompt(self) -> str:
        """Build a system prompt with user context.

        Returns:
            System prompt string
        """
        interests = ", ".join(self.user_profile.preferences.interests) or "not specified"
        topics = ", ".join(self.user_profile.preferences.topics) or "not specified"

        return f"""You are {self.user_profile.name}'s personal AI assistant and co-pilot.

Your role is to:
- Help them understand and solve problems
- Discover interesting content related to their interests
- Learn their preferences and adapt to their needs
- Be proactive in suggesting relevant information

User profile:
- Name: {self.user_profile.name}
- Interests: {interests}
- Topics: {topics}

Be conversational, helpful, and personalized in your responses."""

    def add_interest(self, interest: str) -> None:
        """Add a new interest for the user.

        Args:
            interest: Interest to add
        """
        self.user_profile.add_interest(interest)
        self._save_state()
        logger.info(f"Added interest: {interest}")

    def remove_interest(self, interest: str) -> None:
        """Remove an interest.

        Args:
            interest: Interest to remove
        """
        self.user_profile.remove_interest(interest)
        self._save_state()
        logger.info(f"Removed interest: {interest}")

    def get_status(self) -> Dict[str, Any]:
        """Get agent status and statistics.

        Returns:
            Status dictionary
        """
        return {
            "user": self.user_profile.name,
            "interests": self.user_profile.preferences.interests,
            "topics": self.user_profile.preferences.topics,
            "memory": self.memory.get_summary(),
            "discovered_content_count": len(self.content_discovery.discovered_items),
        }

    async def close(self) -> None:
        """Clean up and save state."""
        self._save_state()
        await self.llm.close()
        logger.info("Agent brain closed")
