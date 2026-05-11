import { For, Show, createSignal } from "solid-js"
import { theme, toolIcons } from "../theme"
import type { AppStore } from "../store"
import type { WSClient } from "../ws"
import * as api from "../api"

export function Header(props: { store: AppStore; ws: WSClient }) {
  const store = props.store
  const ws = props.ws

  async function cycleModel() {
    const models = store.models()
    if (models.length === 0) return
    const cur = store.currentModel()
    const idx = models.findIndex((m) => m.id === cur)
    const next = models[(idx + 1) % models.length]
    store.setCurrentModel(next.id)
    if (store.currentSessionId()) {
      await api.updateSession(store.currentSessionId(), { model_id: next.id })
    }
    store.setStatusMessage(`Model: ${next.id}`)
  }

  return (
    <box
      flexDirection="row"
      height={1}
      paddingX={1}
      backgroundColor={theme.bgPanel}
      borderBottom
      borderColor={theme.border}
      alignItems="center"
    >
      <text fg={theme.primary}>
        <strong>Dream Foundry</strong>
      </text>
      <text fg={theme.textMuted}> ── </text>
      <box onMouseDown={() => cycleModel()}>
        <text fg={theme.accent}>
          ● {store.currentModel()} ▾
        </text>
      </box>
      <text fg={theme.textMuted}> ── </text>
      <text fg={store.connected() ? theme.success : theme.error}>
        [WS {store.connected() ? "●" : "○"}]
      </text>
      <box flexGrow={1} />
      <Show when={store.streaming()}>
        <text fg={theme.warning}>streaming…</text>
      </Show>
    </box>
  )
}
