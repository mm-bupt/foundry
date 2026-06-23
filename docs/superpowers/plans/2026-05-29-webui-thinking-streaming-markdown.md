# WebUI Thinking, Streaming, Markdown Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add thinking display, true streaming deltas, and markdown rendering to the Var WebUI.

**Architecture:** Fix backend `core.py` to use `ModelRequestNode.stream()` for real incremental deltas (text + thinking), then update frontend to render markdown via `react-markdown` + `remark-gfm` and display thinking via `@ant-design/x` `Think` component.

**Tech Stack:** Python/pydantic_ai (backend), React/TypeScript/antd/@ant-design/x (frontend), react-markdown/remark-gfm (markdown)

---

## File Structure

### Backend
- Modify: `var/var_app/agent/core.py` — rewrite streaming to use `ModelRequestNode.stream()`, emit thinking events
- Modify: `var/var_app/shared_protocol.py` — add `thinking.start` and `thinking.end` event types

### Frontend
- Modify: `webui/package.json` — add react-markdown, remark-gfm
- Modify: `webui/src/types.ts` — add thinking state types
- Modify: `webui/src/store.ts` — add thinking state + actions
- Modify: `webui/src/App.tsx` — handle thinking WS events
- Modify: `webui/src/components/ChatPanel.tsx` — Think component, MarkdownContent, remove fake typing
- Create: `webui/src/components/MarkdownContent.tsx` — markdown rendering component

---

### Task 1: Backend — Rewrite streaming in core.py

**Files:**
- Modify: `var/var_app/agent/core.py`

- [ ] **Step 1: Add new imports to core.py**

Add at the top of core.py imports:

```python
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
    ThinkingPart,
    TextPartDelta,
    ThinkingPartDelta,
    PartStartEvent,
    PartDeltaEvent,
    PartEndEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
)
from pydantic_ai.agent import ModelRequestNode, CallToolsNode
```

- [ ] **Step 2: Rewrite stream_chat() to handle both node types**

Replace the entire `stream_chat` function body. The key change: handle `ModelRequestNode` with `.stream()` for real deltas, and `CallToolsNode` for tool events.

