export const theme = {
  bg: "#0d1117",
  bgPanel: "#161b22",
  bgElement: "#21262d",
  bgHover: "#30363d",

  primary: "#58a6ff",
  secondary: "#7ee787",
  accent: "#d2a8ff",

  text: "#e6edf3",
  textMuted: "#8b949e",

  border: "#30363d",
  borderActive: "#58a6ff",

  error: "#f85149",
  warning: "#d29922",
  info: "#58a6ff",

  user: "#58a6ff",
  agent: "#7ee787",
  tool: "#d2a8ff",
  thinking: "#d29922",
} as const

export const spinnerFrames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

export const toolIcons: Record<string, string> = {
  recall_memory: "✱",
  store_memory: "←",
  list_all_memories: "≡",
}
