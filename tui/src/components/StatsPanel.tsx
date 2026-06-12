import { Show, createMemo } from "solid-js"
import type { AppStore } from "../store"
import { theme } from "../theme"
import { formatTokenCount, formatContextBar } from "../utils"

export function StatsPanel(props: { store: AppStore; onClose: () => void }) {
  const s = () => props.store.state

  const currentSession = createMemo(() =>
    s().sessions.find((sess) => sess.id === s().currentSessionId),
  )

  const currentModel = createMemo(() =>
    s().models.find((m) => m.id === s().currentModel),
  )

  const stats = createMemo(() => s().sessionStats)

  const contextBar = createMemo(() => {
    const model = currentModel()
    const st = stats()
    if (!model || !st) return { percentage: 0, bar: "░".repeat(10) }
    return formatContextBar(st.context_tokens, model.context_window)
  })

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
        <text>
          <span fg={theme.primary}>Statistics</span>
        </text>
        <text fg={theme.textMuted} onMouseDown={() => props.onClose()}>
          ✕
        </text>
      </box>

      <box paddingX={1}>
        <box borderBottom borderColor={theme.border} />
      </box>

      <box paddingX={1} paddingY={1}>
        <text fg={theme.textMuted}>Session</text>
      </box>
      <box paddingX={1} flexDirection="column" gap={0}>
        <text>
          {currentSession()?.title
            ? currentSession()!.title.length > 22
              ? currentSession()!.title.slice(0, 22) + "…"
              : currentSession()!.title
            : "N/A"}
        </text>
        <text fg={theme.textMuted}>  {currentModel()?.name || s().currentModel}</text>
      </box>

      <box paddingX={1}>
        <box borderBottom borderColor={theme.border} />
      </box>

      <box paddingX={1} paddingY={1}>
        <text fg={theme.textMuted}>Tokens</text>
      </box>
      <Show
        when={stats()}
        fallback={
          <box paddingX={1}>
            <text fg={theme.textMuted}>  No data</text>
          </box>
        }
      >
        <box paddingX={1} flexDirection="column" gap={0}>
          <text>
            <span fg={theme.textMuted}>  Total   </span>
            <span fg={theme.accent}>{formatTokenCount(stats()!.total_tokens)}</span>
          </text>
          <text fg={theme.textMuted}>
            {"  Input   "}{formatTokenCount(stats()!.total_input_tokens)}
          </text>
          <text fg={theme.textMuted}>
            {"  Output  "}{formatTokenCount(stats()!.total_output_tokens)}
          </text>
          <text>
            <span fg={theme.textMuted}>  Context </span>
            <span fg={theme.warning}>{formatTokenCount(stats()!.context_tokens)}</span>
          </text>
          <box marginTop={1}>
            <text fg={theme.textMuted}>
              {"  "}{contextBar().bar}{" "}{contextBar().percentage}%
            </text>
          </box>
        </box>
      </Show>

      <box paddingX={1}>
        <box borderBottom borderColor={theme.border} />
      </box>

      <box paddingX={1} paddingY={1}>
        <text fg={theme.textMuted}>Messages</text>
      </box>
      <box paddingX={1}>
        <text>
          <span fg={theme.textMuted}>  Count   </span>
          <span fg={theme.accent}>{stats()?.message_count ?? s().messages.length}</span>
        </text>
      </box>

      <box paddingX={1}>
        <box borderBottom borderColor={theme.border} />
      </box>

      <box paddingX={1} paddingY={1}>
        <text fg={theme.textMuted}>Tasks</text>
      </box>
      <box paddingX={1}>
        <text fg={theme.textMuted}>  0 (即将支持)</text>
      </box>

      <box flexGrow={1} />

      <box paddingX={1}>
        <box borderBottom borderColor={theme.border} />
      </box>
      <box flexDirection="column" paddingX={1} paddingY={1} gap={0}>
        <text fg={theme.textMuted}>^R stats</text>
        <text fg={theme.textMuted}>^S sidebar</text>
      </box>
    </box>
  )
}
