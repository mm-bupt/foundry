import { createSignal, createEffect, Show, For } from "solid-js"
import { theme, spinnerFrames } from "./theme"
import { createAppStore, type AppStore } from "./store"
import { createWSClient, type WSClient } from "./ws"
import { matchCommand } from "./commands"
import * as api from "./api"
import { Header } from "./components/Header"
import { Sidebar } from "./components/Sidebar"
import { ChatArea } from "./components/ChatArea"
import { InputBar } from "./components/InputBar"
import { Footer } from "./components/Footer"
import { ContextPanel } from "./components/ContextPanel"
import { ModelPicker } from "./components/ModelPicker"

export function App() {
  const store = createAppStore()
  const ws = createWSClient()
  const [inputValue, setInputValue] = createSignal("")
  const [spinnerIdx, setSpinnerIdx] = createSignal(0)
  let spinnerTimer: ReturnType<typeof setInterval> | null = null

  createEffect(() => {
    if (store.streaming()) {
      if (!spinnerTimer) {
        spinnerTimer = setInterval(() => {
          setSpinnerIdx((i) => (i + 1) % spinnerFrames.length)
        }, 80)
      }
    } else {
      if (spinnerTimer) {
        clearInterval(spinnerTimer)
        spinnerTimer = null
      }
    }
  })

  ws.setEventHandler((event) => {
    switch (event.type) {
      case "stream.delta":
        if (!store.streaming()) store.setStreaming(true)
        store.appendStreamingText((event as any).text ?? "")
        break
      case "stream.done":
        store.finalizeStreamingMessage(
          (event as any).message_id ?? "",
          (event as any).duration_ms
        )
        break
      case "stream.error":
        store.setStreaming(false)
        store.setStreamingText("")
        store.setStatusMessage(`Error: ${(event as any).error?.message ?? "unknown"}`)
        break
      case "tool.call":
        store.addToolCall({
          tool_call_id: (event as any).tool_call_id,
          tool_name: (event as any).tool_name,
          args: (event as any).args ?? {},
        })
        break
      case "tool.result":
        store.resolveToolCall(
          (event as any).tool_call_id,
          (event as any).result ?? ""
        )
        break
    }
  })

  async function loadInitial() {
    const [sessions, models] = await Promise.all([
      api.fetchSessions(),
      api.fetchModels(),
    ])
    store.setSessions(sessions)
    store.setModels(models)
    if (models.length > 0 && !models.find((m) => m.id === store.currentModel())) {
      store.setCurrentModel(models[0].id)
    }
    if (sessions.length > 0) {
      store.setCurrentSessionId(sessions[0].id)
      store.setRoute("session")
      const detail = await api.getSession(sessions[0].id)
      if (detail) {
        store.setMessages(detail.messages ?? [])
      }
      try {
        await ws.connect(sessions[0].id)
      } catch {}
    }
  }

  setTimeout(loadInitial, 0)

  async function switchSession(id: string) {
    store.setCurrentSessionId(id)
    const detail = await api.getSession(id)
    if (detail) {
      store.setMessages(detail.messages ?? [])
      if (detail.model_id) store.setCurrentModel(detail.model_id)
    }
    store.setRoute("session")
    try {
      await ws.connect(id)
    } catch {}
    const mems = await api.fetchMemories(id)
    store.setMemories(mems)
  }

  async function handleSubmit() {
    const text = inputValue().trim()
    if (!text) return
    setInputValue("")

    if (text.startsWith("/")) {
      const spaceIdx = text.indexOf(" ")
      const cmdName = spaceIdx >= 0 ? text.slice(1, spaceIdx) : text.slice(1)
      const cmdArgs = spaceIdx >= 0 ? text.slice(spaceIdx + 1) : ""
      const cmd = matchCommand(cmdName)
      if (cmd) {
        await cmd.action(cmdArgs, store)
      } else {
        store.setStatusMessage(`Unknown command: /${cmdName}`)
      }
      return
    }

    if (store.showModelPicker()) return

    if (!store.currentSessionId()) {
      const session = await api.createSession(undefined, store.currentModel())
      if (session) {
        const list = await api.fetchSessions()
        store.setSessions(list)
        store.setCurrentSessionId(session.id)
        store.setRoute("session")
        try {
          await ws.connect(session.id)
        } catch {}
      } else {
        store.setStatusMessage("Failed to create session")
        return
      }
    }

    store.addMessage({
      id: crypto.randomUUID(),
      session_id: store.currentSessionId(),
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    })
    store.setStreaming(true)
    store.setStreamingText("")
    await ws.send(text)
  }

  return (
    <box flexDirection="column" width="100%" height="100%" backgroundColor={theme.bg}>
      <Header store={store} ws={ws} />
      <box flexDirection="row" flexGrow={1}>
        <Show when={store.sidebarVisible()}>
          <Sidebar store={store} onSwitch={switchSession} />
        </Show>
        <ChatArea store={store} spinnerIdx={spinnerIdx()} />
        <Show when={store.contextPanel()}>
          <ContextPanel store={store} />
        </Show>
      </box>
      <InputBar
        store={store}
        value={inputValue()}
        onInput={setInputValue}
        onSubmit={handleSubmit}
      />
      <Footer store={store} />
      <Show when={store.showModelPicker()}>
        <ModelPicker
          store={store}
          onSelect={async (modelId: string) => {
            store.setCurrentModel(modelId)
            if (store.currentSessionId()) {
              await api.updateSession(store.currentSessionId(), { model_id: modelId })
            }
            store.setShowModelPicker(false)
            store.setStatusMessage(`Model: ${modelId}`)
          }}
          onClose={() => store.setShowModelPicker(false)}
        />
      </Show>
    </box>
  )
}
