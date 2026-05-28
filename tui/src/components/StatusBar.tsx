import { createSignal, onCleanup, Switch, Match } from "solid-js"
import type { AppStore } from "../store"
import { theme } from "../theme"

const BAR_LEN = 10
const SPINNER_FRAMES = ["|", "/", "-", "\\"]

export function StatusBar(props: { store: AppStore; onInterrupt: () => void }) {
  const s = () => props.store.state
  const [tick, setTick] = createSignal(0)

  let timer: ReturnType<typeof setInterval> | undefined
  const startTick = () => {
    if (timer) return
    timer = setInterval(() => setTick((t) => t + 1), 120)
  }
  const stopTick = () => {
    if (timer) {
      clearInterval(timer)
      timer = undefined
      setTick(0)
    }
  }

  const isActive = () => s().status === "streaming" || s().status === "thinking"

  const animatedBar = () => {
    const t = tick()
    const head = t % BAR_LEN
    let bar = ""
    for (let i = 0; i < BAR_LEN; i++) {
      bar += i === head ? ">" : i < head ? "=" : "-"
    }
    return bar
  }

  const spinner = () => SPINNER_FRAMES[tick() % SPINNER_FRAMES.length]

  const contextWindow = () => {
    const models = s().models ?? []
    const model = models.find((m) => m.id === s().currentModel)
    return model?.context_window ?? 128000
  }

  const totalTokens = () => {
    let total = 0
    for (const msg of s().messages ?? []) {
      if (msg.tokens_in) total += msg.tokens_in
      if (msg.tokens_out) total += msg.tokens_out
    }
    return total
  }

  const tokenPercent = () => {
    const total = totalTokens()
    const cw = contextWindow()
    if (cw === 0) return 0
    return Math.min(100, Math.round((total / cw) * 100))
  }

  const tokenText = () => {
    const total = totalTokens()
    if (total === 0) return ""
    if (total >= 1000) {
      return `${(total / 1000).toFixed(1)}K (${tokenPercent()}%)`
    }
    return `${total} (${tokenPercent()}%)`
  }

  if (isActive()) {
    startTick()
  } else {
    stopTick()
  }

  onCleanup(() => stopTick())

  return (
    <box flexDirection="row" justifyContent="space-between" height={1} paddingX={1}>
      <text>
        <Switch>
          <Match when={s().status === "streaming"}>
            <span fg={theme.primary}>[{animatedBar()}]</span>
            <span fg={theme.textMuted}> </span>
            <span fg={theme.warning}>{spinner()}</span>
            <span fg={theme.text}> streaming</span>
            <span fg={theme.textMuted}>  </span>
            <span fg={theme.textMuted}>esc </span>
            <span fg={theme.text}>interrupt</span>
          </Match>
          <Match when={s().status === "thinking"}>
            <span fg={theme.primary}>[{animatedBar()}]</span>
            <span fg={theme.textMuted}> </span>
            <span fg={theme.thinking}>{spinner()}</span>
            <span fg={theme.text}> thinking</span>
            <span fg={theme.textMuted}>  </span>
            <span fg={theme.textMuted}>esc </span>
            <span fg={theme.text}>interrupt</span>
          </Match>
          <Match when={s().status === "error"}>
            <span fg={theme.error}>✗ {s().errorMessage || "error"}</span>
          </Match>
          <Match when={s().status === "disconnected"}>
            <span fg={theme.error}>○ disconnected</span>
          </Match>
        </Switch>
      </text>
      <text>
        <span fg={theme.textMuted}>^S sidebar  ^N new  ^M model  ^/ help</span>
        <span fg={theme.text}>{tokenText() ? "  " + tokenText() : ""}</span>
        <span fg={theme.textMuted}>  </span>
        <span fg={theme.secondary}>*</span>
        <span fg={theme.textMuted}> foundry</span>
      </text>
    </box>
  )
}
