import { useState } from "react"
import { Tag, Progress, Typography } from "antd"
import {
  CheckCircleFilled,
  ClockCircleOutlined,
  MinusCircleFilled,
  SyncOutlined,
} from "@ant-design/icons"
import type { TodoItem } from "../types"

const { Text } = Typography

function getStatusIcon(status: TodoItem["status"]) {
  switch (status) {
    case "in_progress":
      return <SyncOutlined spin style={{ color: "#1677ff", fontSize: 12 }} />
    case "completed":
      return <CheckCircleFilled style={{ color: "#52c41a", fontSize: 12 }} />
    case "cancelled":
      return <MinusCircleFilled style={{ color: "#999", fontSize: 12 }} />
    default:
      return <ClockCircleOutlined style={{ color: "#d9d9d9", fontSize: 12 }} />
  }
}

function getPriorityColor(priority: TodoItem["priority"]): string {
  switch (priority) {
    case "high":
      return "#ff4d4f"
    case "medium":
      return "#faad14"
    default:
      return "#d9d9d9"
  }
}

function TodoListItem({ todo }: { todo: TodoItem }) {
  const isCompleted = todo.status === "completed"
  const isCancelled = todo.status === "cancelled"
  const isDimmed = isCompleted || isCancelled

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "4px 0",
        opacity: isDimmed ? 0.55 : 1,
      }}
    >
      {getStatusIcon(todo.status)}
      <span
        style={{
          flex: 1,
          fontSize: 13,
          textDecoration: isDimmed ? "line-through" : "none",
          color: todo.status === "in_progress" ? "#1677ff" : undefined,
          fontWeight: todo.status === "in_progress" ? 500 : 400,
        }}
      >
        {todo.content}
      </span>
      <div
        style={{
          width: 4,
          height: 4,
          borderRadius: "50%",
          background: getPriorityColor(todo.priority),
          flexShrink: 0,
        }}
      />
    </div>
  )
}

interface TodoDockProps {
  todos: TodoItem[]
}

export function TodoDock({ todos }: TodoDockProps) {
  const [collapsed, setCollapsed] = useState(false)

  if (todos.length === 0) return null

  const completed = todos.filter((t) => t.status === "completed").length
  const total = todos.length
  const percent = total > 0 ? Math.round((completed / total) * 100) : 0
  const active = todos.find((t) => t.status === "in_progress")

  const sortedTodos = [...todos].sort((a, b) => {
    const order: Record<string, number> = { in_progress: 0, pending: 1, completed: 2, cancelled: 3 }
    return (order[a.status] ?? 4) - (order[b.status] ?? 4)
  })

  return (
    <div
      style={{
        margin: "0 16px",
        borderTop: "1px solid #f0f0f0",
        borderRadius: 8,
        background: "#fafbfc",
        overflow: "hidden",
      }}
    >
      <div
        onClick={() => setCollapsed(!collapsed)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "6px 12px",
          cursor: "pointer",
          userSelect: "none",
        }}
      >
        <Tag
          color={percent === 100 ? "success" : "processing"}
          style={{ margin: 0, fontSize: 11, lineHeight: "18px" }}
        >
          Todos
        </Tag>
        <Text style={{ fontSize: 12, color: "#666", flex: 1 }}>
          {completed}/{total} completed
        </Text>
        {!collapsed && active && (
          <Text
            ellipsis
            style={{ fontSize: 12, color: "#1677ff", maxWidth: 300, flex: 2 }}
          >
            {active.content}
          </Text>
        )}
        <Text style={{ fontSize: 11, color: "#999" }}>
          {collapsed ? "▼" : "▲"}
        </Text>
      </div>

      {!collapsed && (
        <div style={{ padding: "2px 12px 8px" }}>
          <Progress
            percent={percent}
            size="small"
            showInfo={false}
            strokeColor={percent === 100 ? "#52c41a" : "#1677ff"}
            style={{ marginBottom: 6 }}
          />
          <div>
            {sortedTodos.map((todo, i) => (
              <TodoListItem key={i} todo={todo} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
