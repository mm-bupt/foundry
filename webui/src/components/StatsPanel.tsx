import { Progress, Typography, Button, Tooltip } from "antd"
import { RightOutlined } from "@ant-design/icons"
import { useAppStore } from "../store"

const { Text, Title } = Typography

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
}

export function StatsPanel() {
  const sessionStats = useAppStore((s) => s.sessionStats)
  const currentModel = useAppStore((s) => s.currentModel)
  const models = useAppStore((s) => s.models)
  const currentSessionId = useAppStore((s) => s.currentSessionId)
  const sessions = useAppStore((s) => s.sessions)
  const messages = useAppStore((s) => s.messages)
  const toggleStatsPanel = useAppStore((s) => s.toggleStatsPanel)

  const model = models.find((m) => m.id === currentModel)
  const session = sessions.find((s) => s.id === currentSessionId)
  const stats = sessionStats

  const contextPct = model && stats
    ? Math.min((stats.context_tokens / model.context_window) * 100, 100)
    : 0

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
          Tasks
        </Text>
        <div style={{ marginTop: 8 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            0 (即将支持)
          </Text>
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