```python
async def stream_chat(
    session_id: str,
    user_message: str,
    send_event: Callable[[dict], Awaitable[None]],
):
    db = await get_db()
    session = await crud.get_session(db, session_id)
    if not session:
        await send_event(
            {
                "type": "stream.error",
                "error": {
                    "code": "session_not_found",
                    "message": f"Session '{session_id}' not found",
                },
            }
        )
        return

    model_id = session["model_id"]
    model_info = get_model_info(model_id)
    if not model_info:
        await send_event(
            {
                "type": "stream.error",
                "error": {
                    "code": "model_not_available",
                    "message": f"Model '{model_id}' not found",
                },
            }
        )
        return

    user_msg = await crud.create_message(db, session_id, "user", user_message)

    messages = await crud.list_messages(db, session_id)
    history = _load_history(messages[:-1])

    agent = create_agent(model_id, session.get("system_prompt", ""))
    deps = AgentDeps(session_id=session_id, model_id=model_id, send_event=send_event)

    start_time = time.monotonic()
    assistant_id = None
    full_text = ""
    thinking_text = ""
    input_tokens = 0
    output_tokens = 0

    try:
        async with agent.iter(user_message, message_history=history, deps=deps) as run:
            async for node in run:
                if isinstance(node, ModelRequestNode):
                    async with node.stream(run.ctx) as agent_stream:
                        async for event in agent_stream:
                            if isinstance(event, PartStartEvent):
                                if isinstance(event.part, ThinkingPart):
                                    await send_event({
                                        "type": "thinking.start",
                                        "message_id": user_msg["id"],
                                    })
                                elif isinstance(event.part, TextPart):
                                    if not assistant_id:
                                        assistant_id = (
                                            await crud.create_message(
                                                db,
                                                session_id,
                                                "assistant",
                                                "",
                                                model_id=model_id,
                                            )
                                        )["id"]
                                    await send_event({
                                        "type": "thinking.end",
                                        "message_id": user_msg["id"],
                                    })
                            elif isinstance(event, PartDeltaEvent):
                                if isinstance(event.delta, TextPartDelta):
                                    delta_text = event.delta.content_delta
                                    if delta_text:
                                        full_text += delta_text
                                        await send_event({
                                            "type": "stream.delta",
                                            "message_id": user_msg["id"],
                                            "part_id": assistant_id or "",
                                            "text": delta_text,
                                        })
                                elif isinstance(event.delta, ThinkingPartDelta):
                                    delta_thinking = event.delta.content_delta
                                    if delta_thinking:
                                        thinking_text += delta_thinking
                                        await send_event({
                                            "type": "thinking.delta",
                                            "message_id": user_msg["id"],
                                            "text": delta_thinking,
                                        })
                            elif isinstance(event, PartEndEvent):
                                pass
                        model_response = agent_stream.response
                        for part in model_response.parts:
                            if isinstance(part, ToolCallPart):
                                tc_id = part.tool_call_id or ""
                                tool_name = part.tool_name
                                args = (
                                    part.args_as_dict()
                                    if hasattr(part, "args_as_dict")
                                    else (part.args if isinstance(part.args, dict) else {})
                                )
                                await send_event({
                                    "type": "tool.call",
                                    "tool_call_id": tc_id,
                                    "tool_name": tool_name,
                                    "args": args,
                                })

                elif isinstance(node, CallToolsNode):
                    async with node.stream(run.ctx) as stream:
                        async for event in stream:
                            if isinstance(event, FunctionToolResultEvent):
                                result_part = event.result
                                if isinstance(result_part, ToolReturnPart):
                                    tc_id = result_part.tool_call_id or ""
                                    await send_event({
                                        "type": "tool.result",
                                        "tool_call_id": tc_id,
                                        "tool_name": "",
                                        "result": str(result_part.content),
                                    })

        result = run.result
        if result:
            if not full_text and result.output:
                full_text = str(result.output)
                if not assistant_id:
                    assistant_id = (
                        await crud.create_message(
                            db, session_id, "assistant", full_text, model_id=model_id
                        )
                    )["id"]
                else:
                    await crud.update_message(db, assistant_id, content=full_text)

            usage = result.usage()
            if usage:
                input_tokens = usage.request_tokens or 0
                output_tokens = usage.response_tokens or 0

            all_msgs = result.all_messages()
            if assistant_id:
                await crud.update_message(
                    db,
                    assistant_id,
                    content=full_text,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    duration_ms=int((time.monotonic() - start_time) * 1000),
                    model_messages_json=json.dumps(
                        [_serialize_msg(m) for m in all_msgs], default=str
                    ),
                )

        duration = int((time.monotonic() - start_time) * 1000)
        await send_event(
            {
                "type": "stream.done",
                "message_id": user_msg["id"],
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                },
                "duration_ms": duration,
            }
        )

        if (
            session.get("title") == "New Chat"
            and len(messages) <= 1
        ):
            from var_app.agent.title import generate_title
            asyncio.create_task(generate_title(session_id, model_id, user_message, send_event))

    except Exception as e:
        print(f"[stream_chat] EXCEPTION: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        await send_event(
            {
                "type": "stream.error",
                "message_id": user_msg["id"],
                "error": {"code": "internal_error", "message": str(e)},
            }
        )
```

- [ ] **Step 3: Remove old ThinkingPart and PartDeltaEvent imports that are not needed**

Ensure the imports section has all the new types listed in Step 1 and remove any unused imports. The old import block referenced `ToolCallPart` and `ToolReturnPart` — keep those, add the new ones.

- [ ] **Step 4: Verify no lint errors**

Run: `cd var && python -c "from var_app.agent.core import stream_chat; print('OK')"`

---

### Task 2: Frontend — Add markdown dependencies

**Files:**
- Modify: `webui/package.json`

- [ ] **Step 1: Install react-markdown and remark-gfm**

Run: `cd webui && bun add react-markdown remark-gfm`

- [ ] **Step 2: Verify installation**

Run: `cd webui && bun pm ls | grep -i markdown`

---

### Task 3: Frontend — Create MarkdownContent component

**Files:**
- Create: `webui/src/components/MarkdownContent.tsx`

- [ ] **Step 1: Create the MarkdownContent component**

Create `webui/src/components/MarkdownContent.tsx`:

