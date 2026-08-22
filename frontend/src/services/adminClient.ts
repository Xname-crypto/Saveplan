const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api"
const ADMIN_SESSION_KEY = "saveplan.admin.profile"

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
  const headers = new Headers(options.headers)

  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json")
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    credentials: "include",
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

export interface AdminProfile {
  id: string
  email: string
  username: string
  is_active: boolean
  roles: string[]
  permissions: string[]
  last_login_at: string | null
  created_at: string
}

export interface AdminAuthResponse {
  token: string
  admin: AdminProfile
}

export interface UserRecord {
  id: string
  email: string
  username: string
  job?: string | null
  bio?: string | null
  interests?: string[]
  point_balance: number
  avatar_name?: string | null
  created_at: string
  updated_at: string
  token_version: number
}

export interface UserCreatePayload {
  email: string
  password: string
  username: string
  job?: string | null
  bio?: string | null
  interests?: string[]
  avatar_name?: string | null
  point_balance?: number | null
}

export interface UserUpdatePayload {
  email?: string | null
  username?: string | null
  job?: string | null
  bio?: string | null
  interests?: string[] | null
  avatar_name?: string | null
}

export interface RedeemCodeRecord {
  id: string
  code: string
  batch_name: string
  points: number
  max_redemptions: number
  redeemed_count: number
  is_active: boolean
  expires_at: string | null
  note: string | null
  created_by_admin_id: string | null
  created_at: string
  updated_at: string
  status: string
}

export interface BroadcastRecord {
  id: string
  channel: "announcement" | "popup" | string
  scope: "global" | "user" | string
  target_user_id: string | null
  title: string
  content: string
  priority: number
  is_active: boolean
  starts_at: string | null
  ends_at: string | null
  created_by_admin_id: string | null
  created_at: string
  updated_at: string
  status: string
}

export interface AuditLogRecord {
  id: string
  admin_id: string | null
  action: string
  resource: string
  detail: Record<string, unknown>
  created_at: string
}

export interface PointAdjustPayload {
  amount: number
  reason: string
}

export interface RedeemCodeCreatePayload {
  batch_name: string
  count: number
  points: number
  prefix?: string | null
  expires_at?: string | null
  note?: string | null
  max_redemptions?: number
}

export interface BroadcastCreatePayload {
  channel: "announcement" | "popup"
  scope: "global" | "user"
  target_user_id?: string | null
  title: string
  content: string
  priority?: number
  starts_at?: string | null
  ends_at?: string | null
}

export interface DashboardSummary {
  total_users: number
  new_users_24h: number
  new_users_7d: number
  active_redeem_codes: number
  active_announcements: number
  active_popups: number
  recent_users: UserRecord[]
  recent_broadcasts: BroadcastRecord[]
  recent_logs: AuditLogRecord[]
}

export interface BroadcastListParams {
  channel?: "announcement" | "popup"
  scope?: "global" | "user"
}

export interface BroadcastTogglePayload {
  is_active: boolean
}

function persistAdminProfile(admin: AdminProfile | null) {
  if (!admin) {
    sessionStorage.removeItem(ADMIN_SESSION_KEY)
    return
  }

  sessionStorage.setItem(ADMIN_SESSION_KEY, JSON.stringify(admin))
}

export function getStoredAdminProfile() {
  const raw = sessionStorage.getItem(ADMIN_SESSION_KEY)
  if (!raw) return null

  try {
    return JSON.parse(raw) as AdminProfile
  } catch (_error) {
    sessionStorage.removeItem(ADMIN_SESSION_KEY)
    return null
  }
}

export const adminClient = {
  async login(email: string, password: string) {
    const response = await request<AdminAuthResponse>("/admin/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    })
    persistAdminProfile(response.admin)
    return response.admin
  },

  async logout() {
    try {
      await request<{ message: string }>("/admin/auth/logout", { method: "POST" })
    } finally {
      persistAdminProfile(null)
    }
  },

  async me() {
    const profile = await request<AdminProfile>("/admin/auth/me")
    persistAdminProfile(profile)
    return profile
  },

  async listUsers(limit = 100, query?: string) {
    const params = new URLSearchParams()
    params.set("limit", String(limit))
    if (query?.trim()) params.set("query", query.trim())
    return request<UserRecord[]>(`/admin/users?${params.toString()}`)
  },

  async getUser(userId: string) {
    return request<UserRecord>(`/admin/users/${userId}`)
  },

  createUser(payload: UserCreatePayload) {
    return request<UserRecord>("/admin/users", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },

  updateUser(userId: string, payload: UserUpdatePayload) {
    return request<UserRecord>(`/admin/users/${userId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    })
  },

  deleteUser(userId: string) {
    return request<UserRecord>(`/admin/users/${userId}`, {
      method: "DELETE",
    })
  },

  adjustPoints(userId: string, payload: PointAdjustPayload) {
    return request<UserRecord>(`/admin/users/${userId}/points`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    })
  },

  async listRedeemCodes(limit = 100) {
    return request<RedeemCodeRecord[]>(`/admin/redeem-codes?limit=${limit}`)
  },

  createRedeemCodes(payload: RedeemCodeCreatePayload) {
    return request<{ batch_name: string; codes: RedeemCodeRecord[] }>("/admin/redeem-codes", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },

  deactivateRedeemCode(codeId: string) {
    return request<RedeemCodeRecord>(`/admin/redeem-codes/${codeId}/deactivate`, {
      method: "PATCH",
    })
  },

  async listBroadcasts(limit = 100, params: BroadcastListParams = {}) {
    const query = new URLSearchParams()
    query.set("limit", String(limit))
    if (params.channel) query.set("channel", params.channel)
    if (params.scope) query.set("scope", params.scope)
    return request<BroadcastRecord[]>(`/admin/broadcasts?${query.toString()}`)
  },

  createBroadcast(payload: BroadcastCreatePayload) {
    return request<BroadcastRecord>("/admin/broadcasts", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },

  toggleBroadcast(messageId: string, payload: BroadcastTogglePayload) {
    return request<BroadcastRecord>(`/admin/broadcasts/${messageId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    })
  },

  async listAuditLogs(limit = 100) {
    return request<AuditLogRecord[]>(`/admin/audit-logs?limit=${limit}`)
  },

  async getDashboardSummary() {
    return request<DashboardSummary>("/admin/dashboard/summary")
  },

  getStoredAdminProfile,
}

export function getAdminErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    return error.message
  }

  if (error instanceof TypeError) {
    return "无法连接后台服务，请确认后端已启动。"
  }

  if (error instanceof Error) {
    return error.message
  }

  return "请求失败，请稍后再试。"
}

export function isAdminAuthError(error: unknown) {
  return error instanceof ApiError && error.status === 401
}
