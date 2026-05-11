import { For } from "solid-js"
import { theme } from "../theme"
import type { AppStore } from "../store"

export function Sidebar(props: { store: AppStore; onSwitch: (id: string) => void }) {
  return (
    <box style={{ width: 42, backgroundColor: theme.bgPanel, flexDirection: "column", border: { right: true }, borderColor: theme.border }}>
      <box style={{ padding: { left: 2, top: 1, bottom: 1 } }}>
        <text content="Sessions" fg={theme.text} />
      </box>
      <scrollbox style={{ flexGrow: 1 }}>
        <For each={props.store.sessions()}>
          {(session) => {
            const isActive = () => session.id === props.store.currentSessionId()
            return (
              <box
                style={{ padding: { left: 2 }, height: 1 }}
                onMouseDown={() => props.onSwitch(session.id)}
              >
                <text
                  content={isActive() ? `● ${session.title}` : `  ${session.title}`}
                  fg={isActive() ? theme.primary : theme.textMuted}
                />
              </box>
            )
          }}
        </For>
      </scrollbox>
      <box style={{ borderTop: true, borderColor: theme.border, padding: { left: 2 }, height: 1 }}>
        <text content={`● ${props.store.memories().length} Memories`} fg={theme.textMuted} />
      </box>
    </box>
  )
}