```tsx
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { CodeHighlighter } from "@ant-design/x"
import type { Components } from "react-markdown"

function CodeBlock({
  className,
  children,
}: {
  className?: string
  children?: React.ReactNode
}) {
  const match = /language-(\w+)/.exec(className || "")
  const lang = match ? match[1] : ""
  const code = String(children).replace(/\n$/, "")

  if (!lang) {
    return (
      <code
        style={{
          background: "#f5f5f5",
          padding: "2px 6px",
          borderRadius: 4,
          fontSize: 13,
        }}
      >
        {code}
      </code>
    )
  }

  return (
    <CodeHighlighter lang={lang} style={{ margin: "8px 0", borderRadius: 8 }}>
      {code}
    </CodeHighlighter>
  )
}

const components: Components = {
  code({ className, children, ...props }) {
    const isBlock = (children as string)?.includes("\n")
    if (isBlock || className) {
      return <CodeBlock className={className}>{children}</CodeBlock>
    }
    return (
      <code
        style={{
          background: "#f5f5f5",
          padding: "2px 6px",
          borderRadius: 4,
          fontSize: 13,
        }}
        {...props}
      >
        {children}
      </code>
    )
  },
  pre({ children }) {
    return <>{children}</>
  },
  p({ children }) {
    return <p style={{ margin: "4px 0", lineHeight: 1.7 }}>{children}</p>
  },
  ul({ children }) {
    return <ul style={{ margin: "4px 0", paddingLeft: 20 }}>{children}</ul>
  },
  ol({ children }) {
    return <ol style={{ margin: "4px 0", paddingLeft: 20 }}>{children}</ol>
  },
  li({ children }) {
    return <li style={{ margin: "2px 0", lineHeight: 1.6 }}>{children}</li>
  },
  blockquote({ children }) {
    return (
      <blockquote
        style={{
          borderLeft: "3px solid #d9d9d9",
          margin: "8px 0",
          padding: "4px 12px",
          color: "#666",
        }}
      >
        {children}
      </blockquote>
    )
  },
  h1({ children }) {
    return <h1 style={{ margin: "12px 0 8px", fontSize: 20 }}>{children}</h1>
  },
  h2({ children }) {
    return <h2 style={{ margin: "10px 0 6px", fontSize: 18 }}>{children}</h2>
  },
  h3({ children }) {
    return <h3 style={{ margin: "8px 0 4px", fontSize: 16 }}>{children}</h3>
  },
  table({ children }) {
    return (
      <table
        style={{
          borderCollapse: "collapse",
          margin: "8px 0",
          width: "100%",
        }}
      >
        {children}
      </table>
    )
  },
  th({ children }) {
    return (
      <th
        style={{
          border: "1px solid #d9d9d9",
          padding: "6px 12px",
          background: "#fafafa",
          textAlign: "left",
        }}
      >
        {children}
      </th>
    )
  },
  td({ children }) {
    return (
      <td
        style={{
          border: "1px solid #d9d9d9",
          padding: "6px 12px",
        }}
      >
        {children}
      </td>
    )
  },
  a({ href, children }) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: "#1677ff" }}>
        {children}
      </a>
    )
  },
}

interface MarkdownContentProps {
  children: string
}

export function MarkdownContent({ children }: MarkdownContentProps) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
      {children}
    </ReactMarkdown>
  )
}
```

- [ ] **Step 2: Verify the component compiles**

Run: `cd webui && npx tsc --noEmit src/components/MarkdownContent.tsx`

---

### Task 4: Frontend — Update types and store for thinking

**Files:**
- Modify: `webui/src/types.ts`
- Modify: `webui/src/store.ts`

- [ ] **Step 1: Update types.ts — add ThinkingMessage type**

Add to `webui/src/types.ts` after the `Message` interface:

```typescript
export interface ThinkingMessage {
  messageId: string
  text: string
  isThinking: boolean
}
```

- [ ] **Step 2: Update store.ts — add thinking state and actions**

In `webui/src/store.ts`, add `thinkingText` and `isThinking` to state, plus actions:

Add import:
```typescript
import type { Session, Message, Model, AppStatus, ThinkingMessage } from "./types"
```

Add to `AppState` interface (after `streamingMessageId: string`):
```typescript
  thinkingText: string
  isThinking: boolean
  thinkingMessageId: string
```

Add to `AppState` interface (actions section):
```typescript
  startThinking: (messageId: string) => void
  appendThinkingText: (text: string) => void
  endThinking: () => void
  clearThinking: () => void
```

Add initial state values (after `streamingMessageId: ""`):
```typescript
    thinkingText: "",
    isThinking: false,
    thinkingMessageId: "",
```

Add action implementations (after `finalizeStream`):
```typescript
  startThinking: (messageId) =>
    set({ isThinking: true, thinkingText: "", thinkingMessageId: messageId }),

  appendThinkingText: (text) =>
    set((s) => ({ thinkingText: s.thinkingText + text })),

  endThinking: () =>
    set({ isThinking: false }),

  clearThinking: () =>
    set({ isThinking: false, thinkingText: "", thinkingMessageId: "" }),
```

Update `switchSession` to clear thinking state:
```typescript
    set({
      currentSessionId: id,
      messages: [],
      status: "idle",
      streamingText: "",
      streamingMessageId: "",
      errorMessage: "",
      thinkingText: "",
      isThinking: false,
      thinkingMessageId: "",
    })
```

- [ ] **Step 3: Verify compilation**

Run: `cd webui && npx tsc --noEmit`

---

### Task 5: Frontend — Handle thinking WS events in App.tsx

**Files:**
- Modify: `webui/src/App.tsx`

- [ ] **Step 1: Add thinking action selectors and WS handlers**

