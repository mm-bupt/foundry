# Debug Logging + Tool Call Display 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 1) 后端添加结构化 debug 日志（记录消息、工具执行、流事件等）；2) WebUI 前端处理并展示工具调用（tool.call / tool.result）。

**Architecture:** 后端使用 Python 标准 `logging` 模块，通过已有的 `settings.debug` 控制日志级别，在 `core.py`、`ws.py`、`tools.py` 中添加关键路径日志。前端在 `store.ts` 新增 toolCalls 状态管理，在 `App.tsx` 添加事件处理，在 `ChatPanel.tsx` 用 Ant Design 组件渲染可折叠的工具调用块。

**Tech Stack:** Python logging / TypeScript / React / Zustand / Ant Design X

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `var/var_app/logger.py` | Create | 日志配置模块，提供 `get_logger()` 工厂 |
| `var/var_app/main.py` | Modify | 启动时初始化日志配置 |
| `var/var_app/agent/core.py` | Modify | 添加 stream_chat 各阶段 debug 日志 |
| `var/var_app/api/ws.py` | Modify | 添加连接/消息/断开日志 |
| `var/var_app/agent/tools.py` | Modify | 添加工具执行前后的日志 |
| `webui/src/types.ts` | Modify | 新增 `ToolCall` 接口，`Message` 增加 `tool_calls` 字段 |
| `webui/src/store.ts` | Modify | 新增 `activeToolCalls` 状态和相关 actions |
| `webui/src/App.tsx` | Modify | 添加 `tool.call` / `tool.result` 事件处理 |
| `webui/src/components/ChatPanel.tsx` | Modify | 渲染工具调用可折叠块 |
| `webui/src/components/ToolCallBlock.tsx` | Create | 工具调用展示组件 |

---

## Task 1: 后端日志模块

**Files:**
- Create: `var/var_app/logger.py`
- Modify: `var/var_app/main.py`

- [ ] **Step 1: 创建 logger.py**

```python
import logging
import sys


def setup_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    root = logging.getLogger("var_app")
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    if not name.startswith("var_app"):
        name = f"var_app.{name}"
    return logging.getLogger(name)
```

- [ ] **Step 2: 在 main.py 启动时初始化日志**

在 `main.py` 的 import 区域添加：

```python
from var_app.logger import setup_logging
```

在 `lifespan` 函数体开头（`db = await get_db()` 之前）添加：

```python
setup_logging(debug=settings.debug)
```

- [ ] **Step 3: 验证**

启动后端 `python -m uvicorn var_app.main:app --reload`，确认无报错。

---

## Task 2: core.py 添加 debug 日志

**Files:**
- Modify: `var/var_app/agent/core.py`

- [ ] **Step 1: 导入 logger**

在 `core.py` import 区域添加：

```python
from var_app.logger import get_logger

logger = get_logger("agent.core")
```

- [ ] **Step 2: stream_chat 入口日志**

在 `stream_chat` 函数体开头（`db = await get_db()` 之前）添加：

```python
logger.debug("stream_chat start | session=%s model=%s msg_len=%d", session_id, "pending", len(user_message))
```

在 `model_id = session["model_id"]` 之后添加：

```python
logger.debug("resolved model: %s", model_id)
```

- [ ] **Step 3: 流事件日志**

在 `PartStartEvent` 的 `ThinkingPart` 分支（`await send_event({"type": "thinking.start"...})` 之后）添加：

```python
logger.debug("thinking.start | session=%s", session_id)
```

在 `TextPart` 分支（`if not assistant_id:` 块之后、`if thinking_text:` 之前）添加：

```python
logger.debug("text.start | session=%s assistant_id=%s", session_id, assistant_id)
```

在 `ToolCallPart` 分支（`await send_event({"type": "tool.call"...})` 之后）添加：

```python
logger.debug("tool.call | session=%s tool=%s args=%s", session_id, tool_name, json.dumps(args, ensure_ascii=False)[:500])
```

- [ ] **Step 4: 工具结果日志**

在 `CallToolsNode` 的 `ToolReturnPart` 分支（`await send_event({"type": "tool.result"...})` 之后）添加：

