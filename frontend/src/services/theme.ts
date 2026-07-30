import { ref } from "vue"

export type ThemeMode = "night" | "day"

const THEME_STORAGE_KEY = "saveplan.theme"
const theme = ref<ThemeMode>("night")

function isThemeMode(value: unknown): value is ThemeMode {
  return value === "night" || value === "day"
}

function getStoredTheme(): ThemeMode {
  if (typeof window === "undefined") return "night"

  const storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY)
  return isThemeMode(storedTheme) ? storedTheme : "night"
}

function applyTheme(nextTheme: ThemeMode) {
  theme.value = nextTheme

  if (typeof document === "undefined") return

  document.documentElement.dataset.theme = nextTheme
  document.documentElement.style.colorScheme = nextTheme === "day" ? "light" : "dark"
}

export function initializeTheme() {
  applyTheme(getStoredTheme())
}

export function setTheme(nextTheme: ThemeMode) {
  applyTheme(nextTheme)

  if (typeof window !== "undefined") {
    window.localStorage.setItem(THEME_STORAGE_KEY, nextTheme)
  }
}

export function toggleTheme() {
  setTheme(theme.value === "day" ? "night" : "day")
}

export function useTheme() {
  return {
    theme,
    setTheme,
    toggleTheme,
  }
}
