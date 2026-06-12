export function formatTokenCount(count: number): string {
  if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(1)}M`
  if (count >= 1_000) return `${(count / 1_000).toFixed(1)}K`
  return count.toString()
}

export function formatContextBar(
  contextTokens: number,
  contextWindow: number,
): { percentage: number; bar: string } {
  const pct = Math.min((contextTokens / contextWindow) * 100, 100)
  const filled = Math.floor(pct / 10)
  const bar = "█".repeat(filled) + "░".repeat(10 - filled)
  return { percentage: Math.round(pct), bar }
}
