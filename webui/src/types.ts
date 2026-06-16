export interface Session {
  id: string
  title: string
  model_id: string
  system_prompt: string | null
  parent_id: string | null
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
  task_records: TaskRecord[]
  todos: TodoItem[]
}

export interface TaskRecord {
  id: string
  parent_session_id: string
  parent_message_id: string | null
  subagent_type: string
  description: string
  status: "running" | "completed" | "error" | "cancelled"
  background: boolean
  result_preview: string | null
  created_at: string
  completed_at: string | null
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

export interface TaskCallSegment {
  type: "task_call"
  taskId: string
  subagentType: string
  description: string
  status: "running" | "completed" | "error"
  background: boolean
  result?: string
  subSegments: StreamSegment[]
}

export type StreamSegment = TextSegment | ToolCallSegment | TaskCallSegment

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

export type AppStatus = "idle" | "streaming" | "thinking" | "error" | "waiting_answer"

export interface QuestionOption {
  label: string
  description: string
}

export interface QuestionInfo {
  question: string
  header: string
  options: QuestionOption[]
  multiple?: boolean
}

export interface PendingQuestion {
  questionId: string
  sessionId: string
  questions: QuestionInfo[]
  submittedAnswers?: string[][]
}

export interface TodoItem {
  content: string
  status: "pending" | "in_progress" | "completed" | "cancelled"
  priority: "high" | "medium" | "low"
}
