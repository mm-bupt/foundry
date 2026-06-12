import { useState } from "react"
import { Tag, Typography } from "antd"
import {
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  RocketOutlined,
} from "@ant-design/icons"
import { ToolCallBlock } from "./ToolCallBlock"
import { MarkdownContent } from "./MarkdownContent"
import { TaskCallSegment } from "../types"

const { Text } = Typography

export function TaskBlock({ segment }: { segment: TaskCallSegment }) {
  const [expanded, setExpanded] = useState(false)
  const isRunning = segment.status === "running"
  const isError = segment.status === "error"

  const toolSegments = segment.subSegments.filter(
    (s) => s.type === "tool_call"
  )
  const completedCount = toolSegments.filter(
    (s) => s.type === "tool_call" && s.toolCall.status === "done"
  ).length

  const statusIcon = isRunning ? (
    <LoadingOutlined style={{ color: "#1677ff" }} />
  ) : isError ? (
    <CloseCircleOutlined style={{ color: "#ff4d4f" }} />
  ) : (
    <CheckCircleOutlined style={{ color: "#52c41a" }} />
  )

  return (
    <div
      style={{
        margin: "4px 0",
        border: `1px solid ${isRunning ? "#91caff" : isError ? "#ffccc7" : "#e8e8e8"}`,
        borderRadius: 8,
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
          background: isRunning
            ? "#f0f5ff"
            : isError
            ? "#fff2f0"
            : "#f6f6f6",
          userSelect: "none",
        }}
      >
        {statusIcon}
        <RocketOutlined style={{ color: "#999" }} />
        <Tag
          color={
            isRunning ? "processing" : isError ? "error" : "default"
          }
          style={{ margin: 0, fontSize: 11 }}
        >
          {segment.subagentType}
        </Tag>
        <Text
          type="secondary"
          ellipsis
          style={{ flex: 1, fontSize: 12, maxWidth: 400 }}
        >
          {segment.description}
        </Text>
        {toolSegments.length > 0 && (
          <Text type="secondary" style={{ fontSize: 11 }}>
            {completedCount}/{toolSegments.length} tools
          </Text>
        )}
        {segment.background && (
          <Tag color="orange" style={{ margin: 0, fontSize: 10 }}>
            BG
          </Tag>
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
          {segment.subSegments.length > 0 ? (
            <div style={{ marginBottom: 4 }}>
              {segment.subSegments.map((seg, i) => {
                if (seg.type === "tool_call") {
                  return (
                    <ToolCallBlock
                      key={seg.toolCall.toolCallId}
                      toolCall={seg.toolCall}
                    />
                  )
                }
                if (seg.type === "text" && seg.content) {
                  return <MarkdownContent key={i}>{seg.content}</MarkdownContent>
                }
                return null
              })}
            </div>
          ) : (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {isRunning ? "Subagent is working..." : "No events recorded"}
            </Text>
          )}
          {segment.result && (
            <div style={{ marginTop: 6 }}>
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
                {segment.result.length > 500
                  ? segment.result.slice(0, 500) +
                    `... (${segment.result.length} chars total)`
                  : segment.result}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
