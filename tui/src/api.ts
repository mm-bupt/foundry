import type { Session, SessionDetail, Model, Memory } from "./types"

const API_BASE = "http://localhost:8000/api"

async function request<T>(path: string, options?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    })
    if (!res.ok) return null
    return (await res.json()) as T
  } catch {
    return null
  }
}

export async function fetchSessions(): Promise<Session[]> {
  const data = await request<{ sessions: Session[] }>("/sessions")
  return data?.sessions ?? []
}

export async function createSession(title?: string, modelId?: string): Promise<Session | null> {
  return request<Session>("/sessions", {
    method: "POST",
    body: JSON.stringify({ title: title ?? "New Chat", model_id: modelId ?? "claude-sonnet" }),
  })
}

export async function getSession(sessionId: string): Promise<SessionDetail | null> {
  return request<SessionDetail>(`/sessions/${sessionId}`)
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
  return request<Session>(`/sessions/${sessionId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  })
}

export async function fetchModels(): Promise<Model[]> {
  return request<Model[]>("/models") ?? []
}

export async function fetchMemories(sessionId: string): Promise<Memory[]> {
  const data = await request<{ memories: Memory[] }>(`/memory/${sessionId}`)
  return data?.memories ?? []
}

export async function deleteMemory(memoryId: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/memory/${memoryId}`, { method: "DELETE" })
    return res.ok
  } catch {
    return false
  }
}
