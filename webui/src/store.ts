import { create } from "zustand"
import type { Session, Message, Model, AppStatus, ToolCall, StreamSegment, TextSegment } from "./types"
import { fetchSessions, createSession, getSession, deleteSession, fetchModels, fetchActiveModel, updateSession } from "./api"

interface AppState {
  sessions: Session[]
  currentSessionId: string
  messages: Message[]
  models: Model[]
  currentModel: string
  status: AppStatus
  streamSegments: StreamSegment[]
  streamingMessageId: string
  thinkingText: string
  isThinking: boolean
  thinkingMessageId: string
  errorMessage: string
  connected: boolean

  init: () => Promise<void>
  switchSession: (id: string) => Promise<void>
  newSession: () => Promise<void>
  removeSession: (id: string) => Promise<void>
  setCurrentModel: (modelId: string) => void
  setStatus: (status: AppStatus) => void
  setConnected: (connected: boolean) => void
  addToolCall: (tc: ToolCall) => void
  updateToolResult: (toolCallId: string, result: string) => void
  startStreaming: (messageId: string) => void
  appendStreamText: (text: string) => void
  finalizeStream: () => void
  finalizeStreamWithMessage: () => void
  startThinking: (messageId: string) => void
  appendThinkingText: (text: string) => void
  endThinking: () => void
  clearThinking: () => void
  setError: (message: string) => void
  clearError: () => void
  addMessage: (msg: Message) => void
  updateSessionTitle: (sessionId: string, title: string) => void
  reloadMessages: () => Promise<void>
  setSessions: (sessions: Session[]) => void
}

function getStreamingText(segments: StreamSegment[]): string {
  return segments
    .filter((seg): seg is TextSegment => seg.type === "text")
    .map((seg) => seg.content)
    .join("")
}

function mapToolCalls(tcList: unknown[]): ToolCall[] {
  if (!Array.isArray(tcList)) return []
  return tcList.map((raw) => {
    const tc = raw as Record<string, unknown>
    return {
      toolCallId: (tc.id as string) ?? "",
      toolName: (tc.tool_name as string) ?? "",
      args: (() => { try { return JSON.parse((tc.args_json as string) || "{}") } catch { return {} } })(),
      result: (tc.result as string) ?? undefined,
      status: (tc.status as "running" | "done") ?? "pending",
    }
  })
}

