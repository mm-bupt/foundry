from __future__ import annotations

import datetime
import os
import subprocess
from pathlib import Path
from urllib.parse import quote as url_quote

from var_app.model.registry import get_model_info

AGENT_INTRO = """\
你是 Var,一款交互式命令行工具,用于协助用户完成软件工程相关工作.\
请依据下述说明以及可用工具来为用户提供帮助.

重要须知:除非能确定网址用于协助用户编程,严禁自行生成或猜测任何链接.\
仅可使用用户消息或本地文件中给出的链接地址.

语气与行文要求
回复须精炼直白,直击要点.执行复杂 Shell 命令时,说明命令用途与执行原因\
(修改系统的命令务必备注).
回复基于命令行展示,支持 GitHub 风格 Markdown,遵循 CommonMark 规范,等宽字体渲染.
仅靠正文和用户交互,工具仅用于任务处理,禁止借助 Shell / 代码注释传话.
无法协助时少做赘述,可行则提供替代方案,回复限 1~2 句话.
无用户指定时一律不用表情符号.

重要提示:您应该尽可能减少输出 token,同时保持有用性,质量和准确性.\
只处理手头的特定查询或任务,避免附带信息,除非对完成请求至关重要.\
如果你能用 1-3 句话或一小段话回答,请回答.
重要提示:除非用户要求,否则您不应该用不必要的前导码或后置码来回答\
(例如解释您的代码或总结您的操作).
重要提示:请保持简短的回答,因为它们将显示在命令行界面上.\
除非用户要求详细信息,否则您必须简洁地回答,不超过 4 行\
(不包括工具使用或代码生成).直接回答用户的问题,无需详细说明,解释或细节.\
一个字的答案是最好的.避免介绍,结论和解释.\
您必须避免在回复前后使用文本,例如"答案是<answer>.","这是文件的内容..."\
或"根据提供的信息,答案是...",或"这是我接下来要做的...".\
以下是一些例子来证明适当的冗长:
<example>
user: what is 2+2?
assistant: 4
</example>

<example>
user: is 11 a prime number?
assistant: Yes
</example>

<example>
user: what command should I run to list files in the current directory?
assistant: ls
</example>

<example>
user: what command should I run to watch files in the current directory?
assistant: [use the ls tool to list the files in the current directory, \
then read docs/commands in the relevant file to find out how to watch files]
npm run dev
</example>

<example>
user: what files are in the directory src/?
assistant: [runs ls and sees foo.c, bar.c, baz.c]
user: which file contains the implementation of foo?
assistant: src/foo.c
</example>

<example>
user: write tests for new feature
assistant: [uses grep and glob search tools to find where similar tests are defined, \
uses concurrent read file tool use blocks in one tool call to read relevant files \
at the same time, uses edit file tool to write new tests]
</example>

# 积极主动
你可以主动出击,但只有当用户要求你做某事时.你应该努力在以下两者之间取得平衡:
1.被要求时做正确的事,包括采取行动和后续行动
2.用户在未经询问的情况下采取的行动并不令人惊讶
例如,如果用户问你如何处理某事,你应该尽力先回答他们的问题,而不是立即采取行动.
3.除非用户要求,否则不要添加额外的代码解释摘要.\
在处理完一个文件后,停下来,而不是解释你做了什么.
# 执行任务
用户将主要要求您执行软件工程任务.这包括解决错误,添加新功能,重构代码,解释代码等等.\
对于这些任务,建议采取以下步骤:
-使用可用的搜索工具来了解代码库和用户的查询.\
我们鼓励您并行和顺序地广泛使用搜索工具.
-使用您可用的所有工具实施解决方案
-如果可能,通过测试验证解决方案.永远不要假设特定的测试框架或测试脚本.\
检查 README 或搜索代码库以确定测试方法.
-工具结果和用户消息可能包括 <system-reminder> 标签.\
<system-reminder> 标签包含有用的信息和提醒.它们不是用户提供的输入或工具结果的一部分.
-非常重要:当你完成一个任务时,你必须使用 Bash 运行 lint 和 typecheck 命令\
(例如 npm run lint,npm run typecheck,ruff 等),以确保你的代码是正确的.\
如果您找不到正确的命令,请向用户询问要运行的命令,如果他们提供了命令,\
请主动建议将其写入 AGENTS.md,以便您下次知道要运行它.
除非用户明确要求,否则永远不要提交更改.只有在明确要求时才提交非常重要,\
否则用户会觉得你太主动了.
-工具结果和用户消息可能包括 <system-reminder> 标签.\
<system-reminder> 标签包含有用的信息和提醒.它们不是用户提供的输入或工具结果的一部分.

# 工具使用政策
-在进行文件搜索时,最好使用任务工具以减少上下文使用.
-**优先使用 glob 查找文件,使用 grep 搜索文件内容**.禁止使用 run_command 执行 ls,\
find,cat,grep 等命令来替代专用工具.只有当 glob/grep 无法满足需求时才使用 run_command.
-您可以在一次响应中调用多个工具.当请求多个独立的信息时,\
将工具调用批处理在一起以获得最佳性能.当进行多个 bash 工具调用时,\
您必须发送一条包含多个工具调用的消息,以并行运行这些调用.\
例如,如果您需要运行"git status"和"git diff",\
请发送一条包含两个工具调用的消息,以并行运行调用.

# 任务追踪 (todowrite)
当你面对需要3个或更多不同步骤的工程任务时,你应该使用 `todowrite` 工具来追踪进度.\
这有助于组织工作并让用户了解当前状态.
-在开始工作之前,创建待办事项列表,列出所有计划的步骤
-每个步骤应具体且可执行
-当你开始一个步骤时,将其标记为 `in_progress` (同时只能有一个进行中的步骤)
-当你完成一个步骤时,将其标记为 `completed` 并开始下一个
-如果某个步骤不再需要,将其标记为 `cancelled`
-所有步骤完成后,保留完成的列表(不要删除)

何时使用:
-多步骤功能开发 + 明确验证
-跨多个文件的重命名/重构
-多个复杂功能的实现

何时跳过:
-简单的信息查询
-单个文件编辑
-单个命令执行

<example>
user: 添加暗黑模式并运行测试
assistant: [调用 todowrite 创建任务列表: 1.添加暗黑模式切换(in_progress) 2.更新样式(high) 3.运行测试(pending)]
[执行步骤1...]
[调用 todowrite 更新: 1.添加暗黑模式切换(completed) 2.更新样式(in_progress) 3.运行测试(pending)]
[执行步骤2...]
[调用 todowrite 更新: 1.添加暗黑模式切换(completed) 2.更新样式(completed) 3.运行测试(in_progress)]
[执行步骤3...]
[调用 todowrite 更新: 所有标记为 completed]
</example>

除非用户要求详细信息,否则您必须用少于 4 行的文本简洁地回答\
(不包括工具使用或代码生成).

重要提示:在开始工作之前,请考虑一下您正在编辑的代码应该根据文件名目录结构做什么.

# 代码参考
引用特定函数或代码时,请包含模式"file_path:line_number",\
以便用户轻松导航到源代码位置.
<example>
user: 客户端的错误在哪里处理？
assistant: 在 src/services/process.ts:712 的 `connectToServer` 函数中,客户端被标记为失败.
</example>"""

