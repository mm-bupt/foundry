# 05 — WebSocket / SSE Protocol

## Protocol Negotiation

```
TUI                         Server
 │                            │
 │── WS connect ──────────────▶│  ← Try WebSocket first
 │◀── WS accept ──────────────│
 │                            │
 │── ping ────────────────────▶│  ← Heartbeat every 30s
 │◀── pong ───────────────────│
 │                            │
 │   (if WS fails)            │
 │── GET /api/chat/stream ────▶│  ← Fall back to SSE
 │◀── SSE: stream.delta ──────│
```

The `ConnectionManager` in the TUI handles protocol selection:

1. Default: attempt WebSocket connection
2. If WS connect fails (timeout 5s, proxy block, etc.): fall back to SSE
3. User can override via config (`protocol: "ws" | "sse"`)
4. UI code subscribes to a unified event stream, protocol is transparent

## WebSocket Protocol

### Message Format

All messages are JSON. Every message has a `type` field.

### Client → Server

#### Send Chat Message

```json
{
  "type": "chat.message",
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "Write a quicksort in Python"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | yes | `"chat.message"` |
| `message_id` | string (UUID) | yes | Client-generated message ID |
| `content` | string | yes | User message text |

#### Interrupt Generation

```json
{
  "type": "chat.interrupt"
}
```

Sent when user presses `Ctrl+\` or submits a new message while generation is ongoing.

#### Heartbeat

```json
{
  "type": "ping"
}
```

Sent every 30 seconds. Server must respond with `pong` within 60 seconds or client considers connection dead.

### Server → Client

#### Stream Delta (text chunk)

```json
{
  "type": "stream.delta",
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "part_id": "660e8400-e29b-41d4-a716-446655440001",
  "text": "Here is the quicksort"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `message_id` | UUID | Matches the client's original message ID |
| `part_id` | UUID | Identifies the response part (for multi-part messages) |
| `text` | string | Incremental text chunk |

#### Stream Done

```json
{
  "type": "stream.done",
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "usage": {
    "input_tokens": 150,
    "output_tokens": 320,
    "total_tokens": 470
  },
  "duration_ms": 3200
}
```

#### Stream Error

```json
{
  "type": "stream.error",
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "error": {
    "code": "rate_limit",
    "message": "OpenAI rate limit exceeded. Retry after 20s."
  }
}
```

#### Tool Call Started

```json
{
  "type": "tool.call",
  "tool_call_id": "770e8400-e29b-41d4-a716-446655440002",
  "tool_name": "recall_memory",
  "args": {
    "query": "user preferences",
    "limit": 5
  }
}
```

#### Tool Call Completed

```json
{
  "type": "tool.result",
  "tool_call_id": "770e8400-e29b-41d4-a716-446655440002",
  "tool_name": "recall_memory",
  "result": "- [preference] User prefers Chinese responses\n- [preference] User prefers concise answers",
  "duration_ms": 150
}
```

#### Thinking Delta (reasoning)

```json
{
  "type": "thinking.delta",
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "text": "The user wants a quicksort. I should..."
}
```

Only sent if the model supports thinking/reasoning output (e.g., Claude extended thinking).

#### Memory Stored

```json
{
  "type": "memory.stored",
  "memory_id": "880e8400-e29b-41d4-a716-446655440003",
  "content": "User prefers Chinese responses",
  "category": "preference"
}
```

Sent as a side-effect notification when `store_memory` tool is called. TUI can update the context panel.

#### Pong

```json
{
  "type": "pong"
}
```

### Error Codes

| Code | Description | Recovery |
|------|-------------|----------|
| `rate_limit` | Provider rate limit | Auto-retry after delay |
| `provider_error` | Upstream API error | Show error, user can retry |
| `context_overflow` | History too long | Auto-trim + summarize |
| `model_not_available` | Model ID invalid | Switch to default model |
| `session_not_found` | Invalid session ID | Create new session |
| `internal_error` | Unexpected error | Show generic error |

## SSE Protocol (Fallback)

### Connection

```
GET /api/chat/{session_id}/stream
Accept: text/event-stream
Last-Event-ID: 1234  ← optional, for reconnection
```

### Sending Messages (SSE Mode)

Since SSE is unidirectional (server → client), messages are sent via HTTP POST:

```
POST /api/chat/{session_id}
Content-Type: application/json

{
  "content": "Write a quicksort",
  "message_id": "uuid"
}
```

### Event Stream Format

SSE events use the same JSON payload as WebSocket messages, wrapped in SSE format:

```
id: 1
event: stream.delta
data: {"message_id":"uuid","part_id":"uuid","text":"Here is"}

id: 2
event: stream.delta
data: {"message_id":"uuid","part_id":"uuid","text":" the quicksort"}

id: 3
event: tool.call
data: {"tool_call_id":"uuid","tool_name":"recall_memory","args":{"query":"user pref"}}

id: 4
event: tool.result
data: {"tool_call_id":"uuid","tool_name":"recall_memory","result":"User prefers..."}

id: 5
event: stream.done
data: {"message_id":"uuid","usage":{"input_tokens":150,"output_tokens":320},"duration_ms":3200}
```

### SSE Event Types

| Event | Matches WS type |
|-------|----------------|
| `stream.delta` | `stream.delta` |
| `stream.done` | `stream.done` |
| `stream.error` | `stream.error` |
| `tool.call` | `tool.call` |
| `tool.result` | `tool.result` |
| `thinking.delta` | `thinking.delta` |
| `memory.stored` | `memory.stored` |

### SSE Keepalive

Server sends a comment line every 15 seconds:

```
: keepalive
```

Client reconnects if no events received within 45 seconds.

## Shared Type Definitions (Python)

```python
# shared/protocol.py

from dataclasses import dataclass, field
from typing import Any

@dataclass
class ChatMessage:
    type: str = "chat.message"
    message_id: str = ""
    content: str = ""

@dataclass
class StreamDelta:
    type: str = "stream.delta"
    message_id: str = ""
    part_id: str = ""
    text: str = ""

@dataclass
class StreamDone:
    type: str = "stream.done"
    message_id: str = ""
    usage: dict = field(default_factory=dict)
    duration_ms: int = 0

@dataclass
class StreamError:
    type: str = "stream.error"
    message_id: str = ""
    error: dict = field(default_factory=dict)

@dataclass
class ToolCall:
    type: str = "tool.call"
    tool_call_id: str = ""
    tool_name: str = ""
    args: dict = field(default_factory=dict)

@dataclass
class ToolResult:
    type: str = "tool.result"
    tool_call_id: str = ""
    tool_name: str = ""
    result: str = ""
    duration_ms: int = 0

@dataclass
class ThinkingDelta:
    type: str = "thinking.delta"
    message_id: str = ""
    text: str = ""

@dataclass
class MemoryStored:
    type: str = "memory.stored"
    memory_id: str = ""
    content: str = ""
    category: str = ""

@dataclass
class Ping:
    type: str = "ping"

@dataclass
class Pong:
    type: str = "pong"
```
