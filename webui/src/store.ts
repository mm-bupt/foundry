import { create } from "zustand"
import type { Session, Message, Model, AppStatus, ToolCall, StreamSegment, TextSegment, TaskCallSegment, SessionStats, TaskRecord, TodoItem } from "./types"
import { fetchSessions, createSession, getSession, deleteSession, fetchModels, fetchActiveModel, updateSession } from "./api"

const PERSIST_KEY = "foundry_webui_state"

interface PersistedState {
  sidebarCollapsed: boolean
  statsPanelVisible: boolean
}

function loadPersisted(): PersistedState {
  try {
    const raw = localStorage.getItem(PERSIST_KEY)
    if (raw) return JSON.parse(raw)
  } catch {}
  return { sidebarCollapsed: false, statsPanelVisible: true }
}

function savePersisted(data: PersistedState): void {
  try {
    localStorage.setItem(PERSIST_KEY, JSON.stringify(data))
  } catch {}
}

function getStreamingText(segments: StreamSegment[]): string {
  return segments
    .filter((seg): seg is TextSegment => seg.type === "text")
    .map((seg) => seg.content)
    .join("")
}

function updateTaskInSegments(
  segments: StreamSegment[],
  taskId: string,
  updater: (seg: TaskCallSegment) => TaskCallSegment
): StreamSegment[] {
  return segments.map((seg) => {
    if (seg.type === "task_call" && seg.taskId === taskId) {
      return updater(seg)
    }
    return seg
  })
}

function appendToTaskSubSegments(
  segments: StreamSegment[],
  taskId: string,
  subSegment: StreamSegment
): StreamSegment[] {
  return updateTaskInSegments(segments, taskId, (task) => ({
    ...task,
    subSegments: [...task.subSegments, subSegment],
  }))
}

function updateTaskSubToolResult(
  segments: StreamSegment[],
  taskId: string,
  toolCallId: string,
  result: string
): StreamSegment[] {
  return updateTaskInSegments(segments, taskId, (task) => ({
    ...task,
    subSegments: task.subSegments.map((sub) => {
      if (
        sub.type === "tool_call" &&
        sub.toolCall.toolCallId === toolCallId
      ) {
        return {
          ...sub,
          toolCall: { ...sub.toolCall, result, status: "done" as const },
        }
      }
      return sub
    }),
  }))
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

function taskRecordsToSegments(records: TaskRecord[]): StreamSegment[] {
  return records
    .filter((r) => r.status !== "cancelled")
    .map(
      (r): TaskCallSegment => ({
        type: "task_call",
        taskId: r.id,
        subagentType: r.subagent_type,
        description: r.description,
        status: r.status as TaskCallSegment["status"],
        background: r.background,
        result: r.result_preview ?? undefined,
        subSegments: [],
      })
    )
}

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
  sessionStats: SessionStats | null
  taskRecords: TaskRecord[]
  sidebarCollapsed: boolean
  statsPanelVisible: boolean
  todos: TodoItem[]

  init: () => Promise<void>
  switchSession: (id: string) => Promise<void>
  newSession: () => Promise<void>
  removeSession: (id: string) => Promise<void>
  setCurrentModel: (modelId: string) => void
  setStatus: (status: AppStatus) => void
  setConnected: (connected: boolean) => void
  addToolCall: (tc: ToolCall) => void
  updateToolResult: (toolCallId: string, result: string) => void
  addTaskCall: (params: { taskId: string; subagentType: string; description: string; background: boolean }) => void
  updateTaskResult: (taskId: string, result: string, status: "completed" | "error") => void
  appendTaskSubSegment: (taskId: string, subSegment: StreamSegment) => void
  updateTaskSubToolResult: (taskId: string, toolCallId: string, result: string) => void
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
  setSessionStats: (stats: SessionStats | null) => void
  toggleSidebar: () => void
  toggleStatsPanel: () => void
  setTodos: (todos: TodoItem[]) => void
}

