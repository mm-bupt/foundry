import { For, Show, createSignal } from "solid-js"
import type { AppStore } from "../store"
import type { Session } from "../types"
import { theme } from "../theme"

export function ContextPanel(props: {
  store: AppStore
  onSwitchSession: (id: string) => void
  onClose: () => void
  onDelete: (id: string) => void
}) {
  const s = () => props.store.state

  return (
    <box
      flexDirection="column"
      width={26}
      backgroundColor={theme.bgPanel}
      border
      borderStyle="single"
      borderColor={theme.border}
    >
      <box padding={1} flexDirection="row" justifyContent="space-between">
        <box flexDirection="row">
          <text>
            <span fg={theme.primary}>foundry</span>
          </text>
          <Show when={s().connected} fallback={<text fg={theme.error}> ●</text>}>
            <text fg={theme.secondary}> ●</text>
          </Show>
        </box>
        <text fg={theme.textMuted} onMouseDown={() => props.onClose()}>
          ✕
        </text>
      </box>

      <box paddingX={1}>
        <box borderBottom borderColor={theme.border} />
      </box>

      <box paddingX={1} paddingY={1}>
        <text fg={theme.textMuted}>Sessions</text>
      </box>
      <For each={s().sessions}>
        {(session: Session) => {
          const [hovered, setHovered] = createSignal(false)
          const isActive = () => session.id === s().currentSessionId
          const title =
            session.title.length > 14 ? session.title.slice(0, 14) + "…" : session.title

          return (
            <box
              paddingX={1}
              backgroundColor={isActive() ? theme.bgHover : undefined}
              onMouseDown={() => props.onSwitchSession(session.id)}
              onMouseEnter={() => setHovered(true)}
              onMouseLeave={() => setHovered(false)}
            >
              <text>
                {isActive() ? (
                  <span fg={theme.primary}>▸ </span>
                ) : (
                  <span fg={theme.textMuted}>  </span>
                )}
                <span fg={isActive() ? theme.text : theme.textMuted}>{title}</span>
                <Show when={hovered()}>
                  <span
                    fg={theme.error}
                    onMouseDown={() => props.onDelete(session.id)}
                  >
                    {" "}🗑
                  </span>
                </Show>
              </text>
            </box>
          )
        }}
      </For>

      <box paddingX={1}>
        <box borderBottom borderColor={theme.border} />
      </box>

      <box paddingX={1} paddingY={1}>
        <text fg={theme.textMuted}>Model</text>
      </box>
      <box paddingX={1}>
        <text>
          <span fg={theme.accent}>  {s().currentModel}</span>
        </text>
      </box>

      <box paddingX={1}>
        <box borderBottom borderColor={theme.border} />
      </box>

      <box paddingX={1} paddingY={1} flexDirection="column" gap={0}>
        <text fg={theme.textMuted}>Memory   {s().memories.length}</text>
        <Show when={s().lastTokens}>
          {(tokens: () => { input: number; output: number }) => (
            <text fg={theme.textMuted}>
              Tokens   {tokens().input + tokens().output}
            </text>
          )}
        </Show>
        <text fg={theme.textMuted}>Msgs     {s().messages.length}</text>
      </box>

      <box flexGrow={1} />

      <box paddingX={1}>
        <box borderBottom borderColor={theme.border} />
      </box>
      <box flexDirection="column" paddingX={1} paddingY={1} gap={0}>
        <text fg={theme.textMuted}>^S sidebar</text>
        <text fg={theme.textMuted}>^N new</text>
        <text fg={theme.textMuted}>^M model</text>
        <text fg={theme.textMuted}>^/ help</text>
      </box>
    </box>
  )
}
