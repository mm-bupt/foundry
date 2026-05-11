import type { AppStore } from "./store"
import * as api from "./api"

export interface Command {
  name: string
  aliases: string[]
  description: string
  action: (args: string, store: AppStore) => void | Promise<void>
}

export const commands: Command[] = [
  {
    name: "new",
    aliases: ["n"],
    description: "Create new session",
    action: async (_args, store) => {
      const session = await api.createSession(undefined, store.currentModel())
      if (session) {
        const list = await api.fetchSessions()
        store.setSessions(list)
        store.setCurrentSessionId(session.id)
        store.setMessages([])
        store.setStreamingText("")
        store.setRoute("session")
        store.setStatusMessage(`Created session: ${session.title}`)
      }
    },
  },
  {
    name: "sessions",
    aliases: ["resume", "continue", "s"],
    description: "Switch session",
    action: async (args, store) => {
      if (args) {
        store.setCurrentSessionId(args.trim())
        const detail = await api.getSession(args.trim())
        if (detail) {
          store.setMessages(detail.messages ?? [])
        }
        store.setRoute("session")
      } else {
        store.setSidebarVisible((v) => !v)
      }
    },
  },
  {
    name: "models",
    aliases: ["model", "m"],
    description: "Switch model",
    action: async (args, store) => {
      if (args) {
        const modelId = args.trim()
        store.setCurrentModel(modelId)
        if (store.currentSessionId()) {
          await api.updateSession(store.currentSessionId(), { model_id: modelId })
        }
        store.setStatusMessage(`Model: ${modelId}`)
      } else {
        const models = store.models()
        if (models.length > 0) {
          const names = models.map((m) => m.id).join(", ")
          store.setStatusMessage(`Available: ${names}`)
        }
      }
    },
  },
  {
    name: "sidebar",
    aliases: [],
    description: "Toggle sidebar",
    action: async (_args, store) => {
      store.setSidebarVisible((v) => !v)
    },
  },
  {
    name: "context",
    aliases: [],
    description: "Toggle context panel",
    action: async (_args, store) => {
      store.setContextPanel((v) => !v)
    },
  },
  {
    name: "help",
    aliases: ["h", "?"],
    description: "Show available commands",
    action: async (_args, store) => {
      const lines = commands.map((c) => `  /${c.name.padEnd(10)} ${c.description}`)
      const helpText = lines.join("\n")
      store.setStatusMessage(helpText)
    },
  },
  {
    name: "exit",
    aliases: ["quit", "q"],
    description: "Exit app",
    action: async () => {
      process.exit(0)
    },
  },
  {
    name: "compact",
    aliases: ["summarize"],
    description: "Compact current session",
    action: async (_args, store) => {
      store.setStatusMessage("Compact not yet implemented")
    },
  },
  {
    name: "rename",
    aliases: [],
    description: "Rename current session",
    action: async (args, store) => {
      const sid = store.currentSessionId()
      if (!sid) return
      const title = args?.trim()
      if (!title) {
        store.setStatusMessage("Usage: /rename <new title>")
        return
      }
      await api.updateSession(sid, { title })
      const list = await api.fetchSessions()
      store.setSessions(list)
      store.setStatusMessage(`Renamed to: ${title}`)
    },
  },
  {
    name: "memories",
    aliases: [],
    description: "View memories",
    action: async (_args, store) => {
      const sid = store.currentSessionId()
      if (!sid) {
        store.setStatusMessage("No active session")
        return
      }
      const mems = await api.fetchMemories(sid)
      store.setMemories(mems)
      if (mems.length === 0) {
        store.setStatusMessage("No memories")
      } else {
        store.setContextPanel(true)
        store.setStatusMessage(`${mems.length} memories loaded`)
      }
    },
  },
  {
    name: "clear",
    aliases: ["cls"],
    description: "Clear message display",
    action: async (_args, store) => {
      store.setMessages([])
      store.setStreamingText("")
      store.setStatusMessage("Cleared")
    },
  },
  {
    name: "delete",
    aliases: ["del"],
    description: "Delete current session",
    action: async (_args, store) => {
      const sid = store.currentSessionId()
      if (!sid) return
      await api.deleteSession(sid)
      const list = await api.fetchSessions()
      store.setSessions(list)
      if (list.length > 0) {
        store.setCurrentSessionId(list[0].id)
        const detail = await api.getSession(list[0].id)
        store.setMessages(detail?.messages ?? [])
      } else {
        store.setCurrentSessionId("")
        store.setMessages([])
        store.setRoute("home")
      }
      store.setStatusMessage("Session deleted")
    },
  },
]

export function matchCommand(input: string): Command | null {
  const trimmed = input.trim().toLowerCase()
  for (const cmd of commands) {
    if (cmd.name === trimmed) return cmd
    if (cmd.aliases.includes(trimmed)) return cmd
  }
  return null
}

export function getCompletions(prefix: string): Command[] {
  const p = prefix.toLowerCase()
  return commands.filter(
    (c) =>
      c.name.startsWith(p) || c.aliases.some((a) => a.startsWith(p))
  )
}
