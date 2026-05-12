import { createSignal, Show } from "solid-js"
import { useKeyboard } from "@opentui/solid"
import { theme } from "../theme"
import type { AppStore } from "../store"

interface ModelPickerProps {
  store: AppStore
  onSelect: (modelId: string) => void
  onClose: () => void
}

export function ModelPicker(props: ModelPickerProps) {
  const store = props.store
  const models = () => store.models()
  const currentModel = () => store.currentModel()

  const initialIndex = () => {
    const idx = models().findIndex((m) => m.id === currentModel())
    return idx >= 0 ? idx : 0
  }

  const [selectedIndex, setSelectedIndex] = createSignal(initialIndex())

  useKeyboard((key: any) => {
    if (key.name === "escape") {
      key.preventDefault()
      props.onClose()
      return
    }
    if (key.name === "enter") {
      key.preventDefault()
      const modelsList = models()
      const idx = selectedIndex()
      if (modelsList[idx]) {
        props.onSelect(modelsList[idx].id)
      }
      return
    }
    if (key.name === "up" || key.name === "k") {
      key.preventDefault()
      setSelectedIndex((i) => (i > 0 ? i - 1 : models().length - 1))
      return
    }
    if (key.name === "down" || key.name === "j") {
      key.preventDefault()
      setSelectedIndex((i) => (i < models().length - 1 ? i + 1 : 0))
      return
    }
    key.preventDefault()
  })

  if (models().length === 0) {
    props.onClose()
    return null
  }

  return (
    <box
      position="absolute"
      top={0}
      left={0}
      width="100%"
      height="100%"
      alignItems="center"
      justifyContent="center"
    >
      <box
        flexDirection="column"
        width={44}
        height={Math.min(models().length + 4, 20)}
        backgroundColor={theme.bgElement}
        border
        borderColor={theme.borderActive}
        paddingX={1}
        paddingY={0}
      >
        <box paddingBottom={1}>
          <text fg={theme.primary}>
            <strong>Select Model</strong>
          </text>
          <text fg={theme.textMuted}> (↑↓ nav, Enter ok, Esc cancel)</text>
        </box>
        <box flexDirection="column" flexGrow={1}>
          {models().map((model, idx) => {
            const isSelected = () => idx === selectedIndex()
            const isCurrent = () => model.id === currentModel()
            return (
              <box
                flexDirection="row"
                paddingX={1}
                backgroundColor={isSelected() ? theme.bgMenu : undefined}
              >
                <text fg={isSelected() ? theme.primary : isCurrent() ? theme.accent : theme.text}>
                  {isSelected() ? "▸ " : "  "}{model.id}
                </text>
                <text fg={theme.textMuted}>
                  {" "}({model.provider})
                </text>
                <Show when={isCurrent()}>
                  <text fg={theme.success}> ●</text>
                </Show>
              </box>
            )
          })}
        </box>
        <box paddingTop={1} border borderColor={theme.border}>
          <text fg={theme.textMuted}>
            {selectedIndex() + 1}/{models().length}{" "}
            {models()[selectedIndex()]?.provider ?? ""}
          </text>
        </box>
      </box>
    </box>
  )
}
