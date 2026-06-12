export interface Session {
  id: string
  title: string
  model_id: string
  system_prompt: string | null
  created_at: string
  updated_at: string
}

export interface SessionStats {
  total_input_tokens: number
  total_output_tokens: number
  total_tokens: number
  context_tokens: number
  message_count: number
}

export interface SessionDetail extends Session {
  messages: Message[]
  stats: SessionStats
}

export interface ToolCall {
  toolCallId: string
  toolName: string
  args: Record<string, unknown>
  result?: string
  status: "running" | "done"
}

export interface TextSegment {
  type: "text"
  content: string
}

export interface ToolCallSegment {
  type: "tool_call"
  toolCall: ToolCall
}

export type StreamSegment = TextSegment | ToolCallSegment

export interface Message {
  id: string
  session_id: string
  role: "user" | "assistant"
  content: string
  thinking_content: string | null
  tool_calls: ToolCall[]
  segments?: StreamSegment[]
  model_id: string | null
  tokens_in: number | null
  tokens_out: number | null
  duration_ms: number | null
  created_at: string
}

export interface ThinkingMessage {
  messageId: string
  text: string
  isThinking: boolean
}

export interface Model {
  id: string
  name: string
  provider: string
  provider_prefix: string
  context_window: number
  max_output_tokens: number
}

export type AppStatus = "idle" | "streaming" | "thinking" | "error"
