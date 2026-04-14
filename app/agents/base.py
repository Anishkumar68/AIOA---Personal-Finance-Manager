"""Base agent abstraction layer."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time


class AgentType(str, Enum):
    """Supported AI agent types."""
    QWEN = "qwen"
    CODEX = "codex"


class AgentRole(str, Enum):
    """Agent roles in a multi-agent setup."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Message:
    """Chat message structure."""
    role: AgentRole
    content: str
    metadata: dict = field(default_factory=dict)


@dataclass
class TaskRequest:
    """Request to execute an agent task."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: list[Message] = field(default_factory=list)
    agent_type: AgentType = AgentType.QWEN
    system_prompt: str = ""
    max_tokens: int | None = None
    temperature: float | None = None
    stream: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class TaskResponse:
    """Response from agent task execution."""
    task_id: str
    status: TaskStatus
    content: str = ""
    usage: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    error: str | None = None


@dataclass
class AgentCapabilities:
    """Agent capability description."""
    agent_type: AgentType
    model_name: str
    max_context_length: int
    supports_streaming: bool
    supports_function_calling: bool
    supports_vision: bool = False
    metadata: dict = field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base class for AI agents."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the agent connection/client."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Clean up agent resources."""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        system_prompt: str = "",
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> TaskResponse:
        """Execute a non-streaming chat completion."""
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[Message],
        system_prompt: str = "",
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> AsyncGenerator[str, None]:
        """Execute a streaming chat completion."""
        yield ""

    @abstractmethod
    async def get_capabilities(self) -> AgentCapabilities:
        """Return agent capabilities."""
        pass

    def _build_system_message(self, system_prompt: str) -> Message | None:
        """Helper to build system message."""
        if system_prompt:
            return Message(role=AgentRole.SYSTEM, content=system_prompt)
        return None

    def _format_messages(
        self,
        messages: list[Message],
        system_prompt: str = "",
    ) -> list[Message]:
        """Format messages with optional system prompt."""
        formatted = []
        system_msg = self._build_system_message(system_prompt)
        if system_msg:
            formatted.append(system_msg)
        formatted.extend(messages)
        return formatted
