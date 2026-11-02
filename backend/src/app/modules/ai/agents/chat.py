"""The general chat assistant."""

from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, ModelFallbackMiddleware

from app.config.settings import get_settings
from app.modules.ai import models
from app.modules.ai.agents.spec import AgentGraph, AgentSpec
from app.modules.ai.prompts.loader import load_prompt
from app.modules.ai.tools import INTERACTION_TOOLS, TOOLS
from app.modules.ai.tools.context import TurnContext
from app.modules.ai.tools.permissions import ToolPermissionMiddleware


def build(tool_names: frozenset[str]) -> AgentGraph:
    tools = [TOOLS[name] for name in sorted(tool_names & TOOLS.keys())]
    middleware: list[AgentMiddleware[Any, Any]] = [
        ToolPermissionMiddleware(frozenset(get_settings().tools_requiring_approval))
    ]
    if fallbacks := models.build_fallback_models():
        middleware.append(ModelFallbackMiddleware(*fallbacks))
    return create_agent(
        model=models.build_chat_model(),
        tools=[*tools, *INTERACTION_TOOLS.values()],
        system_prompt=load_prompt("chat"),
        context_schema=TurnContext,
        middleware=middleware,
    )


CHAT = AgentSpec(key="chat", version="chat-ai-v1", build=build)
