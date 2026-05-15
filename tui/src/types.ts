export interface Session {
  id: string
  title: string
  model_id: string
  system_prompt: string | null
  created_at: string
  updated_at: string
}

export interface SessionDetail extends Session {
  messages: Message[]
}

export interface Message {
  id: string
  session_id: string
  role: "user" | "assistant"
  content: string
  model_id: string | null
  tokens_in: number | null
  tokens_out: number | null
  duration_ms: number | null
  created_at: string
}

export interface Model {
  id: string
  name: string
  provider: string
  provider_prefix: string
  context_window: number
  max_output_tokens: number
}

export interface Memory {
  id: string
  session_id: string
  content: string
  category: string
  created_at: string
  relevance_score?: number
}

export interface ToolCall {
  tool_call_id: string
  tool_name: string
  args: Record<string, unknown>
  result?: string
  duration_ms?: number
}
