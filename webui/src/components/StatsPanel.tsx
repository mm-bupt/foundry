import { Progress, Typography, Button, Tooltip, Tag } from "antd"
import { RightOutlined, RocketOutlined, CheckCircleOutlined, CloseCircleOutlined, LoadingOutlined, CloudOutlined, StopOutlined, CheckCircleFilled, ClockCircleOutlined, MinusCircleFilled, SyncOutlined } from "@ant-design/icons"
import { useAppStore } from "../store"
import type { StreamSegment, TodoItem } from "../types"

const { Text, Title } = Typography

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
}

interface TaskItem {
  taskId: string
  subagentType: string
  description: string
  status: "running" | "completed" | "error" | "cancelled"
  background: boolean
}

function collectLiveTasks(segments: StreamSegment[]): TaskItem[] {
  const tasks: TaskItem[] = []
  for (const seg of segments) {
    if (seg.type === "task_call") {
      tasks.push({
        taskId: seg.taskId,
        subagentType: seg.subagentType,
        description: seg.description,
        status: seg.status,
        background: seg.background,
      })
    }
  }
  return tasks
}

function mergeTasks(live: TaskItem[], persisted: TaskItem[]): TaskItem[] {
  const map = new Map<string, TaskItem>()
  for (const t of persisted) {
    map.set(t.taskId, t)
  }
  for (const t of live) {
    map.set(t.taskId, t)
  }
  return [...map.values()]
}

