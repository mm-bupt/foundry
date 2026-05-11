import { For, Show } from "solid-js"
import { theme } from "../theme"
import type { AppStore } from "../store"

export function ContextPanel(props: { store: AppStore }) {
  const store = props.store

  return (
    <box
      width={30}
      flexDirection="column"
      backgroundColor={theme.bgPanel}
      borderLeft
      borderColor={theme.border}
    >
      <box paddingX={1} borderBottom borderColor={theme.border}>
        <text fg={theme.textMuted}>
          <strong>Context</strong>
        </text>
      </box>
      <scrollbox flexGrow={1}>
        <box flexDirection="column" padding={1}>
          <Show when={store.currentSessionId()}>
            <text fg={theme.textMuted}>Session</text>
            <text fg={theme.text}>{store.currentSessionId().slice(0, 12)}…</text>
          </Show>
          <box height={1} />
          <text fg={theme.textMuted}>Model</text>
          <text fg={theme.accent}>{store.currentModel()}</text>
          <box height={1} />
          <text fg={theme.textMuted}>Messages</text>
          <text fg={theme.text}>{store.messages().length}</text>
          <box height={1} />
          <Show when={store.memories().length > 0}>
            <text fg={theme.textMuted}>
              <strong>Memories ({store.memories().length})</strong>
            </text>
            <For each={store.memories()}>
              {(mem) => (
                <box marginBottom={1} paddingLeft={1}>
                  <text fg={theme.secondary}>{mem.content}</text>
                </box>
              )}
            </For>
          </Show>
        </box>
      </scrollbox>
    </box>
  )
}
