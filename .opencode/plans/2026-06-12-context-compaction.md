# Context Compaction 实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 参考 opencode 的 context 压缩系统，为 foundry 实现完整的 head/tail 分割压缩、增量摘要生成、工具输出裁剪和手动压缩 API。

**Architecture:** 重构现有 `context.py` 的简单 `trim_and_summarize`，引入 `compaction.py`（head/tail 分割 + 摘要生成）、`overflow.py`（溢出检测），仍作为 pydantic-ai `history_processor` 集成。压缩使用 session 当前模型。DB schema 新增 `is_compaction`/`is_summary`/`tail_start_id`/`compacted_at` 四个独立字段。

**Tech Stack:** Python / pydantic-ai / aiosqlite / FastAPI

**参考实现:** `D:\1-Project\opencode\packages\opencode\src\session\compaction.ts`

---

## 常量约定

以下常量在实现中统一使用：

| 常量 | 值 | 含义 |
|------|---|------|
| `COMPACTION_BUFFER` | 20,000 | 溢出检测预留 token |
| `PRUNE_MINIMUM` | 20,000 | 最少可释放 token 才触发 prune |
| `PRUNE_PROTECT` | 40,000 | 最近工具输出保护量 |
| `PRUNE_PROTECTED_TOOLS` | `["skill"]` | 永不裁剪的工具 |
| `TOOL_OUTPUT_MAX_CHARS` | 2,000 | 压缩时工具输出截断长度 |
| `DEFAULT_TAIL_TURNS` | 2 | 保留最近几轮完整对话 |
| `MIN_PRESERVE_TOKENS` | 2,000 | tail 最小 token 预算 |
| `MAX_PRESERVE_TOKENS` | 8,000 | tail 最大 token 预算 |
| `COMPACT_SUMMARY_MAX_CHARS` | 300 | 紧凑摘要中每条消息截断长度 |
| `COMPACT_TOOL_RESULT_MAX_CHARS` | 150 | 紧凑摘要中工具结果截断长度 |
| `PRUNE_PLACEHOLDER` | `"[Old tool result content cleared]"` | 裁剪后占位文本 |

---

## File Structure

| 操作 | 文件 | 职责 |
|------|------|------|
| 新增 | `foundry/foundry_app/agent/overflow.py` | token 预算计算 + 溢出检测 |
| 新增 | `foundry/foundry_app/agent/compaction.py` | head/tail 分割、摘要生成、prune、filter_compacted |
| 修改 | `foundry/foundry_app/agent/context.py` | 重构为调用 compaction 模块 |
| 修改 | `foundry/foundry_app/agent/core.py` | 传入 model_id 给 history_processor、添加 prune 调用 |
| 修改 | `foundry/foundry_app/db/database.py` | schema 新增字段 + migration |
| 修改 | `foundry/foundry_app/db/models.py` | Message model 新增字段 |
| 修改 | `foundry/foundry_app/db/crud.py` | create/update 支持新字段 |
| 修改 | `foundry/foundry_app/config.py` | 新增压缩相关配置项 |
| 修改 | `foundry/foundry_app/shared_protocol.py` | 新增 `CompactCmd` + `CompactionDone` |
| 修改 | `foundry/foundry_app/api/ws.py` | 处理 `chat.compact` 命令 |
| 新增 | `foundry/foundry_app/api/compact.py` | REST API `POST /api/sessions/{id}/compact` |

---

## Chunk 1: 基础设施（overflow + config + DB schema）

### Task 1: 新增 overflow.py — token 预算计算与溢出检测

**Files:**
- 新增: `foundry/foundry_app/agent/overflow.py`

- [ ] **Step 1: 创建 overflow.py**

```python
# foundry/foundry_app/agent/overflow.py
from foundry_app.agent.registry import get_model_info

COMPACTION_BUFFER = 20_000


def usable_tokens(model_id: str) -> int:
    info = get_model_info(model_id)
    if not info:
        return 80_000
    context = info.context_window
    max_output = info.max_output_tokens
    reserved = COMPACTION_BUFFER
    return max(0, context - max_output - reserved)


def is_overflow(model_id: str, tokens_used: int) -> bool:
    from foundry_app.config import settings
    if not settings.auto_compaction:
        return False
    info = get_model_info(model_id)
    if info and info.context_window == 0:
        return False
    return tokens_used >= usable_tokens(model_id)
```

