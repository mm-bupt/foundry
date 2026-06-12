const STORAGE_KEY = "foundry_tui_state"

export interface PersistedState {
  contextVisible: boolean
  rightPanelVisible: boolean
}

export function loadPersistedState(): PersistedState | null {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    return data ? JSON.parse(data) : null
  } catch {
    return null
  }
}

export function savePersistedState(state: PersistedState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch {
  }
}
