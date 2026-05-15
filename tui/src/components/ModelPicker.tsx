import { For, createSignal } from "solid-js"
import { useKeyboard } from "@opentui/solid"
import type { AppStore } from "../store"
import { theme } from "../theme"

export function ModelPicker(props: { store: AppStore }) {
  const [selectedIndex, setSelectedIndex] = createSignal(0)
  const models = () => props.store.state.models

  useKeyboard((key) => {
    if (key.name === "escape") {
      props.store.setShowModelPicker(false)
      return
    }
    if (key.name === "up" || key.name === "k") {
      setSelectedIndex((i) => Math.max(0, i - 1))
      return
    }
    if (key.name === "down" || key.name === "j") {
      setSelectedIndex((i) => Math.min(models().length - 1, i + 1))
      return
    }
    if (key.name === "enter") {
      const model = models()[selectedIndex()]
      if (model) {
        props.store.setCurrentModel(model.id)
      }
      props.store.setShowModelPicker(false)
      return
    }
  })

  return (
    <box
      position="absolute"
      top={3}
      right={28}
      width={30}
      backgroundColor={theme.bgPanel}
      border
      borderColor={theme.borderActive}
    >
      <box padding={1}>
        <text fg={theme.primary}>Select Model</text>
      </box>
      <For each={models()}>
        {(model, index) => (
          <box
            paddingX={1}
            backgroundColor={index() === selectedIndex() ? theme.bgHover : undefined}
          >
            <text>
              {model.id === props.store.state.currentModel ? (
                <span fg={theme.secondary}>● </span>
              ) : (
                <span fg={theme.textMuted}>  </span>
              )}
              <span fg={index() === selectedIndex() ? theme.text : theme.textMuted}>
                {model.id}
              </span>
              <span fg={theme.textMuted}> ({model.provider})</span>
            </text>
          </box>
        )}
      </For>
    </box>
  )
}