- [ ] **Step 2: 验证**

```bash
cd foundry && python -c "from foundry_app.agent.overflow import usable_tokens, is_overflow; print(usable_tokens('gpt-4o'), is_overflow('gpt-4o', 50000)); print(usable_tokens('claude-sonnet'), is_overflow('claude-sonnet', 50000))"
```

预期: `gpt-4o` usable ≈ 91616, `claude-sonnet` usable ≈ 171808

---

### Task 2: 扩展 config.py — 新增压缩配置项

**Files:**
- 修改: `foundry/foundry_app/config.py`

- [ ] **Step 1: 在 Settings 类中新增字段**

在 `context_window_threshold` 之后添加：

```python
    # Compaction settings
    auto_compaction: bool = True
    compaction_prune: bool = True
    compaction_tail_turns: int = 2
    compaction_reserved: int = 20_000
```

同时**删除** `summary_model` 字段（压缩改用 session 当前模型）。

---

### Task 3: DB schema 变更 — messages 表新增字段

**Files:**
- 修改: `foundry/foundry_app/db/database.py`
- 修改: `foundry/foundry_app/db/models.py`
- 修改: `foundry/foundry_app/db/crud.py`

- [ ] **Step 1: 更新 models.py — Message 类新增字段**

在 `model_messages_json` 之后添加：

```python
    is_compaction: bool = Field(default=False)
    is_summary: bool = Field(default=False)
    tail_start_id: Optional[str] = Field(default=None)
    compacted_at: Optional[str] = Field(default=None)
```

- [ ] **Step 2: 更新 database.py — schema + migration**

在 `_SCHEMA` 的 `messages` 表定义中，`created_at` 之前添加：

```sql
    is_compaction INTEGER NOT NULL DEFAULT 0,
    is_summary INTEGER NOT NULL DEFAULT 0,
    tail_start_id TEXT,
    compacted_at TEXT,
```

在 `_MIGRATIONS` 列表中添加（对已有数据库生效）：

```python
_MIGRATIONS = [
    "ALTER TABLE messages ADD COLUMN thinking_content TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE sessions ADD COLUMN parent_id TEXT",
    "ALTER TABLE messages ADD COLUMN is_compaction INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE messages ADD COLUMN is_summary INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE messages ADD COLUMN tail_start_id TEXT",
    "ALTER TABLE messages ADD COLUMN compacted_at TEXT",
]
```

- [ ] **Step 3: 更新 crud.py — create_message 和 update_message**

`create_message` 函数签名新增参数：

```python
async def create_message(
    db: aiosqlite.Connection,
    session_id: str,
    role: str,
    content: str,
    model_id: str | None = None,
    duration_ms: int = 0,
    input_tokens: int = 0,
    output_tokens: int = 0,
    model_messages_json: str = "[]",
    is_compaction: bool = False,
    is_summary: bool = False,
    tail_start_id: str | None = None,
) -> dict:
```

INSERT 语句中添加对应字段。

`update_message` 函数的白名单中添加：

```python
if k in (
    "content",
    "thinking_content",
    "model_id",
    "duration_ms",
    "input_tokens",
    "output_tokens",
    "model_messages_json",
    "is_compaction",
    "is_summary",
    "tail_start_id",
    "compacted_at",
):
```

- [ ] **Step 4: 验证 migration**

```bash
cd foundry && python -c "
import asyncio
from foundry_app.db.database import init_db, _connect
async def test():
    db = await _connect()
    await init_db(db)
    cursor = await db.execute('PRAGMA table_info(messages)')
    cols = await cursor.fetchall()
    for c in cols:
        print(c[1], c[2])
    await db.close()
asyncio.run(test())
"
```

预期输出中包含 `is_compaction`, `is_summary`, `tail_start_id`, `compacted_at`。

- [ ] **Step 5: Commit**

```bash
git add foundry/foundry_app/agent/overflow.py foundry/foundry_app/config.py foundry/foundry_app/db/database.py foundry/foundry_app/db/models.py foundry/foundry_app/db/crud.py
git commit -m "feat: add overflow detection, compaction config, and DB schema for context compression"
```

---

## Chunk 2: 核心压缩引擎（compaction.py）

### Task 4: 创建 compaction.py — 完整实现

**Files:**
- 新增: `foundry/foundry_app/agent/compaction.py`

此文件包含 5 个核心函数，按依赖顺序实现。

