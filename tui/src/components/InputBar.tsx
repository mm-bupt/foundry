import { createSignal, Show } from "solid-js"
import { useKeyboard, useRenderer } from "@opentui/solid"
import type { AppStore } from "../store"
import { theme } from "../theme"
import { matchCommand } from "../commands"

export function InputBar(props: { store: AppStore; onSubmit: (content: string) => void }) {
  const [value, setValue] = createSignal("")
  const renderer = useRenderer()

  const s = () => props.store.state

  const sessionTitle = () => {
    const sid = s().currentSessionId
    if (!sid) return ""
    const sessions = s().sessions ?? []
    const session = sessions.find((x) => x.id === sid)
    return session?.title ?? ""
  }

  const modelInfo = () => {
    const modelId = s().currentModel
    const models = s().models ?? []
    const model = models.find((m) => m.id === modelId)
    return model?.name ?? modelId
  }

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

  const width = () => renderer.width

  return (
    <box flexDirection="column" paddingX={1}>
      <box flexDirection="row" backgroundColor="#1e1e1e" height={1}>
        <text fg={theme.primary}>┃ </text>
        <text fg={theme.text}>{modelInfo()}</text>
        <Show when={sessionTitle()}>
          <text fg={theme.textMuted}> · </text>
          <text fg={theme.text}>{sessionTitle()}</text>
        </Show>
      </box>
      <box flexDirection="row" backgroundColor="#1e1e1e" height={1}>
        <text fg={theme.primary}>┃ </text>
        <input
          value={value()}
          onInput={(v: string) => setValue(v)}
          onSubmit={() => handleSubmit()}
          placeholder="Type a message..."
          focused
          flexGrow={1}
          backgroundColor="#1e1e1e"
        />
      </box>
      <box backgroundColor="#1e1e1e" height={1}>
        <text fg={theme.primary}>  </text>
      </box>
      <text fg={theme.primary}>╹{"─".repeat(Math.max(1, width() - 3))}</text>
    </box>
  )
}
