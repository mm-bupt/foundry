import { useEffect, useMemo } from "react"
import { Conversations } from "@ant-design/x"
import { ConfigProvider, Layout, theme, Typography, Button, Tooltip } from "antd"
import { PlusOutlined, DeleteOutlined, MenuFoldOutlined, MenuUnfoldOutlined, BarChartOutlined } from "@ant-design/icons"
import { useAppStore } from "./store"
import { createWSClient } from "./ws"
import { fetchSessions } from "./api"
import { ChatPanel } from "./components/ChatPanel"
import { StatsPanel } from "./components/StatsPanel"
import type { ConversationsProps } from "@ant-design/x"
import type { ToolCall } from "./types"

const { Content } = Layout
const { Title } = Typography

function IconColumn({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        width: 44,
        flexShrink: 0,
        background: "#fafafa",
        borderRight: "1px solid #f0f0f0",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        paddingTop: 12,
        gap: 4,
      }}
    >
      {children}
    </div>
  )
}

function IconButton({ icon, title, active, onClick }: { icon: React.ReactNode; title: string; active?: boolean; onClick: () => void }) {
  return (
    <Tooltip title={title} placement="right">
      <Button
        type="text"
        size="small"
        icon={icon}
        onClick={onClick}
        style={{
          width: 36,
          height: 36,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          borderRadius: 8,
          background: active ? "#e6f4ff" : undefined,
          color: active ? "#1677ff" : "#666",
        }}
      />
    </Tooltip>
  )
}

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
  const addToolCall = useAppStore((s) => s.addToolCall)
  const updateToolResult = useAppStore((s) => s.updateToolResult)
  const addTaskCall = useAppStore((s) => s.addTaskCall)
  const updateTaskResultStore = useAppStore((s) => s.updateTaskResult)
  const appendTaskSubSegment = useAppStore((s) => s.appendTaskSubSegment)
  const updateTaskSubToolResult = useAppStore((s) => s.updateTaskSubToolResult)
  const sidebarCollapsed = useAppStore((s) => s.sidebarCollapsed)
  const statsPanelVisible = useAppStore((s) => s.statsPanelVisible)
  const toggleSidebar = useAppStore((s) => s.toggleSidebar)
  const toggleStatsPanel = useAppStore((s) => s.toggleStatsPanel)
  const setTodos = useAppStore((s) => s.setTodos)
  const setPendingQuestion = useAppStore((s) => s.setPendingQuestion)
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
        case "tool.call": {
          const toolCallId = (event.tool_call_id as string) ?? ""
          const toolName = (event.tool_name as string) ?? ""
          const args = (event.args as Record<string, unknown>) ?? {}
          const taskId = event.task_id as string | undefined

          if (taskId) {
            appendTaskSubSegment(taskId, {
              type: "tool_call",
              toolCall: {
                toolCallId,
                toolName,
                args,
                status: "running",
              },
            })
          } else {
            const tc: ToolCall = {
              toolCallId,
              toolName,
              args,
              status: "running",
            }
            addToolCall(tc)
          }
          break
        }
        case "tool.result": {
          const tcId = (event.tool_call_id as string) ?? ""
          const result = (event.result as string) ?? ""
          const taskId = event.task_id as string | undefined

          if (taskId) {
            updateTaskSubToolResult(taskId, tcId, result)
          } else {
            updateToolResult(tcId, result)
          }
          break
        }
        case "task.started": {
          const taskId = (event.task_id as string) ?? ""
          const subagentType = (event.subagent_type as string) ?? ""
          const desc = (event.description as string) ?? ""
          const bg = (event.background as boolean) ?? false
          addTaskCall({
            taskId,
            subagentType,
            description: desc,
            background: bg,
          })
          break
        }
        case "task.completed": {
          const taskId = (event.task_id as string) ?? ""
          const preview = (event.result_preview as string) ?? ""
          updateTaskResultStore(taskId, preview, "completed")
          break
        }
        case "task.error": {
          const taskId = (event.task_id as string) ?? ""
          const errMsg = (event.error as string) ?? "Unknown error"
          updateTaskResultStore(taskId, errMsg, "error")
          break
        }
        case "stream.done":
          finalizeStreamWithMessage()
          setPendingQuestion(null)
          useAppStore.getState().reloadMessages()
          setTimeout(() => {
            fetchSessions().then((sessions) => {
              if (sessions) useAppStore.getState().setSessions(sessions)
            })
          }, 8000)
          break
        case "stream.error": {
          const msg =
            ((event.error as Record<string, string>)?.message as string) ??
            "Unknown error"
          setError(msg)
          setPendingQuestion(null)
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
        case "todo.updated": {
          const todos = (event.todos as import("./types").TodoItem[]) ?? []
          setTodos(todos)
          break
        }
        case "question.asked": {
          const qid = (event.question_id as string) ?? ""
          const sid = (event.session_id as string) ?? ""
          const questions = (event.questions as import("./types").QuestionInfo[]) ?? []
          if (qid && questions.length > 0) {
            setPendingQuestion({ questionId: qid, sessionId: sid, questions })
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
    const model = useAppStore.getState().currentModel
    ws.send(content, model)
  }

  function handleInterrupt() {
    ws.interrupt()
  }

  const conversationItems: ConversationsProps["items"] = sessions.map((s) => ({
    key: s.id,
    label: (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%" }}>
        <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {s.title}
        </span>
        <DeleteOutlined
          onClick={(e) => {
            e.stopPropagation()
            removeSession(s.id)
          }}
          style={{
            color: "#ff4d4f",
            fontSize: 12,
            opacity: 0,
            transition: "opacity 0.2s",
            flexShrink: 0,
            marginLeft: 8,
          }}
          className="session-delete-btn"
        />
      </div>
    ),
  }))

  return (
    <ConfigProvider theme={{ algorithm: theme.defaultAlgorithm }}>
      <Layout style={{ height: "100vh", flexDirection: "row" }}>
        {/* 左侧图标列 - 始终可见 */}
        <IconColumn>
          <IconButton
            icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            active={!sidebarCollapsed}
            onClick={toggleSidebar}
          />
          <IconButton
            icon={<BarChartOutlined />}
            title={statsPanelVisible ? "Hide stats" : "Show stats"}
            active={statsPanelVisible}
            onClick={toggleStatsPanel}
          />
        </IconColumn>

        {/* 左侧边栏 */}
        {!sidebarCollapsed && (
          <div
            style={{
              width: 280,
              flexShrink: 0,
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
                Foundry
              </Title>
            </div>
            <style>{`
              .session-delete-btn { opacity: 0 !important; }
              .ant-conversations-item:hover .session-delete-btn { opacity: 1 !important; }
            `}</style>
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
          </div>
        )}

        {/* 中间聊天区 */}
        <Content style={{ display: "flex", flexDirection: "column", background: "#fff", flex: 1 }}>
          <ChatPanel onSend={handleSend} onInterrupt={handleInterrupt} ws={ws} />
        </Content>

        {/* 右侧统计面板 */}
        {statsPanelVisible && <StatsPanel />}
      </Layout>
    </ConfigProvider>
  )
}
