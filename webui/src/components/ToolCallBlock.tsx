import { useState } from "react"
import { Tag, Typography } from "antd"
import { LoadingOutlined, CheckCircleOutlined, ToolOutlined, CheckCircleFilled, ClockCircleOutlined, MinusCircleFilled, SyncOutlined } from "@ant-design/icons"
import type { ToolCall, TodoItem } from "../types"

const { Text } = Typography

const STATUS_ORDER: Record<string, number> = { in_progress: 0, pending: 1, completed: 2, cancelled: 3 }

function getTodoStatusIcon(status: string) {
  switch (status) {
    case "in_progress":
      return <SyncOutlined spin style={{ color: "#1677ff", fontSize: 11 }} />
    case "completed":
      return <CheckCircleFilled style={{ color: "#52c41a", fontSize: 11 }} />
    case "cancelled":
      return <MinusCircleFilled style={{ color: "#999", fontSize: 11 }} />
    default:
      return <ClockCircleOutlined style={{ color: "#d9d9d9", fontSize: 11 }} />
  }
}

function formatArgs(args: Record<string, unknown>): string {
  const entries = Object.entries(args)
  if (entries.length === 0) return ""
  return entries
    .map(([k, v]) => `${k}: ${typeof v === "string" ? v : JSON.stringify(v)}`)
    .join("\n")
}

function truncateResult(result: string, maxLen = 500): string {
  if (result.length <= maxLen) return result
  return result.slice(0, maxLen) + `... (${result.length} chars total)`
}

function TodoWriteContent({ toolCall }: { toolCall: ToolCall }) {
  const [expanded, setExpanded] = useState(false)
  const todos = ((toolCall.args.todos ?? []) as TodoItem[]).slice().sort(
    (a, b) => (STATUS_ORDER[a.status] ?? 4) - (STATUS_ORDER[b.status] ?? 4)
  )
  const isRunning = toolCall.status === "running"
  const allPending = todos.every((t) => t.status === "pending")
  const allCompleted = todos.every((t) => t.status === "completed")

  let title = "Updating plan"
  if (allPending) title = "Creating plan"
  else if (allCompleted) title = "Completing plan"

  const completed = todos.filter((t) => t.status === "completed").length

  return (
    <div
      style={{
        margin: "4px 0",
        border: "1px solid #e8e8e8",
        borderRadius: 6,
        overflow: "hidden",
        fontSize: 13,
      }}
    >
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          padding: "6px 10px",
          cursor: "pointer",
          background: isRunning ? "#fafafa" : "#f6f6f6",
          userSelect: "none",
        }}
      >
        {isRunning ? (
          <LoadingOutlined style={{ color: "#1677ff" }} />
        ) : (
          <CheckCircleOutlined style={{ color: "#52c41a" }} />
        )}
        <Tag
          color={isRunning ? "processing" : "default"}
          style={{ margin: 0, fontSize: 11 }}
        >
          todowrite
        </Tag>
        <Text style={{ fontSize: 12, flex: 1 }}>{title}</Text>
        {todos.length > 0 && (
          <Text type="secondary" style={{ fontSize: 11 }}>
            {completed}/{todos.length}
          </Text>
        )}
        <Text type="secondary" style={{ fontSize: 11 }}>
          {expanded ? "▲" : "▼"}
        </Text>
      </div>
      {expanded && todos.length > 0 && (
        <div style={{ padding: "4px 12px 8px", borderTop: "1px solid #f0f0f0", background: "#fafafa" }}>
          {todos.map((todo, i) => {
            const isDimmed = todo.status === "completed" || todo.status === "cancelled"
            return (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 6, padding: "2px 0", opacity: isDimmed ? 0.55 : 1 }}>
                {getTodoStatusIcon(todo.status)}
                <span style={{ fontSize: 12, textDecoration: isDimmed ? "line-through" : "none", color: todo.status === "in_progress" ? "#1677ff" : undefined }}>
                  {todo.content}
                </span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export function ToolCallBlock({ toolCall }: { toolCall: ToolCall }) {
  if (toolCall.toolName === "todowrite") {
    return <TodoWriteContent toolCall={toolCall} />
  }

  const [expanded, setExpanded] = useState(false)
  const isRunning = toolCall.status === "running"
  const argsStr = formatArgs(toolCall.args)

  const mainArg =
    toolCall.args.path ||
    toolCall.args.pattern ||
    toolCall.args.query ||
    toolCall.args.command ||
    toolCall.args.name ||
    ""

  return (
    <div
      style={{
        margin: "4px 0",
        border: "1px solid #e8e8e8",
        borderRadius: 6,
        overflow: "hidden",
        fontSize: 13,
      }}
    >
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          padding: "6px 10px",
          cursor: "pointer",
          background: isRunning ? "#fafafa" : "#f6f6f6",
          userSelect: "none",
        }}
      >
        {isRunning ? (
          <LoadingOutlined style={{ color: "#1677ff" }} />
        ) : (
          <CheckCircleOutlined style={{ color: "#52c41a" }} />
        )}
        <ToolOutlined style={{ color: "#999" }} />
        <Tag
          color={isRunning ? "processing" : "default"}
          style={{ margin: 0, fontSize: 11 }}
        >
          {toolCall.toolName}
        </Tag>
        {mainArg && (
          <Text
            type="secondary"
            ellipsis
            style={{ flex: 1, fontSize: 12, maxWidth: 400 }}
          >
            {String(mainArg)}
          </Text>
        )}
        <Text type="secondary" style={{ fontSize: 11 }}>
          {expanded ? "▲" : "▼"}
        </Text>
      </div>
      {expanded && (
        <div
          style={{
            padding: "8px 12px",
            borderTop: "1px solid #f0f0f0",
            background: "#fafafa",
          }}
        >
          {argsStr && (
            <div style={{ marginBottom: 6 }}>
              <Text type="secondary" style={{ fontSize: 11 }}>
                Arguments:
              </Text>
              <pre
                style={{
                  margin: "2px 0 0",
                  fontSize: 12,
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-all",
                  background: "#f5f5f5",
                  padding: 6,
                  borderRadius: 4,
                }}
              >
                {argsStr}
              </pre>
            </div>
          )}
          {toolCall.result !== undefined && (
            <div>
              <Text type="secondary" style={{ fontSize: 11 }}>
                Result:
              </Text>
              <pre
                style={{
                  margin: "2px 0 0",
                  fontSize: 12,
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-all",
                  background: "#f5f5f5",
                  padding: 6,
                  borderRadius: 4,
                  maxHeight: 300,
                  overflow: "auto",
                }}
              >
                {truncateResult(toolCall.result)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function ToolCallList({ toolCalls }: { toolCalls: ToolCall[] }) {
  if (toolCalls.length === 0) return null
  return (
    <div style={{ margin: "4px 0" }}>
      {toolCalls.map((tc) => (
        <ToolCallBlock key={tc.toolCallId} toolCall={tc} />
      ))}
    </div>
  )
}
