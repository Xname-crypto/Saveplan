const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (globalThis.location?.hostname === "127.0.0.1" || globalThis.location?.hostname === "localhost"
    ? "http://127.0.0.1:8000/api"
    : "/api")
const AUTH_TOKEN_KEY = "saveplan.auth.token"

export interface ConversionQuestion {
  number: number
  stem: string
  options: Record<string, string>
  answer: string
  analysis: string
  issues: string[]
}

export interface ConversionAsset {
  id: string
  kind: "image" | "scan_page" | "ocr_placeholder"
  source: string
  status: "pending_ocr" | "manual_review" | "unsupported"
  note: string
  marker?: string | null
  page?: number | null
  filename?: string | null
  stored_path?: string | null
  mime_type?: string | null
  preview_url?: string | null
  transcript: string
  target_question_number?: number | null
  target_field: "stem" | "analysis" | "option_A" | "option_B" | "option_C" | "option_D"
}

export interface ConversionSummary {
  id: string
  filename: string
  subject: Subject
  status: string
  question_count: number
  issue_count: number
  created_at: string
  updated_at: string
}

export type Subject = "general" | "politics" | "math" | "physics" | "chemistry" | "biology"

export interface ConversionDetail extends ConversionSummary {
  text_state: string
  raw_text: string
  issues: string[]
  questions: ConversionQuestion[]
  assets: ConversionAsset[]
  export_text?: string | null
}

export interface ConversionExport {
  export_text: string
  question_count: number
  issues: string[]
}

export interface ConversionOcrResult {
  asset: ConversionAsset
  message: string
}

function normalizeConversionSummary(summary: ConversionSummary): ConversionSummary {
  return {
    ...summary,
    filename: summary.filename ?? "",
    status: summary.status ?? "",
    question_count: summary.question_count ?? 0,
    issue_count: summary.issue_count ?? 0,
  }
}

function normalizeQuestion(question: ConversionQuestion): ConversionQuestion {
  return {
    ...question,
    options: question.options ?? {},
    stem: question.stem ?? "",
    answer: question.answer ?? "",
    analysis: question.analysis ?? "",
    issues: Array.isArray(question.issues) ? question.issues : [],
  }
}

function normalizeAsset(asset: ConversionAsset): ConversionAsset {
  return {
    ...asset,
    note: asset.note ?? "",
    transcript: asset.transcript ?? "",
    target_field: asset.target_field ?? "stem",
  }
}

function normalizeConversionDetail(detail: ConversionDetail): ConversionDetail {
  return {
    ...detail,
    raw_text: detail.raw_text ?? "",
    issues: Array.isArray(detail.issues) ? detail.issues : [],
    questions: Array.isArray(detail.questions) ? detail.questions.map(normalizeQuestion) : [],
    assets: Array.isArray(detail.assets) ? detail.assets.map(normalizeAsset) : [],
  }
}

class ConversionApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message)
    this.name = "ConversionApiError"
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
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
    throw new ConversionApiError(detail, response.status)
  }

  return payload as T
}

function authHeaders() {
  const headers = new Headers()
  const token = localStorage.getItem(AUTH_TOKEN_KEY)
  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }
  return headers
}

async function request<T>(path: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers)
  authHeaders().forEach((value, key) => headers.set(key, value))
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), 45000)

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
      signal: controller.signal,
    })
    return parseResponse<T>(response)
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("请求超过 45 秒仍未完成。请确认后端服务是否正常，或先尝试粘贴文本解析。")
    }
    throw error
  } finally {
    window.clearTimeout(timeoutId)
  }
}

export const conversionClient = {
  async list() {
    const summaries = await request<ConversionSummary[]>("/conversions")
    return Array.isArray(summaries) ? summaries.map(normalizeConversionSummary) : []
  },

  async get(id: string) {
    return normalizeConversionDetail(await request<ConversionDetail>(`/conversions/${id}`))
  },

  delete(id: string) {
    return request<void>(`/conversions/${id}`, {
      method: "DELETE",
    })
  },

  async upload(file: File, subject: Subject = "general", includeAssets = true) {
    const form = new FormData()
    form.append("file", file)
    form.append("subject", subject)
    form.append("include_assets", String(includeAssets))
    return normalizeConversionDetail(await request<ConversionDetail>("/conversions", {
      method: "POST",
      body: form,
    }))
  },

  async createFromText(title: string, text: string, subject: Subject = "general") {
    return normalizeConversionDetail(await request<ConversionDetail>("/conversions/text", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ title, text, subject }),
    }))
  },

  async saveQuestions(id: string, questions: ConversionQuestion[]) {
    return normalizeConversionDetail(await request<ConversionDetail>(`/conversions/${id}/questions`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(questions),
    }))
  },

  async saveAssets(id: string, assets: ConversionAsset[]) {
    return normalizeConversionDetail(await request<ConversionDetail>(`/conversions/${id}/assets`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(assets),
    }))
  },

  ocrAsset(conversionId: string, assetId: string) {
    return request<ConversionOcrResult>(`/conversions/${conversionId}/assets/${assetId}/ocr`, {
      method: "POST",
    })
  },

  exportKshuati(id: string) {
    return request<ConversionExport>(`/conversions/${id}/export/kshuati`, {
      method: "POST",
    })
  },

  async assetPreviewUrl(path: string) {
    const response = await fetch(`${API_BASE_URL}${path.replace(/^\/api/, "")}`, {
      headers: authHeaders(),
    })
    if (!response.ok) {
      await parseResponse<unknown>(response)
    }
    return URL.createObjectURL(await response.blob())
  },
}

export function getConversionErrorMessage(error: unknown) {
  if (error instanceof ConversionApiError) return error.message
  if (error instanceof TypeError) return "无法连接后端服务，请确认 API 已启动。"
  if (error instanceof Error) return error.message
  return "请求失败，请稍后再试。"
}
