import { For, Show } from "solid-js"
import type { AppStore } from "../store"
import { theme } from "../theme"
import { MessageBubble } from "./MessageBubble"

export function ChatArea(props: { store: AppStore }) {
  const hasMessages = () => props.store.state.messages.length > 0 || props.store.state.streamingText

  return (
    <box flexDirection="column" flexGrow={1} backgroundColor={theme.bg}>
      <Show
        when={hasMessages()}
        fallback={
          <box flexGrow={1} justifyContent="center" alignItems="center">
            <box flexDirection="column" alignItems="center" gap={1}>
              <text>
                <span fg={theme.primary}>var</span>
              </text>
              <text fg={theme.textMuted}>AI Agent TUI</text>
              <text fg={theme.textMuted}>Type a message or /help for commands</text>
            </box>
          </box>
        }
      >
        <scrollbox flexDirection="column" flexGrow={1} padding={1} stickyScroll={true} stickyStart="bottom">
          <For each={props.store.state.messages}>
            {(msg) => <MessageBubble message={msg} store={props.store} />
            }
          </For>
          <Show when={props.store.state.streamingText}>
            <box flexDirection="column" marginTop={1}>
              <text>
                <span fg={theme.agent}>▣ </span>
                <span>{props.store.state.currentModel}</span>
              </text>
              <box paddingLeft={2}>
                <text>{props.store.state.streamingText}</text>
              </box>
            </box>
          </Show>
        </scrollbox>
      </Show>
    </box>
  )
}