export const useAppStore = create<AppState>((set, get) => ({
  sessions: [],
  currentSessionId: "",
  messages: [],
  models: [],
  currentModel: "",
  status: "idle",
  streamSegments: [],
  streamingMessageId: "",
  thinkingText: "",
  isThinking: false,
  thinkingMessageId: "",
  errorMessage: "",
  connected: false,

  init: async () => {
    const [sessions, models, active] = await Promise.all([
      fetchSessions(),
      fetchModels(),
      fetchActiveModel(),
    ])
    const defaultModel = active?.model_id ?? (models.length > 0 ? models[0]!.id : "")
    set({ sessions, models, currentModel: defaultModel })
    if (sessions.length > 0) {
      await get().switchSession(sessions[0]!.id)
    }
  },

  switchSession: async (id: string) => {
    set({
      currentSessionId: id,
      messages: [],
      status: "idle",
      streamSegments: [],
      streamingMessageId: "",
      thinkingText: "",
      isThinking: false,
      thinkingMessageId: "",
      errorMessage: "",
    })
    const detail = await getSession(id)
    if (detail) {
      const availableIds = get().models.map((m) => m.id)
      const modelId = availableIds.includes(detail.model_id) ? detail.model_id : get().currentModel
      const msgs: Message[] = detail.messages.map((m) => ({
        ...m,
        tool_calls: mapToolCalls((m as unknown as Record<string, unknown>).tool_calls as unknown[]),
      }))
      set({ messages: msgs, currentModel: modelId })
    }
  },

  newSession: async () => {
    const session = await createSession(undefined, get().currentModel)
    if (!session) return
    set((s) => ({
      sessions: [session, ...s.sessions],
      currentSessionId: session.id,
      messages: [],
      status: "idle",
      streamSegments: [],
      streamingMessageId: "",
    }))
  },

  removeSession: async (id: string) => {
    const ok = await deleteSession(id)
    if (!ok) return
    const sessions = get().sessions.filter((s) => s.id !== id)
    set({ sessions })
    if (get().currentSessionId === id) {
      if (sessions.length > 0) {
        await get().switchSession(sessions[0]!.id)
      } else {
        set({ currentSessionId: "", messages: [] })
      }
    }
  },

  setCurrentModel: (modelId) => {
    set({ currentModel: modelId })
    const sid = get().currentSessionId
    if (sid) {
      updateSession(sid, { model_id: modelId })
    }
  },
  setStatus: (status) => set({ status }),
  setConnected: (connected) => set({ connected }),

  addToolCall: (tc) =>
    set((s) => ({
      streamSegments: [...s.streamSegments, { type: "tool_call", toolCall: tc }],
    })),

  updateToolResult: (toolCallId, result) =>
    set((s) => ({
      streamSegments: s.streamSegments.map((seg) =>
        seg.type === "tool_call" && seg.toolCall.toolCallId === toolCallId
          ? { ...seg, toolCall: { ...seg.toolCall, result, status: "done" as const } }
          : seg
      ),
    })),

  startStreaming: (messageId) =>
    set({ status: "streaming", streamSegments: [], streamingMessageId: messageId }),

  appendStreamText: (text) =>
    set((s) => {
      const segs = [...s.streamSegments]
      const last = segs[segs.length - 1]
      if (last && last.type === "text") {
        segs[segs.length - 1] = { type: "text", content: last.content + text }
      } else {
        segs.push({ type: "text", content: text })
      }
      return { streamSegments: segs }
    }),

  finalizeStream: () =>
    set({ status: "idle", streamSegments: [], streamingMessageId: "" }),

  finalizeStreamWithMessage: () => {
    const s = get()
    if (s.status === "idle") return
    const fullText = getStreamingText(s.streamSegments)
    const toolCalls = s.streamSegments
      .filter((seg): seg is { type: "tool_call"; toolCall: ToolCall } => seg.type === "tool_call")
      .map((seg) => seg.toolCall)
    const assistantMsg: Message = {
      id: s.streamingMessageId || crypto.randomUUID(),
      session_id: s.currentSessionId,
      role: "assistant",
      content: fullText,
      thinking_content: s.thinkingText || null,
      tool_calls: toolCalls,
      segments: [...s.streamSegments],
      model_id: null,
      tokens_in: null,
      tokens_out: null,
      duration_ms: null,
      created_at: new Date().toISOString(),
    }
    set({
      status: "idle",
      streamSegments: [],
      streamingMessageId: "",
      isThinking: false,
      thinkingText: "",
      thinkingMessageId: "",
      messages: [...s.messages, assistantMsg],
    })
  },

  startThinking: (messageId) =>
    set({ isThinking: true, thinkingText: "", thinkingMessageId: messageId }),

  appendThinkingText: (text) =>
    set((s) => ({ thinkingText: s.thinkingText + text })),

  endThinking: () =>
    set({ isThinking: false }),

  clearThinking: () =>
    set({ isThinking: false, thinkingText: "", thinkingMessageId: "" }),

  setError: (message) => set({ status: "error", errorMessage: message }),
  clearError: () => set({ status: "idle", errorMessage: "" }),

  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),

  updateSessionTitle: (sessionId, title) =>
    set((s) => ({
      sessions: s.sessions.map((sess) =>
        sess.id === sessionId ? { ...sess, title } : sess
      ),
    })),

  reloadMessages: async () => {
    const sid = get().currentSessionId
    if (!sid) return
    const detail = await getSession(sid)
    if (detail) {
      const msgs: Message[] = detail.messages.map((m) => ({
        ...m,
        tool_calls: mapToolCalls((m as unknown as Record<string, unknown>).tool_calls as unknown[]),
      }))
      set({ messages: msgs })
    }
  },

  setSessions: (sessions) => set({ sessions }),
}))
