import { For, Show } from "solid-js"
import type { AppStore } from "../store"
import type { Session, Message } from "../types"
import { theme } from "../theme"

export function ContextPanel(props: { store: AppStore; onSwitchSession: (id: string) => void }) {
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
      <box padding={1}>
        <text>
          <span fg={theme.primary}>foundry</span>
        </text>
        <Show when={s().connected} fallback={<text fg={theme.error}> ●</text>}>
          <text fg={theme.secondary}> ●</text>
        </Show>
      </box>

      <box paddingX={1}>
        <box borderBottom borderColor={theme.border} />
      </box>

      <box paddingX={1} paddingY={1}>
        <text fg={theme.textMuted}>Sessions</text>
      </box>
      <For each={s().sessions}>
        {(session: Session) => (
          <box
            paddingX={1}
            backgroundColor={session.id === s().currentSessionId ? theme.bgHover : undefined}
            onMouseDown={() => props.onSwitchSession(session.id)}
          >
            <text>
              {session.id === s().currentSessionId ? (
                <span fg={theme.primary}>▸ </span>
              ) : (
                <span fg={theme.textMuted}>  </span>
              )}
              <span
                fg={session.id === s().currentSessionId ? theme.text : theme.textMuted}
              >
                {session.title.length > 18
                  ? session.title.slice(0, 18) + "…"
                  : session.title}
              </span>
            </text>
          </box>
        )}
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
          {(tokens) => <text fg={theme.textMuted}>Tokens   {tokens().input + tokens().output}</text>}
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