- [ ] **Step 1: 创建文件骨架 + 常量 + 辅助函数**

```python
# foundry/foundry_app/agent/compaction.py
import json
from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    UserPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    ThinkingPart,
)

from foundry_app.agent.registry import estimate_tokens, get_model_info, get_provider_prefix
from foundry_app.agent.overflow import usable_tokens
from foundry_app.config import settings
from foundry_app.logger import get_logger

logger = get_logger("agent.compaction")

PRUNE_MINIMUM = 20_000
PRUNE_PROTECT = 40_000
PRUNE_PROTECTED_TOOLS = ["skill"]
TOOL_OUTPUT_MAX_CHARS = 2_000
DEFAULT_TAIL_TURNS = 2
MIN_PRESERVE_TOKENS = 2_000
MAX_PRESERVE_TOKENS = 8_000
COMPACT_SUMMARY_MAX_CHARS = 300
COMPACT_TOOL_RESULT_MAX_CHARS = 150
PRUNE_PLACEHOLDER = "[Old tool result content cleared]"

SUMMARY_TEMPLATE = """## Goal
[Single-sentence task summary]

## Constraints & Preferences
[User constraints and preferences]

## Progress
### Done
- [Completed items]

### In Progress
- [Items currently being worked on]

### Blocked
- [Blocked items]

## Key Decisions
- [Decision + reasoning]

## Next Steps
1. [Next actions in order]

## Critical Context
[Technical facts, error messages, open questions]

## Relevant Files
- path/to/file — [Why it matters]
"""
```

- [ ] **Step 2: 实现 _count_msg_tokens — 完整版 token 计数**

```python
def _count_msg_tokens(msg: ModelMessage) -> int:
    total = 0
    if isinstance(msg, ModelRequest):
        for part in msg.parts:
            if isinstance(part, UserPromptPart):
                content = part.content
                if isinstance(content, str):
                    total += estimate_tokens(content)
                elif isinstance(content, list):
                    total += estimate_tokens(" ".join(str(c) for c in content))
    elif isinstance(msg, ModelResponse):
        for part in msg.parts:
            if isinstance(part, TextPart):
                total += estimate_tokens(part.content)
            elif isinstance(part, ToolCallPart):
                total += estimate_tokens(part.tool_name)
                total += estimate_tokens(str(part.args))
            elif isinstance(part, ToolReturnPart):
                total += estimate_tokens(str(part.content))
            elif isinstance(part, ThinkingPart):
                total += estimate_tokens(part.content or "")
    return total
```

**与旧版差异**: 新增了 `ToolCallPart`、`ToolReturnPart`、`ThinkingPart` 的计数。

- [ ] **Step 3: 实现 _turns + _split_turn — 消息分组**

```python
def _turns(messages: list[ModelMessage]) -> list[dict]:
    turns = []
    for i, msg in enumerate(messages):
        if isinstance(msg, ModelRequest):
            has_user_text = any(
                isinstance(p, UserPromptPart) for p in msg.parts
            )
            if has_user_text:
                turns.append({"start": i, "end": len(messages), "index": len(turns)})
    for j in range(len(turns) - 1):
        turns[j]["end"] = turns[j + 1]["start"]
    return turns


def _split_turn(
    messages: list[ModelMessage], turn: dict, budget: int
) -> dict | None:
    if budget <= 0 or turn["end"] - turn["start"] <= 1:
        return None
    for start in range(turn["start"] + 1, turn["end"]):
        size = sum(_count_msg_tokens(m) for m in messages[start : turn["end"]])
        if size <= budget:
            return {"start": start}
    return None
```

- [ ] **Step 4: 实现 select — head/tail 分割算法**

这是核心算法，参考 opencode `compaction.ts:245-294`。