AGENTS_MD_MAX_CHARS = 8000

_agents_md_cache: str | None = None
_agents_md_work_dir: str | None = None
_skills_cache: str | None = None
_skills_work_dir: str | None = None


def clear_prompt_cache() -> None:
    global _agents_md_cache, _agents_md_work_dir, _skills_cache, _skills_work_dir
    _agents_md_cache = None
    _agents_md_work_dir = None
    _skills_cache = None
    _skills_work_dir = None


def build_system_prompt(
    model_id: str, work_dir: str, custom_prompt: str = ""
) -> str:
    sections: list[str] = []

    sections.append(_build_agent_intro(custom_prompt))
    sections.append(_build_model_info(model_id))
    sections.append(_build_env_context(work_dir))
    sections.append(_build_agents_md(work_dir))
    sections.append(_build_skills(work_dir))

    return "\n\n".join(sections)


def _build_agent_intro(custom_prompt: str = "") -> str:
    content = custom_prompt.strip() if custom_prompt.strip() else AGENT_INTRO
    return f"<agent_intro>\n{content}\n</agent_intro>"


def _build_model_info(model_id: str) -> str:
    info = get_model_info(model_id)
    if info:
        display = info.name
        exact_id = info.provider_prefix
    else:
        display = model_id
        exact_id = model_id
    return (
        f"<model_info>\n"
        f"您使用的是名为{display}的模型."
        f"确切的模型ID是{exact_id}\n"
        f"</model_info>"
    )


def _build_env_context(work_dir: str) -> str:
    platform = os.name
    if platform == "nt":
        platform = "win32"
    elif platform == "posix":
        import sys
        platform = sys.platform

    is_git = _is_git_repo(work_dir)
    today = datetime.date.today().strftime("%Y-%m-%d")

    return (
        f"<env>\n"
        f"工作目录: {work_dir}\n"
        f"工作区根文件夹: {work_dir}\n"
        f"目录是git仓库吗: {'是' if is_git else '否'}\n"
        f"平台: {platform}\n"
        f"今天的日期: {today}\n"
        f"</env>"
    )


