import { createSignal } from "solid-js"

export interface WSEvent {
  type: string
  [key: string]: unknown
}

export function createWSClient(baseUrl = "ws://localhost:8000") {
  let ws: WebSocket | null = null
  let sessionId = ""
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  const [connected, setConnected] = createSignal(false)
  let onEvent: ((event: WSEvent) => void) | null = null

  function clearReconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  return {
    connected,
    setEventHandler(handler: (event: WSEvent) => void) {
      onEvent = handler
    },
    async connect(sid: string) {
      this.disconnect()
      sessionId = sid
      return new Promise<void>((resolve, reject) => {
        try {
          ws = new WebSocket(`${baseUrl}/ws/${sid}`)
          ws.onopen = () => {
            setConnected(true)
            clearReconnect()
            resolve()
          }
          ws.onmessage = (event) => {
            try {
              const parsed = JSON.parse(event.data as string) as WSEvent
              if (parsed.type === "pong") return
              onEvent?.(parsed)
            } catch {}
          }
          ws.onclose = () => {
            setConnected(false)
            ws = null
            reconnectTimer = setTimeout(() => {
              if (sessionId) this.connect(sessionId)
            }, 3000)
          }
          ws.onerror = () => {
            setConnected(false)
            reject(new Error("WebSocket connection failed"))
          }
        } catch (err) {
          reject(err)
        }
      })
    },
    async disconnect() {
      clearReconnect()
      sessionId = ""
      if (ws) {
        ws.onclose = null
        ws.onerror = null
        ws.onmessage = null
        ws.close()
        ws = null
      }
      setConnected(false)
    },
    async send(content: string) {
      if (!ws || ws.readyState !== WebSocket.OPEN) return
      const messageId = crypto.randomUUID()
      ws.send(JSON.stringify({
        type: "chat.message",
        content,
        message_id: messageId,
      }))
    },
    async interrupt() {
      if (!ws || ws.readyState !== WebSocket.OPEN) return
      ws.send(JSON.stringify({ type: "chat.interrupt" }))
    },
    async reconnect() {
      if (sessionId) {
        await this.connect(sessionId)
      }
    },
  }
}

export type WSClient = ReturnType<typeof createWSClient>
