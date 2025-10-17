"""Google Gemini LLM implementation."""

import logging
from typing import Optional, List, Dict, Any
import google.generativeai as genai

from .base import BaseLLM, LLMConfig, LLMResponse, ModelProvider

logger = logging.getLogger(__name__)


class GeminiLLM(BaseLLM):
    """Google Gemini LLM implementation."""

    async def initialize(self) -> None:
        """Initialize the Gemini client."""
        try:
            genai.configure(api_key=self.config.api_key)

            # Configure generation settings
            generation_config = {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "max_output_tokens": self.config.max_tokens,
            }

            if self.config.top_k:
                generation_config["top_k"] = self.config.top_k

            if self.config.stop_sequences:
                generation_config["stop_sequences"] = self.config.stop_sequences

            # Apply extra params if provided
            if self.config.extra_params:
                generation_config.update(self.config.extra_params)

            # Initialize the model
            self._client = genai.GenerativeModel(
                model_name=self.config.model_name,
                generation_config=generation_config,
            )

            logger.info(f"Initialized Gemini model: {self.config.model_name}")

        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            raise

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from Gemini.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt (prepended to prompt)
            **kwargs: Additional Gemini-specific parameters

        Returns:
            LLMResponse with the generated content
        """
        if not self._client:
            await self.initialize()

        try:
            # Combine system prompt with user prompt if provided
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

            # Generate content
            response = await self._client.generate_content_async(full_prompt)

            # Extract usage information if available
            usage = None
            if hasattr(response, 'usage_metadata'):
                usage = {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count,
                }

            return LLMResponse(
                content=response.text,
                model=self.config.model_name,
                provider=ModelProvider.GEMINI,
                usage=usage,
                finish_reason=response.candidates[0].finish_reason.name if response.candidates else None,
                raw_response=response,
            )

        except Exception as e:
            logger.error(f"Error generating content with Gemini: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        """Generate a streaming response from Gemini.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            **kwargs: Additional Gemini-specific parameters

        Yields:
            Chunks of the generated content
        """
        if not self._client:
            await self.initialize()

        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

            response = await self._client.generate_content_async(
                full_prompt,
                stream=True
            )

            async for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Error streaming content with Gemini: {e}")
            raise

    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """Have a multi-turn conversation with Gemini.

        Args:
            messages: List of messages with 'role' and 'content'
                     role can be 'user' or 'model' (Gemini terminology)
            **kwargs: Additional Gemini-specific parameters

        Returns:
            LLMResponse with the generated content
        """
        if not self._client:
            await self.initialize()

        try:
            # Start a chat session
            chat = self._client.start_chat(history=[])

            # Convert messages to Gemini format and build history
            gemini_history = []
            last_message = None

            for msg in messages:
                role = msg["role"]
                content = msg["content"]

                # Convert 'assistant' or 'ai' to 'model' for Gemini
                if role in ["assistant", "ai"]:
                    role = "model"
                elif role == "system":
                    # System messages can be prepended to the first user message
                    continue

                if role in ["user", "model"]:
                    gemini_history.append({
                        "role": role,
                        "parts": [content]
                    })
                    last_message = content

            # Set the history (excluding the last user message)
            if len(gemini_history) > 1:
                chat = self._client.start_chat(history=gemini_history[:-1])
                last_message = gemini_history[-1]["parts"][0]
            else:
                last_message = gemini_history[0]["parts"][0] if gemini_history else ""

            # Send the last message
            response = await chat.send_message_async(last_message)

            # Extract usage information if available
            usage = None
            if hasattr(response, 'usage_metadata'):
                usage = {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count,
                }

            return LLMResponse(
                content=response.text,
                model=self.config.model_name,
                provider=ModelProvider.GEMINI,
                usage=usage,
                finish_reason=response.candidates[0].finish_reason.name if response.candidates else None,
                raw_response=response,
            )

        except Exception as e:
            logger.error(f"Error in chat with Gemini: {e}")
            raise

    async def close(self) -> None:
        """Clean up resources."""
        self._client = None
        logger.info("Closed Gemini client")
