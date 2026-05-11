import { For, Show } from "solid-js"
import { theme, spinnerFrames, toolIcons } from "../theme"
import type { AppStore, Message, ToolCall } from "../store"

export function ChatArea(props: { store: AppStore; spinnerIdx: number }) {
  const store = props.store

  function formatTime(dateStr: string): string {
    try {
      const d = new Date(dateStr)
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    } catch {
      return ""
    }
  }

  return (
    <box flexDirection="column" flexGrow={1} backgroundColor={theme.bg}>
      <Show
        when={store.route() === "session"}
        fallback={<HomeScreen />}
      >
        <scrollbox flexGrow={1}>
          <box flexDirection="column" padding={1}>
            <For each={store.messages()}>
              {(msg) => (
                <MessageBubble msg={msg} formatTime={formatTime} />
              )}
            </For>
            <Show when={store.streaming()}>
              <StreamingBubble
                text={store.streamingText()}
                spinner={spinnerFrames[props.spinnerIdx]}
                toolCalls={store.pendingToolCalls()}
              />
            </Show>
            <Show when={store.messages().length === 0 && !store.streaming()}>
              <box paddingY={2} justifyContent="center">
                <text fg={theme.textMuted}>Send a message to start chatting</text>
              </box>
            </Show>
          </box>
        </scrollbox>
      </Show>
    </box>
  )
}

function MessageBubble(props: { msg: Message; formatTime: (d: string) => string }) {
  const isUser = () => props.msg.role === "user"
  const color = () => isUser() ? theme.primary : theme.accent
  const icon = () => isUser() ? "┃" : "▣"

  return (
    <box flexDirection="column" marginBottom={1}>
      <box flexDirection="row" gap={1}>
        <text fg={color()}>
          <strong>{icon()}</strong>
        </text>
        <text fg={color()}>
          <strong>{isUser() ? "You" : "Agent"}</strong>
        </text>
        <Show when={!isUser() && props.msg.model_id}>
          <text fg={theme.textMuted}>· {props.msg.model_id}</text>
        </Show>
        <Show when={!isUser() && props.msg.duration_ms}>
          <text fg={theme.textMuted}>· {(props.msg.duration_ms! / 1000).toFixed(1)}s</text>
        </Show>
      </box>
      <box paddingLeft={2}>
        <text fg={theme.text}>{props.msg.content}</text>
      </box>
    </box>
  )
}

function StreamingBubble(props: {
  text: string
  spinner: string
  toolCalls: Record<string, ToolCall>
}) {
  const toolCallList = () => Object.values(props.toolCalls)

  return (
    <box flexDirection="column">
      <Show when={props.text}>
        <box flexDirection="column" marginBottom={1}>
          <box flexDirection="row" gap={1}>
            <text fg={theme.accent}>
              <strong>▣</strong>
            </text>
            <text fg={theme.accent}>
              <strong>Agent</strong>
            </text>
            <text fg={theme.warning}>{props.spinner}</text>
          </box>
          <box paddingLeft={2}>
            <text fg={theme.text}>{props.text}</text>
          </box>
        </box>
      </Show>
      <For each={toolCallList()}>
        {(tc) => (
          <box paddingLeft={2} flexDirection="column" marginBottom={0}>
            <box flexDirection="row" gap={1}>
              <text fg={theme.secondary}>
                {toolIcons[tc.tool_name] ?? "◆"} {tc.tool_name}
              </text>
            </box>
            <Show when={tc.result}>
              <box paddingLeft={2}>
                <text fg={theme.textMuted}>{tc.result}</text>
              </box>
            </Show>
          </box>
        )}
      </For>
      <Show when={!props.text && toolCallList().length === 0}>
        <box flexDirection="row" gap={1}>
          <text fg={theme.accent}>
            <strong>▣</strong>
          </text>
          <text fg={theme.warning}>{props.spinner} thinking…</text>
        </box>
      </Show>
    </box>
  )
}

function HomeScreen() {
  return (
    <box flexGrow={1} justifyContent="center" alignItems="center" flexDirection="column">
      <text fg={theme.primary}>
        <strong>Dream Foundry</strong>
      </text>
      <text fg={theme.textMuted}>AI Agent TUI</text>
      <text fg={theme.textMuted}>Type a message or /help for commands</text>
    </box>
  )
}
