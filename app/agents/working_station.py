"""Agent Working Station - Orchestrates AI agent tasks."""

import asyncio
from typing import AsyncGenerator
from collections import defaultdict

from app.agents.base import (
    BaseAgent,
    AgentType,
    Message,
    TaskRequest,
    TaskResponse,
    TaskStatus,
    AgentCapabilities,
    AgentRole,
)
from app.agents.factory import AgentFactory
from app.core.config import settings
from app.core.logger import logger


class AgentWorkingStation:
    """
    Central orchestration layer for managing multiple AI agents.
    
    Handles task routing, execution, caching, and multi-agent workflows.
    """

    def __init__(self):
        self._agents: dict[AgentType, BaseAgent] = {}
        self._task_history: dict[str, TaskResponse] = {}
        self._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_AGENTS)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all registered agents."""
        if self._initialized:
            return

        for agent_type in AgentFactory.get_available_agents():
            try:
                agent = AgentFactory.create(agent_type)
                await agent.initialize()
                self._agents[agent_type] = agent
                logger.info(f"Initialized agent: {agent_type}")
            except Exception as e:
                logger.error(f"Failed to initialize agent {agent_type}: {e}")

        self._initialized = True
        logger.info("AgentWorkingStation initialized")

    async def shutdown(self) -> None:
        """Shutdown all agents."""
        for agent_type, agent in self._agents.items():
            try:
                await agent.shutdown()
                logger.info(f"Shutdown agent: {agent_type}")
            except Exception as e:
                logger.error(f"Error shutting down {agent_type}: {e}")
        
        self._agents.clear()
        self._initialized = False
        logger.info("AgentWorkingStation shutdown complete")

    async def execute_task(self, request: TaskRequest) -> TaskResponse:
        """Execute a single task with the specified agent."""
        async with self._semaphore:
            agent = self._get_agent(request.agent_type)
            if not agent:
                return TaskResponse(
                    task_id=request.task_id,
                    status=TaskStatus.FAILED,
                    error=f"Agent {request.agent_type} not available",
                )

            logger.info(
                f"Executing task {request.task_id} with {request.agent_type}"
            )

            try:
                if request.stream:
                    # Streaming handled separately
                    response = await agent.chat(
                        messages=request.messages,
                        system_prompt=request.system_prompt,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                    )
                else:
                    response = await agent.chat(
                        messages=request.messages,
                        system_prompt=request.system_prompt,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                    )

                response.task_id = request.task_id
                response.completed_at = response.completed_at or response.created_at
                
                # Store in history
                self._task_history[request.task_id] = response
                
                return response

            except Exception as e:
                logger.error(f"Task {request.task_id} failed: {e}")
                error_response = TaskResponse(
                    task_id=request.task_id,
                    status=TaskStatus.FAILED,
                    error=str(e),
                )
                self._task_history[request.task_id] = error_response
                return error_response

    async def execute_task_stream(
        self, request: TaskRequest
    ) -> AsyncGenerator[str, None]:
        """Execute a task with streaming response."""
        async with self._semaphore:
            agent = self._get_agent(request.agent_type)
            if not agent:
                yield f"[ERROR] Agent {request.agent_type} not available"
                return

            logger.info(
                f"Streaming task {request.task_id} with {request.agent_type}"
            )

            async for chunk in agent.chat_stream(
                messages=request.messages,
                system_prompt=request.system_prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            ):
                yield chunk

    async def execute_multi_agent_workflow(
        self,
        prompt: str,
        agent_sequence: list[AgentType],
        system_prompts: dict[AgentType, str] | None = None,
    ) -> dict[str, TaskResponse]:
        """
        Execute a workflow across multiple agents in sequence.
        Each agent receives the previous agent's output as context.
        """
        results = {}
        current_context = prompt

        for agent_type in agent_sequence:
            system_prompt = ""
            if system_prompts and agent_type in system_prompts:
                system_prompt = system_prompts[agent_type]

            request = TaskRequest(
                messages=[Message(role=AgentRole.USER, content=current_context)],
                agent_type=agent_type,
                system_prompt=system_prompt,
            )

            response = await self.execute_task(request)
            results[agent_type.value] = response

            if response.status == TaskStatus.FAILED:
                logger.error(
                    f"Workflow failed at {agent_type}: {response.error}"
                )
                break

            # Pass output to next agent as context
            current_context = (
                f"Previous agent ({agent_type.value}) response:\n"
                f"{response.content}\n\n"
                f"Continue with this context."
            )

        return results

    async def get_agent_capabilities(
        self, agent_type: AgentType
    ) -> AgentCapabilities | None:
        """Get capabilities of a specific agent."""
        agent = self._get_agent(agent_type)
        if agent:
            return await agent.get_capabilities()
        return None

    async def get_all_capabilities(self) -> dict[str, AgentCapabilities]:
        """Get capabilities of all available agents."""
        capabilities = {}
        for agent_type in self._agents:
            caps = await self.get_agent_capabilities(agent_type)
            if caps:
                capabilities[agent_type.value] = caps
        return capabilities

    def get_task_history(self, task_id: str | None = None) -> dict:
        """Retrieve task history."""
        if task_id:
            return {task_id: self._task_history.get(task_id)}
        return dict(self._task_history)

    def _get_agent(self, agent_type: AgentType) -> BaseAgent | None:
        """Get agent instance by type."""
        return self._agents.get(agent_type)


# Singleton instance
working_station = AgentWorkingStation()
