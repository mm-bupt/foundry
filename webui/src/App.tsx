import { useEffect, useMemo } from "react"
import { Conversations } from "@ant-design/x"
import { ConfigProvider, Layout, theme, Typography } from "antd"
import { PlusOutlined, DeleteOutlined } from "@ant-design/icons"
import { useAppStore } from "./store"
import { createWSClient } from "./ws"
import { ChatPanel } from "./components/ChatPanel"
import type { ConversationsProps } from "@ant-design/x"

const { Sider, Content } = Layout
const { Title } = Typography

export default function App() {
  const currentSessionId = useAppStore((s) => s.currentSessionId)
  const sessions = useAppStore((s) => s.sessions)
  const storeInit = useAppStore((s) => s.init)
  const switchSession = useAppStore((s) => s.switchSession)
  const newSession = useAppStore((s) => s.newSession)
  const removeSession = useAppStore((s) => s.removeSession)
  const setConnected = useAppStore((s) => s.setConnected)
  const appendStreamText = useAppStore((s) => s.appendStreamText)
  const finalizeStreamWithMessage = useAppStore((s) => s.finalizeStreamWithMessage)
  const setError = useAppStore((s) => s.setError)
  const updateSessionTitle = useAppStore((s) => s.updateSessionTitle)
  const startThinking = useAppStore((s) => s.startThinking)
  const appendThinkingText = useAppStore((s) => s.appendThinkingText)
  const endThinking = useAppStore((s) => s.endThinking)
  const ws = useMemo(() => createWSClient(), [])

  useEffect(() => {
    ws.setEventHandler((event) => {
      switch (event.type) {
        case "ws.connected":
          setConnected(true)
          break
        case "ws.disconnected":
          setConnected(false)
          break
        case "stream.delta":
          appendStreamText((event.text as string) ?? "")
          break
        case "thinking.start":
          startThinking((event.message_id as string) ?? "")
          break
        case "thinking.delta":
          appendThinkingText((event.text as string) ?? "")
          break
        case "thinking.end":
          endThinking()
          break
        case "stream.done":
          finalizeStreamWithMessage()
          break
        case "stream.error": {
          const msg =
            ((event.error as Record<string, string>)?.message as string) ??
            "Unknown error"
          setError(msg)
          break
        }
        case "session.title_updated": {
          const sid = event.session_id as string
          const title = event.title as string
          if (sid && title) {
            updateSessionTitle(sid, title)
          }
          break
        }
      }
    })

    storeInit()

    return () => {
      ws.disconnect()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (currentSessionId) {
      ws.connect(currentSessionId)
    }
    return () => {
      ws.disconnect()
    }
  }, [currentSessionId, ws])

  function handleSend(content: string) {
    ws.send(content)
  }

  function handleInterrupt() {
    ws.interrupt()
  }

  const conversationItems: ConversationsProps["items"] = sessions.map((s) => ({
    key: s.id,
    label: s.title,
  }))

  return (
    <ConfigProvider theme={{ algorithm: theme.defaultAlgorithm }}>
      <Layout style={{ height: "100vh" }}>
        <Sider
          width={280}
          style={{
            background: "#fff",
            borderRight: "1px solid #f0f0f0",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div
            style={{
              padding: "16px 16px 8px",
              borderBottom: "1px solid #f0f0f0",
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <div
              style={{
                width: 28,
                height: 28,
                borderRadius: 6,
                background: "linear-gradient(135deg, #1677ff, #722ed1)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#fff",
                fontWeight: 700,
                fontSize: 14,
                flexShrink: 0,
              }}
            >
              D
            </div>
            <Title level={5} style={{ margin: 0, fontSize: 15 }}>
              Dream Foundry
            </Title>
          </div>
          <div style={{ flex: 1, overflow: "auto", padding: "8px 12px" }}>
            <Conversations
              activeKey={currentSessionId}
              onActiveChange={(key) => switchSession(key)}
              items={conversationItems ?? []}
              menu={(conv) => ({
                items: [
                  {
                    key: "delete",
                    label: "Delete",
                    icon: <DeleteOutlined />,
                    danger: true,
                  },
                ],
                onClick: () => {
                  removeSession(conv.key as string)
                },
              })}
              styles={{ item: { borderRadius: 8 } }}
            />
          </div>
          <div style={{ padding: "8px 12px 12px" }}>
            <button
              onClick={() => newSession()}
              style={{
                width: "100%",
                padding: "8px 16px",
                borderRadius: 8,
                border: "1px dashed #d9d9d9",
                background: "transparent",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 8,
                color: "#1677ff",
                fontSize: 13,
              }}
            >
              <PlusOutlined /> New Chat
            </button>
          </div>
        </Sider>
        <Content
          style={{ display: "flex", flexDirection: "column", background: "#fff" }}
        >
          <ChatPanel onSend={handleSend} onInterrupt={handleInterrupt} />
        </Content>
      </Layout>
    </ConfigProvider>
  )
}
