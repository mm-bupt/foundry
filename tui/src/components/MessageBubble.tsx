import { Show } from "solid-js"
import type { Message } from "../types"
import type { AppStore } from "../store"
import { theme } from "../theme"

export function MessageBubble(props: { message: Message; store: AppStore }) {
  const isUser = () => props.message.role === "user"

  return (
    <box flexDirection="column">
      <Show when={isUser()}>
        <text>
          <span fg={theme.user}>┃</span>
          <span> </span>
          <span>{props.message.content}</span>
        </text>
      </Show>
      <Show when={!isUser()}>
        <text>
          <span fg={theme.agent}>▣ </span>
          <span>{props.message.model_id ?? "agent"}</span>
          <Show when={props.message.duration_ms}>
            <span fg={theme.textMuted}> · {(props.message.duration_ms! / 1000).toFixed(1)}s</span>
          </Show>
        </text>
        <box paddingLeft={2}>
          <text>{props.message.content}</text>
        </box>
      </Show>
    </box>
  )
}
