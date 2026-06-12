import type { AppStore } from "./store"
import { createSession, deleteSession, updateSession, fetchSessions } from "./api"

interface Command {
  name: string
  aliases: string[]
  description: string
  action: (store: AppStore, input: string) => void
}

const commands: Command[] = [
  {
    name: "/new",
    aliases: ["/n"],
    description: "Create new session",
    action: async (store) => {
      const session = await createSession(undefined, store.state.currentModel)
      if (session) {
        store.setSessions([session, ...store.state.sessions])
        store.setCurrentSession(session.id)
        store.setMessages([])
        store.setStatus("idle")
        store.setState({ streamingText: "", lastDurationMs: null, lastTokens: null })
        store.setMemories([])
      }
    },
  },
  {
    name: "/delete",
    aliases: ["/del"],
    description: "Delete current session",
    action: async (store) => {
      const sid = store.state.currentSessionId
      if (!sid) return
      await deleteSession(sid)
      const sessions = store.state.sessions.filter((s) => s.id !== sid)
      store.setSessions(sessions)
      if (sessions.length > 0) {
        store.setCurrentSession(sessions[0].id)
        store.setMessages([])
      } else {
        store.setCurrentSession("")
        store.setMessages([])
      }
    },
  },
  {
    name: "/rename",
    aliases: [],
    description: "Rename session: /rename <title>",
    action: async (store, input) => {
      const title = input.replace(/^\/rename\s*/, "").trim()
      if (!title || !store.state.currentSessionId) return
      await updateSession(store.state.currentSessionId, { title })
      const sessions = store.state.sessions.map((s) =>
        s.id === store.state.currentSessionId ? { ...s, title } : s
      )
      store.setSessions(sessions)
    },
  },
  {
    name: "/model",
    aliases: ["/m"],
    description: "Switch model: /model <id> or open picker",
    action: (store, input) => {
      const modelId = input.replace(/^\/model\s*/, "").replace(/^\/m\s*/, "").trim()
      if (modelId) {
        store.setCurrentModel(modelId)
      } else {
        store.toggleModelPicker()
      }
    },
  },
  {
    name: "/clear",
    aliases: ["/cls"],
    description: "Clear messages",
    action: (store) => {
      store.setMessages([])
    },
  },
  {
    name: "/memories",
    aliases: [],
    description: "View memories",
    action: (store) => {
      store.setShowModelPicker(false)
    },
  },
  {
    name: "/sidebar",
    aliases: [],
    description: "Toggle sidebar",
    action: (store) => {
      store.toggleContext()
    },
  },
  {
    name: "/stats",
    aliases: [],
    description: "Toggle stats panel",
    action: (store) => {
      store.toggleRightPanel()
    },
  },
  {
    name: "/help",
    aliases: ["/h", "/?"],
    description: "Show commands",
    action: (store) => {
      store.setError(
        "Commands: /new /sessions /model /delete /rename /clear /memories /sidebar /stats /help /exit"
      )
    },
  },
  {
    name: "/exit",
    aliases: ["/q", "/quit"],
    description: "Exit",
    action: () => {
      process.exit(0)
    },
  },
  {
    name: "/sessions",
    aliases: ["/s"],
    description: "List sessions",
    action: async (store) => {
      const sessions = await fetchSessions()
      store.setSessions(sessions)
    },
  },
  {
    name: "/compact",
    aliases: [],
    description: "Compact session (not yet implemented)",
    action: (store) => {
      store.setError("compact: not yet implemented")
    },
  },
]

export function matchCommand(input: string): Command | null {
  const parts = input.split(/\s+/)
  const cmd = parts[0].toLowerCase()
  for (const c of commands) {
    if (c.name === cmd || c.aliases.includes(cmd)) return c
  }
  return null
}

export function getCommands(): Command[] {
  return commands
}
