import { Show } from "solid-js"
import { theme } from "../theme"
import type { AppStore } from "../store"

export function Footer(props: { store: AppStore }) {
  return (
    <box style={{ height: 1, backgroundColor: theme.bgPanel, borderTop: true, borderColor: theme.border, padding: { left: 2, right: 2 }, flexDirection: "row", justifyContent: "space-between" }}>
      <text content={` agent · ${props.store.currentModel()}`} fg={theme.textMuted} />
      <box style={{ flexDirection: "row" }}>
        <text content={`${props.store.memories().length} Memory  `} fg={theme.textMuted} />
        <Show when={props.store.streaming()}>
          <text content="● " fg={theme.warning} />
        </Show>
        <text content="/help" fg={theme.textMuted} />
      </box>
    </box>
  )
}
