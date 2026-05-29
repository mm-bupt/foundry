import { useState, useCallback, type ReactNode } from "react"
import XMarkdown from "@ant-design/x-markdown"
import type { ComponentProps } from "@ant-design/x-markdown"
import { CodeHighlighter, Mermaid } from "@ant-design/x"
import { Button, Tooltip } from "antd"
import { CopyOutlined, CheckOutlined } from "@ant-design/icons"

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

function extractText(domNode: ComponentProps["domNode"]): string {
  if (!domNode) return ""
  if (domNode.type === "text") return (domNode as { data: string }).data || ""
  if ("children" in domNode && Array.isArray(domNode.children)) {
    return (domNode.children as ComponentProps["domNode"][]).map(extractText).join("")
  }
  return ""
}

function CodeBlock({ domNode, lang, block, children }: ComponentProps) {
  const code = extractText(domNode).replace(/\n$/, "")

  if (!block) {
    return (
      <code style={{ background: "#f5f5f5", padding: "2px 6px", borderRadius: 4, fontSize: 13 }}>
        {children}
      </code>
    )
  }

  if (lang === "mermaid") {
    return <Mermaid style={{ margin: "8px 0" }}>{code}</Mermaid>
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

function withStyle(tag: string, style: React.CSSProperties) {
  function Styled({ children }: ComponentProps) {
    const Tag = tag as keyof JSX.IntrinsicElements
    return <Tag style={style}>{children as ReactNode}</Tag>
  }
  Styled.displayName = `Styled_${tag}`
  return Styled
}

const components: Record<string, React.ComponentType<ComponentProps>> = {
  code: CodeBlock,
  pre({ children }: ComponentProps) {
    return <>{children as ReactNode}</>
  },
  p: withStyle("p", { margin: "4px 0", lineHeight: 1.7 }),
  ul: withStyle("ul", { margin: "4px 0", paddingLeft: 20 }),
  ol: withStyle("ol", { margin: "4px 0", paddingLeft: 20 }),
  li: withStyle("li", { margin: "2px 0", lineHeight: 1.6 }),
  blockquote: withStyle("blockquote", { borderLeft: "3px solid #d9d9d9", margin: "8px 0", padding: "4px 12px", color: "#666" }),
  h1: withStyle("h1", { margin: "12px 0 8px", fontSize: 20 }),
  h2: withStyle("h2", { margin: "10px 0 6px", fontSize: 18 }),
  h3: withStyle("h3", { margin: "8px 0 4px", fontSize: 16 }),
  table: withStyle("table", { borderCollapse: "collapse", margin: "8px 0", width: "100%" }),
  th: withStyle("th", { border: "1px solid #d9d9d9", padding: "6px 12px", background: "#fafafa", textAlign: "left" }),
  td: withStyle("td", { border: "1px solid #d9d9d9", padding: "6px 12px" }),
  a({ href, children }: ComponentProps & { href?: string }) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: "#1677ff" }}>
        {children as ReactNode}
      </a>
    )
  },
}

interface MarkdownContentProps {
  children: string
}

export function MarkdownContent({ children }: MarkdownContentProps) {
  return (
    <XMarkdown components={components} openLinksInNewTab>
      {children}
    </XMarkdown>
  )
}
