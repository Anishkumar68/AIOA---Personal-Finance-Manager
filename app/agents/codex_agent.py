"""OpenAI Codex agent implementation."""

import asyncio
from typing import AsyncGenerator

from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import ChatCompletionChunk

from app.agents.base import (
    BaseAgent,
    AgentCapabilities,
    AgentRole,
    AgentType,
    Message,
    TaskResponse,
    TaskStatus,
)
from app.core.config import settings
from app.core.logger import logger


class CodexAgent(BaseAgent):
    """OpenAI Codex agent for code generation and reasoning."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = base_url or settings.OPENAI_BASE_URL
        self.model = model or settings.CODEX_MODEL
        self._client: AsyncOpenAI | None = None

    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        if not self._client:
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
            logger.info(f"CodexAgent initialized with model: {self.model}")

    async def shutdown(self) -> None:
        """Clean up OpenAI client resources."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("CodexAgent shutdown complete")

    async def chat(
        self,
        messages: list[Message],
        system_prompt: str = "",
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> TaskResponse:
        """Execute non-streaming chat completion."""
        await self.initialize()

        formatted_messages = self._format_messages(messages, system_prompt)
        max_tokens = max_tokens or settings.CODEX_MAX_TOKENS
        temperature = temperature if temperature is not None else settings.CODEX_TEMPERATURE

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": msg.role.value, "content": msg.content}
                    for msg in formatted_messages
                ],
                max_completion_tokens=max_tokens,
                temperature=temperature,
            )

            choice = response.choices[0]
            return TaskResponse(
                task_id="",  # Will be set by caller
                status=TaskStatus.COMPLETED,
                content=choice.message.content or "",
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                } if response.usage else {},
            )

        except Exception as e:
            logger.error(f"Codex chat error: {e}")
            return TaskResponse(
                task_id="",
                status=TaskStatus.FAILED,
                error=str(e),
            )

    async def chat_stream(
        self,
        messages: list[Message],
        system_prompt: str = "",
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> AsyncGenerator[str, None]:
        """Execute streaming chat completion."""
        await self.initialize()

        formatted_messages = self._format_messages(messages, system_prompt)
        max_tokens = max_tokens or settings.CODEX_MAX_TOKENS
        temperature = temperature if temperature is not None else settings.CODEX_TEMPERATURE

        try:
            stream: AsyncStream[ChatCompletionChunk] = (
                await self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": msg.role.value, "content": msg.content}
                        for msg in formatted_messages
                    ],
                    max_completion_tokens=max_tokens,
                    temperature=temperature,
                    stream=True,
                )
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Codex stream error: {e}")
            yield f"[ERROR] {str(e)}"

    async def get_capabilities(self) -> AgentCapabilities:
        """Return Codex agent capabilities."""
        return AgentCapabilities(
            agent_type=AgentType.CODEX,
            model_name=self.model,
            max_context_length=128000,  # o1 model context window
            supports_streaming=True,
            supports_function_calling=True,
            supports_vision=False,
            metadata={
                "provider": "OpenAI",
                "base_url": self.base_url,
            },
        )
