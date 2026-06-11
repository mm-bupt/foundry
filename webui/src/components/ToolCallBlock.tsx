import { useState } from "react"
import { Tag, Typography } from "antd"
import { LoadingOutlined, CheckCircleOutlined, ToolOutlined } from "@ant-design/icons"
import type { ToolCall } from "../types"

const { Text } = Typography

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

export function ToolCallBlock({ toolCall }: { toolCall: ToolCall }) {
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