```python
logger.debug("tool.result | session=%s tool=%s result_len=%d", session_id, meta.get("tool_name", ""), len(str(result_part.content)))
```

- [ ] **Step 5: stream 完成日志**

在 `duration = int(...)` 行之后、`await send_event({"type": "stream.done"...})` 之前添加：

```python
logger.debug("stream.done | session=%s duration=%dms tokens=%d+%d text_len=%d", session_id, duration, input_tokens, output_tokens, len(full_text))
```

- [ ] **Step 6: 异常日志**

将 `except Exception as e:` 块中的 `print(...)` 和 `traceback.print_exc` 替换为：

```python
logger.exception("stream_chat error | session=%s error=%s", session_id, e)
```

删除原来的 `print` 和 `traceback.print_exc` 行。

- [ ] **Step 7: 验证**

设置 `VAR_DEBUG=true`，启动后端发送一条消息，观察 stderr 中出现 debug 日志。

---

## Task 3: ws.py 添加连接/消息日志

**Files:**
- Modify: `var/var_app/api/ws.py`

- [ ] **Step 1: 导入 logger**

在 `ws.py` import 区域添加：

```python
from var_app.logger import get_logger

logger = get_logger("api.ws")
```

- [ ] **Step 2: 连接日志**

在 `await websocket.accept()` 之后添加：

```python
logger.debug("ws connected | session=%s", session_id)
```

- [ ] **Step 3: 消息接收日志**

在 `msg_type = data.get("type", "")` 之后添加：

```python
logger.debug("ws recv | session=%s type=%s", session_id, msg_type)
```

- [ ] **Step 4: 断开日志**

在 `except WebSocketDisconnect:` 分支添加：

```python
logger.debug("ws disconnected | session=%s", session_id)
```

- [ ] **Step 5: 验证**

设置 debug 模式，通过 WebUI 连接 WS，确认连接/消息/断开日志输出。

---

## Task 4: tools.py 添加工具执行日志

**Files:**
- Modify: `var/var_app/agent/tools.py`

- [ ] **Step 1: 读取 tools.py 了解结构**

先读取 `var/var_app/agent/tools.py`，了解各工具注册函数的实现方式。

- [ ] **Step 2: 导入 logger**

在 `tools.py` import 区域添加：

```python
from var_app.logger import get_logger

logger = get_logger("agent.tools")
```

- [ ] **Step 3: 在每个工具函数内部添加执行日志**

对每个注册的工具函数（如 `read_file`、`write_file`、`run_command`、`glob`、`grep`、`skill`），在函数体开头添加执行开始日志，在返回前添加结果日志。具体代码取决于各工具函数的参数签名，需要在实施时适配。

- [ ] **Step 4: 验证**

Debug 模式下发送触发工具调用的消息，确认工具执行日志。

---

## Task 5: 前端 types.ts 扩展

**Files:**
- Modify: `webui/src/types.ts`

- [ ] **Step 1: 添加 ToolCall 接口**

在 `types.ts` 的 `Message` 接口之前添加：

```typescript
export interface ToolCall {
  toolCallId: string
  toolName: string
  args: Record<string, unknown>
  result?: string
  status: "running" | "done"
}
```

- [ ] **Step 2: Message 接口增加 tool_calls 字段**

在 `Message` 接口中，在 `thinking_content: string` 行之后添加：

```typescript
tool_calls: ToolCall[]
```

同时将 `thinking_content: string` 改为 `thinking_content: string | null`。

- [ ] **Step 3: 验证**

运行 `cd webui && npx tsc --noEmit` 确认类型无误。

---

## Task 6: 前端 store.ts 添加 toolCalls 状态管理

**Files:**
- Modify: `webui/src/store.ts`

- [ ] **Step 1: 添加 activeToolCalls 状态字段**

在 `AppState` 接口中，`connected: boolean` 之后添加：

```typescript
activeToolCalls: ToolCall[]
```

在 `create<AppState>((set, get) => ({` 的初始状态中，`connected: false,` 之后添加：

