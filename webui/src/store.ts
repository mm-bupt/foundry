import { create } from "zustand"
import type { Session, Message, Model, AppStatus } from "./types"
import { fetchSessions, createSession, getSession, deleteSession, fetchModels, fetchActiveModel } from "./api"

interface AppState {
  sessions: Session[]
  currentSessionId: string
  messages: Message[]
  models: Model[]
  currentModel: string
  status: AppStatus
  streamingText: string
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
  startStreaming: (messageId: string) => void
  appendStreamText: (text: string) => void
  finalizeStream: () => void
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

export const useAppStore = create<AppState>((set, get) => ({
  sessions: [],
  currentSessionId: "",
  messages: [],
  models: [],
  currentModel: "",
  status: "idle",
  streamingText: "",
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
      streamingText: "",
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
      set({ messages: detail.messages, currentModel: modelId })
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
      streamingText: "",
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

  setCurrentModel: (modelId) => set({ currentModel: modelId }),
  setStatus: (status) => set({ status }),
  setConnected: (connected) => set({ connected }),

  startStreaming: (messageId) =>
    set({ status: "streaming", streamingText: "", streamingMessageId: messageId }),

  appendStreamText: (text) =>
    set((s) => ({ streamingText: s.streamingText + text })),

  finalizeStream: () =>
    set({ status: "idle", streamingText: "", streamingMessageId: "" }),

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
      set({ messages: detail.messages })
    }
  },

  setSessions: (sessions) => set({ sessions }),
}))
