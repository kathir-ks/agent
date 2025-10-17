"""Example usage of the LLM abstraction layer."""

import asyncio
import logging
from dotenv import load_dotenv
import os

from .base import LLMConfig, ModelProvider
from .factory import LLMFactory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_generate():
    """Example: Simple text generation."""
    load_dotenv()

    config = LLMConfig(
        provider=ModelProvider.GEMINI,
        model_name="gemini-pro",
        api_key=os.getenv("GEMINI_API_KEY", ""),
        temperature=0.7,
        max_tokens=1024,
    )

    async with LLMFactory.create(config) as llm:
        response = await llm.generate(
            prompt="What are 3 interesting facts about space exploration?",
            system_prompt="You are a helpful assistant that provides concise, interesting information."
        )

        print(f"\nModel: {response.model}")
        print(f"Response: {response.content}")
        print(f"Usage: {response.usage}")


async def example_chat():
    """Example: Multi-turn conversation."""
    load_dotenv()

    config = LLMConfig(
        provider=ModelProvider.GEMINI,
        model_name="gemini-pro",
        api_key=os.getenv("GEMINI_API_KEY", ""),
        temperature=0.8,
    )

    async with LLMFactory.create(config) as llm:
        messages = [
            {"role": "user", "content": "What's your favorite programming language?"},
            {"role": "model", "content": "I don't have personal preferences, but Python is very popular for its readability!"},
            {"role": "user", "content": "Can you explain why Python is good for beginners?"},
        ]

        response = await llm.chat(messages)

        print(f"\nChat Response: {response.content}")


async def example_streaming():
    """Example: Streaming response."""
    load_dotenv()

    config = LLMConfig(
        provider=ModelProvider.GEMINI,
        model_name="gemini-pro",
        api_key=os.getenv("GEMINI_API_KEY", ""),
    )

    async with LLMFactory.create(config) as llm:
        print("\nStreaming response:")
        async for chunk in llm.generate_stream(
            prompt="Write a short poem about artificial intelligence."
        ):
            print(chunk, end="", flush=True)
        print()


async def main():
    """Run all examples."""
    print("=== Example 1: Simple Generation ===")
    await example_generate()

    print("\n=== Example 2: Chat Conversation ===")
    await example_chat()

    print("\n=== Example 3: Streaming ===")
    await example_streaming()


if __name__ == "__main__":
    asyncio.run(main())
