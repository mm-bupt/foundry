import { useRef, useState, useCallback } from "react"
import { Bubble, Sender, Think } from "@ant-design/x"
import type { BubbleListRef } from "@ant-design/x/es/bubble"
import { Alert, Select, Button, Tooltip } from "antd"
import { CopyOutlined, CheckOutlined } from "@ant-design/icons"
import { useAppStore } from "../store"
import { MarkdownContent } from "./MarkdownContent"
import { ToolCallBlock } from "./ToolCallBlock"
import { TaskBlock } from "./TaskBlock"
import { QuestionBlock } from "./QuestionBlock"
import type { Message, StreamSegment, TextSegment } from "../types"

interface ChatItem {
  key: string
  role: "user" | "ai"
  content: string
  thinkingText?: string
  isThinking?: boolean
  segments?: StreamSegment[]
}

function getSegmentsText(segments: StreamSegment[]): string {
  return segments
    .filter((seg): seg is TextSegment => seg.type === "text")
    .map((seg) => seg.content)
    .join("")
}

function toolCallsToSegments(toolCalls: import("../types").ToolCall[]): StreamSegment[] {
  if (!toolCalls || toolCalls.length === 0) return []
  return toolCalls.map((tc) => ({ type: "tool_call" as const, toolCall: tc }))
}

function messagesToItems(
  messages: Message[],
  streamSegments: StreamSegment[],
  streamingMessageId: string,
  thinkingText: string,
  isThinking: boolean,
): ChatItem[] {
  const items: ChatItem[] = messages.map((m) => {
    const segments = m.segments && m.segments.length > 0
      ? m.segments
      : toolCallsToSegments(m.tool_calls)
    return {
      key: m.id,
      role: m.role === "assistant" ? ("ai" as const) : ("user" as const),
      content: m.content,
      thinkingText: m.thinking_content || undefined,
      isThinking: false,
      segments,
    }
  })

  if (streamingMessageId && (streamSegments.length > 0 || isThinking)) {
    items.push({
      key: streamingMessageId,
      role: "ai",
      content: getSegmentsText(streamSegments),
      thinkingText,
      isThinking,
      segments: streamSegments,
    })
  }

  return items
}

function SegmentRenderer({ segments, fallback }: { segments?: StreamSegment[]; fallback: string }) {
  if (!segments || segments.length === 0) {
    return <MarkdownContent>{fallback}</MarkdownContent>
  }
  return (
    <>
      {segments.map((seg, i) => {
        if (seg.type === "text") {
          if (!seg.content) return null
          return <MarkdownContent key={i}>{seg.content}</MarkdownContent>
        }
        if (seg.type === "task_call") {
          return <TaskBlock key={seg.taskId} segment={seg} />
        }
        return <ToolCallBlock key={seg.toolCall.toolCallId} toolCall={seg.toolCall} />
      })}
    </>
  )
}

interface ChatPanelProps {
  onSend: (content: string) => void
  onInterrupt: () => void
  ws: { questionReply: (questionId: string, answers: string[][]) => void; questionReject: (questionId: string) => void }
}

function CopyRawButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }, [text])

  if (!text) return null

  return (
    <Tooltip title={copied ? "Copied" : "Copy raw"}>
      <Button
        type="text"
        size="small"
        icon={copied ? <CheckOutlined style={{ color: "#52c41a" }} /> : <CopyOutlined />}
        onClick={handleCopy}
        style={{ color: "#bbb", fontSize: 12 }}
      >
        {copied ? "Copied" : "Copy"}
      </Button>
    </Tooltip>
  )
}

