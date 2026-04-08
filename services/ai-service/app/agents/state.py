"""Shared agent state definition for LangGraph agents."""

from typing import TypedDict


class AgentState(TypedDict, total=False):
    user_id: str
    user_profile: dict
    messages: list
    current_agent: str
    tools_used: list[str]
    agent_results: dict
    follow_up_actions: list[dict]
    language: str
    error: str | None