```python
def select(
    messages: list[ModelMessage], model_id: str
) -> tuple[list[ModelMessage], int | None]:
    """
    Returns: (head, tail_start_index)
    - head: messages to summarize
    - tail_start_index: index where preserved messages begin (None = no tail)
    """
    tail_turns = settings.compaction_tail_turns
    if tail_turns <= 0:
        return messages, None

    budget = _preserve_recent_budget(model_id)
    all_turns = _turns(messages)
    if not all_turns:
        return messages, None

    recent = all_turns[-tail_turns:]
    sizes = []
    for t in recent:
        size = sum(_count_msg_tokens(m) for m in messages[t["start"] : t["end"]])
        sizes.append(size)

    total = 0
    keep = None
    for i in range(len(recent) - 1, -1, -1):
        if total + sizes[i] <= budget:
            total += sizes[i]
            keep = recent[i]
        else:
            remaining = budget - total
            split = _split_turn(messages, recent[i], remaining)
            if split:
                keep = split
            elif keep is None:
                logger.warning(
                    "compaction select: cannot fit any recent turn in budget=%d, keeping last turn",
                    budget,
                )
                keep = recent[-1]
            break

    if keep is None or keep["start"] == 0:
        return messages, None

    head = messages[: keep["start"]]
    return head, keep["start"]


def _preserve_recent_budget(model_id: str) -> int:
    usable = usable_tokens(model_id)
    budget = int(usable * 0.25)
    return max(MIN_PRESERVE_TOKENS, min(budget, MAX_PRESERVE_TOKENS))
```

- [ ] **Step 5: 实现 _build_compact_summary — 消息文本化**

```python
def _build_compact_summary(
    messages: list[ModelMessage], tool_max: int = COMPACT_TOOL_RESULT_MAX_CHARS
) -> str:
    lines = []
    for msg in messages:
        try:
            if isinstance(msg, ModelRequest):
                for part in msg.parts:
                    if isinstance(part, UserPromptPart):
                        content = part.content
                        if isinstance(content, str):
                            text = content[:COMPACT_SUMMARY_MAX_CHARS]
                        elif isinstance(content, list):
                            text = " ".join(str(c)[:150] for c in content)[
                                :COMPACT_SUMMARY_MAX_CHARS
                            ]
                        else:
                            text = str(content)[:COMPACT_SUMMARY_MAX_CHARS]
                        lines.append(f"User: {text}")
            elif isinstance(msg, ModelResponse):
                for part in msg.parts:
                    if isinstance(part, TextPart):
                        lines.append(
                            f"Assistant: {part.content[:COMPACT_SUMMARY_MAX_CHARS]}"
                        )
                    elif isinstance(part, ToolCallPart):
                        args_str = str(part.args)[:tool_max]
                        lines.append(f"Tool call: {part.tool_name}({args_str})")
                    elif isinstance(part, ToolReturnPart):
                        content_str = str(part.content)[:tool_max]
                        lines.append(f"Tool result: {content_str}")
        except Exception:
            pass
    return "\n".join(lines)
```

- [ ] **Step 6: 实现 _build_prompt + _generate_summary — 摘要生成**

```python
def _build_prompt(previous_summary: str | None) -> str:
    if previous_summary:
        return (
            "Update the anchored summary below using the conversation history above. "
            "Preserve still-true details, remove stale details, and merge in the new facts.\n\n"
            f"<previous-summary>\n{previous_summary}\n</previous-summary>\n\n"
            "Produce an updated summary following this template:\n"
            + SUMMARY_TEMPLATE
        )
    return (
        "Create a new anchored summary from the conversation history above.\n\n"
        "Follow this template:\n"
        + SUMMARY_TEMPLATE
    )


async def _generate_summary(
    messages: list[ModelMessage],
    model_id: str,
    previous_summary: str | None = None,
) -> str:
    text = _build_compact_summary(messages, tool_max=TOOL_OUTPUT_MAX_CHARS)
    if not text.strip():
        return "Previous conversation occurred."

    model_string = get_provider_prefix(model_id)
    prompt = _build_prompt(previous_summary)

    try:
        agent = Agent(
            model_string,
            instructions="Summarize concisely. Preserve key decisions, preferences, technical details, file paths, and error messages. Keep every section even if empty.",
        )
        result = await agent.run(f"{prompt}\n\n{text}")
        return str(result.output)
    except Exception:
        logger.exception("compaction summary generation failed")
        return text[:2000] if text else "Previous conversation occurred."
```

- [ ] **Step 7: 实现 compact — 主入口 (history_processor)**

```python
async def compact(
    messages: list[ModelMessage], model_id: str
) -> list[ModelMessage]:
    """
    history_processor 入口。被 pydantic-ai 每次调用 LLM 前自动执行。
    不再检查 overflow（overflow 在 stream_chat 主循环中检测，通过创建压缩标记触发）。
    此函数只负责处理已有的压缩标记和 filter_compacted。
    """
    return filter_compacted(messages)
```

- [ ] **Step 8: 实现 filter_compacted — 消息重排**

