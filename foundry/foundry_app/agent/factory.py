from pydantic_ai import Agent

from foundry_app.model.client import resolve_api_key, create_model_client
from foundry_app.model.registry import get_model_info, get_provider_prefix
from foundry_app.agent.deps import AgentDeps
from foundry_app.agent.system_prompt import build_system_prompt
from foundry_app.session.compaction import trim_and_summarize
from foundry_app.config import settings


def create_agent(model_id: str, system_prompt: str = "") -> Agent:
    model_info = get_model_info(model_id)
    model_string = get_provider_prefix(model_id)

    instructions = build_system_prompt(
        model_id, str(settings.work_dir), custom_prompt=system_prompt
    )

    if model_info and model_info.api_base:
        api_key = model_info.api_key or resolve_api_key(model_info.provider)
        model_obj = create_model_client(
            model_string, model_info.provider, api_key, model_info.api_base
        )
        agent = Agent(
            model_obj,
            instructions=instructions,
            deps_type=AgentDeps,
            history_processors=[trim_and_summarize],
        )
    else:
        agent = Agent(
            model_string,
            instructions=instructions,
            deps_type=AgentDeps,
            history_processors=[trim_and_summarize],
        )
    _register_tools(agent)
    return agent


def _register_tools(agent: Agent):
    from foundry_app.agent.tools import register_file_tools, register_search_tools, register_skill_tools
    from foundry_app.agent.subagent_tools import register_task_tools
    from foundry_app.agent.todo_tools import register_todo_tools

    register_file_tools(agent)
    register_search_tools(agent)
    register_skill_tools(agent)
    register_task_tools(agent)
    register_todo_tools(agent)