export function ChatPanel({ onSend, onInterrupt, ws }: ChatPanelProps) {
  const messages = useAppStore((s) => s.messages)
  const status = useAppStore((s) => s.status)
  const streamSegments = useAppStore((s) => s.streamSegments)
  const streamingMessageId = useAppStore((s) => s.streamingMessageId)
  const currentSessionId = useAppStore((s) => s.currentSessionId)
  const errorMessage = useAppStore((s) => s.errorMessage)
  const models = useAppStore((s) => s.models)
  const currentModel = useAppStore((s) => s.currentModel)
  const setCurrentModel = useAppStore((s) => s.setCurrentModel)
  const connected = useAppStore((s) => s.connected)
  const thinkingText = useAppStore((s) => s.thinkingText)
  const isThinking = useAppStore((s) => s.isThinking)
  const pendingQuestion = useAppStore((s) => s.pendingQuestion)
  const setPendingQuestion = useAppStore((s) => s.setPendingQuestion)

  const [inputValue, setInputValue] = useState("")
  const bubbleListRef = useRef<BubbleListRef>(null)

  const items = messagesToItems(messages, streamSegments, streamingMessageId, thinkingText, isThinking)
  if (pendingQuestion) {
    items.push({
      key: `question-${pendingQuestion.questionId}`,
      role: "user",
      content: "",
    })
  }
  const isStreaming = status === "streaming" || status === "thinking"
  const isLastItemStreaming = !!(streamingMessageId && (streamSegments.length > 0 || isThinking))

  function handleSubmit(message: string) {
    if (!message.trim()) return
    const store = useAppStore.getState()

    store.addMessage({
      id: crypto.randomUUID(),
      session_id: store.currentSessionId,
      role: "user",
      content: message,
      thinking_content: null,
      tool_calls: [],
      model_id: null,
      tokens_in: null,
      tokens_out: null,
      duration_ms: null,
      created_at: new Date().toISOString(),
    })

    const messageId = crypto.randomUUID()
    store.startStreaming(messageId)
    onSend(message)
    setInputValue("")
  }

  if (!currentSessionId) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100%",
          color: "#999",
        }}
      >
        Create or select a session to start chatting
      </div>
    )
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ flex: 1, overflow: "hidden" }}>
        <Bubble.List
          ref={bubbleListRef}
          autoScroll
          items={items.map((item, idx) => {
            const isStreamingBubble =
              isLastItemStreaming &&
              idx === items.length - 1 &&
              item.role === "ai"
            const isQuestionBubble = item.key.startsWith("question-")
            return {
              key: item.key,
              content: isQuestionBubble
                ? ((
                    <QuestionBlock
                      pendingQuestion={pendingQuestion!}
                      onReply={(qid, answers) => {
                        ws.questionReply(qid, answers)
                        setPendingQuestion({ ...pendingQuestion!, submittedAnswers: answers })
                      }}
                      onReject={(qid) => {
                        ws.questionReject(qid)
                        setPendingQuestion(null)
                      }}
                    />
                  ) as unknown as string)
                : item.role === "ai"
                  ? ((
                      <SegmentRenderer segments={item.segments} fallback={item.content} />
                    ) as unknown as string)
                  : item.content,
              role: item.role,
              streaming: isStreamingBubble,
              header: (item.thinkingText || item.isThinking)
                ? ((
                    <Think
                      loading={item.isThinking}
                      blink={item.isThinking}
                      style={{ marginBottom: 4 }}
                    >
                      {item.thinkingText && <MarkdownContent>{item.thinkingText}</MarkdownContent>}
                    </Think>
                  ) as React.ReactNode)
                : undefined,
              footer: item.role === "ai"
                ? ((
                    <div style={{ borderTop: "1px solid #f0f0f0", marginTop: 4, paddingTop: 4, display: "flex", justifyContent: "flex-end" }}>
                      <CopyRawButton text={item.content} />
                    </div>
                  ) as React.ReactNode)
                : undefined,
            }
          })}
          role={{
            ai: {
              placement: "start" as const,
              variant: "borderless" as const,
              styles: {
                root: { width: "100%" },
                body: { maxWidth: "unset", margin: 0, width: "100%" },
                content: { maxWidth: "unset", margin: 0, width: "auto" },
                footer: { maxWidth: "unset", margin: 0 },
              },
            },
            user: {
              placement: "end" as const,
              styles: {
                root: { maxWidth: 800, width: "100%", marginLeft: "auto", marginRight: "auto" },
              },
            },
          }}
          styles={{ bubble: { width: "100%" } }}
          style={{ height: "100%", maxWidth: 800, margin: "0 auto", padding: "0 16px" }}
        />
      </div>
      {status === "error" && errorMessage && (
        <div style={{ padding: "0 16px 8px" }}>
          <Alert
            type="error"
            message={errorMessage}
            closable
            onClose={() => useAppStore.getState().clearError()}
            showIcon
          />
        </div>
      )}
      <div style={{ padding: "12px 16px 8px", borderTop: "1px solid #f0f0f0" }}>
        <Sender
          value={inputValue}
          onChange={setInputValue}
          onSubmit={handleSubmit}
          loading={isStreaming}
          onCancel={onInterrupt}
          placeholder="Type a message..."
        />
      </div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "4px 16px 8px",
          fontSize: 12,
          color: "#999",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: connected ? "#52c41a" : "#ff4d4f",
            display: "inline-block",
          }} />
          <span>{connected ? "Connected" : "Disconnected"}</span>
        </div>
        <Select
          size="small"
          value={currentModel || undefined}
          onChange={(val) => setCurrentModel(val)}
          style={{ minWidth: 160 }}
          options={models.map((m) => ({
            value: m.id,
            label: m.name,
          }))}
          variant="borderless"
          popupMatchSelectWidth={false}
        />
      </div>
    </div>
  )
}