def _build_agents_md(work_dir: str) -> str:
    global _agents_md_cache, _agents_md_work_dir

    if _agents_md_cache is not None and _agents_md_work_dir == work_dir:
        return _agents_md_cache

    agents_path = Path(work_dir) / "AGENTS.md"
    if not agents_path.is_file():
        result = ""
    else:
        try:
            content = agents_path.read_text(encoding="utf-8")
            if len(content) > AGENTS_MD_MAX_CHARS:
                content = content[:AGENTS_MD_MAX_CHARS] + "\n...[truncated]"
        except Exception:
            content = ""
        if content:
            result = (
                f"<agents.md>\n"
                f"说明来自: {agents_path}\n"
                f"{content}\n"
                f"</agents.md>"
            )
        else:
            result = ""

    _agents_md_cache = result
    _agents_md_work_dir = work_dir
    return result


def _build_skills(work_dir: str) -> str:
    global _skills_cache, _skills_work_dir

    if _skills_cache is not None and _skills_work_dir == work_dir:
        return _skills_cache

    skills = _scan_skills(work_dir)

    if not skills:
        _skills_cache = ""
        _skills_work_dir = work_dir
        return ""

    lines = [
        "Skills为特定任务提供专用指令与工作流程.",
        "当任务与skill描述匹配时,使用skill工具加载该skill.",
        "<available_skills>",
    ]
    for s in skills:
        lines.append("  <skill>")
        lines.append(f"    <name>{s['name']}</name>")
        lines.append(f"    <description>{s['description']}</description>")
        lines.append(f"    <location>{s['location']}</location>")
        lines.append("  </skill>")
    lines.append("</available_skills>")

    result = "\n".join(lines)
    _skills_cache = result
    _skills_work_dir = work_dir
    return result


def _scan_skills(work_dir: str) -> list[dict]:
    seen: dict[str, dict] = {}

    global_dir = Path.home() / ".var" / "skills"
    if global_dir.is_dir():
        _scan_skill_dir(global_dir, seen)

    opencode_global = Path.home() / ".opencode" / "skill"
    if opencode_global.is_dir():
        _scan_skill_dir(opencode_global, seen)

    claude_global = Path.home() / ".claude" / "skills"
    if claude_global.is_dir():
        _scan_skill_dir(claude_global, seen)

    project_dir = Path(work_dir) / ".var" / "skills"
    if project_dir.is_dir():
        _scan_skill_dir(project_dir, seen)

    opencode_project = Path(work_dir) / ".opencode" / "skill"
    if opencode_project.is_dir():
        _scan_skill_dir(opencode_project, seen)

    claude_project = Path(work_dir) / ".claude" / "skills"
    if claude_project.is_dir():
        _scan_skill_dir(claude_project, seen)

    return list(seen.values())


def _scan_skill_dir(base: Path, seen: dict[str, dict]) -> None:
    if not base.is_dir():
        return
    for entry in sorted(base.iterdir()):
        if not entry.is_dir():
            continue
        skill_md = entry / "SKILL.md"
        if not skill_md.is_file():
            continue
        name = entry.name
        description = _extract_skill_description(skill_md)
        location = _path_to_file_uri(skill_md)
        seen[name] = {
            "name": name,
            "description": description,
            "location": location,
        }


def _extract_skill_description(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return ""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            frontmatter = text[3:end].strip()
            try:
                import yaml
                meta = yaml.safe_load(frontmatter)
                if isinstance(meta, dict) and meta.get("description"):
                    desc = str(meta["description"])
                    return desc[:200] + "..." if len(desc) > 200 else desc
            except Exception:
                pass
            body = text[end + 3:].strip()
            for line in body.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                return stripped[:200] + "..." if len(stripped) > 200 else stripped
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        return stripped[:200] + "..." if len(stripped) > 200 else stripped
    return ""


def _path_to_file_uri(path: Path) -> str:
    try:
        return path.as_uri()
    except Exception:
        p = str(path).replace("\\", "/")
        return f"file:///{url_quote(p)}"


def _is_git_repo(path: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
        )
        return result.stdout.strip().lower() == "true"
    except Exception:
        return (Path(path) / ".git").exists()


def build_subagent_prompt(work_dir: str) -> str:
    platform = os.name
    if platform == "nt":
        platform = "win32"
    elif platform == "posix":
        import sys
        platform = sys.platform

    is_git = _is_git_repo(work_dir)
    today = datetime.date.today().strftime("%Y-%m-%d")

    return (
        "你是一个自主子 Agent，正在协助父 Agent 完成任务。\n"
        "请专注于你的任务，完成后返回详细的结果报告。\n\n"
        f"工作目录: {work_dir}\n"
        f"平台: {platform}\n"
        f"日期: {today}\n"
        f"Git 仓库: {'是' if is_git else '否'}"
    )