```python
def filter_compacted(messages: list[ModelMessage]) -> list[ModelMessage]:
    """
    如果 messages 中有 SystemPromptPart 格式的压缩摘要，
    保留摘要 + 其后所有消息，丢弃被摘要替代的历史。
    """
    summary_idx = None
    for i, msg in enumerate(messages):
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if (
                    isinstance(part, SystemPromptPart)
                    and part.content.startswith("[Conversation Summary]\n")
                ):
                    summary_idx = i

    if summary_idx is not None and summary_idx > 0:
        return messages[summary_idx:]

    return messages
```

- [ ] **Step 9: 实现 process_compaction — 完整压缩流程**

此函数在 `stream_chat` 主循环中被调用，当检测到 overflow 或手动压缩时触发。

```python
async def process_compaction(
    messages: list[ModelMessage],
    model_id: str,
    previous_summary: str | None = None,
) -> str:
    """
    执行完整的压缩流程：
    1. select() 分割 head/tail
    2. 生成摘要
    3. 返回摘要文本

    调用方负责将摘要存入 DB 和构建新的 history。
    """
    head, tail_start = select(messages, model_id)

    if tail_start is None:
        logger.info("compaction: no tail split possible, summarizing all")
        head = messages

    summary = await _generate_summary(head, model_id, previous_summary)
    return summary
```

- [ ] **Step 10: 实现 prune — 工具输出裁剪**

```python
async def prune(
    messages: list[ModelMessage],
) -> list[ModelMessage]:
    """
    裁剪旧工具输出。返回修改后的消息列表。
    保护最近 PRUNE_PROTECT tokens 的工具输出。
    只在可释放 > PRUNE_MINIMUM 时才执行。
    """
    if not settings.compaction_prune:
        return messages

    total = 0
    to_prune = []
    turns = 0

    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        if isinstance(msg, ModelRequest):
            turns += 1
        if turns < 2:
            continue

        if isinstance(msg, ModelResponse):
            for j, part in enumerate(msg.parts):
                if not isinstance(part, ToolReturnPart):
                    continue
                tool_name = getattr(part, "tool_name", "")
                if tool_name in PRUNE_PROTECTED_TOOLS:
                    continue

                part_tokens = estimate_tokens(str(part.content))
                total += part_tokens
                if total > PRUNE_PROTECT:
                    to_prune.append((i, j))

    if not to_prune or total - PRUNE_PROTECT < PRUNE_MINIMUM:
        return messages

    result = []
    prune_set = {(i, j) for i, j in to_prune}
    for i, msg in enumerate(messages):
        if isinstance(msg, ModelResponse) and any(pi == i for pi, _ in prune_set):
            new_parts = []
            for j, part in enumerate(msg.parts):
                if (i, j) in prune_set:
                    new_parts.append(
                        ToolReturnPart(
                            content=PRUNE_PLACEHOLDER,
                            tool_call_id=part.tool_call_id,
                        )
                    )
                else:
                    new_parts.append(part)
            result.append(ModelResponse(parts=new_parts))
        else:
            result.append(msg)

    logger.info("prune: replaced %d tool outputs with placeholder", len(to_prune))
    return result
```

- [ ] **Step 11: 验证模块可导入**

```bash
cd foundry && python -c "from foundry_app.agent.compaction import select, filter_compacted, process_compaction, prune; print('OK')"
```

- [ ] **Step 12: Commit**

```bash
git add foundry/foundry_app/agent/compaction.py
git commit -m "feat: add compaction engine with head/tail split, summary generation, and prune"
```

---

## Chunk 3: 集成到 context.py 和 core.py

### Task 5: 重构 context.py — 调用 compaction 模块

**Files:**
- 修改: `foundry/foundry_app/agent/context.py`

- [ ] **Step 1: 重写 context.py**

完全替换现有内容。新版本作为 `history_processor` 入口，委托给 compaction 模块：

```python
from pydantic_ai.messages import ModelMessage

from foundry_app.agent.compaction import filter_compacted


async def trim_and_summarize(messages: list[ModelMessage]) -> list[ModelMessage]:
    return filter_compacted(messages)
```

**说明**: 复杂的压缩逻辑已移至 `compaction.py`。此函数现在只负责消息重排（filter_compacted）。实际的 overflow 检测和压缩触发由 `stream_chat` 主循环负责（在下一个 Task 中实现）。