export const useAppStore = create<AppState>((set, get) => {
  const persisted = loadPersisted()

  return {
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
  sessionStats: null,
  taskRecords: [],
  sidebarCollapsed: persisted.sidebarCollapsed,
  statsPanelVisible: persisted.statsPanelVisible,
  todos: [],

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
      sessionStats: null,
      taskRecords: [],
      todos: [],
    })
    const detail = await getSession(id)
    if (detail) {
      const availableIds = get().models.map((m) => m.id)
      const modelId = availableIds.includes(detail.model_id) ? detail.model_id : get().currentModel
      const taskSegments = taskRecordsToSegments(detail.task_records ?? [])
      const msgs: Message[] = detail.messages.map((m) => {
        const raw = m as unknown as Record<string, unknown>
        const tcList = (raw.tool_calls as unknown[]) ?? []
        const toolSegments = tcList.length > 0
          ? (mapToolCalls(tcList).map((tc) => ({ type: "tool_call" as const, toolCall: tc })))
          : []
        const allSegments = [...taskSegments, ...toolSegments]
        return {
          ...m,
          tool_calls: mapToolCalls(tcList),
          segments: allSegments.length > 0 ? allSegments : undefined,
        }
      })
      set({
        messages: msgs,
        currentModel: modelId,
        sessionStats: detail.stats ?? null,
        taskRecords: detail.task_records ?? [],
        todos: detail.todos ?? [],
      })
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

  addTaskCall: ({ taskId, subagentType, description, background }) =>
    set((s) => ({
      streamSegments: [
        ...s.streamSegments,
        {
          type: "task_call" as const,
          taskId,
          subagentType,
          description,
          status: "running" as const,
          background,
          subSegments: [],
        },
      ],
    })),

  updateTaskResult: (taskId, result, status) =>
    set((s) => ({
      streamSegments: updateTaskInSegments(
        s.streamSegments,
        taskId,
        (task) => ({ ...task, status, result })
      ),
    })),

  appendTaskSubSegment: (taskId, subSegment) =>
    set((s) => ({
      streamSegments: appendToTaskSubSegments(
        s.streamSegments,
        taskId,
        subSegment
      ),
    })),

  updateTaskSubToolResult: (taskId, toolCallId, result) =>
    set((s) => ({
      streamSegments: updateTaskSubToolResult(
        s.streamSegments,
        taskId,
        toolCallId,
        result
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
      const taskSegments = taskRecordsToSegments(detail.task_records ?? [])
      const msgs: Message[] = detail.messages.map((m) => {
        const raw = m as unknown as Record<string, unknown>
        const tcList = (raw.tool_calls as unknown[]) ?? []
        const toolSegments = tcList.length > 0
          ? (mapToolCalls(tcList).map((tc) => ({ type: "tool_call" as const, toolCall: tc })))
          : []
        const allSegments = [...taskSegments, ...toolSegments]
        return {
          ...m,
          tool_calls: mapToolCalls(tcList),
          segments: allSegments.length > 0 ? allSegments : undefined,
        }
      })
      set({
        messages: msgs,
        sessionStats: detail.stats ?? null,
        taskRecords: detail.task_records ?? [],
        todos: detail.todos ?? [],
      })
    }
  },

  setSessions: (sessions) => set({ sessions }),
  setSessionStats: (stats) => set({ sessionStats: stats }),
  toggleSidebar: () => {
    const next = !get().sidebarCollapsed
    set({ sidebarCollapsed: next })
    savePersisted({ sidebarCollapsed: next, statsPanelVisible: get().statsPanelVisible })
  },
  toggleStatsPanel: () => {
    const next = !get().statsPanelVisible
    set({ statsPanelVisible: next })
    savePersisted({ sidebarCollapsed: get().sidebarCollapsed, statsPanelVisible: next })
  },
  setTodos: (todos) => set({ todos }),
}})