export function StatsPanel() {
  const sessionStats = useAppStore((s) => s.sessionStats)
  const currentModel = useAppStore((s) => s.currentModel)
  const models = useAppStore((s) => s.models)
  const currentSessionId = useAppStore((s) => s.currentSessionId)
  const sessions = useAppStore((s) => s.sessions)
  const messages = useAppStore((s) => s.messages)
  const taskRecords = useAppStore((s) => s.taskRecords)
  const streamSegments = useAppStore((s) => s.streamSegments)
  const status = useAppStore((s) => s.status)
  const toggleStatsPanel = useAppStore((s) => s.toggleStatsPanel)
  const todos = useAppStore((s) => s.todos)

  const model = models.find((m) => m.id === currentModel)
  const session = sessions.find((s) => s.id === currentSessionId)
  const stats = sessionStats

  const contextPct = model && stats
    ? Math.min((stats.context_tokens / model.context_window) * 100, 100)
    : 0

  const liveTasks = collectLiveTasks(streamSegments)
  const persistedTasks: TaskItem[] = taskRecords
    .map((r) => ({
      taskId: r.id,
      subagentType: r.subagent_type,
      description: r.description,
      status: r.status as TaskItem["status"],
      background: r.background,
    }))

  const allTasks = status === "streaming"
    ? mergeTasks(liveTasks, persistedTasks)
    : liveTasks.length > 0
      ? liveTasks
      : persistedTasks

  const runningCount = allTasks.filter((t) => t.status === "running").length
  const completedCount = allTasks.filter((t) => t.status === "completed").length
  const errorCount = allTasks.filter((t) => t.status === "error").length
  const cancelledCount = allTasks.filter((t) => t.status === "cancelled").length

  return (
    <div
      style={{
        width: 280,
        borderLeft: "1px solid #f0f0f0",
        background: "#fff",
        display: "flex",
        flexDirection: "column",
        overflow: "auto",
      }}
    >
      <div
        style={{
          padding: "12px 16px 8px",
          borderBottom: "1px solid #f0f0f0",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Title level={5} style={{ margin: 0, fontSize: 14 }}>
          Statistics
        </Title>
        <Tooltip title="Collapse stats panel">
          <Button
            type="text"
            size="small"
            icon={<RightOutlined />}
            onClick={toggleStatsPanel}
          />
        </Tooltip>
      </div>

      <div style={{ padding: "12px 16px", borderBottom: "1px solid #f0f0f0" }}>
        <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: 0.5 }}>
          Session
        </Text>
        <div style={{ marginTop: 8 }}>
          <Text strong ellipsis style={{ display: "block", maxWidth: 240 }}>
            {session?.title || "N/A"}
          </Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {model?.name || currentModel}
          </Text>
        </div>
      </div>

      <div style={{ padding: "12px 16px", borderBottom: "1px solid #f0f0f0" }}>
        <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: 0.5 }}>
          Tokens
        </Text>
        {stats ? (
          <div style={{ marginTop: 8 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>Total</Text>
              <Text strong style={{ fontSize: 12, color: "#722ed1" }}>
                {formatTokens(stats.total_tokens)}
              </Text>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>Input</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {formatTokens(stats.total_input_tokens)}
              </Text>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>Output</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {formatTokens(stats.total_output_tokens)}
              </Text>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>Context Used</Text>
              <Text strong style={{ fontSize: 12, color: "#d48806" }}>
                {formatTokens(stats.context_tokens)}
              </Text>
            </div>
            <Progress
              percent={Math.round(contextPct)}
              size="small"
              strokeColor={contextPct > 80 ? "#ff4d4f" : contextPct > 50 ? "#faad14" : "#1677ff"}
              format={(pct) => `${pct}%`}
            />
          </div>
        ) : (
          <Text type="secondary" style={{ fontSize: 12, display: "block", marginTop: 8 }}>
            No data
          </Text>
        )}
      </div>

      <div style={{ padding: "12px 16px", borderBottom: "1px solid #f0f0f0" }}>
        <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: 0.5 }}>
          Messages
        </Text>
        <div style={{ marginTop: 8 }}>
          <Text strong style={{ fontSize: 14 }}>
            {stats?.message_count ?? messages.length}
          </Text>
        </div>
      </div>

      <div style={{ padding: "12px 16px", borderBottom: "1px solid #f0f0f0" }}>
        <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: 0.5 }}>
          Todos
        </Text>
        <div style={{ marginTop: 8 }}>
          {todos.length === 0 ? (
            <Text type="secondary" style={{ fontSize: 12 }}>
              No todos
            </Text>
          ) : (
            <>
              <div style={{ marginBottom: 8 }}>
                <Progress
                  percent={Math.round((todos.filter((t) => t.status === "completed").length / todos.length) * 100)}
                  size="small"
                  showInfo={false}
                  strokeColor={todos.every((t) => t.status === "completed") ? "#52c41a" : "#1677ff"}
                />
                <Text type="secondary" style={{ fontSize: 11, marginTop: 2, display: "block" }}>
                  {todos.filter((t) => t.status === "completed").length}/{todos.length} completed
                </Text>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                {todos.map((todo, i) => (
                  <TodoItemRow key={i} todo={todo} />
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      <div style={{ padding: "12px 16px", borderBottom: "1px solid #f0f0f0" }}>
        <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: 0.5 }}>
          Tasks
        </Text>
        <div style={{ marginTop: 8 }}>
          {allTasks.length === 0 ? (
            <Text type="secondary" style={{ fontSize: 12 }}>
              No tasks
            </Text>
          ) : (
            <>
              <div style={{ display: "flex", gap: 8, marginBottom: 8, fontSize: 12, flexWrap: "wrap" }}>
                {runningCount > 0 && (
                  <span style={{ color: "#1677ff" }}>
                    <LoadingOutlined /> {runningCount} running
                  </span>
                )}
                {completedCount > 0 && (
                  <span style={{ color: "#52c41a" }}>
                    <CheckCircleOutlined /> {completedCount} done
                  </span>
                )}
                {errorCount > 0 && (
                  <span style={{ color: "#ff4d4f" }}>
                    <CloseCircleOutlined /> {errorCount} failed
                  </span>
                )}
                {cancelledCount > 0 && (
                  <span style={{ color: "#999" }}>
                    {cancelledCount} cancelled
                  </span>
                )}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {allTasks.map((task) => (
                  <TaskItem key={task.taskId} task={task} />
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      <div style={{ flex: 1 }} />

      <div
        style={{
          padding: "12px 16px",
          borderTop: "1px solid #f0f0f0",
          fontSize: 11,
          color: "#999",
        }}
      >
        <div>Ctrl+S sidebar</div>
        <div>Ctrl+R stats</div>
      </div>
    </div>
  )
}

function TaskItem({ task }: { task: TaskItem }) {
  const { status } = task
  const isRunning = status === "running"
  const isError = status === "error"
  const isCancelled = status === "cancelled"

  const borderColor = isRunning ? "#91caff" : isError ? "#ffccc7" : isCancelled ? "#f0f0f0" : "#d9f7be"
  const bgColor = isRunning ? "#f0f5ff" : isError ? "#fff2f0" : isCancelled ? "#fafafa" : "#f6ffed"

  const statusIcon = isRunning ? (
    <LoadingOutlined style={{ color: "#1677ff", fontSize: 10 }} />
  ) : isError ? (
    <CloseCircleOutlined style={{ color: "#ff4d4f", fontSize: 10 }} />
  ) : isCancelled ? (
    <StopOutlined style={{ color: "#999", fontSize: 10 }} />
  ) : (
    <CheckCircleOutlined style={{ color: "#52c41a", fontSize: 10 }} />
  )

  const tagColor = isRunning ? "processing" : isError ? "error" : isCancelled ? "default" : "success"

  return (
    <div
      style={{
        padding: "6px 8px",
        borderRadius: 6,
        border: `1px solid ${borderColor}`,
        background: bgColor,
        fontSize: 12,
        opacity: isCancelled ? 0.55 : 1,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
        {statusIcon}
        <RocketOutlined style={{ color: "#999", fontSize: 10 }} />
        <Tag
          color={tagColor}
          style={{ margin: 0, fontSize: 10, lineHeight: "16px", padding: "0 4px" }}
        >
          {task.subagentType}
        </Tag>
        {task.background && (
          <CloudOutlined style={{ color: "#faad14", fontSize: 10 }} />
        )}
        <Text type="secondary" style={{ fontSize: 10, marginLeft: "auto" }}>
          {isRunning ? "running" : isError ? "failed" : isCancelled ? "cancelled" : "done"}
        </Text>
      </div>
      <Text
        type="secondary"
        ellipsis
        style={{ fontSize: 11, display: "block", marginTop: 2, maxWidth: 210 }}
      >
        {task.description}
      </Text>
    </div>
  )
}

function getTodoStatusIcon(status: TodoItem["status"]) {
  switch (status) {
    case "in_progress":
      return <SyncOutlined spin style={{ color: "#1677ff", fontSize: 10 }} />
    case "completed":
      return <CheckCircleFilled style={{ color: "#52c41a", fontSize: 10 }} />
    case "cancelled":
      return <MinusCircleFilled style={{ color: "#999", fontSize: 10 }} />
    default:
      return <ClockCircleOutlined style={{ color: "#d9d9d9", fontSize: 10 }} />
  }
}

function TodoItemRow({ todo }: { todo: TodoItem }) {
  const isDimmed = todo.status === "completed" || todo.status === "cancelled"
  const borderColor = todo.status === "in_progress" ? "#91caff" : isDimmed ? "#f0f0f0" : "#e8e8e8"
  const bgColor = todo.status === "in_progress" ? "#f0f5ff" : isDimmed ? "#fafafa" : "#fff"

  return (
    <div
      style={{
        padding: "4px 8px",
        borderRadius: 4,
        border: `1px solid ${borderColor}`,
        background: bgColor,
        display: "flex",
        alignItems: "center",
        gap: 6,
        opacity: isDimmed ? 0.55 : 1,
      }}
    >
      {getTodoStatusIcon(todo.status)}
      <span
        style={{
          fontSize: 11,
          textDecoration: isDimmed ? "line-through" : "none",
          color: todo.status === "in_progress" ? "#1677ff" : undefined,
          fontWeight: todo.status === "in_progress" ? 500 : 400,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
          flex: 1,
        }}
      >
        {todo.content}
      </span>
      <div
        style={{
          width: 4,
          height: 4,
          borderRadius: "50%",
          background: todo.priority === "high" ? "#ff4d4f" : todo.priority === "medium" ? "#faad14" : "#d9d9d9",
          flexShrink: 0,
        }}
      />
    </div>
  )
}
