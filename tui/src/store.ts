import { createSignal } from "solid-js"

export interface Session {
  id: string
  title: string
  model_id: string
  system_prompt: string
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  session_id: string
  role: string
  content: string
  model_id?: string
  duration_ms?: number
  created_at: string
}

export interface Model {
  id: string
  name: string
  provider: string
  context_window: number
}

export interface Memory {
  id: string
  session_id: string
  content: string
  category: string
  created_at: string
}

export interface ToolCall {
  tool_call_id: string
  tool_name: string
  args: Record<string, unknown>
  result?: string
}

export function createAppStore() {
  const [sessions, setSessions] = createSignal<Session[]>([])
  const [currentSessionId, setCurrentSessionId] = createSignal("")
  const [currentModel, setCurrentModel] = createSignal("claude-sonnet")
  const [models, setModels] = createSignal<Model[]>([])
  const [messages, setMessages] = createSignal<Message[]>([])
  const [memories, setMemories] = createSignal<Memory[]>([])
  const [connected, setConnected] = createSignal(false)
  const [streaming, setStreaming] = createSignal(false)
  const [streamingText, setStreamingText] = createSignal("")
  const [pendingToolCalls, setPendingToolCalls] = createSignal<Record<string, ToolCall>>({})
  const [sidebarVisible, setSidebarVisible] = createSignal(true)
  const [contextPanel, setContextPanel] = createSignal(false)
  const [route, setRoute] = createSignal<"home" | "session">("home")
  const [statusMessage, setStatusMessage] = createSignal("")
  const [inputText, setInputText] = createSignal("")
  const [showModelPicker, setShowModelPicker] = createSignal(false)

  function addMessage(msg: Message) {
    setMessages((prev) => [...prev, msg])
  }

  function appendStreamingText(text: string) {
    setStreamingText((prev) => prev + text)
  }

  function finalizeStreamingMessage(messageId: string, durationMs?: number) {
    const text = streamingText()
    if (text) {
      addMessage({
        id: messageId,
        session_id: currentSessionId(),
        role: "assistant",
        content: text,
        model_id: currentModel(),
        duration_ms: durationMs,
        created_at: new Date().toISOString(),
      })
    }
    setStreamingText("")
    setStreaming(false)
    setPendingToolCalls({})
  }

  function addToolCall(tc: ToolCall) {
    setPendingToolCalls((prev) => ({ ...prev, [tc.tool_call_id]: tc }))
  }

  function resolveToolCall(toolCallId: string, result: string) {
    setPendingToolCalls((prev) => {
      const existing = prev[toolCallId]
      if (!existing) return prev
      return { ...prev, [toolCallId]: { ...existing, result } }
    })
  }

  return {
    sessions, setSessions,
    currentSessionId, setCurrentSessionId,
    currentModel, setCurrentModel,
    models, setModels,
    messages, setMessages,
    memories, setMemories,
    connected, setConnected,
    streaming, setStreaming,
    streamingText, setStreamingText,
    pendingToolCalls, setPendingToolCalls,
    sidebarVisible, setSidebarVisible,
    contextPanel, setContextPanel,
    route, setRoute,
    statusMessage, setStatusMessage,
    inputText, setInputText,
    showModelPicker, setShowModelPicker,
    addMessage,
    appendStreamingText,
    finalizeStreamingMessage,
    addToolCall,
    resolveToolCall,
  }
}

export type AppStore = ReturnType<typeof createAppStore>