- [ ] **Step 2: Commit**

```bash
git add foundry/foundry_app/agent/context.py
git commit -m "refactor: simplify context.py to delegate to compaction module"
```

---

### Task 6: 修改 core.py — 集成压缩主流程

**Files:**
- 修改: `foundry/foundry_app/agent/core.py`

这是最关键的集成点。需要修改 `stream_chat` 函数：

1. 在 LLM 调用后检查 overflow
2. 如果 overflow → 执行压缩 → 生成摘要 → 存储到 DB → 自动继续
3. 在对话结束后执行 prune
4. 传入 `model_id` 给 `history_processor`（通过 deps 或闭包）

- [ ] **Step 1: 修改 history_processor 注册方式**

pydantic-ai 的 `history_processors` 签名是 `async (messages) -> messages`，无法直接传入 model_id。我们改用闭包方式：

在 `create_agent` 中：

```python
def create_agent(model_id: str, system_prompt: str = "") -> Agent:
    # ... 现有 model 解析逻辑不变 ...

    from foundry_app.agent.context import trim_and_summarize

    agent = Agent(
        model_obj_or_string,  # 根据现有逻辑
        instructions=instructions,
        deps_type=AgentDeps,
        history_processors=[trim_and_summarize],
    )
    _register_tools(agent)
    return agent
```

`trim_and_summarize` 签名不变，它只做 `filter_compacted`。

- [ ] **Step 2: 在 stream_chat 中添加压缩逻辑**

在 `stream_chat` 函数中，`result = run.result` 之后（约 line 326），添加 overflow 检测和压缩处理：

```python
        result = run.result
        if result:
            # ... 现有 full_text / usage 处理 ...

            all_msgs = result.all_messages()
            usage = result.usage
            input_tokens = usage.request_tokens or 0 if usage else 0
            output_tokens = usage.response_tokens or 0 if usage else 0

            # ── Overflow 检测 + 压缩 ──
            from foundry_app.agent.overflow import is_overflow
            from foundry_app.agent.compaction import process_compaction, prune

            total_tokens = input_tokens + output_tokens
            if is_overflow(model_id, total_tokens):
                logger.info(
                    "overflow detected | model=%s tokens=%d, triggering compaction",
                    model_id,
                    total_tokens,
                )
                await _do_compaction(
                    db, session_id, model_id, all_msgs, send_event
                )

            # ... 现有 update_message 逻辑 ...

            # ── Post-loop prune ──
            try:
                pruned = await prune(all_msgs)
                if assistant_id:
                    await crud.update_message(
                        db,
                        assistant_id,
                        model_messages_json=json.dumps(
                            [_serialize_msg(m) for m in pruned], default=str
                        ),
                    )
            except Exception:
                logger.exception("prune failed | session=%s", session_id)
```

- [ ] **Step 3: 实现 _do_compaction 辅助函数**

在 `core.py` 中新增（模块级别函数）：

```python
async def _do_compaction(
    db, session_id: str, model_id: str,
    all_msgs: list[ModelMessage], send_event
):
    from foundry_app.agent.compaction import process_compaction
    from foundry_app.db import crud

    previous_summary = _find_previous_summary(all_msgs)

    summary = await process_compaction(all_msgs, model_id, previous_summary)

    compaction_msg = await crud.create_message(
        db, session_id, "user",
        "[Compaction triggered]",
        is_compaction=True,
    )
    summary_msg = await crud.create_message(
        db, session_id, "assistant",
        summary,
        model_id=model_id,
        is_summary=True,
        tail_start_id=compaction_msg["id"],
    )

    logger.info(
        "compaction done | session=%s summary_len=%d",
        session_id,
        len(summary),
    )

    await send_event({
        "type": "compaction.done",
        "session_id": session_id,
        "summary_message_id": summary_msg["id"],
    })

    summary_part = SystemPromptPart(
        content=f"[Conversation Summary]\n{summary}"
    )
    summary_model_msg = ModelRequest(parts=[summary_part])

    compacted_json = json.dumps(
        [_serialize_msg(summary_model_msg)], default=str
    )
    await crud.update_message(
        db, summary_msg["id"], model_messages_json=compacted_json
    )


def _find_previous_summary(messages: list[ModelMessage]) -> str | None:
    for msg in messages:
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if (
                    isinstance(part, SystemPromptPart)
                    and part.content.startswith("[Conversation Summary]\n")
                ):
                    return part.content.replace("[Conversation Summary]\n", "")
    return None
```

