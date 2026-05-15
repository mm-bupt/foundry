import { Switch, Match } from "solid-js"
import type { AppStore } from "../store"
import { theme } from "../theme"

export function StatusBar(props: { store: AppStore; onInterrupt: () => void }) {
  const s = () => props.store.state

  return (
    <box
      flexDirection="row"
      justifyContent="space-between"
      backgroundColor={theme.bgPanel}
      paddingX={1}
      height={1}
    >
      <Switch>
        <Match when={s().status === "idle"}>
          <text>
            <span fg={theme.secondary}>○</span>
            <span fg={theme.textMuted}> idle │ ready</span>
          </text>
        </Match>
        <Match when={s().status === "streaming"}>
          <text>
            <span fg={theme.warning}>◉</span>
            <span fg={theme.textMuted}> streaming</span>
          </text>
        </Match>
        <Match when={s().status === "thinking"}>
          <text>
            <span fg={theme.thinking}>◉</span>
            <span fg={theme.textMuted}> thinking...</span>
          </text>
        </Match>
        <Match when={s().status === "error"}>
          <text>
            <span fg={theme.error}>✗</span>
            <span fg={theme.error}> {s().errorMessage || "error"}</span>
          </text>
        </Match>
        <Match when={s().status === "disconnected"}>
          <text>
            <span fg={theme.error}>○</span>
            <span fg={theme.textMuted}> disconnected</span>
          </text>
        </Match>
      </Switch>
      <text fg={theme.textMuted}>^S sidebar  ^N new  ^M model  ^/ help</text>
    </box>
  )
}
