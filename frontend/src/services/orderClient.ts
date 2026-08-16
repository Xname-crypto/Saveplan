const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (globalThis.location?.hostname === "127.0.0.1" || globalThis.location?.hostname === "localhost"
    ? "http://127.0.0.1:8000/api"
    : "/api")

const AUTH_TOKEN_KEY = "saveplan.auth.token"

export interface CreatePendingOrderPayload {
  plan_id: string
  contact_name: string
  contact_phone: string
  contact_email: string
}

export interface PendingOrder {
  order_id: string
  status: "pending_payment"
  payment_url: string
}

class OrderApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message)
    this.name = "OrderApiError"
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  const token = localStorage.getItem(AUTH_TOKEN_KEY)

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
        : "订单暂时无法创建，请稍后重试。"
    throw new OrderApiError(detail, response.status)
  }

  return payload as T
}

export const orderClient = {
  createPendingOrder(payload: CreatePendingOrderPayload) {
    return request<PendingOrder>("/orders/pending", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },
}

export function getOrderErrorMessage(error: unknown) {
  if (error instanceof OrderApiError) return error.message
  if (error instanceof TypeError) return "无法连接订单服务，请确认后端服务已启动。"
  if (error instanceof Error) return error.message
  return "订单暂时无法创建，请稍后重试。"
}