**重要**: `_do_compaction` 将摘要存入 DB 的 `messages` 表（is_summary=True），同时将 `SystemPromptPart` 格式的摘要存入 `model_messages_json`。下次 `_load_history` 加载时，`filter_compacted` 会识别并只保留摘要及之后的消息。

- [ ] **Step 4: 修改 _load_history — 支持 filter_compacted**

当前的 `_load_history` 只取最后一条有 `model_messages_json` 的消息。需要改为：如果存在 summary 消息，从 summary 消息开始构建历史。

```python
def _load_history(messages: list[dict]) -> list[ModelMessage]:
    if not messages:
        return []
    
    summary_json = None
    for msg in reversed(messages):
        if msg.get("is_summary") and msg.get("model_messages_json", "[]") != "[]":
            summary_json = msg["model_messages_json"]
            break
    
    if summary_json:
        try:
            data = json.loads(summary_json)
            result = []
            for m in data:
                try:
                    result.append(ModelMessage.model_validate(m))
                except Exception:
                    pass
            if result:
                return result
        except Exception:
            pass
    
    for msg in reversed(messages):
        raw = msg.get("model_messages_json", "[]")
        if raw and raw != "[]":
            try:
                data = json.loads(raw)
                result = []
                for m in data:
                    try:
                        result.append(ModelMessage.model_validate(m))
                    except Exception:
                        pass
                if result:
                    return result
            except Exception:
                pass
    return []
```

- [ ] **Step 5: 验证基本流程**

```bash
cd foundry && python -c "
from foundry_app.agent.core import create_agent, _load_history
agent = create_agent('gpt-4o')
print('Agent created with history_processors:', agent._history_processors)
print('_load_history([]):', _load_history([]))
"
```

- [ ] **Step 6: Commit**

```bash
git add foundry/foundry_app/agent/core.py foundry/foundry_app/agent/context.py
git commit -m "feat: integrate compaction into stream_chat with overflow detection, summary storage, and prune"
```

---

## Chunk 4: 手动压缩 API + WebSocket 命令

### Task 7: 新增 shared_protocol 事件类型

**Files:**
- 修改: `foundry/foundry_app/shared_protocol.py`

- [ ] **Step 1: 新增 CompactCmd 和 CompactionDone 事件**

在文件末尾 `parse_command` 之前添加：

```python
@dataclass
class CompactCmd:
    type: str = "chat.compact"
    session_id: str = ""


@dataclass
class CompactionDone:
    type: str = "compaction.done"
    session_id: str = ""
    summary_message_id: str = ""
```

修改 `parse_command`：

```python
def parse_command(data: dict) -> ChatMessageCmd | CompactCmd | None:
    msg_type = data.get("type", "")
    if msg_type == "chat.message":
        return ChatMessageCmd(
            message_id=data.get("message_id", str(uuid.uuid4())),
            content=data.get("content", ""),
            model_id=data.get("model_id", ""),
        )
    if msg_type == "chat.compact":
        return CompactCmd(
            session_id=data.get("session_id", ""),
        )
    return None
```

- [ ] **Step 2: Commit**

```bash
git add foundry/foundry_app/shared_protocol.py
git commit -m "feat: add CompactCmd and CompactionDone protocol types"
```

---

### Task 8: WebSocket 处理 chat.compact 命令

**Files:**
- 修改: `foundry/foundry_app/api/ws.py`

- [ ] **Step 1: 在 websocket_chat 中添加 compact 处理**

在 `if msg_type == "chat.interrupt":` 块之后，`if msg_type == "chat.message":` 块之前添加：

```python
            if msg_type == "chat.compact":
                async def do_compact():
                    from foundry_app.agent.core import _do_compaction, _load_history
                    from foundry_app.db import crud
                    db_conn = await get_db()
                    msgs = await crud.list_messages(db_conn, session_id)
                    model_id = (await crud.get_session(db_conn, session_id) or {}).get("model_id", settings.default_model)
                    history = _load_history(msgs)
                    if history:
                        await _do_compaction(db_conn, session_id, model_id, history, send_event)
                    else:
                        await send_event({"type": "compaction.done", "session_id": session_id, "summary_message_id": ""})

                asyncio.create_task(do_compact())
                continue
```

同时添加 `get_db` import：

```python
from foundry_app.db.database import get_db
```

