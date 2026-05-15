import { onMount, onCleanup } from "solid-js"
import { createAppStore } from "./store"
import { createWSClient } from "./ws"
import { fetchSessions, fetchModels, getSession, createSession, fetchMemories } from "./api"
import { ChatArea } from "./components/ChatArea"
import { InputBar } from "./components/InputBar"
import { StatusBar } from "./components/StatusBar"
import { ContextPanel } from "./components/ContextPanel"
import { ModelPicker } from "./components/ModelPicker"
import { theme } from "./theme"

export function App() {
  const store = createAppStore()
  const ws = createWSClient()

  ws.setEventHandler((event) => {
    switch (event.type) {
      case "stream.delta":
        store.appendStreamText(event.text as string)
        break
      case "stream.done":
        store.finalizeStream(
          (event.duration_ms as number) ?? 0,
          {
            input: ((event.usage as Record<string, number>)?.input_tokens as number) ?? 0,
            output: ((event.usage as Record<string, number>)?.output_tokens as number) ?? 0,
          }
        )
        reloadMessages()
        break
      case "stream.error":
        store.setError(((event.error as Record<string, string>)?.message as string) ?? "Unknown error")
        break
      case "tool.call":
        store.addToolCall({
          tool_call_id: event.tool_call_id as string,
          tool_name: event.tool_name as string,
          args: (event.args as Record<string, unknown>) ?? {},
        })
        break
      case "tool.result":
        store.resolveToolCall(
          event.tool_call_id as string,
          event.result as string,
          (event.duration_ms as number) ?? 0
        )
        break
      case "thinking.delta":
        if (store.state.status !== "thinking") store.setStatus("thinking")
        store.appendStreamText(event.text as string)
        break
      case "memory.stored":
        reloadMemories()
        break
    }
  })

  async function reloadMessages() {
    const sid = store.state.currentSessionId
    if (!sid) return
    const detail = await getSession(sid)
    if (detail) store.setMessages(detail.messages)
  }

  async function reloadMemories() {
    const sid = store.state.currentSessionId
    if (!sid) return
    const memories = await fetchMemories(sid)
    store.setMemories(memories)
  }

  async function switchSession(id: string) {
    ws.disconnect()
    store.setCurrentSession(id)
    store.setMessages([])
    store.setStatus("idle")
    store.setState({ streamingText: "", lastDurationMs: null, lastTokens: null })

    const detail = await getSession(id)
    if (detail) {
      store.setMessages(detail.messages)
      store.setCurrentModel(detail.model_id)
    }

    const memories = await fetchMemories(id)
    store.setMemories(memories)

    ws.connect(id)
  }

  async function handleSubmit(content: string) {
    if (store.state.status === "streaming" || store.state.status === "thinking") {
      ws.interrupt()
      return
    }

    let sid = store.state.currentSessionId
    if (!sid) {
      const session = await createSession(undefined, store.state.currentModel)
      if (!session) return
      sid = session.id
      store.setCurrentSession(sid)
      store.setSessions([...store.state.sessions, session])
      ws.connect(sid)
    }

    store.addMessage({
      id: crypto.randomUUID(),
      session_id: sid,
      role: "user",
      content,
      model_id: null,
      tokens_in: null,
      tokens_out: null,
      duration_ms: null,
      created_at: new Date().toISOString(),
    })

    const messageId = crypto.randomUUID()
    store.startStreaming(messageId)
    ws.send(content)
  }

  onMount(async () => {
    const [sessions, models] = await Promise.all([fetchSessions(), fetchModels()])
    store.setSessions(sessions)
    store.setModels(models)

    if (sessions.length > 0) {
      await switchSession(sessions[0].id)
    }
  })

  onCleanup(() => {
    ws.disconnect()
  })

  return (
    <box flexDirection="column" width="100%" height="100%" backgroundColor={theme.bg}>
      <box flexDirection="row" flexGrow={1}>
        <box flexDirection="column" flexGrow={1}>
          <ChatArea store={store} />
          <InputBar store={store} onSubmit={handleSubmit} />
        </box>
        {store.state.contextVisible && (
          <ContextPanel store={store} onSwitchSession={switchSession} />
        )}
      </box>
      <StatusBar store={store} onInterrupt={() => ws.interrupt()} />
      {store.state.showModelPicker && (
        <ModelPicker store={store} />
      )}
    </box>
  )
}