```typescript
activeToolCalls: [],
```

- [ ] **Step 2: 添加 toolCalls 相关 actions**

在 `AppState` 接口中，`setConnected` 之后添加：

```typescript
addToolCall: (tc: ToolCall) => void
updateToolResult: (toolCallId: string, result: string) => void
clearToolCalls: () => void
```

在 store 实现中，`setConnected` 实现之后添加：

```typescript
addToolCall: (tc) =>
  set((s) => ({ activeToolCalls: [...s.activeToolCalls, tc] })),

updateToolResult: (toolCallId, result) =>
  set((s) => ({
    activeToolCalls: s.activeToolCalls.map((tc) =>
      tc.toolCallId === toolCallId
        ? { ...tc, result, status: "done" as const }
        : tc
    ),
  })),

clearToolCalls: () => set({ activeToolCalls: [] }),
```

- [ ] **Step 3: finalizeStreamWithMessage 中清除 toolCalls 并写入 Message**

修改 `finalizeStreamWithMessage`：

```typescript
finalizeStreamWithMessage: () => {
  const s = get()
  const assistantMsg: Message = {
    id: s.streamingMessageId || crypto.randomUUID(),
    session_id: s.currentSessionId,
    role: "assistant",
    content: s.streamingText,
    thinking_content: s.thinkingText || null,
    tool_calls: [...s.activeToolCalls],
    model_id: null,
    tokens_in: null,
    tokens_out: null,
    duration_ms: null,
    created_at: new Date().toISOString(),
  }
  set({
    status: "idle",
    streamingText: "",
    streamingMessageId: "",
    isThinking: false,
    thinkingText: "",
    thinkingMessageId: "",
    activeToolCalls: [],
    messages: [...s.messages, assistantMsg],
  })
},
```

- [ ] **Step 4: 验证**

运行 `cd webui && npx tsc --noEmit` 确认类型无误。

---

## Task 7: 前端 App.tsx 添加 tool.call / tool.result 事件处理

**Files:**
- Modify: `webui/src/App.tsx`

- [ ] **Step 1: 从 store 引入 toolCall actions 并导入 ToolCall 类型**

在 `App.tsx` 的 store 解构中添加：

```typescript
const addToolCall = useAppStore((s) => s.addToolCall)
const updateToolResult = useAppStore((s) => s.updateToolResult)
```

在文件顶部 import：

```typescript
import type { ToolCall } from "./types"
```

- [ ] **Step 2: 在 switch 中添加 tool.call case**

在 `case "thinking.end":` 之后添加：

```typescript
case "tool.call": {
  const tc: ToolCall = {
    toolCallId: (event.tool_call_id as string) ?? "",
    toolName: (event.tool_name as string) ?? "",
    args: (event.args as Record<string, unknown>) ?? {},
    status: "running",
  }
  addToolCall(tc)
  break
}
```

- [ ] **Step 3: 在 switch 中添加 tool.result case**

在 `case "tool.call"` 块之后添加：

```typescript
case "tool.result": {
  const tcId = (event.tool_call_id as string) ?? ""
  const result = (event.result as string) ?? ""
  updateToolResult(tcId, result)
  break
}
```

- [ ] **Step 4: 验证**

运行 `cd webui && npx tsc --noEmit`。

---

## Task 8: 前端 ToolCallBlock 组件

**Files:**
- Create: `webui/src/components/ToolCallBlock.tsx`

- [ ] **Step 1: 创建 ToolCallBlock 组件**