Add selectors after `updateSessionTitle`:
```typescript
  const startThinking = useAppStore((s) => s.startThinking)
  const appendThinkingText = useAppStore((s) => s.appendThinkingText)
  const endThinking = useAppStore((s) => s.endThinking)
```

Add cases to the WS event handler `switch` block (after the `stream.delta` case):
```typescript
        case "thinking.start":
          startThinking((event.message_id as string) ?? "")
          break
        case "thinking.delta":
          appendThinkingText((event.text as string) ?? "")
          break
        case "thinking.end":
          endThinking()
          break
```

- [ ] **Step 2: Verify compilation**

Run: `cd webui && npx tsc --noEmit`

---

### Task 6: Frontend — Update ChatPanel with Think, Markdown, and streaming fix

**Files:**
- Modify: `webui/src/components/ChatPanel.tsx`

- [ ] **Step 1: Update imports**

Replace the imports at top of `ChatPanel.tsx`:

```tsx
import { useRef, useState } from "react"
import { Bubble, Sender, Think } from "@ant-design/x"
import type { BubbleListRef } from "@ant-design/x/es/bubble"
import { Alert, Select } from "antd"
import { useAppStore } from "../store"
import { MarkdownContent } from "./MarkdownContent"
import type { Message } from "../types"
```

- [ ] **Step 2: Update ChatItem to support thinking**

Replace the `ChatItem` interface:

```tsx
interface ChatItem {
  key: string
  role: "user" | "ai"
  content: string
  thinkingText?: string
  isThinking?: boolean
}
```

- [ ] **Step 3: Update messagesToItems to include thinking**

Replace `messagesToItems` function:

```tsx
function messagesToItems(
  messages: Message[],
  streamingText: string,
  streamingMessageId: string,
  thinkingText: string,
  isThinking: boolean,
): ChatItem[] {
  const items: ChatItem[] = messages.map((m) => ({
    key: m.id,
    role: m.role === "assistant" ? ("ai" as const) : ("user" as const),
    content: m.content,
  }))

  if (streamingMessageId && (streamingText || isThinking)) {
    items.push({
      key: streamingMessageId,
      role: "ai",
      content: streamingText,
      thinkingText,
      isThinking,
    })
  }

  return items
}
```

- [ ] **Step 4: Update ChatPanel component — add thinking selectors**

Add after `connected` selector:

```tsx
  const thinkingText = useAppStore((s) => s.thinkingText)
  const isThinking = useAppStore((s) => s.isThinking)
```

Update the `items` call to pass thinking params:

```tsx
  const items = messagesToItems(messages, streamingText, streamingMessageId, thinkingText, isThinking)
```

- [ ] **Step 5: Update Bubble.List — add Think header and Markdown contentRender**

Replace the `<Bubble.List>` section. The `role` config needs `contentRender` for markdown and `header` for thinking:

```tsx
        <Bubble.List
          ref={bubbleListRef}
          autoScroll
          items={items.map((item, idx) => {
            const isStreamingBubble =
              isLastItemStreaming &&
              idx === items.length - 1 &&
              item.role === "ai"
            return {
              key: item.key,
              content: item.content,
              role: item.role,
              streaming: isStreamingBubble,
              header: (item.thinkingText || item.isThinking) ? (
                <Think
                  loading={item.isThinking}
                  blink={item.isThinking}
                  content={item.thinkingText ? <MarkdownContent>{item.thinkingText}</MarkdownContent> : undefined}
                  style={{ marginBottom: 4 }}
                />
              ) : undefined,
            }
          })}
          role={{
            ai: {
              placement: "start" as const,
              variant: "borderless" as const,
              contentRender: (content: string) => <MarkdownContent>{content}</MarkdownContent>,
            },
            user: {
              placement: "end" as const,
            },
          }}
          style={{ height: "100%" }}
        />
```

Note: Removed `typing: { effect: "typing", step: 5, interval: 50 }` — real streaming provides incremental text.

- [ ] **Step 6: Verify full build**

Run: `cd webui && npx tsc --noEmit`

---

### Task 7: Integration test — manual verification

- [ ] **Step 1: Start backend**

Run: `cd var && python -m uvicorn var_app.main:app --host 0.0.0.0 --port 8000 --reload`

- [ ] **Step 2: Start frontend**

Run: `cd webui && bun run dev`

- [ ] **Step 3: Verify streaming**

Send a message, confirm text appears incrementally (not all at once).

- [ ] **Step 4: Verify markdown**

Send "Show me a code example in Python", confirm code block renders with syntax highlighting.

- [ ] **Step 5: Verify thinking**

If using Claude with extended thinking enabled, confirm thinking panel appears and is collapsible.
