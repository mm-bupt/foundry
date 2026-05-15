import { Show } from "solid-js"
import type { Message } from "../types"
import type { AppStore } from "../store"
import { theme } from "../theme"

export function MessageBubble(props: { message: Message; store: AppStore }) {
  const isUser = () => props.message.role === "user"

  return (
    <box flexDirection="column" marginBottom={1}>
      <text>
        {isUser() ? (
          <span>
            <span fg={theme.user}>┃</span>
            <span fg={theme.textMuted}> you</span>
          </span>
        ) : (
          <span>
            <span fg={theme.agent}>▣</span>
            <span fg={theme.textMuted}> agent ▸ </span>
            <span fg={theme.accent}>{props.message.model_id ?? ""}</span>
          </span>
        )}
      </text>
      <box paddingLeft={2}>
        <text>{props.message.content}</text>
      </box>
      <Show when={!isUser() && props.message.duration_ms}>
        <box paddingLeft={2}>
          <text fg={theme.textMuted}>
            {(props.message.duration_ms! / 1000).toFixed(1)}s
          </text>
        </box>
      </Show>
    </box>
  )
}
