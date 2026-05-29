import { useState, useCallback } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { CodeHighlighter } from "@ant-design/x"
import { Button, Tooltip } from "antd"
import { CopyOutlined, CheckOutlined } from "@ant-design/icons"
import type { Components } from "react-markdown"

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }, [text])

  return (
    <Tooltip title={copied ? "Copied" : "Copy"}>
      <Button
        type="text"
        size="small"
        icon={copied ? <CheckOutlined style={{ color: "#52c41a" }} /> : <CopyOutlined />}
        onClick={handleCopy}
        style={{ color: "#999" }}
      />
    </Tooltip>
  )
}

function CodeBlock({
  className,
  children,
}: {
  className?: string
  children?: React.ReactNode
}) {
  const match = /language-(\w+)/.exec(className || "")
  const lang = match ? match[1] : ""
  const code = String(children).replace(/\n$/, "")

  if (!lang) {
    return (
      <code
        style={{
          background: "#f5f5f5",
          padding: "2px 6px",
          borderRadius: 4,
          fontSize: 13,
        }}
      >
        {code}
      </code>
    )
  }

  return (
    <CodeHighlighter
      lang={lang}
      style={{ margin: "8px 0", borderRadius: 8 }}
      header={
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", paddingRight: 4 }}>
          <span style={{ fontSize: 12, color: "#999" }}>{lang}</span>
          <CopyButton text={code} />
        </div>
      }
    >
      {code}
    </CodeHighlighter>
  )
}

const components: Components = {
  code({ className, children, ...props }) {
    const isBlock = (children as string)?.includes("\n")
    if (isBlock || className) {
      return <CodeBlock className={className}>{children}</CodeBlock>
    }
    return (
      <code
        style={{
          background: "#f5f5f5",
          padding: "2px 6px",
          borderRadius: 4,
          fontSize: 13,
        }}
        {...props}
      >
        {children}
      </code>
    )
  },
  pre({ children }) {
    return <>{children}</>
  },
  p({ children }) {
    return <p style={{ margin: "4px 0", lineHeight: 1.7 }}>{children}</p>
  },
  ul({ children }) {
    return <ul style={{ margin: "4px 0", paddingLeft: 20 }}>{children}</ul>
  },
  ol({ children }) {
    return <ol style={{ margin: "4px 0", paddingLeft: 20 }}>{children}</ol>
  },
  li({ children }) {
    return <li style={{ margin: "2px 0", lineHeight: 1.6 }}>{children}</li>
  },
  blockquote({ children }) {
    return (
      <blockquote
        style={{
          borderLeft: "3px solid #d9d9d9",
          margin: "8px 0",
          padding: "4px 12px",
          color: "#666",
        }}
      >
        {children}
      </blockquote>
    )
  },
  h1({ children }) {
    return <h1 style={{ margin: "12px 0 8px", fontSize: 20 }}>{children}</h1>
  },
  h2({ children }) {
    return <h2 style={{ margin: "10px 0 6px", fontSize: 18 }}>{children}</h2>
  },
  h3({ children }) {
    return <h3 style={{ margin: "8px 0 4px", fontSize: 16 }}>{children}</h3>
  },
  table({ children }) {
    return (
      <table
        style={{
          borderCollapse: "collapse",
          margin: "8px 0",
          width: "100%",
        }}
      >
        {children}
      </table>
    )
  },
  th({ children }) {
    return (
      <th
        style={{
          border: "1px solid #d9d9d9",
          padding: "6px 12px",
          background: "#fafafa",
          textAlign: "left",
        }}
      >
        {children}
      </th>
    )
  },
  td({ children }) {
    return (
      <td
        style={{
          border: "1px solid #d9d9d9",
          padding: "6px 12px",
        }}
      >
        {children}
      </td>
    )
  },
  a({ href, children }) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: "#1677ff" }}>
        {children}
      </a>
    )
  },
}

interface MarkdownContentProps {
  children: string
}

export function MarkdownContent({ children }: MarkdownContentProps) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
      {children}
    </ReactMarkdown>
  )
}
