const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api"

async function request<T>(path: string): Promise<T> {
  const token = localStorage.getItem("saveplan.auth.token")
  const headers = new Headers()
  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
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
    throw new Error(detail)
  }

  return payload as T
}

export interface BroadcastMessage {
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
  status: string
}

export const messageClient = {
  listActiveBroadcasts() {
    return request<BroadcastMessage[]>("/broadcasts/active")
  },
  listMyMessages() {
    return request<BroadcastMessage[]>("/broadcasts/me")
  },
}
