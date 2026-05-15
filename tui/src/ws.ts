import { createSignal } from "solid-js"

type WSEventHandler = (event: { type: string; [key: string]: unknown }) => void

export function createWSClient(baseUrl = "ws://localhost:8000") {
  let ws: WebSocket | null = null
  let sessionId = ""
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let handler: WSEventHandler | null = null
  const [connected, setConnected] = createSignal(false)

  function connect(sid: string) {
    disconnect()
    sessionId = sid
    ws = new WebSocket(`${baseUrl}/ws/${sid}`)

    ws.onopen = () => setConnected(true)

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.type === "pong") return
        handler?.(data)
      } catch {}
    }

    ws.onclose = () => {
      setConnected(false)
      reconnectTimer = setTimeout(() => connect(sessionId), 3000)
    }

    ws.onerror = () => {
      ws?.close()
    }
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (ws) {
      ws.onclose = null
      ws.close()
      ws = null
    }
    setConnected(false)
  }

  function send(content: string) {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(
        JSON.stringify({
          type: "chat.message",
          content,
          message_id: crypto.randomUUID(),
        })
      )
    }
  }

  function interrupt() {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "chat.interrupt" }))
    }
  }

  function setEventHandler(h: WSEventHandler) {
    handler = h
  }

  return { connect, disconnect, send, interrupt, setEventHandler, connected }
}
