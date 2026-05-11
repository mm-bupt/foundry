import { Show } from "solid-js"
import { useKeyboard } from "@opentui/solid"
import { theme } from "../theme"
import type { AppStore } from "../store"

export function InputBar(props: {
  store: AppStore
  value: string
  onInput: (val: string) => void
  onSubmit: () => void
}) {
  const store = props.store

  useKeyboard((key) => {
    if (key.name === "enter") {
      props.onSubmit()
    }
    if (key.name === "escape" && store.streaming()) {
      store.setStatusMessage("Interrupt not implemented via escape")
    }
  })

  return (
    <box
      flexDirection="column"
      backgroundColor={theme.bgPanel}
      borderTop
      borderColor={theme.border}
      paddingX={1}
    >
      <input
        value={props.value}
        onInput={(val) => props.onInput(val)}
        placeholder="Ask anything... (type /help for commands)"
        focused
        width="100%"
        backgroundColor={theme.bgElement}
        textColor={theme.text}
        cursorColor={theme.primary}
        placeholderColor={theme.textMuted}
      />
      <box flexDirection="row" justifyContent="space-between">
        <text fg={theme.textMuted}>
          agent · {store.currentModel()}
        </text>
        <Show when={store.streaming()}>
          <text fg={theme.warning}>Ctrl+\ to interrupt</text>
        </Show>
      </box>
    </box>
  )
}
