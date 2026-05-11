const API_BASE = "http://localhost:8000/api"

async function request<T>(path: string, options?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    })
    if (!res.ok) return null
    if (res.status === 204) return null
    return (await res.json()) as T
  } catch {
    return null
  }
}

export interface Session {
  id: string
  title: string
  model_id: string
  system_prompt: string
  created_at: string
  updated_at: string
}

export interface SessionDetail extends Session {
  messages: Message[]
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

export async function fetchSessions(): Promise<Session[]> {
  return (await request<Session[]>("/sessions")) ?? []
}

export async function createSession(title?: string, modelId?: string): Promise<Session | null> {
  const body: Record<string, string> = {}
  if (title) body.title = title
  if (modelId) body.model_id = modelId
  return await request<Session>("/sessions", {
    method: "POST",
    body: JSON.stringify(body),
  })
}

export async function getSession(sessionId: string): Promise<SessionDetail | null> {
  return await request<SessionDetail>(`/sessions/${sessionId}`)
}

export async function deleteSession(sessionId: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}`, { method: "DELETE" })
    return res.ok
  } catch {
    return false
  }
}

export async function updateSession(sessionId: string, data: Record<string, unknown>): Promise<Session | null> {
  return await request<Session>(`/sessions/${sessionId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  })
}

export async function fetchModels(): Promise<Model[]> {
  return (await request<Model[]>("/models")) ?? []
}

export async function fetchMemories(sessionId: string): Promise<Memory[]> {
  return (await request<Memory[]>(`/memory/${sessionId}`)) ?? []
}

export async function deleteMemory(memoryId: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/memory/item/${memoryId}`, { method: "DELETE" })
    return res.ok
  } catch {
    return false
  }
}
