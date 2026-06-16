type WSEventHandler = (event: Record<string, unknown>) => void

export function createWSClient() {
  let ws: WebSocket | null = null
  let sessionId = ""
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let handler: WSEventHandler | null = null

  function connect(sid: string) {
    disconnect()
    sessionId = sid
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
    const host = window.location.host
    ws = new WebSocket(`${protocol}//${host}/ws/${sid}`)

    ws.onopen = () => {
      handler?.({ type: "ws.connected" })
    }

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.type === "pong") return
        handler?.(data)
      } catch {
        // ignore parse errors
      }
    }

    ws.onclose = () => {
      handler?.({ type: "ws.disconnected" })
      reconnectTimer = setTimeout(() => {
        if (sessionId) connect(sessionId)
      }, 3000)
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
  }

  function send(content: string, modelId?: string) {
    if (ws?.readyState === WebSocket.OPEN) {
      const msg: Record<string, string> = {
        type: "chat.message",
        content,
        message_id: crypto.randomUUID(),
      }
      if (modelId) {
        msg.model_id = modelId
      }
      ws.send(JSON.stringify(msg))
    }
  }

  function interrupt() {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "chat.interrupt" }))
    }
  }

  function questionReply(questionId: string, answers: string[][]) {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: "question.reply",
        question_id: questionId,
        answers,
      }))
    }
  }

  function questionReject(questionId: string) {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: "question.reject",
        question_id: questionId,
      }))
    }
  }

  function setEventHandler(h: WSEventHandler) {
    handler = h
  }

  return { connect, disconnect, send, interrupt, questionReply, questionReject, setEventHandler }
}
