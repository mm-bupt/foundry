import { createStore } from "solid-js/store"
import type { Session, Message, Model, Memory, ToolCall } from "./types"

export type AppStatus = "idle" | "streaming" | "thinking" | "error" | "disconnected"

interface AppState {
  sessions: Session[]
  currentSessionId: string
  messages: Message[]
  models: Model[]
  currentModel: string
  status: AppStatus
  streamingText: string
  streamingMessageId: string
  pendingToolCalls: Record<string, ToolCall>
  errorMessage: string
  lastDurationMs: number | null
  lastTokens: { input: number; output: number } | null
  connected: boolean
  contextVisible: boolean
  showModelPicker: boolean
  memories: Memory[]
}

export function createAppStore() {
  const [state, setState] = createStore<AppState>({
    sessions: [],
    currentSessionId: "",
    messages: [],
    models: [],
    currentModel: "claude-sonnet",
    status: "idle",
    streamingText: "",
    streamingMessageId: "",
    pendingToolCalls: {},
    errorMessage: "",
    lastDurationMs: null,
    lastTokens: null,
    connected: false,
    contextVisible: true,
    showModelPicker: false,
    memories: [],
  })

  return {
    state,
    setState,

    setSessions: (sessions: Session[]) => setState({ sessions }),
    setCurrentSession: (id: string) => setState({ currentSessionId: id }),
    setMessages: (messages: Message[]) => setState({ messages }),
    addMessage: (msg: Message) => setState("messages", (prev) => [...prev, msg]),

    setModels: (models: Model[]) => setState({ models }),
    setCurrentModel: (model: string) => setState({ currentModel: model }),

    setConnected: (connected: boolean) => setState({ connected }),
    setStatus: (status: AppStatus) => setState({ status }),
    setError: (message: string) => setState({ status: "error", errorMessage: message }),
    clearError: () => setState({ status: "idle", errorMessage: "" }),

    startStreaming: (messageId: string) =>
      setState({ status: "streaming", streamingText: "", streamingMessageId: messageId, pendingToolCalls: {} }),
    appendStreamText: (text: string) => setState("streamingText", (prev) => prev + text),
    finalizeStream: (durationMs: number, tokens: { input: number; output: number }) =>
      setState({
        status: "idle",
        streamingText: "",
        streamingMessageId: "",
        lastDurationMs: durationMs,
        lastTokens: tokens,
      }),

    addToolCall: (tc: ToolCall) => setState("pendingToolCalls", tc.tool_call_id, tc),
    resolveToolCall: (id: string, result: string, durationMs: number) =>
      setState("pendingToolCalls", id, { result, duration_ms: durationMs }),

    toggleContext: () => setState("contextVisible", (v) => !v),
    toggleModelPicker: () => setState("showModelPicker", (v) => !v),
    setShowModelPicker: (show: boolean) => setState({ showModelPicker: show }),

    setMemories: (memories: Memory[]) => setState({ memories }),
  }
}

export type AppStore = ReturnType<typeof createAppStore>
