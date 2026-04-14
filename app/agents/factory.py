"""Agent factory for creating agent instances."""

from app.agents.base import BaseAgent, AgentType
from app.agents.qwen_agent import QwenAgent
from app.agents.codex_agent import CodexAgent
from app.core.logger import logger


class AgentFactory:
    """Factory for creating AI agent instances."""

    _registry: dict[AgentType, type[BaseAgent]] = {
        AgentType.QWEN: QwenAgent,
        AgentType.CODEX: CodexAgent,
    }

    @classmethod
    def create(cls, agent_type: AgentType, **kwargs) -> BaseAgent:
        """Create an agent instance by type."""
        agent_class = cls._registry.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")
        logger.info(f"Creating agent of type: {agent_type}")
        return agent_class(**kwargs)

    @classmethod
    def register(cls, agent_type: AgentType, agent_class: type[BaseAgent]) -> None:
        """Register a new agent type."""
        cls._registry[agent_type] = agent_class
        logger.info(f"Registered agent type: {agent_type}")

    @classmethod
    def get_available_agents(cls) -> list[AgentType]:
        """Get list of available agent types."""
        return list(cls._registry.keys())
