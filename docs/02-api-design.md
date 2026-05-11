# 02 — API Design

## Base URL

```
http://localhost:8000
```

## WebSocket Endpoint (Default)

### `ws://localhost:8000/ws/{session_id}`

Bidirectional real-time communication. Default transport.

**Client → Server messages:**

| type | Fields | Description |
|------|--------|-------------|
| `chat.message` | `content: str`, `message_id: str` | Send a user message |
| `chat.interrupt` | _(none)_ | Interrupt ongoing generation |
| `ping` | _(none)_ | Heartbeat keepalive |

**Server → Client messages:**

| type | Fields | Description |
|------|--------|-------------|
| `stream.delta` | `message_id`, `part_id`, `text` | Streaming text chunk |
| `stream.done` | `message_id`, `usage` | Generation complete |
| `stream.error` | `message_id`, `error` | Generation failed |
| `tool.call` | `tool_call_id`, `tool_name`, `args` | Tool invocation started |
| `tool.result` | `tool_call_id`, `tool_name`, `result` | Tool completed |
| `thinking.delta` | `message_id`, `text` | Thinking/reasoning chunk |
| `memory.stored` | `content`, `category` | Memory entry stored |
| `pong` | _(none)_ | Heartbeat response |

**Heartbeat:**
- Client sends `ping` every 30 seconds
- Server closes connection if no ping received within 60 seconds
- Client auto-reconnects with exponential backoff (1s, 2s, 4s, 8s, max 30s)

**Reconnection:**
- On reconnect, client replays the last `message_id` it received
- Server can optionally replay missed deltas

---

## REST Endpoints

### Sessions

#### `GET /api/sessions`

List all sessions.

```json
// Response 200
{
  "sessions": [
    {
      "id": "uuid",
      "title": "Quick sort implementation",
      "model_id": "claude-sonnet",
      "created_at": "2026-05-11T10:00:00Z",
      "updated_at": "2026-05-11T10:05:00Z",
      "message_count": 12
    }
  ]
}
```

#### `POST /api/sessions`

Create a new session.

```json
// Request
{
  "title": "New Chat",
  "model_id": "claude-sonnet"
}

// Response 201
{
  "id": "uuid",
  "title": "New Chat",
  "model_id": "claude-sonnet",
  "created_at": "2026-05-11T10:00:00Z",
  "updated_at": "2026-05-11T10:00:00Z",
  "message_count": 0
}
```

#### `GET /api/sessions/{session_id}`

Get session detail with messages.

```json
// Response 200
{
  "id": "uuid",
  "title": "Quick sort implementation",
  "model_id": "claude-sonnet",
  "created_at": "2026-05-11T10:00:00Z",
  "updated_at": "2026-05-11T10:05:00Z",
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "Write a quicksort",
      "created_at": "2026-05-11T10:00:00Z"
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "Here is the implementation...",
      "model": "claude-sonnet",
      "duration_ms": 3200,
      "usage": { "input_tokens": 50, "output_tokens": 120 },
      "created_at": "2026-05-11T10:00:05Z"
    }
  ]
}
```

#### `PATCH /api/sessions/{session_id}`

Update session (title, model).

```json
// Request
{
  "title": "Updated title",
  "model_id": "gpt-4o"
}

// Response 200
{ /* updated session */ }
```

#### `DELETE /api/sessions/{session_id}`

Delete a session and all its messages.

```
// Response 204 No Content
```

---

### Chat (SSE fallback mode)

#### `POST /api/chat/{session_id}`

Send a message (SSE mode — initiate generation).

```json
// Request
{
  "content": "Hello",
  "message_id": "uuid"
}

// Response 202 Accepted
{
  "message_id": "uuid",
  "status": "processing"
}
```

#### `GET /api/chat/{session_id}/stream`

SSE stream for real-time events.

```
// Response: text/event-stream
event: stream.delta
data: {"message_id": "uuid", "part_id": "uuid", "text": "Hello"}

event: stream.delta
data: {"message_id": "uuid", "part_id": "uuid", "text": " world"}

event: tool.call
data: {"tool_call_id": "uuid", "tool_name": "recall_memory", "args": {"query": "user preferences"}}

event: tool.result
data: {"tool_call_id": "uuid", "tool_name": "recall_memory", "result": "User prefers Chinese"}

event: stream.done
data: {"message_id": "uuid", "usage": {"input_tokens": 50, "output_tokens": 120}}
```

**SSE reconnection:** Uses `Last-Event-ID` header to resume from last received event.

---

### Models

#### `GET /api/models`

List available models.

```json
// Response 200
{
  "models": [
    {
      "id": "gpt-4o",
      "name": "GPT-4o",
      "provider": "openai",
      "provider_prefix": "openai:gpt-4o",
      "context_window": 128000,
      "max_output_tokens": 16384
    },
    {
      "id": "claude-sonnet",
      "name": "Claude Sonnet 4",
      "provider": "anthropic",
      "provider_prefix": "anthropic:claude-sonnet-4-20250514",
      "context_window": 200000,
      "max_output_tokens": 8192
    },
    {
      "id": "claude-haiku",
      "name": "Claude Haiku 4",
      "provider": "anthropic",
      "provider_prefix": "anthropic:claude-haiku-4-20250414",
      "context_window": 200000,
      "max_output_tokens": 8192
    },
    {
      "id": "gpt-4o-mini",
      "name": "GPT-4o Mini",
      "provider": "openai",
      "provider_prefix": "openai:gpt-4o-mini",
      "context_window": 128000,
      "max_output_tokens": 16384
    }
  ]
}
```

#### `GET /api/models/active`

Get currently active model for default session.

```json
{
  "model_id": "claude-sonnet",
  "provider": "anthropic"
}
```

---

### Memory

#### `GET /api/memory/{session_id}`

List memory entries for a session.

```json
// Response 200
{
  "memories": [
    {
      "id": "uuid",
      "content": "User prefers Chinese responses",
      "category": "preference",
      "created_at": "2026-05-11T10:00:00Z",
      "relevance_score": null
    }
  ]
}
```

#### `POST /api/memory/{session_id}/search`

Search memories by semantic similarity.

```json
// Request
{
  "query": "user language preference",
  "limit": 5
}

// Response 200
{
  "memories": [
    {
      "id": "uuid",
      "content": "User prefers Chinese responses",
      "category": "preference",
      "created_at": "2026-05-11T10:00:00Z",
      "relevance_score": 0.92
    }
  ]
}
```

#### `DELETE /api/memory/{memory_id}`

Delete a specific memory entry.

```
// Response 204 No Content
```

---

### Health

#### `GET /api/health`

```json
{
  "status": "ok",
  "version": "0.1.0",
  "db": "connected"
}
```

---

## Error Response Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "session_not_found",
    "message": "Session with id 'abc' not found"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|------------|-------------|
| `session_not_found` | 404 | Session ID does not exist |
| `model_not_available` | 400 | Model ID not in registry |
| `rate_limit` | 429 | Provider rate limit hit |
| `provider_error` | 502 | Upstream provider error |
| `context_overflow` | 400 | Message history exceeds context window |
| `generation_interrupted` | 499 | Client disconnected mid-generation |
| `internal_error` | 500 | Unexpected server error |
