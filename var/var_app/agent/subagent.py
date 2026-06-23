from __future__ import annotations

from dataclasses import dataclass, field

from pydantic_ai import Agent

from var_app.agent.deps import AgentDeps
from var_app.model.client import resolve_api_key, create_model_client
from var_app.model.registry import get_provider_prefix, get_model_info
from var_app.logger import get_logger

logger = get_logger("agent.subagent")

EXPLORE_PROMPT = """\
你是一个代码库探索专家。你的任务是快速准确地查找文件、搜索代码模式、回答关于代码库结构的问题。

工作方式:
- 优先使用 glob 查找文件，使用 grep 搜索内容
- 不要修改任何文件（只读）
- 返回精确的文件路径和行号
- 完成后返回一份简洁、结构化的最终报告
- 彻底性级别：quick（基本搜索）、medium（适度探索）、very thorough（跨多个位置和命名规范的全面分析）

重要:
- 你是在子 Agent 中运行，结果会返回给父 Agent
- 只做研究/搜索，不做任何代码修改
- 在最终报告中包含所有发现的文件路径和关键信息\
"""

GENERAL_PROMPT = """\
你是一个通用多步骤研究代理。你可以执行多种独立的工作单元来回答复杂问题。

工作方式:
- 使用所有可用工具来完成任务
- 可以并行读取多个文件
- 返回完整、详细的结果报告

重要:
- 你是在子 Agent 中运行，结果会返回给父 Agent
- 在最终报告中包含所有关键发现和信息\
"""


@dataclass
class SubAgentDef:
    name: str
    description: str
    system_prompt: str
    allowed_tools: list[str] | None = None
    deny_tools: list[str] = field(default_factory=list)
    model_id: str | None = None


SUBAGENTS: dict[str, SubAgentDef] = {
    "explore": SubAgentDef(
        name="explore",
        description="快速代码库搜索专家，用于查找文件、搜索代码、回答代码库结构问题。"
        "指定彻底性级别：quick（基本搜索）、medium（适度探索）、very thorough（全面分析）。",
        system_prompt=EXPLORE_PROMPT,
        allowed_tools=["glob", "grep", "read_file", "run_command"],
        deny_tools=["write_file", "task"],
    ),
    "general": SubAgentDef(
        name="general",
        description="通用多步骤研究代理，用于并行执行多个独立的研究和编码任务。",
        system_prompt=GENERAL_PROMPT,
        allowed_tools=None,
        deny_tools=["task"],
    ),
}

_MAX_NESTING_DEPTH = 2


def get_subagent(name: str) -> SubAgentDef | None:
    return SUBAGENTS.get(name)


def list_subagents() -> list[SubAgentDef]:
    return list(SUBAGENTS.values())


def create_sub_agent(sub_def: SubAgentDef, model_id: str, work_dir: str) -> Agent:
    from var_app.agent.system_prompt import build_subagent_prompt

    model_info = get_model_info(model_id)
    model_string = get_provider_prefix(model_id)

    system_prompt = sub_def.system_prompt or build_subagent_prompt(work_dir)
    instructions = f"{system_prompt}\n\n工作目录: {work_dir}"

    if model_info and model_info.api_base:
        api_key = model_info.api_key or resolve_api_key(model_info.provider)
        model_obj = create_model_client(
            model_string, model_info.provider, api_key, model_info.api_base
        )
        agent = Agent(
            model_obj,
            instructions=instructions,
            deps_type=AgentDeps,
        )
    else:
        agent = Agent(
            model_string,
            instructions=instructions,
            deps_type=AgentDeps,
        )

    _register_filtered_tools(agent, sub_def)
    return agent


def _register_filtered_tools(agent: Agent, sub_def: SubAgentDef) -> None:
    from var_app.agent.tools import (
        register_file_tools,
        register_search_tools,
        register_skill_tools,
    )

    allowed = set(sub_def.allowed_tools) if sub_def.allowed_tools else None
    denied = set(sub_def.deny_tools)

    def _is_ok(name: str) -> bool:
        if name in denied:
            return False
        if allowed is not None:
            return name in allowed
        return True

    tool_groups = {
        "read_file": register_file_tools,
        "write_file": register_file_tools,
        "run_command": register_file_tools,
        "glob": register_search_tools,
        "grep": register_search_tools,
        "skill": register_skill_tools,
    }

    registered_groups: set[str] = set()
    for tool_name, register_fn in tool_groups.items():
        if _is_ok(tool_name) and register_fn.__name__ not in registered_groups:
            register_fn(agent)
            registered_groups.add(register_fn.__name__)