```tsx
import { useState } from "react"
import { Tag, Typography } from "antd"
import { LoadingOutlined, CheckCircleOutlined, ToolOutlined } from "@ant-design/icons"
import type { ToolCall } from "../types"

const { Text } = Typography

function formatArgs(args: Record<string, unknown>): string {
  const entries = Object.entries(args)
  if (entries.length === 0) return ""
  return entries
    .map(([k, v]) => `${k}: ${typeof v === "string" ? v : JSON.stringify(v)}`)
    .join("\n")
}

function truncateResult(result: string, maxLen = 500): string {
  if (result.length <= maxLen) return result
  return result.slice(0, maxLen) + `... (${result.length} chars total)`
}

export function ToolCallBlock({ toolCall }: { toolCall: ToolCall }) {
  const [expanded, setExpanded] = useState(false)
  const isRunning = toolCall.status === "running"
  const argsStr = formatArgs(toolCall.args)

  const mainArg =
    toolCall.args.path ||
    toolCall.args.pattern ||
    toolCall.args.query ||
    toolCall.args.command ||
    toolCall.args.name ||
    ""

  return (
    <div
      style={{
        margin: "4px 0",
        border: "1px solid #e8e8e8",
        borderRadius: 6,
        overflow: "hidden",
        fontSize: 13,
      }}
    >
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          padding: "6px 10px",
          cursor: "pointer",
          background: isRunning ? "#fafafa" : "#f6f6f6",
          userSelect: "none",
        }}
      >
        {isRunning ? (
          <LoadingOutlined style={{ color: "#1677ff" }} />
        ) : (
          <CheckCircleOutlined style={{ color: "#52c41a" }} />
        )}
        <ToolOutlined style={{ color: "#999" }} />
        <Tag
          color={isRunning ? "processing" : "default"}
          style={{ margin: 0, fontSize: 11 }}
        >
          {toolCall.toolName}
        </Tag>
        {mainArg && (
          <Text
            type="secondary"
            ellipsis
            style={{ flex: 1, fontSize: 12, maxWidth: 400 }}
          >
            {String(mainArg)}
          </Text>
        )}
        <Text type="secondary" style={{ fontSize: 11 }}>
          {expanded ? "▲" : "▼"}
        </Text>
      </div>
      {expanded && (
        <div
          style={{
            padding: "8px 12px",
            borderTop: "1px solid #f0f0f0",
            background: "#fafafa",
          }}
        >
          {argsStr && (
            <div style={{ marginBottom: 6 }}>
              <Text type="secondary" style={{ fontSize: 11 }}>
                Arguments:
              </Text>
              <pre
                style={{
                  margin: "2px 0 0",
                  fontSize: 12,
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-all",
                  background: "#f5f5f5",
                  padding: 6,
                  borderRadius: 4,
                }}
              >
                {argsStr}
              </pre>
            </div>
          )}
          {toolCall.result !== undefined && (
            <div>
              <Text type="secondary" style={{ fontSize: 11 }}>
                Result:
              </Text>
              <pre
                style={{
                  margin: "2px 0 0",
                  fontSize: 12,
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-all",
                  background: "#f5f5f5",
                  padding: 6,
                  borderRadius: 4,
                  maxHeight: 300,
                  overflow: "auto",
                }}
              >
                {truncateResult(toolCall.result)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function ToolCallList({ toolCalls }: { toolCalls: ToolCall[] }) {
  if (toolCalls.length === 0) return null
  return (
    <div style={{ margin: "4px 0" }}>
      {toolCalls.map((tc) => (
        <ToolCallBlock key={tc.toolCallId} toolCall={tc} />
      ))}
    </div>
  )
}
```

- [ ] **Step 2: 验证**

运行 `cd webui && npx tsc --noEmit`。

---

## Task 9: ChatPanel.tsx 集成工具调用展示

**Files:**
- Modify: `webui/src/components/ChatPanel.tsx`

- [ ] **Step 1: 导入 ToolCallList 组件和 ToolCall 类型**

在 `ChatPanel.tsx` import 区域添加：

```typescript
import { ToolCallList } from "./ToolCallBlock"
import type { ToolCall } from "../types"
```

- [ ] **Step 2: 扩展 ChatItem 接口**

在 `ChatItem` 接口中，`isThinking?: boolean` 之后添加：

```typescript
toolCalls?: ToolCall[]
```

- [ ] **Step 3: 更新 messagesToItems 函数**

函数签名增加 `activeToolCalls: ToolCall[]` 参数：

```typescript
function messagesToItems(
  messages: Message[],
  streamingText: string,
  streamingMessageId: string,
  thinkingText: string,
  isThinking: boolean,
  activeToolCalls: ToolCall[],
): ChatItem[] {
```

