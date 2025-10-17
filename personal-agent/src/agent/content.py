"""Content discovery and recommendation."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class ContentType(str, Enum):
    """Types of content."""
    ARTICLE = "article"
    VIDEO = "video"
    PAPER = "paper"
    PODCAST = "podcast"
    TWEET = "tweet"
    REDDIT = "reddit"
    GITHUB = "github"
    OTHER = "other"


@dataclass
class ContentItem:
    """A piece of discovered content."""
    title: str
    url: str
    content_type: ContentType
    description: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    score: float = 0.0
    discovered_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "content_type": self.content_type.value,
            "description": self.description,
            "source": self.source,
            "tags": self.tags,
            "score": self.score,
            "discovered_at": self.discovered_at.isoformat(),
            "metadata": self.metadata,
        }


class ContentDiscovery:
    """Content discovery and recommendation engine."""

    def __init__(self, llm=None):
        """Initialize content discovery.

        Args:
            llm: LLM instance for content analysis
        """
        self.llm = llm
        self.discovered_items: List[ContentItem] = []

    async def discover_for_user(
        self,
        user_profile,
        limit: int = 10
    ) -> List[ContentItem]:
        """Discover content tailored for a user.

        Args:
            user_profile: User profile with preferences
            limit: Maximum number of items to return

        Returns:
            List of content items
        """
        # This is a placeholder - in a real implementation, you would:
        # 1. Query various APIs (HackerNews, Reddit, Twitter, etc.)
        # 2. Use the LLM to analyze relevance
        # 3. Score and rank content
        # 4. Filter based on user preferences

        interests = user_profile.preferences.interests
        topics = user_profile.preferences.topics

        if self.llm:
            # Use LLM to generate content suggestions
            prompt = f"""Based on the following user interests and topics, suggest {limit} interesting
            content items (articles, videos, papers) that would be valuable.

            Interests: {', '.join(interests)}
            Topics: {', '.join(topics)}

            For each suggestion, provide:
            1. Title
            2. Brief description
            3. Why it would be interesting to this user

            Format as a numbered list."""

            response = await self.llm.generate(
                prompt=prompt,
                system_prompt="You are a content curator helping find interesting material."
            )

            # Parse the response and create ContentItems
            # This is simplified - you'd want better parsing
            items = self._parse_llm_suggestions(response.content)
            self.discovered_items.extend(items)
            return items[:limit]

        return []

    def _parse_llm_suggestions(self, text: str) -> List[ContentItem]:
        """Parse LLM output into content items.

        Args:
            text: LLM response text

        Returns:
            List of ContentItem
        """
        # Simplified parsing - in production you'd want structured output
        items = []
        lines = text.strip().split('\n')

        current_title = None
        current_desc = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Simple heuristic: numbered lines are titles
            if line[0].isdigit() and '.' in line[:3]:
                if current_title:
                    items.append(ContentItem(
                        title=current_title,
                        url="",  # Would need to be extracted or searched
                        content_type=ContentType.ARTICLE,
                        description='\n'.join(current_desc),
                    ))
                current_title = line.split('.', 1)[1].strip()
                current_desc = []
            else:
                current_desc.append(line)

        # Add last item
        if current_title:
            items.append(ContentItem(
                title=current_title,
                url="",
                content_type=ContentType.ARTICLE,
                description='\n'.join(current_desc),
            ))

        return items

    async def analyze_content(self, content_item: ContentItem) -> Dict[str, Any]:
        """Analyze a content item for relevance and quality.

        Args:
            content_item: Content item to analyze

        Returns:
            Analysis results
        """
        if not self.llm:
            return {"score": 0.5, "reasoning": "No LLM available"}

        prompt = f"""Analyze this content item:

        Title: {content_item.title}
        Description: {content_item.description}
        Type: {content_item.content_type.value}

        Provide:
        1. A relevance score (0-1)
        2. Key topics/themes
        3. Target audience
        4. Brief quality assessment
        """

        response = await self.llm.generate(prompt=prompt)

        return {
            "analysis": response.content,
            "score": 0.7,  # Would extract from response
        }

    def rank_content(
        self,
        items: List[ContentItem],
        user_profile
    ) -> List[ContentItem]:
        """Rank content items based on user preferences.

        Args:
            items: List of content items
            user_profile: User profile

        Returns:
            Sorted list of content items
        """
        interests = set(user_profile.preferences.interests)
        topics = set(user_profile.preferences.topics)

        for item in items:
            score = 0.5  # Base score

            # Boost score for matching interests/topics
            item_tags = set(item.tags)
            if item_tags & interests:
                score += 0.3
            if item_tags & topics:
                score += 0.2

            item.score = min(score, 1.0)

        return sorted(items, key=lambda x: x.score, reverse=True)

    def get_recent_discoveries(self, limit: int = 20) -> List[ContentItem]:
        """Get recent discovered items.

        Args:
            limit: Maximum number of items

        Returns:
            List of recent content items
        """
        return sorted(
            self.discovered_items,
            key=lambda x: x.discovered_at,
            reverse=True
        )[:limit]
