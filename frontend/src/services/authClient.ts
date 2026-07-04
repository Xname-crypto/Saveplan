const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api"
const AUTH_TOKEN_KEY = "saveplan.auth.token"
const AUTH_USER_KEY = "saveplan.auth.user"
const AUTH_AVATAR_SOURCES_KEY = "saveplan.auth.avatarSources"
export const AUTH_SESSION_CHANGE_EVENT = "saveplan:auth-session-change"

export interface AuthUser {
  id: string
  email: string
  username: string
  job?: string
  bio?: string
  interests: string[]
  avatar_name?: string
  avatar_url?: string
  created_at: string
}

interface AuthResponse {
  token: string
  user: AuthUser
}

interface RegisterPayload {
  email: string
  password: string
  username: string
  job: string
  bio?: string
  interests?: string[]
  avatar_name?: string
}

interface ForgotPasswordResponse {
  message: string
  reset_token?: string
  reset_url?: string
}

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem(AUTH_TOKEN_KEY)
  const headers = new Headers(options.headers)

  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json")
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  let payload: unknown = null
  try {
    payload = await response.json()
  } catch (_error) {
    payload = null
  }

  if (!response.ok) {
    const detail =
      payload && typeof payload === "object" && "detail" in payload
        ? String((payload as { detail?: unknown }).detail)
        : "请求失败，请稍后再试。"
    throw new ApiError(detail, response.status)
  }

  return payload as T
}

function persistSession(response: AuthResponse) {
  const avatarUrl = getStoredAvatarSource(response.user)
  const user = avatarUrl ? { ...response.user, avatar_url: avatarUrl } : response.user

  localStorage.setItem(AUTH_TOKEN_KEY, response.token)
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user))
  emitAuthSessionChange(user)
}

function emitAuthSessionChange(user: AuthUser | null) {
  window.dispatchEvent(new CustomEvent<AuthUser | null>(AUTH_SESSION_CHANGE_EVENT, { detail: user }))
}

export function getStoredAuthUser() {
  if (!localStorage.getItem(AUTH_TOKEN_KEY)) return null

  const rawUser = localStorage.getItem(AUTH_USER_KEY)

  if (!rawUser) return null

  try {
    const user = JSON.parse(rawUser) as AuthUser
    const avatarUrl = user.avatar_url || getStoredAvatarSource(user)

    return avatarUrl ? { ...user, avatar_url: avatarUrl } : user
  } catch (_error) {
    localStorage.removeItem(AUTH_USER_KEY)
    return null
  }
}

function getAvatarStorageKey(user: AuthUser | null) {
  return user?.id || user?.email?.trim().toLowerCase() || ""
}

function readStoredAvatarSources() {
  const rawSources = localStorage.getItem(AUTH_AVATAR_SOURCES_KEY)

  if (!rawSources) return {}

  try {
    const parsed = JSON.parse(rawSources)

    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      return {}
    }

    return Object.entries(parsed).reduce<Record<string, string>>((sources, [key, value]) => {
      if (typeof value === "string") {
        sources[key] = value
      }

      return sources
    }, {})
  } catch (_error) {
    localStorage.removeItem(AUTH_AVATAR_SOURCES_KEY)
    return {}
  }
}

function isUsableAvatarSource(source: string) {
  return (
    source.startsWith("https://") ||
    source.startsWith("http://") ||
    source.startsWith("/") ||
    source.startsWith("data:") ||
    source.startsWith("blob:")
  )
}

function getStoredAvatarSource(user: AuthUser | null) {
  const avatarKey = getAvatarStorageKey(user)

  if (!avatarKey) return ""

  const source = readStoredAvatarSources()[avatarKey]?.trim()

  return source && isUsableAvatarSource(source) ? source : ""
}

export function saveAuthAvatarSource(user: AuthUser | null, source: string) {
  const avatarKey = getAvatarStorageKey(user)
  const avatarSource = source.trim()

  if (!avatarKey || !isUsableAvatarSource(avatarSource)) return

  const sources = readStoredAvatarSources()
  sources[avatarKey] = avatarSource

  try {
    localStorage.setItem(AUTH_AVATAR_SOURCES_KEY, JSON.stringify(sources))
  } catch (_error) {
    return
  }

  const storedUser = getStoredAuthUser()

  if (storedUser && getAvatarStorageKey(storedUser) === avatarKey) {
    const updatedUser = { ...storedUser, avatar_url: avatarSource }
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(updatedUser))
    emitAuthSessionChange(updatedUser)
  }
}

export function getAuthAvatarSource(user: AuthUser | null) {
  const avatarUrl = user?.avatar_url?.trim()

  if (avatarUrl && isUsableAvatarSource(avatarUrl)) {
    return avatarUrl
  }

  const avatarName = user?.avatar_name?.trim()

  if (!avatarName) return getStoredAvatarSource(user)

  if (isUsableAvatarSource(avatarName)) {
    return avatarName
  }

  return getStoredAvatarSource(user)
}

export function getAuthAvatarInitial(user: AuthUser | null) {
  const displayName = user?.username?.trim() || user?.email?.trim() || "用户"
  return Array.from(displayName)[0]?.toUpperCase() || "用"
}

export const authClient = {
  async login(email: string, password: string) {
    const response = await request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    })
    persistSession(response)
    return response.user
  },

  async register(payload: RegisterPayload) {
    const response = await request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    })
    persistSession(response)
    return response.user
  },

  forgotPassword(email: string) {
    return request<ForgotPasswordResponse>("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    })
  },

  resetPassword(token: string, password: string) {
    return request<{ message: string }>("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, password }),
    })
  },

  async me() {
    return request<AuthUser>("/auth/me")
  },

  logout() {
    localStorage.removeItem(AUTH_TOKEN_KEY)
    localStorage.removeItem(AUTH_USER_KEY)
    emitAuthSessionChange(null)
  },
}

export function getAuthErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    return error.message
  }

  if (error instanceof TypeError) {
    return "无法连接后端服务，请确认 EdgeSpark API 已启动。"
  }

  if (error instanceof Error) {
    return error.message
  }

  return "请求失败，请稍后再试。"
}
export function isAuthSessionInvalid(error: unknown) {
  return error instanceof ApiError && error.status === 401
}
