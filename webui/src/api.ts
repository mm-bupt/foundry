import type { Session, SessionDetail, Model } from "./types"

const API_BASE = "/api"

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

export async function fetchModels(): Promise<Model[]> {
  return (await request<Model[]>("/models")) ?? []
}

export async function fetchActiveModel(): Promise<{ model_id: string; provider: string } | null> {
  return request<{ model_id: string; provider: string }>("/models/active")
}

export async function updateSession(sessionId: string, data: { model_id?: string; title?: string }): Promise<Session | null> {
  return request<Session>(`/sessions/${sessionId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  })
}