在 `messages.map` 中添加 `toolCalls` 映射：

```typescript
toolCalls: m.tool_calls?.length ? m.tool_calls : undefined,
```

streaming item 条件和内容更新：

```typescript
if (streamingMessageId && (streamingText || isThinking || activeToolCalls.length > 0)) {
  items.push({
    key: streamingMessageId,
    role: "ai",
    content: streamingText,
    thinkingText,
    isThinking,
    toolCalls: activeToolCalls.length > 0 ? activeToolCalls : undefined,
  })
}
```

- [ ] **Step 4: 传入 activeToolCalls**

在 `ChatPanel` 组件中，从 store 获取 `activeToolCalls`：

```typescript
const activeToolCalls = useAppStore((s) => s.activeToolCalls)
```

更新 `messagesToItems` 调用：

```typescript
const items = messagesToItems(messages, streamingText, streamingMessageId, thinkingText, isThinking, activeToolCalls)
```

- [ ] **Step 5: 在 Bubble items 中渲染 toolCalls**

将 `items.map` 的返回值改为统一在 item 级别设置 footer（移除 `role.ai.footer`）：

```typescript
items.map((item, idx) => {
  const isStreamingBubble =
    isLastItemStreaming &&
    idx === items.length - 1 &&
    item.role === "ai"
  const hasToolCalls = item.toolCalls && item.toolCalls.length > 0
  return {
    key: item.key,
    content: item.content,
    role: item.role,
    streaming: isStreamingBubble,
    header: (item.thinkingText || item.isThinking)
      ? ((
          <Think
            loading={item.isThinking}
            blink={item.isThinking}
            style={{ marginBottom: 4 }}
          >
            {item.thinkingText && <MarkdownContent>{item.thinkingText}</MarkdownContent>}
          </Think>
        ) as React.ReactNode)
      : undefined,
    footer: item.role === "ai"
      ? ((
          <>
            {hasToolCalls && <ToolCallList toolCalls={item.toolCalls!} />}
            <div style={{ borderTop: "1px solid #f0f0f0", marginTop: 4, paddingTop: 4, display: "flex", justifyContent: "flex-end" }}>
              <CopyRawButton text={item.content} />
            </div>
          </>
        ) as React.ReactNode)
      : undefined,
  }
})
```

并从 `role.ai` 配置中**移除** `footer` 属性（保留 `contentRender`）。

- [ ] **Step 6: 更新用户消息添加 tool_calls**

在 `handleSubmit` 中，用户消息构造添加 `tool_calls: []`：

```typescript
store.addMessage({
  id: crypto.randomUUID(),
  session_id: store.currentSessionId,
  role: "user",
  content: message,
  thinking_content: null,
  tool_calls: [],
  model_id: null,
  tokens_in: null,
  tokens_out: null,
  duration_ms: null,
  created_at: new Date().toISOString(),
})
```

- [ ] **Step 7: 验证**

运行 `cd webui && npx tsc --noEmit`。启动 dev 环境，发送一条会触发工具调用的消息，确认工具调用块正确显示。

---

## Task 10: 端到端验证

**Files:** 无新文件

- [ ] **Step 1: 后端 debug 日志验证**

1. 设置 `VAR_DEBUG=true`
2. 启动后端
3. 通过 WebUI 发送消息
4. 确认 stderr 输出包含：`ws connected`、`stream_chat start`、`text.start`、`tool.call`、`tool.result`、`stream.done`、`ws disconnected` 等日志
5. 不设置 debug 时确认只有 INFO 级别日志

- [ ] **Step 2: 前端工具调用展示验证**

1. 启动 WebUI dev server
2. 创建新 session
3. 发送需要工具调用的消息
4. 确认：工具调用块出现、运行中显示 loading、完成后显示对勾、可展开查看参数和结果
5. 切换 session 后确认历史消息中的工具调用正确显示
6. Copy 按钮正常工作

- [ ] **Step 3: 最终 commit**

```bash
git add -A
git commit -m "feat: add debug logging and tool call display"
```
