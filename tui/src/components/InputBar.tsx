import { createSignal } from "solid-js"
import { useKeyboard, useRenderer } from "@opentui/solid"
import type { AppStore } from "../store"
import { theme } from "../theme"
import { matchCommand } from "../commands"

export function InputBar(props: { store: AppStore; onSubmit: (content: string) => void }) {
  const [value, setValue] = createSignal("")
  const renderer = useRenderer()

  useKeyboard((key) => {
    if (key.name === "escape") {
      if (props.store.state.showModelPicker) {
        props.store.setShowModelPicker(false)
        return
      }
    }
    if (key.ctrl && key.name === "q") {
      renderer.destroy()
    }
    if (key.ctrl && key.name === "s") {
      props.store.toggleContext()
    }
    if (key.ctrl && key.name === "m") {
      props.store.toggleModelPicker()
    }
    if (key.ctrl && key.name === "n") {
      props.store.clearError()
      setValue("/new")
    }
    if (key.ctrl && key.name === "\\") {
      if (props.store.state.status === "streaming" || props.store.state.status === "thinking") {
        props.onSubmit("")
      }
    }
  })

  function handleSubmit() {
    const content = value().trim()
    if (!content) return
    setValue("")

    const cmd = matchCommand(content)
    if (cmd) {
      cmd.action(props.store, content)
      return
    }

    props.onSubmit(content)
  }

  return (
    <box flexDirection="column" backgroundColor={theme.bgPanel} paddingX={1}>
      <box flexDirection="row" alignItems="center">
        <text fg={theme.primary}>▸ </text>
        <input
          value={value()}
          onInput={(v: string) => setValue(v)}
          placeholder="Type a message..."
          focused
          flexGrow={1}
        />
      </box>
      <box flexDirection="row" justifyContent="space-between">
        <text fg={theme.textMuted}>
          agent · <span fg={theme.accent}>{props.store.state.currentModel}</span>
        </text>
        <text fg={theme.textMuted}>/help for commands</text>
      </box>
    </box>
  )
}
