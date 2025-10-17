"""Tests for content discovery."""

import pytest
from datetime import datetime

from src.agent.content import ContentDiscovery, ContentItem, ContentType
from src.agent.profile import UserProfile


def test_content_type_enum():
    """Test content type enum."""
    assert ContentType.ARTICLE == "article"
    assert ContentType.VIDEO == "video"
    assert ContentType.PAPER == "paper"


def test_content_item_creation():
    """Test creating a content item."""
    item = ContentItem(
        title="Test Article",
        url="https://example.com/article",
        content_type=ContentType.ARTICLE,
        description="A test article",
        source="example.com",
        tags=["test", "article"],
        score=0.85,
    )

    assert item.title == "Test Article"
    assert item.url == "https://example.com/article"
    assert item.content_type == ContentType.ARTICLE
    assert item.description == "A test article"
    assert "test" in item.tags
    assert item.score == 0.85


def test_content_item_to_dict():
    """Test converting content item to dictionary."""
    item = ContentItem(
        title="Test",
        url="https://test.com",
        content_type=ContentType.VIDEO,
    )

    data = item.to_dict()

    assert data["title"] == "Test"
    assert data["url"] == "https://test.com"
    assert data["content_type"] == "video"
    assert "discovered_at" in data


def test_content_discovery_creation():
    """Test creating content discovery instance."""
    discovery = ContentDiscovery()

    assert discovery.llm is None
    assert len(discovery.discovered_items) == 0


def test_content_discovery_with_llm(mock_llm):
    """Test content discovery with LLM."""
    discovery = ContentDiscovery(llm=mock_llm)

    assert discovery.llm == mock_llm


@pytest.mark.asyncio
async def test_discover_for_user(mock_llm):
    """Test discovering content for a user."""
    profile = UserProfile.create_default()
    profile.add_interest("AI")
    profile.add_interest("Python")

    discovery = ContentDiscovery(llm=mock_llm)

    items = await discovery.discover_for_user(profile, limit=5)

    # Mock LLM should return some items
    assert isinstance(items, list)
    # The mock implementation will parse the response
    # Check that LLM was called
    assert mock_llm.call_count >= 1


@pytest.mark.asyncio
async def test_discover_without_llm():
    """Test discovering content without LLM."""
    profile = UserProfile.create_default()
    profile.add_interest("AI")

    discovery = ContentDiscovery(llm=None)

    items = await discovery.discover_for_user(profile, limit=5)

    # Without LLM, should return empty list
    assert items == []


def test_rank_content():
    """Test ranking content items."""
    profile = UserProfile.create_default()
    profile.add_interest("AI")
    profile.add_interest("Python")

    items = [
        ContentItem(
            title="Python Tutorial",
            url="https://test.com/1",
            content_type=ContentType.ARTICLE,
            tags=["Python", "programming"],
        ),
        ContentItem(
            title="Java Guide",
            url="https://test.com/2",
            content_type=ContentType.ARTICLE,
            tags=["Java", "programming"],
        ),
        ContentItem(
            title="AI Research",
            url="https://test.com/3",
            content_type=ContentType.PAPER,
            tags=["AI", "research"],
        ),
    ]

    discovery = ContentDiscovery()
    ranked = discovery.rank_content(items, profile)

    # Items with matching interests should rank higher
    assert ranked[0].score > 0.5  # Should have boosted score
    # Check that items are sorted by score
    for i in range(len(ranked) - 1):
        assert ranked[i].score >= ranked[i + 1].score


def test_get_recent_discoveries():
    """Test getting recent discoveries."""
    discovery = ContentDiscovery()

    # Add some items
    for i in range(10):
        item = ContentItem(
            title=f"Item {i}",
            url=f"https://test.com/{i}",
            content_type=ContentType.ARTICLE,
        )
        discovery.discovered_items.append(item)

    # Get recent (default limit 20)
    recent = discovery.get_recent_discoveries(limit=5)

    assert len(recent) == 5
    # Should be in reverse chronological order (newest first)
    assert recent[0].title == "Item 9"


@pytest.mark.asyncio
async def test_analyze_content(mock_llm):
    """Test analyzing a content item."""
    item = ContentItem(
        title="AI Breakthrough",
        url="https://test.com",
        content_type=ContentType.ARTICLE,
        description="Amazing AI discovery",
    )

    discovery = ContentDiscovery(llm=mock_llm)

    analysis = await discovery.analyze_content(item)

    assert isinstance(analysis, dict)
    assert "analysis" in analysis or "score" in analysis


@pytest.mark.asyncio
async def test_analyze_content_without_llm():
    """Test analyzing content without LLM."""
    item = ContentItem(
        title="Test",
        url="https://test.com",
        content_type=ContentType.ARTICLE,
    )

    discovery = ContentDiscovery(llm=None)

    analysis = await discovery.analyze_content(item)

    assert "No LLM available" in analysis["reasoning"]


def test_parse_llm_suggestions():
    """Test parsing LLM suggestions."""
    discovery = ContentDiscovery()

    text = """
    1. Quantum Computing Breakthrough
    This is an amazing discovery in quantum computing that could revolutionize the field.

    2. New Python Framework Released
    A new framework that makes development easier.

    3. AI Ethics Guidelines Published
    Important guidelines for responsible AI development.
    """

    items = discovery._parse_llm_suggestions(text)

    assert len(items) >= 2  # Should parse at least some items
    for item in items:
        assert isinstance(item, ContentItem)
        assert item.title
        assert item.content_type == ContentType.ARTICLE