- [ ] **Step 2: Commit**

```bash
git add foundry/foundry_app/api/ws.py
git commit -m "feat: handle chat.compact WebSocket command"
```

---

### Task 9: REST API — POST /api/sessions/{id}/compact

**Files:**
- 新增: `foundry/foundry_app/api/compact.py`
- 修改: `foundry/foundry_app/main.py`

- [ ] **Step 1: 创建 compact.py**

```python
from fastapi import APIRouter, HTTPException

from foundry_app.db.database import get_db
from foundry_app.db import crud
from foundry_app.agent.core import _do_compaction, _load_history

router = APIRouter(tags=["compaction"])


@router.post("/api/sessions/{session_id}/compact")
async def compact_session(session_id: str):
    db = await get_db()
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail={"error": {"code": "session_not_found"}})

    messages = await crud.list_messages(db, session_id)
    model_id = session.get("model_id", "claude-sonnet")
    history = _load_history(messages)

    if not history:
        return {"status": "noop", "message": "No messages to compact"}

    async def noop_send(event: dict):
        pass

    await _do_compaction(db, session_id, model_id, history, noop_send)

    return {"status": "ok", "session_id": session_id}
```

- [ ] **Step 2: 在 main.py 中注册路由**

```python
from foundry_app.api.compact import router as compact_router
app.include_router(compact_router)
```

- [ ] **Step 3: Commit**

```bash
git add foundry/foundry_app/api/compact.py foundry/foundry_app/main.py
git commit -m "feat: add POST /api/sessions/{id}/compact endpoint"
```

---

## Chunk 5: 端到端验证

### Task 10: 集成测试

- [ ] **Step 1: 启动后端验证所有模块加载正常**

```bash
cd foundry && python -c "
from foundry_app.agent.overflow import usable_tokens, is_overflow
from foundry_app.agent.compaction import select, filter_compacted, process_compaction, prune
from foundry_app.agent.context import trim_and_summarize
from foundry_app.agent.core import create_agent, _do_compaction, _load_history
from foundry_app.config import settings

print('auto_compaction:', settings.auto_compaction)
print('compaction_tail_turns:', settings.compaction_tail_turns)
print('gpt-4o usable:', usable_tokens('gpt-4o'))
print('claude-sonnet usable:', usable_tokens('claude-sonnet'))
print('All modules loaded OK')
"
```

- [ ] **Step 2: 启动后端确认无 import 错误**

```bash
cd foundry && python -m uvicorn foundry_app.main:app --host 0.0.0.0 --port 8000
```

在另一个终端测试 API：

```bash
curl http://localhost:8000/api/health
```

- [ ] **Step 3: 测试 compact API**

```bash
# 创建 session
SESSION=$(curl -s -X POST http://localhost:8000/api/sessions -H "Content-Type: application/json" -d '{"title":"Test Compaction"}' | python -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "Session: $SESSION"

# compact 空 session
curl -s -X POST http://localhost:8000/api/sessions/$SESSION/compact | python -m json.tool
```

预期: `{"status": "noop", "message": "No messages to compact"}`

- [ ] **Step 4: Final Commit**

```bash
git add -A
git commit -m "feat: complete context compaction system (overflow detection, head/tail split, summary, prune, manual compact API)"
```

---

## 数据流总览

```
用户发消息 → stream_chat()
    │
    ├─ _load_history(messages) → 从 DB 加载，优先取 summary 消息的 model_messages_json
    │
    ├─ agent.iter(user_message, message_history=history)
    │   │
    │   └─ [pydantic-ai 内部] → trim_and_summarize() → filter_compacted()
    │       └─ 如果有 [Conversation Summary] 开头的 SystemPromptPart → 跳过之前的消息
    │
    ├─ LLM 返回 → 记录 tokens
    │
    ├─ is_overflow(model_id, total_tokens)?
    │   ├─ 是 → _do_compaction()
    │   │       ├─ process_compaction() → select() + _generate_summary()
    │   │       ├─ 存储到 DB (is_compaction=True, is_summary=True)
    │   │       └─ send_event("compaction.done")
    │   └─ 否 → 正常结束
    │
    └─ prune(all_msgs) → 异步裁剪旧工具输出
```

## 手动压缩入口

```
WebSocket: {"type": "chat.compact", "session_id": "xxx"}
REST API:  POST /api/sessions/{session_id}/compact
```
