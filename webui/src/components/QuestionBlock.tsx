import { useState, useCallback } from "react"
import { Card, Button, Typography, Tag, Checkbox, Input } from "antd"
import { CheckCircleOutlined, CloseOutlined } from "@ant-design/icons"
import type { QuestionInfo, PendingQuestion } from "../types"

const { Title } = Typography

interface QuestionBlockProps {
  pendingQuestion: PendingQuestion
  onReply: (questionId: string, answers: string[][]) => void
  onReject: (questionId: string) => void
}

function SingleQuestion({
  question,
  index,
  selected,
  customText,
  onToggle,
  onCustomChange,
  disabled,
}: {
  question: QuestionInfo
  index: number
  selected: string[]
  customText: string
  onToggle: (label: string) => void
  onCustomChange: (text: string) => void
  disabled?: boolean
}) {
  return (
    <div style={{ marginBottom: index > 0 ? 16 : 0 }}>
      <div style={{ marginBottom: 8 }}>
        {question.header && (
          <Tag color="blue" style={{ marginBottom: 4, fontSize: 12 }}>
            {question.header}
          </Tag>
        )}
        <div style={{ fontWeight: 500, marginTop: 4 }}>{question.question}</div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {question.options.map((opt) => {
          const isSelected = selected.includes(opt.label)
          const baseStyle: React.CSSProperties = {
            display: "flex",
            alignItems: "flex-start",
            gap: 8,
            padding: "8px 12px",
            borderRadius: 8,
            border: `1px solid ${isSelected ? "#1677ff" : "#f0f0f0"}`,
            background: isSelected ? "#e6f4ff" : "#fafafa",
            cursor: disabled ? "default" : "pointer",
            transition: "all 0.2s",
            opacity: disabled && !isSelected ? 0.5 : 1,
          }
          if (question.multiple) {
            return (
              <label key={opt.label} style={baseStyle}>
                <Checkbox checked={isSelected} disabled={disabled} style={{ marginTop: 2 }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500, fontSize: 13 }}>{opt.label}</div>
                  <div style={{ fontSize: 12, color: "#888", marginTop: 2 }}>{opt.description}</div>
                </div>
              </label>
            )
          }
          return (
            <div
              key={opt.label}
              onClick={() => !disabled && onToggle(opt.label)}
              style={baseStyle}
            >
              <div
                style={{
                  width: 16,
                  height: 16,
                  borderRadius: "50%",
                  border: `2px solid ${isSelected ? "#1677ff" : "#d9d9d9"}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  marginTop: 2,
                  flexShrink: 0,
                }}
              >
                {isSelected && (
                  <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#1677ff" }} />
                )}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 500, fontSize: 13 }}>{opt.label}</div>
                <div style={{ fontSize: 12, color: "#888", marginTop: 2 }}>{opt.description}</div>
              </div>
            </div>
          )
        })}
        {!disabled && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "8px 12px",
              borderRadius: 8,
              border: "1px dashed #d9d9d9",
              background: "#fafafa",
            }}
          >
            <Checkbox
              checked={selected.includes("__custom__")}
              onChange={() => onToggle("__custom__")}
            />
            <Input
              size="small"
              placeholder="Type your own answer..."
              value={customText}
              onChange={(e) => onCustomChange(e.target.value)}
              onClick={() => {
                if (!selected.includes("__custom__")) onToggle("__custom__")
              }}
              style={{ flex: 1 }}
            />
          </div>
        )}
      </div>
    </div>
  )
}

export function QuestionBlock({ pendingQuestion, onReply, onReject }: QuestionBlockProps) {
  const { questionId, questions, submittedAnswers } = pendingQuestion
  const isSubmitted = !!submittedAnswers

  const submittedSelections: Record<number, string[]> = {}
  if (submittedAnswers) {
    submittedAnswers.forEach((ans, i) => {
      submittedSelections[i] = ans
    })
  }

  const [selections, setSelections] = useState<Record<number, string[]>>({})
  const [customTexts, setCustomTexts] = useState<Record<number, string>>({})

  const handleToggle = useCallback((qIndex: number, label: string) => {
    setSelections((prev) => {
      const question = questions[qIndex]!
      const current = prev[qIndex] ?? []

      if (label === "__custom__") {
        if (current.includes("__custom__")) {
          return { ...prev, [qIndex]: current.filter((l) => l !== "__custom__") }
        }
        return { ...prev, [qIndex]: [...current, "__custom__"] }
      }

      if (question.multiple) {
        if (current.includes(label)) {
          return { ...prev, [qIndex]: current.filter((l) => l !== label) }
        }
        return { ...prev, [qIndex]: [...current, label] }
      }

      return { ...prev, [qIndex]: [label] }
    })
  }, [questions])

  const handleCustomChange = useCallback((qIndex: number, text: string) => {
    setCustomTexts((prev) => ({ ...prev, [qIndex]: text }))
  }, [])

  const handleSubmit = useCallback(() => {
    const answers: string[][] = questions.map((_, i) => {
      const sel = selections[i] ?? []
      const custom = customTexts[i] ?? ""
      return sel
        .filter((s) => s !== "__custom__")
        .concat(custom && sel.includes("__custom__") ? [custom] : [])
    })
    onReply(questionId, answers)
  }, [questions, questionId, selections, customTexts, onReply])

  const hasSelection = questions.some((_, i) => (selections[i]?.length ?? 0) > 0)

  const activeSelections = isSubmitted ? submittedSelections : selections
  const activeCustomTexts = isSubmitted ? {} : customTexts

  return (
    <Card
      size="small"
      style={{
        border: `1px solid ${isSubmitted ? "#52c41a" : "#1677ff"}`,
        borderRadius: 10,
        background: "#fff",
        boxShadow: "0 2px 8px rgba(22, 119, 255, 0.1)",
      }}
      title={
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <CheckCircleOutlined style={{ color: isSubmitted ? "#52c41a" : "#1677ff" }} />
          <Title level={5} style={{ margin: 0, fontSize: 14 }}>
            {isSubmitted ? "Answered" : "AI is asking a question"}
          </Title>
        </div>
      }
      extra={
        !isSubmitted ? (
          <Button
            type="text"
            size="small"
            icon={<CloseOutlined />}
            onClick={() => onReject(questionId)}
            style={{ color: "#999" }}
          >
            Dismiss
          </Button>
        ) : undefined
      }
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {questions.map((q, i) => (
          <SingleQuestion
            key={i}
            question={q}
            index={i}
            selected={activeSelections[i] ?? []}
            customText={activeCustomTexts[i] ?? ""}
            onToggle={(label) => handleToggle(i, label)}
            onCustomChange={(text) => handleCustomChange(i, text)}
            disabled={isSubmitted}
          />
        ))}
        {!isSubmitted && (
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 4 }}>
            <Button onClick={() => onReject(questionId)}>
              Cancel
            </Button>
            <Button
              type="primary"
              onClick={handleSubmit}
              disabled={!hasSelection}
            >
              Submit Answer
            </Button>
          </div>
        )}
      </div>
    </Card>
  )
}
