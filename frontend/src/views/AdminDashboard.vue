<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch, type Component } from "vue"
import {
  Ban,
  BellRing,
  CalendarDays,
  Check,
  Clock3,
  Download,
  Copy,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Edit3,
  Eye,
  FileClock,
  LayoutGrid,
  LoaderCircle,
  LogOut,
  Megaphone,
  Plus,
  RefreshCcw,
  Search,
  ShieldCheck,
  Ticket,
  Trash2,
  X,
  Users,
  UserPlus,
} from "lucide-vue-next"
import { useRouter } from "@/router"
import {
  adminClient,
  getAdminErrorMessage,
  getStoredAdminProfile,
  isAdminAuthError,
   type AdminProfile,
  type AuditLogRecord,
  type BroadcastRecord,
  type DashboardSummary,
  type RedeemCodeRecord,
  type UserRecord,
} from "@/services/adminClient"

type TabKey = "overview" | "users" | "redeem-codes" | "announcements" | "popups" | "logs"
type UserFormMode = "create" | "edit"
type ToastTone = "success" | "error" | "neutral"
type DatePickerKey = "redeem-expires" | "broadcast-start" | "broadcast-end"
type ToastItem = {
  id: number
  message: string
  tone: ToastTone
}

function normalizeTabKey(value: string | null): TabKey {
  switch (value) {
    case "overview":
    case "users":
    case "redeem-codes":
    case "announcements":
    case "popups":
    case "logs":
      return value
    default:
      return "overview"
  }
}

const router = useRouter()
const activeTab = ref<TabKey>(normalizeTabKey(localStorage.getItem("saveplan.admin.active-tab")))
const loading = ref(true)
const reloading = ref(false)
const sidebarCollapsed = ref(localStorage.getItem("saveplan.admin.sidebar-collapsed") === "1")
const error = ref("")
const profile = ref<AdminProfile | null>(getStoredAdminProfile())
const summary = ref<DashboardSummary | null>(null)
const users = ref<UserRecord[]>([])
const redeemCodes = ref<RedeemCodeRecord[]>([])
const broadcasts = ref<BroadcastRecord[]>([])
const logs = ref<AuditLogRecord[]>([])
const userQuery = ref("")
const selectedUser = ref<UserRecord | null>(null)
const userEditorOpen = ref(false)
const userEditorMode = ref<UserFormMode>("create")
const userSaving = ref(false)
const deleteTargetUser = ref<UserRecord | null>(null)
const deleteConfirmationInput = ref("")
const toasts = ref<ToastItem[]>([])
let toastId = 0
const userPage = ref(1)
const userPageSize = 10
const redeemPage = ref(1)
const redeemPageSize = 8
const logPage = ref(1)
const logPageSize = 10

type BroadcastDraft = {
  channel: "announcement" | "popup"
  scope: "global" | "user"
  target_user_id: string
  title: string
  content: string
  priority: number
  starts_at: string
  ends_at: string
}

type RedeemDraft = {
  batch_name: string
  count: number
  points: number
  custom_code: string
  expires_date: string
  note: string
  max_redemptions: number
}

function loadDraft<T>(key: string): T | null {
  const raw = localStorage.getItem(key)
  if (!raw) return null
  try {
    return JSON.parse(raw) as T
  } catch (_error) {
    localStorage.removeItem(key)
    return null
  }
}

function saveDraft<T>(key: string, value: T) {
  localStorage.setItem(key, JSON.stringify(value))
}

function clearDraft(key: string) {
  localStorage.removeItem(key)
}

function escapeCsv(value: unknown) {
  const text = value == null ? "" : String(value)
  return `"${text.replace(/"/g, '""')}"`
}

function downloadCsv(filename: string, headers: string[], rows: Array<Array<unknown>>) {
  const lines = [headers.map(escapeCsv).join(","), ...rows.map((row) => row.map(escapeCsv).join(","))]
  const blob = new Blob(["\ufeff", lines.join("\r\n")], { type: "text/csv;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

function exportDataset(filename: string, headers: string[], rows: Array<Array<unknown>>) {
  downloadCsv(filename, headers, rows)
}

const userForm = reactive({
  email: "",
  username: "",
  password: "",
  job: "",
  bio: "",
  interests: "",
  avatar_name: "",
  point_balance: 100,
})
const targetUserPickerRef = ref<HTMLElement | null>(null)
const targetUserPickerOpen = ref(false)
const targetUserSearch = ref("")
const activeDatePicker = ref<DatePickerKey | null>(null)
const pointAmount = ref(0)
const pointReason = ref("后台人工调整")
const codeSaving = ref(false)
const broadcastSaving = ref(false)
const codeForm = reactive({
  batch_name: "",
  count: 10,
  points: 20,
  custom_code: "",
  expires_date: "",
  note: "",
  max_redemptions: 1,
})
const broadcastForm = reactive({
  channel: "announcement" as "announcement" | "popup",
  scope: "global" as "global" | "user",
  target_user_id: "",
  title: "",
  content: "",
  priority: 0,
  starts_at: "",
  ends_at: "",
})
const broadcastPreviewOpen = ref(false)
const logQuery = ref("")
const BROADCAST_ANNOUNCEMENT_DRAFT_KEY = "saveplan.admin.broadcast-draft.announcement"
const BROADCAST_POPUP_DRAFT_KEY = "saveplan.admin.broadcast-draft.popup"
const REDEEM_DRAFT_KEY = "saveplan.admin.redeem-draft"
const weekdayLabels = ["一", "二", "三", "四", "五", "六", "日"]
const calendarMonths = reactive<Record<DatePickerKey, string>>({
  "redeem-expires": "",
  "broadcast-start": "",
  "broadcast-end": "",
})

const tabs: Array<{ key: TabKey; label: string; icon: Component }> = [
  { key: "overview", label: "概览", icon: LayoutGrid },
  { key: "users", label: "用户", icon: Users },
  { key: "redeem-codes", label: "兑换码", icon: Ticket },
  { key: "announcements", label: "公告", icon: BellRing },
  { key: "popups", label: "弹窗", icon: Megaphone },
  { key: "logs", label: "审计", icon: FileClock },
]

function pushToast(message: string, tone: ToastTone = "neutral") {
  const id = ++toastId
  toasts.value = [...toasts.value, { id, message, tone }]
  window.setTimeout(() => {
    toasts.value = toasts.value.filter((toast) => toast.id !== id)
  }, 3600)
}

function dismissToast(id: number) {
  toasts.value = toasts.value.filter((toast) => toast.id !== id)
}

function setNotice(message: string, tone: ToastTone = "neutral") {
  pushToast(message, tone)
}

function formatDate(value: string | null | undefined) {
  if (!value) return "未设置"
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value))
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value))
}

function toIso(value: string, fallbackTime = "23:59:59") {
  const raw = value.trim()
  if (!raw) return null
  const normalized = raw.replace(/\s+/g, "T")
  const candidate =
    normalized.length === 10
      ? `${normalized}T${fallbackTime}`
      : normalized.length === 16
        ? `${normalized}:00`
        : normalized
  const parsed = new Date(candidate)
  if (Number.isNaN(parsed.getTime())) return null
  return parsed.toISOString()
}

function toDateOnly(value: string) {
  const raw = value.trim()
  if (!raw) return ""
  const normalized = raw.replace(/\s+/g, "T")
  const directDate = normalized.match(/^\d{4}-\d{2}-\d{2}/)?.[0]
  if (directDate) return directDate

  const parsed = new Date(normalized)
  if (Number.isNaN(parsed.getTime())) return ""

  const year = parsed.getFullYear()
  const month = String(parsed.getMonth() + 1).padStart(2, "0")
  const day = String(parsed.getDate()).padStart(2, "0")
  return `${year}-${month}-${day}`
}

function getLocalDateParts(date: Date) {
  return {
    year: date.getFullYear(),
    month: date.getMonth() + 1,
    day: date.getDate(),
  }
}

function toDateKey(date: Date) {
  const { year, month, day } = getLocalDateParts(date)
  return `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`
}

function getMonthKey(date: Date) {
  const { year, month } = getLocalDateParts(date)
  return `${year}-${String(month).padStart(2, "0")}`
}

function parseDateOnly(value: string) {
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (!match) return null
  const year = Number(match[1])
  const month = Number(match[2])
  const day = Number(match[3])
  const parsed = new Date(year, month - 1, day)
  if (parsed.getFullYear() !== year || parsed.getMonth() !== month - 1 || parsed.getDate() !== day) return null
  return parsed
}

function displayDateOnly(value: string) {
  return value ? value.replace(/-/g, "/") : "选择日期"
}

function datePickerValue(key: DatePickerKey) {
  if (key === "redeem-expires") return codeForm.expires_date
  if (key === "broadcast-start") return broadcastForm.starts_at
  return broadcastForm.ends_at
}

function setDatePickerValue(key: DatePickerKey, value: string) {
  if (key === "redeem-expires") {
    codeForm.expires_date = value
    return
  }
  if (key === "broadcast-start") {
    broadcastForm.starts_at = value
    return
  }
  broadcastForm.ends_at = value
}

function ensureCalendarMonth(key: DatePickerKey) {
  if (calendarMonths[key]) return
  const selectedDate = parseDateOnly(datePickerValue(key))
  calendarMonths[key] = getMonthKey(selectedDate ?? new Date())
}

function toggleDatePicker(key: DatePickerKey) {
  if (activeDatePicker.value === key) {
    activeDatePicker.value = null
    return
  }
  const selectedDate = parseDateOnly(datePickerValue(key))
  calendarMonths[key] = getMonthKey(selectedDate ?? new Date())
  activeDatePicker.value = key
}

function shiftCalendarMonth(key: DatePickerKey, offset: number) {
  ensureCalendarMonth(key)
  const [year, month] = calendarMonths[key].split("-").map(Number)
  calendarMonths[key] = getMonthKey(new Date(year, month - 1 + offset, 1))
}

function calendarMonthLabel(key: DatePickerKey) {
  ensureCalendarMonth(key)
  const [year, month] = calendarMonths[key].split("-")
  return `${year}年${month}月`
}

function calendarCells(key: DatePickerKey) {
  ensureCalendarMonth(key)
  const [year, month] = calendarMonths[key].split("-").map(Number)
  const firstDay = new Date(year, month - 1, 1)
  const mondayOffset = (firstDay.getDay() + 6) % 7
  const startDate = new Date(year, month - 1, 1 - mondayOffset)
  const selectedValue = datePickerValue(key)
  const todayValue = toDateKey(new Date())

  return Array.from({ length: 42 }, (_, index) => {
    const date = new Date(startDate)
    date.setDate(startDate.getDate() + index)
    const value = toDateKey(date)
    return {
      value,
      label: String(date.getDate()),
      inMonth: date.getMonth() === month - 1,
      selected: value === selectedValue,
      today: value === todayValue,
    }
  })
}

function selectDate(key: DatePickerKey, value: string) {
  setDatePickerValue(key, value)
  activeDatePicker.value = null
}

function clearDate(key: DatePickerKey) {
  setDatePickerValue(key, "")
  activeDatePicker.value = null
}

function normalizeRedeemCodeInput(value: string) {
  return value
    .toUpperCase()
    .replace(/[^A-Z0-9-]/g, "")
    .replace(/-{2,}/g, "-")
    .slice(0, 48)
}

function generateRandomCodeSegment(length: number) {
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
  const bytes = new Uint8Array(length)
  window.crypto.getRandomValues(bytes)
  return Array.from(bytes, (byte) => alphabet[byte % alphabet.length]).join("")
}

function generateRedeemCodeValue() {
  return `SP-${generateRandomCodeSegment(4)}-${generateRandomCodeSegment(4)}`
}

function generateCustomRedeemCode() {
  codeForm.custom_code = generateRedeemCodeValue()
  codeForm.count = 1
  if (!codeForm.batch_name.trim()) {
    codeForm.batch_name = "手动兑换码"
  }
}

function handleCustomRedeemCodeInput(event: Event) {
  const input = event.target as HTMLInputElement
  const normalized = normalizeRedeemCodeInput(input.value)
  codeForm.custom_code = normalized
  input.value = normalized
  if (normalized) {
    codeForm.count = 1
  }
}

function formatDraftDateTime(value: string, fallbackTime: string) {
  const raw = value.trim()
  if (!raw) return "未设置"
  const normalized = raw.replace(/\s+/g, " ")
  if (normalized.length === 10) return `${normalized} ${fallbackTime.slice(0, 5)}`
  if (normalized.length === 16) return `${normalized}:00`
  return normalized
}

function statusBadge(status: string) {
  switch (status) {
    case "active":
      return "bg-emerald-50 text-emerald-700 border-emerald-200"
    case "scheduled":
      return "bg-sky-50 text-sky-700 border-sky-200"
    case "expired":
      return "bg-amber-50 text-amber-700 border-amber-200"
    case "used":
      return "bg-slate-100 text-slate-600 border-slate-200"
    default:
      return "bg-rose-50 text-rose-700 border-rose-200"
  }
}

function formatStatus(status: string) {
  switch (status) {
    case "active":
      return "生效中"
    case "scheduled":
      return "待生效"
    case "expired":
      return "已过期"
    case "used":
      return "已使用"
    case "inactive":
      return "已停用"
    default:
      return status || "未知"
  }
}

const filteredUsers = computed(() => {
  const query = userQuery.value.trim().toLowerCase()
  if (!query) return users.value
  return users.value.filter((item) => {
    const interestText = Array.isArray(item.interests) ? item.interests.join(", ") : ""
    return [item.id, item.username, item.email, item.job || "", item.bio || "", item.avatar_name || "", interestText].some((field) =>
      field.toLowerCase().includes(query),
    )
  })
})

const paginatedUsers = computed(() =>
  filteredUsers.value.slice((userPage.value - 1) * userPageSize, userPage.value * userPageSize),
)
const userPageCount = computed(() => Math.max(1, Math.ceil(filteredUsers.value.length / userPageSize)))

const overviewStats = computed(() => [
  { label: "总用户", value: summary.value?.total_users ?? users.value.length, icon: Users },
  { label: "近24小时新增", value: summary.value?.new_users_24h ?? 0, icon: UserPlus },
  { label: "近7天新增", value: summary.value?.new_users_7d ?? 0, icon: Clock3 },
  { label: "有效兑换码", value: summary.value?.active_redeem_codes ?? redeemCodes.value.filter((item) => item.status === "active").length, icon: Ticket },
  { label: "有效公告", value: summary.value?.active_announcements ?? broadcasts.value.filter((item) => item.channel === "announcement" && item.status === "active").length, icon: BellRing },
  { label: "有效弹窗", value: summary.value?.active_popups ?? broadcasts.value.filter((item) => item.channel === "popup" && item.status === "active").length, icon: Megaphone },
])

const selectedUserPreview = computed(() => selectedUser.value)
const recentUsers = computed(() => summary.value?.recent_users ?? users.value.slice(0, 5))
const recentBroadcasts = computed(() => summary.value?.recent_broadcasts ?? broadcasts.value.slice(0, 5))
const recentLogs = computed(() => summary.value?.recent_logs ?? logs.value.slice(0, 5))
const sortedRedeemCodes = computed(() =>
  redeemCodes.value.slice().sort((a, b) => b.created_at.localeCompare(a.created_at)),
)
const paginatedRedeemCodes = computed(() =>
  sortedRedeemCodes.value.slice((redeemPage.value - 1) * redeemPageSize, redeemPage.value * redeemPageSize),
)
const redeemPageCount = computed(() => Math.max(1, Math.ceil(sortedRedeemCodes.value.length / redeemPageSize)))
const sortedLogs = computed(() =>
  logs.value.slice().sort((a, b) => b.created_at.localeCompare(a.created_at)),
)
const filteredLogs = computed(() => {
  const query = logQuery.value.trim().toLowerCase()
  const source = sortedLogs.value
  if (!query) return source
  return source.filter((log) =>
    [log.action, log.resource, JSON.stringify(log.detail)].some((field) =>
      field.toLowerCase().includes(query),
    ),
  )
})
const paginatedLogs = computed(() =>
  filteredLogs.value.slice((logPage.value - 1) * logPageSize, logPage.value * logPageSize),
)
const logPageCount = computed(() => Math.max(1, Math.ceil(filteredLogs.value.length / logPageSize)))
const userExportRows = computed(() =>
  filteredUsers.value.map((item) => [
    item.id,
    item.username,
    item.email,
    item.job || "",
    item.point_balance,
    formatDate(item.created_at),
    formatDate(item.updated_at),
  ]),
)
const redeemExportRows = computed(() =>
  sortedRedeemCodes.value.map((item) => [
    item.code,
    item.batch_name,
    item.points,
    formatStatus(item.status),
    formatDate(item.expires_at),
    formatDate(item.created_at),
  ]),
)
const logExportRows = computed(() =>
  filteredLogs.value.map((item) => [
    item.action,
    item.resource,
    JSON.stringify(item.detail),
    formatDateTime(item.created_at),
  ]),
)
const activeRedeemCodeList = computed(() =>
  redeemCodes.value.filter((item) => item.status === "active" || item.status === "scheduled"),
)
const announcementBroadcasts = computed(() =>
  broadcasts.value.filter((item) => item.channel === "announcement"),
)
const popupBroadcasts = computed(() => broadcasts.value.filter((item) => item.channel === "popup"))
const globalPopups = computed(() => popupBroadcasts.value.filter((item) => item.scope === "global"))
const directPopups = computed(() => popupBroadcasts.value.filter((item) => item.scope === "user"))
const broadcastTargetUsers = computed(() =>
  users.value.slice().sort((a, b) => a.username.localeCompare(b.username)),
)
const filteredBroadcastTargetUsers = computed(() => {
  const query = targetUserSearch.value.trim().toLowerCase()
  if (!query) return broadcastTargetUsers.value
  return broadcastTargetUsers.value.filter((item) => {
    return [item.username, item.email, item.job || ""].some((field) =>
      field.toLowerCase().includes(query),
    )
  })
})
const selectedBroadcastTargetUser = computed(() =>
  users.value.find((item) => item.id === broadcastForm.target_user_id) ?? null,
)
const selectedBroadcastTargetLabel = computed(() => {
  if (!selectedBroadcastTargetUser.value) return "请选择用户"
  return `${selectedBroadcastTargetUser.value.username} / ${selectedBroadcastTargetUser.value.email}`
})

const broadcastPreviewSummary = computed(() => ({
  kind:
    broadcastForm.channel === "announcement"
      ? "全站公告"
      : broadcastForm.scope === "user"
        ? "单用户弹窗"
        : "全站弹窗",
  title: broadcastForm.title.trim() || "未填写标题",
  content: broadcastForm.content.trim() || "未填写内容",
  target: broadcastForm.scope === "user" ? selectedBroadcastTargetLabel.value : "全站",
  startsAt: formatDraftDateTime(broadcastForm.starts_at, "00:00"),
  endsAt: formatDraftDateTime(broadcastForm.ends_at, "23:59"),
}))

function getBroadcastDraftKey(channel: "announcement" | "popup") {
  return channel === "announcement" ? BROADCAST_ANNOUNCEMENT_DRAFT_KEY : BROADCAST_POPUP_DRAFT_KEY
}

function persistBroadcastDraft() {
  saveDraft(getBroadcastDraftKey(broadcastForm.channel), {
    channel: broadcastForm.channel,
    scope: broadcastForm.scope,
    target_user_id: broadcastForm.target_user_id,
    title: broadcastForm.title,
    content: broadcastForm.content,
    priority: broadcastForm.priority,
    starts_at: broadcastForm.starts_at,
    ends_at: broadcastForm.ends_at,
  } satisfies BroadcastDraft)
}

function restoreBroadcastDraft(channel: "announcement" | "popup") {
  const draft = loadDraft<BroadcastDraft>(getBroadcastDraftKey(channel))
  if (draft) {
    Object.assign(broadcastForm, draft)
    broadcastForm.starts_at = toDateOnly(broadcastForm.starts_at)
    broadcastForm.ends_at = toDateOnly(broadcastForm.ends_at)
    return
  }

  broadcastForm.channel = channel
  broadcastForm.scope = channel === "announcement" ? "global" : "global"
  broadcastForm.target_user_id = ""
  broadcastForm.title = ""
  broadcastForm.content = ""
  broadcastForm.priority = 0
  broadcastForm.starts_at = ""
  broadcastForm.ends_at = ""
}

function restoreRedeemDraft() {
  const draft = loadDraft<RedeemDraft>(REDEEM_DRAFT_KEY)
  if (draft) {
    const legacyDraft = draft as RedeemDraft & { prefix?: string }
    const nextDraft = { ...legacyDraft }
    delete nextDraft.prefix
    Object.assign(codeForm, nextDraft)
    codeForm.custom_code = normalizeRedeemCodeInput(codeForm.custom_code || "")
    codeForm.expires_date = toDateOnly(codeForm.expires_date)
    if (codeForm.custom_code) codeForm.count = 1
  }
}

function broadcastTargetLabel(userId: string | null | undefined) {
  if (!userId) return "全站"
  const user = users.value.find((item) => item.id === userId)
  return user ? `${user.username} / ${user.email}` : userId
}

function toggleTargetUserPicker() {
  if (broadcastForm.channel !== "popup" || broadcastForm.scope !== "user") return
  const opening = !targetUserPickerOpen.value
  targetUserPickerOpen.value = opening
  if (opening) targetUserSearch.value = ""
}

function closeTargetUserPicker() {
  targetUserPickerOpen.value = false
}

function selectTargetUser(user: UserRecord) {
  broadcastForm.target_user_id = user.id
  targetUserSearch.value = ""
  closeTargetUserPicker()
}

function openDirectPopupForUser(user: UserRecord) {
  activeTab.value = "popups"
  broadcastForm.channel = "popup"
  broadcastForm.scope = "user"
  broadcastForm.target_user_id = user.id
  broadcastForm.title = `${user.username} 的定向弹窗`
  broadcastForm.content = ""
  targetUserSearch.value = ""
  targetUserPickerOpen.value = false
}

function openCreateUser() {
  userEditorMode.value = "create"
  selectedUser.value = null
  userForm.email = ""
  userForm.username = ""
  userForm.password = ""
  userForm.job = ""
  userForm.bio = ""
  userForm.interests = ""
  userForm.avatar_name = ""
  userForm.point_balance = 100
  userEditorOpen.value = true
}

function openEditUser(user: UserRecord) {
  userEditorMode.value = "edit"
  selectedUser.value = user
  userForm.email = user.email
  userForm.username = user.username
  userForm.password = ""
  userForm.job = user.job || ""
  userForm.bio = user.bio || ""
  userForm.interests = (user.interests || []).join(", ")
  userForm.avatar_name = user.avatar_name || ""
  userForm.point_balance = user.point_balance
  userEditorOpen.value = true
}

function closeUserEditor() {
  userEditorOpen.value = false
}

function openDeleteTarget(user: UserRecord) {
  deleteTargetUser.value = user
  deleteConfirmationInput.value = ""
}

function closeDeleteTarget() {
  deleteTargetUser.value = null
  deleteConfirmationInput.value = ""
}

function parseInterests(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
}

async function submitUserForm() {
  const email = userForm.email.trim()
  const username = userForm.username.trim()
  if (email.length < 3 || username.length < 3) return
  if (userEditorMode.value === "create" && userForm.password.trim().length < 6) return

  userSaving.value = true
  try {
    const payload = {
      email,
      username,
      job: userForm.job.trim() || null,
      bio: userForm.bio.trim() || null,
      interests: parseInterests(userForm.interests),
      avatar_name: userForm.avatar_name.trim() || null,
    }
    const updated =
      userEditorMode.value === "create"
        ? await adminClient.createUser({
            ...payload,
            password: userForm.password,
            point_balance: userForm.point_balance,
          })
        : selectedUser.value
          ? await adminClient.updateUser(selectedUser.value.id, payload)
          : null

    if (updated) {
      users.value =
        userEditorMode.value === "create"
          ? [updated, ...users.value]
          : users.value.map((item) => (item.id === updated.id ? updated : item))
      selectedUser.value = updated
      setNotice(userEditorMode.value === "create" ? "已创建用户。" : "已更新用户。", "success")
      await refreshLogs()
      closeUserEditor()
    }
  } catch (submitError) {
    setNotice(getAdminErrorMessage(submitError), "error")
  } finally {
    userSaving.value = false
  }
}

async function confirmDeleteUser() {
  if (!deleteTargetUser.value) return
  if (deleteConfirmationInput.value.trim() !== deleteTargetUser.value.username) {
    setNotice("请输入完整用户名以确认删除。", "error")
    return
  }
  try {
    const deleted = await adminClient.deleteUser(deleteTargetUser.value.id)
    users.value = users.value.filter((item) => item.id !== deleted.id)
    if (selectedUser.value?.id === deleted.id) selectedUser.value = null
    setNotice("已删除用户。", "success")
    await refreshLogs()
    closeDeleteTarget()
  } catch (deleteError) {
    setNotice(getAdminErrorMessage(deleteError), "error")
  }
}

async function refreshLogs() {
  logs.value = await adminClient.listAuditLogs(100)
}

async function loadDashboard() {
  loading.value = true
  error.value = ""
  try {
    profile.value = await adminClient.me()
    const [summaryResult, userResult, codeResult, broadcastResult, logResult] = await Promise.allSettled([
      adminClient.getDashboardSummary(),
      adminClient.listUsers(300),
      adminClient.listRedeemCodes(200),
      adminClient.listBroadcasts(200),
      adminClient.listAuditLogs(100),
    ])

    if (summaryResult.status === "fulfilled") summary.value = summaryResult.value
    if (userResult.status === "fulfilled") users.value = userResult.value
    if (codeResult.status === "fulfilled") redeemCodes.value = codeResult.value
    if (broadcastResult.status === "fulfilled") broadcasts.value = broadcastResult.value
    if (logResult.status === "fulfilled") logs.value = logResult.value

    const rejected = [summaryResult, userResult, codeResult, broadcastResult, logResult].find(
      (item) => item.status === "rejected",
    )
    if (rejected && rejected.status === "rejected") {
      setNotice(getAdminErrorMessage(rejected.reason), "error")
    }
  } catch (loadError) {
    if (isAdminAuthError(loadError)) {
      await router.replace("/admin/login")
      return
    }
    error.value = getAdminErrorMessage(loadError)
  } finally {
    loading.value = false
  }
}

async function reloadDashboard() {
  reloading.value = true
  try {
    await loadDashboard()
  } finally {
    reloading.value = false
  }
}

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem("saveplan.admin.sidebar-collapsed", sidebarCollapsed.value ? "1" : "0")
}

function openUserDetail(user: UserRecord) {
  selectedUser.value = user
  pointAmount.value = 0
  pointReason.value = "后台人工调整"
}

async function saveUserPoints() {
  if (!selectedUser.value || !pointAmount.value || pointReason.value.trim().length < 2) return

  userSaving.value = true
  try {
    const updated = await adminClient.adjustPoints(selectedUser.value.id, {
      amount: pointAmount.value,
      reason: pointReason.value.trim(),
    })
    users.value = users.value.map((item) => (item.id === updated.id ? updated : item))
    selectedUser.value = updated
    pointAmount.value = 0
    setNotice(`已调整 ${updated.username} 的积分。`, "success")
    const latestLogs = await adminClient.listAuditLogs(100)
    logs.value = latestLogs
  } catch (adjustError) {
    setNotice(getAdminErrorMessage(adjustError), "error")
  } finally {
    userSaving.value = false
  }
}

async function createRedeemCodeBatch() {
  if (!codeForm.batch_name.trim() || !codeForm.count || !codeForm.points) return

  codeSaving.value = true
  try {
    const customCode = normalizeRedeemCodeInput(codeForm.custom_code)
    const response = await adminClient.createRedeemCodes({
      batch_name: codeForm.batch_name.trim(),
      count: customCode ? 1 : codeForm.count,
      points: codeForm.points,
      custom_code: customCode || null,
      expires_at: toIso(codeForm.expires_date),
      note: codeForm.note.trim() || null,
      max_redemptions: codeForm.max_redemptions,
    })
    redeemCodes.value = [...response.codes, ...redeemCodes.value]
    setNotice(`已生成 ${response.codes.length} 个兑换码。`, "success")
    clearDraft(REDEEM_DRAFT_KEY)
    codeForm.batch_name = ""
    codeForm.custom_code = ""
    codeForm.expires_date = ""
    codeForm.note = ""
    const latestLogs = await adminClient.listAuditLogs(100)
    logs.value = latestLogs
  } catch (createError) {
    setNotice(getAdminErrorMessage(createError), "error")
  } finally {
    codeSaving.value = false
  }
}

async function deactivateRedeemCode(codeId: string) {
  try {
    const updated = await adminClient.deactivateRedeemCode(codeId)
    redeemCodes.value = redeemCodes.value.map((item) => (item.id === updated.id ? updated : item))
    setNotice(`兑换码 ${updated.code} 已停用。`, "success")
    const latestLogs = await adminClient.listAuditLogs(100)
    logs.value = latestLogs
  } catch (deactivateError) {
    setNotice(getAdminErrorMessage(deactivateError), "error")
  }
}

async function createBroadcast() {
  if (!broadcastForm.title.trim() || !broadcastForm.content.trim()) return
  if (broadcastForm.scope === "user" && !broadcastForm.target_user_id) {
    setNotice("请选择目标用户。", "error")
    return
  }

  broadcastSaving.value = true
  try {
    const submittedChannel = broadcastForm.channel
    const created = await adminClient.createBroadcast({
      channel: submittedChannel,
      scope: broadcastForm.scope,
      target_user_id: broadcastForm.scope === "user" ? broadcastForm.target_user_id : null,
      title: broadcastForm.title.trim(),
      content: broadcastForm.content.trim(),
      priority: broadcastForm.priority,
      starts_at: toIso(broadcastForm.starts_at, "00:00:00"),
      ends_at: toIso(broadcastForm.ends_at, "23:59:59"),
    })
    broadcasts.value = [created, ...broadcasts.value]
    setNotice(
      `已发布${created.scope === "user" ? "定向弹窗" : created.channel === "popup" ? "全站弹窗" : "公告"}.`,
      "success",
    )
    clearDraft(getBroadcastDraftKey(submittedChannel))
    broadcastForm.title = ""
    broadcastForm.content = ""
    broadcastForm.priority = 0
    broadcastForm.scope = "global"
    broadcastForm.target_user_id = ""
    broadcastForm.starts_at = ""
    broadcastForm.ends_at = ""
    broadcastPreviewOpen.value = false
    const latestLogs = await adminClient.listAuditLogs(100)
    logs.value = latestLogs
  } catch (broadcastError) {
    setNotice(getAdminErrorMessage(broadcastError), "error")
  } finally {
    broadcastSaving.value = false
  }
}

async function toggleBroadcastState(message: BroadcastRecord) {
  try {
    const updated = await adminClient.toggleBroadcast(message.id, {
      is_active: !message.is_active,
    })
    broadcasts.value = broadcasts.value.map((item) => (item.id === updated.id ? updated : item))
    setNotice(`${updated.title} 已${updated.is_active ? "恢复" : "撤回"}。`, "success")
    const latestLogs = await adminClient.listAuditLogs(100)
    logs.value = latestLogs
  } catch (broadcastError) {
    setNotice(getAdminErrorMessage(broadcastError), "error")
  }
}

async function handleLogout() {
  try {
    await adminClient.logout()
  } finally {
    await router.replace("/admin/login")
  }
}

async function copyCode(code: string) {
  await navigator.clipboard.writeText(code)
  setNotice(`已复制 ${code}。`, "success")
}

function handleDocumentPointerDown(event: MouseEvent) {
  const target = event.target as Node
  const targetElement = target instanceof Element ? target : target.parentNode instanceof Element ? target.parentNode : null
  if (!targetElement?.closest("[data-admin-date-picker]")) {
    activeDatePicker.value = null
  }
  if (targetUserPickerRef.value && !targetUserPickerRef.value.contains(target)) {
    closeTargetUserPicker()
  }
}

async function createAnnouncement() {
  broadcastForm.channel = "announcement"
  broadcastForm.scope = "global"
  if (!broadcastForm.title.trim() || !broadcastForm.content.trim()) {
    setNotice("请先填写标题和内容。", "error")
    return
  }
  broadcastPreviewOpen.value = true
}

async function createPopup() {
  broadcastForm.channel = "popup"
  if (broadcastForm.scope === "user" && !broadcastForm.target_user_id) {
    setNotice("请选择目标用户。", "error")
    return
  }
  if (!broadcastForm.title.trim() || !broadcastForm.content.trim()) {
    setNotice("请先填写标题和内容。", "error")
    return
  }
  broadcastPreviewOpen.value = true
}

async function confirmBroadcastPublish() {
  await createBroadcast()
}

const filteredAnnouncements = computed(() =>
  announcementBroadcasts.value.slice().sort((a, b) => b.priority - a.priority || b.created_at.localeCompare(a.created_at)),
)

const filteredGlobalPopups = computed(() =>
  globalPopups.value.slice().sort((a, b) => b.priority - a.priority || b.created_at.localeCompare(a.created_at)),
)

const filteredDirectPopups = computed(() =>
  directPopups.value.slice().sort((a, b) => b.priority - a.priority || b.created_at.localeCompare(a.created_at)),
)

watch(
  () => broadcastForm.channel,
  (channel) => {
    broadcastPreviewOpen.value = false
    if (channel === "announcement") {
      broadcastForm.scope = "global"
      broadcastForm.target_user_id = ""
      targetUserSearch.value = ""
      closeTargetUserPicker()
    }
  },
)

watch(
  () => broadcastForm.scope,
  (scope) => {
    broadcastPreviewOpen.value = false
    if (scope === "global") {
      broadcastForm.target_user_id = ""
      targetUserSearch.value = ""
      closeTargetUserPicker()
    }
    if (broadcastForm.channel === "announcement" && scope === "user") {
      broadcastForm.scope = "global"
    }
  },
)

watch(
  broadcastForm,
  () => {
    persistBroadcastDraft()
  },
  { deep: true },
)

watch(
  codeForm,
  () => {
    saveDraft(REDEEM_DRAFT_KEY, { ...codeForm })
  },
  { deep: true },
)

watch(userQuery, () => {
  userPage.value = 1
})

watch(logQuery, () => {
  logPage.value = 1
})

watch(
  () => filteredUsers.value.length,
  () => {
    userPage.value = Math.min(userPage.value, userPageCount.value)
  },
)

watch(
  () => sortedRedeemCodes.value.length,
  () => {
    redeemPage.value = Math.min(redeemPage.value, redeemPageCount.value)
  },
)

watch(
  () => filteredLogs.value.length,
  () => {
    logPage.value = Math.min(logPage.value, logPageCount.value)
  },
)

watch(
  () => activeTab.value,
  (tab) => {
    localStorage.setItem("saveplan.admin.active-tab", tab)
    broadcastPreviewOpen.value = false
    if (tab === "announcements") {
      restoreBroadcastDraft("announcement")
      closeTargetUserPicker()
      activeDatePicker.value = null
    }
    if (tab === "popups") {
      restoreBroadcastDraft("popup")
      activeDatePicker.value = null
    }
    if (tab === "redeem-codes") {
      restoreRedeemDraft()
      activeDatePicker.value = null
    }
  },
  { immediate: true },
)

onMounted(() => {
  document.addEventListener("mousedown", handleDocumentPointerDown)
  void loadDashboard()
})

onBeforeUnmount(() => {
  document.removeEventListener("mousedown", handleDocumentPointerDown)
})
</script>

<template>
  <main class="min-h-screen bg-[#f6f7f3] text-slate-900">
    <div v-if="loading" class="fixed inset-0 z-40 flex items-center justify-center bg-[#f6f7f3]/95 backdrop-blur-sm">
      <div class="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 shadow-sm">
        <LoaderCircle class="h-4 w-4 animate-spin" />
        正在加载管理台...
      </div>
    </div>

    <div
      class="grid min-h-screen transition-[grid-template-columns] duration-200 lg:grid-cols-[280px_minmax(0,1fr)]"
      :class="sidebarCollapsed ? 'lg:grid-cols-[92px_minmax(0,1fr)]' : 'lg:grid-cols-[280px_minmax(0,1fr)]'"
    >
      <aside
        class="relative flex flex-col border-r border-slate-200 bg-white/80 backdrop-blur lg:sticky lg:top-0 lg:h-screen lg:overflow-y-auto"
        :class="sidebarCollapsed ? 'px-3 py-4 lg:px-3' : 'px-5 py-6'"
      >
        <div v-if="sidebarCollapsed" class="flex h-full flex-col items-center">
          <div class="flex flex-col items-center gap-3">
            <button
              type="button"
              class="inline-flex h-12 w-12 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-500 transition hover:bg-slate-50"
              aria-label="展开侧边栏"
              title="展开侧边栏"
              @click="toggleSidebar"
            >
              <ChevronRight class="h-4 w-4" />
            </button>

            <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-900 text-white">
              <ShieldCheck class="h-5 w-5" />
            </div>
          </div>

          <nav class="mt-6 grid justify-items-center gap-3">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              type="button"
              class="flex h-12 w-12 items-center justify-center rounded-xl border text-left text-sm transition"
              :title="tab.label"
              :aria-label="tab.label"
              :class="[
                activeTab === tab.key
                  ? 'border-slate-900 bg-slate-900 text-white'
                  : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50',
              ]"
              @click="activeTab = tab.key"
            >
              <component :is="tab.icon" class="h-4 w-4" />
            </button>
          </nav>

          <div class="mt-auto flex flex-col items-center gap-3 pb-2 pt-6">
            <button
              type="button"
              class="inline-flex h-12 w-12 items-center justify-center rounded-xl border border-rose-200 text-rose-600 transition hover:bg-rose-50"
              title="退出登录"
              aria-label="退出登录"
              @click="handleLogout"
            >
              <LogOut class="h-4 w-4" />
            </button>
          </div>
        </div>

        <div v-else class="flex h-full flex-col">
          <div class="flex items-center gap-3 pr-12">
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-900 text-white">
              <ShieldCheck class="h-5 w-5" />
            </div>
            <div>
              <p class="text-sm text-slate-500">Saveplan</p>
              <h1 class="text-lg font-semibold">管理后台</h1>
            </div>
            <button
              type="button"
              class="ml-auto inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 transition hover:bg-slate-50"
              :aria-label="'收起侧边栏'"
              title="收起侧边栏"
              @click="toggleSidebar"
            >
              <ChevronLeft class="h-4 w-4" />
            </button>
          </div>

          <nav class="mt-6 grid flex-1 content-start gap-2">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              type="button"
              class="flex items-center rounded-xl border text-left text-sm transition"
              :title="tab.label"
              :aria-label="tab.label"
              :class="[
                'w-full justify-between px-4 py-3',
                activeTab === tab.key
                  ? 'border-slate-900 bg-slate-900 text-white'
                  : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50',
              ]"
              @click="activeTab = tab.key"
            >
              <span class="flex items-center gap-3">
                <component :is="tab.icon" class="h-4 w-4" />
                <span>{{ tab.label }}</span>
              </span>
            </button>
          </nav>

          <div class="mt-auto pt-6">
            <div class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-4">
              <p class="text-xs uppercase tracking-[0.2em] text-slate-500">当前管理员</p>
              <p class="mt-2 text-sm font-semibold">{{ profile?.username || "加载中" }}</p>
              <p class="mt-1 break-all text-xs leading-5 text-slate-500">{{ profile?.email || "..." }}</p>
            </div>

            <button
              type="button"
              class="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 px-4 py-3 text-sm font-medium text-rose-600 transition hover:border-rose-200 hover:bg-rose-50"
              @click="handleLogout"
            >
              <LogOut class="h-4 w-4" />
              <span>退出登录</span>
            </button>
          </div>
        </div>
      </aside>

      <section class="px-4 py-4 sm:px-6 lg:px-8 lg:py-6">
        <div class="mx-auto max-w-[1600px] space-y-6">
          <header class="rounded-xl border border-slate-200 bg-white px-5 py-4 shadow-sm">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 class="text-2xl font-semibold">管理后台</h2>
                <p class="mt-1 text-sm text-slate-500">用户、积分、公告、弹窗和审计集中管理。</p>
              </div>
              <div class="flex items-center gap-3">
                <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                  {{ profile?.roles?.[0] || "super_admin" }}
                </span>
                <button
                  type="button"
                  class="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                  @click="reloadDashboard"
                >
                  <RefreshCcw class="h-4 w-4" :class="{ 'animate-spin': reloading }" />
                  重新同步
                </button>
              </div>
            </div>
          </header>

          <section v-if="activeTab === 'overview'" class="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
            <article class="xl:col-span-2">
              <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                <article
                  v-for="stat in overviewStats"
                  :key="stat.label"
                  class="rounded-xl border border-slate-200 bg-white px-4 py-4 shadow-sm"
                >
                  <div class="flex items-center justify-between">
                    <p class="text-sm text-slate-500">{{ stat.label }}</p>
                    <component :is="stat.icon" class="h-4 w-4 text-slate-400" />
                  </div>
                  <p class="mt-3 text-3xl font-semibold tracking-tight">{{ stat.value }}</p>
                </article>
              </div>
            </article>

            <article class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-slate-500">最近新增用户</p>
                  <h3 class="mt-1 text-lg font-semibold">用户增长概览</h3>
                </div>
                <UserPlus class="h-5 w-5 text-slate-400" />
              </div>
              <div class="mt-4 grid gap-3">
                <div v-for="user in recentUsers" :key="user.id" class="rounded-lg border border-slate-200 px-4 py-3">
                  <div class="flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <p class="truncate text-sm font-medium text-slate-900">{{ user.username }}</p>
                      <p class="truncate text-xs text-slate-500">{{ user.email }}</p>
                    </div>
                    <span class="text-xs text-slate-400">{{ formatDate(user.created_at) }}</span>
                  </div>
                </div>
                <p v-if="!recentUsers.length" class="py-8 text-center text-sm text-slate-400">暂无用户。</p>
              </div>
            </article>

            <article class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-slate-500">最近动态</p>
                  <h3 class="mt-1 text-lg font-semibold">操作与发布记录</h3>
                </div>
                <FileClock class="h-5 w-5 text-slate-400" />
              </div>
              <div class="mt-4 grid gap-3">
                <div v-for="message in recentBroadcasts" :key="message.id" class="rounded-lg border border-slate-200 px-4 py-3">
                  <div class="flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <p class="truncate text-sm font-medium text-slate-900">{{ message.title }}</p>
                      <p class="mt-1 text-xs text-slate-500">{{ message.channel === 'popup' ? '弹窗' : '公告' }} · {{ message.scope === 'user' ? '单用户' : '全站' }}</p>
                    </div>
                    <span class="rounded-full border px-2.5 py-1 text-[11px] font-medium" :class="statusBadge(message.status)">{{ formatStatus(message.status) }}</span>
                  </div>
                </div>
                <p v-if="!recentBroadcasts.length" class="py-4 text-center text-sm text-slate-400">暂无发布记录。</p>
              </div>

              <div class="mt-6 grid gap-3">
                <div v-for="log in recentLogs" :key="log.id" class="rounded-lg border border-slate-200 px-4 py-3">
                  <p class="text-sm font-medium">{{ log.action }}</p>
                  <p class="mt-1 text-xs text-slate-500">{{ log.resource }}</p>
                  <p class="mt-1 text-xs text-slate-400">{{ formatDate(log.created_at) }}</p>
                </div>
                <p v-if="!recentLogs.length" class="py-8 text-center text-sm text-slate-400">暂无审计记录。</p>
              </div>
            </article>
          </section>

          <section v-else-if="activeTab === 'users'" class="space-y-6">
            <article class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <p class="text-sm text-slate-500">用户管理</p>
                  <h3 class="mt-1 text-lg font-semibold">真实用户列表与 CRUD</h3>
                </div>
                <div class="flex items-center gap-3">
                  <label class="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                    <Search class="h-4 w-4 text-slate-400" />
                    <input
                      v-model="userQuery"
                      type="search"
                      class="w-72 bg-transparent text-sm outline-none"
                      placeholder="搜索用户名、邮箱、身份"
                    />
                  </label>
                  <button
                    type="button"
                    class="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                    @click="exportDataset(`saveplan-users-${new Date().toISOString().slice(0, 10)}.csv`, ['用户ID', '用户名', '邮箱', '身份', '积分', '注册时间', '更新时间'], userExportRows)"
                  >
                    <Download class="h-4 w-4" />
                    导出
                  </button>
                  <button
                    type="button"
                    class="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800"
                    @click="openCreateUser"
                  >
                    <UserPlus class="h-4 w-4" />
                    新建用户
                  </button>
                </div>
              </div>

              <div class="mt-4 overflow-x-auto">
                <table class="min-w-full border-separate border-spacing-0 text-left">
                  <thead>
                    <tr class="text-xs uppercase tracking-[0.2em] text-slate-400">
                      <th class="border-b border-slate-200 py-3 font-medium">用户</th>
                      <th class="border-b border-slate-200 py-3 font-medium">邮箱</th>
                      <th class="border-b border-slate-200 py-3 font-medium">身份</th>
                      <th class="border-b border-slate-200 py-3 font-medium">积分</th>
                      <th class="border-b border-slate-200 py-3 font-medium">注册时间</th>
                      <th class="border-b border-slate-200 py-3 text-right font-medium">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="user in paginatedUsers" :key="user.id" class="border-b border-slate-100">
                      <td class="py-4 pr-4">
                        <p class="font-medium">{{ user.username }}</p>
                        <p class="mt-1 text-xs text-slate-500">ID: {{ user.id }}</p>
                      </td>
                      <td class="py-4 pr-4 text-sm text-slate-700">{{ user.email }}</td>
                      <td class="py-4 pr-4 text-sm text-slate-600">{{ user.job || "未填写" }}</td>
                      <td class="py-4 pr-4 text-sm font-medium">{{ user.point_balance }}</td>
                      <td class="py-4 pr-4 text-sm text-slate-600">{{ formatDate(user.created_at) }}</td>
                      <td class="py-4 pr-4 text-right">
                        <div class="flex flex-wrap items-center justify-end gap-2">
                          <button type="button" class="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50" @click="openUserDetail(user)">
                            <Eye class="h-3.5 w-3.5" />
                            详情
                          </button>
                          <button type="button" class="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50" @click="openEditUser(user)">
                            <Edit3 class="h-3.5 w-3.5" />
                            编辑
                          </button>
                          <button type="button" class="inline-flex items-center gap-1 rounded-lg border border-rose-200 px-3 py-2 text-sm font-medium text-rose-700 hover:bg-rose-50" @click="openDeleteTarget(user)">
                            <Trash2 class="h-3.5 w-3.5" />
                            删除
                          </button>
                        </div>
                      </td>
                    </tr>
                    <tr v-if="!paginatedUsers.length">
                      <td colspan="6" class="py-10 text-center text-sm text-slate-400">没有匹配的用户。</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div class="mt-4 flex items-center justify-between text-sm text-slate-500">
                <span>共 {{ filteredUsers.length }} 条</span>
                <div class="flex items-center gap-2">
                  <button type="button" class="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-600 disabled:opacity-40" :disabled="userPage === 1" @click="userPage -= 1">
                    <ChevronLeft class="h-4 w-4" />
                  </button>
                  <span>第 {{ userPage }} / {{ userPageCount }} 页</span>
                  <button type="button" class="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-600 disabled:opacity-40" :disabled="userPage === userPageCount" @click="userPage += 1">
                    <ChevronRight class="h-4 w-4" />
                  </button>
                </div>
              </div>
            </article>
          </section>

          <section v-else-if="activeTab === 'redeem-codes'" class="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
            <article class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div class="flex items-center gap-2">
                <Ticket class="h-4 w-4 text-slate-500" />
                <h3 class="text-lg font-semibold">批量发放兑换码</h3>
              </div>

              <div class="mt-4 grid gap-3">
                <label class="block">
                  <span class="mb-1 block text-sm text-slate-500">批次名称</span>
                  <input v-model="codeForm.batch_name" class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-slate-400 focus:bg-white" placeholder="2026 夏季运营批次" />
                </label>
                <div class="grid grid-cols-2 gap-3">
                  <label class="block">
                    <span class="mb-1 block text-sm text-slate-500">数量</span>
                    <input
                      v-model.number="codeForm.count"
                      type="number"
                      min="1"
                      max="500"
                      :disabled="Boolean(codeForm.custom_code.trim())"
                      class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-slate-400 focus:bg-white disabled:cursor-not-allowed disabled:text-slate-400"
                    />
                  </label>
                  <label class="block">
                    <span class="mb-1 block text-sm text-slate-500">积分</span>
                    <input v-model.number="codeForm.points" type="number" min="1" max="100000" class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-slate-400 focus:bg-white" />
                  </label>
                </div>
                <label class="block">
                  <span class="mb-1 block text-sm text-slate-500">兑换码</span>
                  <div class="flex gap-2">
                    <input
                      v-model="codeForm.custom_code"
                      class="min-w-0 flex-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 font-mono text-sm uppercase tracking-[0.08em] outline-none transition placeholder:font-sans placeholder:normal-case placeholder:tracking-normal focus:border-slate-400 focus:bg-white"
                      placeholder="点击随机生成"
                      @input="handleCustomRedeemCodeInput"
                    />
                    <button
                      type="button"
                      class="inline-flex shrink-0 items-center gap-2 rounded-lg border border-slate-200 px-3 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                      @click="generateCustomRedeemCode"
                    >
                      <RefreshCcw class="h-4 w-4" />
                      随机生成
                    </button>
                  </div>
                  <p class="mt-1 text-xs text-slate-400">填入或随机生成完整兑换码；使用指定兑换码时数量自动为 1。</p>
                </label>
                <div class="grid grid-cols-2 gap-3">
                  <label class="block">
                    <span class="mb-1 block text-sm text-slate-500">单码可兑次数</span>
                    <input v-model.number="codeForm.max_redemptions" type="number" min="1" max="999" class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-slate-400 focus:bg-white" />
                  </label>
                  <label class="block">
                    <span class="mb-1 block text-sm text-slate-500">过期日期</span>
                    <div class="relative" data-admin-date-picker>
                      <button type="button" class="flex h-11 w-full items-center justify-between gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm outline-none transition hover:border-slate-300 hover:bg-white focus:border-slate-400 focus:bg-white" @click="toggleDatePicker('redeem-expires')">
                        <span :class="datePickerValue('redeem-expires') ? 'text-slate-900' : 'text-slate-400'">{{ displayDateOnly(datePickerValue('redeem-expires')) }}</span>
                        <CalendarDays class="h-4 w-4 shrink-0 text-slate-400" />
                      </button>
                      <div v-if="activeDatePicker === 'redeem-expires'" class="absolute left-0 top-full z-40 mt-2 w-full rounded-xl border border-slate-200 bg-white p-2 text-slate-900 shadow-[0_18px_45px_rgba(15,23,42,0.14)]">
                        <div class="flex items-center justify-between">
                          <button type="button" class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100" @click="shiftCalendarMonth('redeem-expires', -1)">
                            <ChevronLeft class="h-4 w-4" />
                          </button>
                          <p class="text-sm font-semibold">{{ calendarMonthLabel('redeem-expires') }}</p>
                          <button type="button" class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100" @click="shiftCalendarMonth('redeem-expires', 1)">
                            <ChevronRight class="h-4 w-4" />
                          </button>
                        </div>
                        <div class="mt-2 grid grid-cols-7 gap-0.5 text-center text-[11px] font-medium text-slate-400">
                          <span v-for="day in weekdayLabels" :key="day" class="py-1">{{ day }}</span>
                        </div>
                        <div class="grid grid-cols-7 gap-0.5">
                          <button v-for="day in calendarCells('redeem-expires')" :key="day.value" type="button" class="inline-flex h-7 items-center justify-center rounded-md text-xs font-medium transition" :class="day.selected ? 'bg-slate-900 text-white' : day.today ? 'border border-slate-300 text-slate-900' : day.inMonth ? 'text-slate-700 hover:bg-slate-100' : 'text-slate-300 hover:bg-slate-50'" @click="selectDate('redeem-expires', day.value)">
                            {{ day.label }}
                          </button>
                        </div>
                        <div class="mt-2 flex items-center justify-between border-t border-slate-100 pt-2 text-xs">
                          <button type="button" class="font-medium text-slate-500 hover:text-slate-900" @click="clearDate('redeem-expires')">清空</button>
                          <button type="button" class="font-medium text-slate-900 hover:text-slate-600" @click="selectDate('redeem-expires', toDateKey(new Date()))">今天</button>
                        </div>
                      </div>
                    </div>
                  </label>
                </div>
                <p class="text-xs text-slate-400">选择日期即可，未填则不设置过期时间。</p>
                <label class="block">
                  <span class="mb-1 block text-sm text-slate-500">备注</span>
                  <textarea v-model="codeForm.note" rows="4" class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-slate-400 focus:bg-white" placeholder="发放场景、活动说明、回收时间等"></textarea>
                </label>
              </div>

              <button
                type="button"
                :disabled="codeSaving"
                class="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:opacity-60"
                @click="createRedeemCodeBatch"
              >
                <LoaderCircle v-if="codeSaving" class="h-4 w-4 animate-spin" />
                <Plus v-else class="h-4 w-4" />
                生成兑换码
              </button>
            </article>

            <article class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-sm text-slate-500">兑换码列表</p>
                  <h3 class="mt-1 text-lg font-semibold">最近发放记录</h3>
                </div>
                <div class="flex items-center gap-3 text-right text-sm text-slate-500">
                  <button
                    type="button"
                    class="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                    @click="exportDataset(`saveplan-redeem-codes-${new Date().toISOString().slice(0, 10)}.csv`, ['兑换码', '批次', '积分', '状态', '过期时间', '创建时间'], redeemExportRows)"
                  >
                    <Download class="h-4 w-4" />
                    导出
                  </button>
                  <div>
                    <p>有效：{{ activeRedeemCodeList.length }} 条</p>
                    <p>总计：{{ redeemCodes.length }} 条</p>
                  </div>
                </div>
              </div>

              <div class="mt-4 overflow-x-auto">
                <table class="min-w-full text-left">
                  <thead>
                    <tr class="text-xs uppercase tracking-[0.2em] text-slate-400">
                      <th class="border-b border-slate-200 py-3 font-medium">兑换码</th>
                      <th class="border-b border-slate-200 py-3 font-medium">批次</th>
                      <th class="border-b border-slate-200 py-3 font-medium">积分</th>
                      <th class="border-b border-slate-200 py-3 text-center font-medium">状态</th>
                      <th class="border-b border-slate-200 py-3 font-medium">过期</th>
                      <th class="border-b border-slate-200 py-3 text-right font-medium">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="code in paginatedRedeemCodes" :key="code.id" class="border-b border-slate-100">
                      <td class="py-4 pr-4">
                        <p class="font-mono text-sm font-semibold">{{ code.code }}</p>
                        <p class="mt-1 text-xs text-slate-500">可兑 {{ code.max_redemptions }} 次</p>
                      </td>
                      <td class="py-4 pr-4 text-sm text-slate-700">{{ code.batch_name }}</td>
                      <td class="py-4 pr-4 text-sm font-medium">{{ code.points }}</td>
                      <td class="py-4 pr-4 text-center">
                        <span class="inline-flex min-w-14 justify-center rounded-full border px-2.5 py-1 text-[11px] font-medium" :class="statusBadge(code.status)">{{ formatStatus(code.status) }}</span>
                      </td>
                      <td class="py-4 pr-4 text-sm text-slate-600">{{ formatDate(code.expires_at) }}</td>
                      <td class="py-4 pr-4 text-right">
                        <div class="flex flex-wrap items-center justify-end gap-2">
                          <button type="button" class="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50" @click="copyCode(code.code)">
                            <Copy class="h-3.5 w-3.5" />
                            复制
                          </button>
                          <button
                            type="button"
                            class="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                            :disabled="code.status === 'inactive'"
                            @click="deactivateRedeemCode(code.id)"
                          >
                            <Ban class="h-3.5 w-3.5" />
                            停用
                          </button>
                        </div>
                      </td>
                    </tr>
                    <tr v-if="!paginatedRedeemCodes.length">
                      <td colspan="6" class="py-10 text-center text-sm text-slate-400">暂无兑换码。</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div class="mt-4 flex items-center justify-between text-sm text-slate-500">
                <span>共 {{ sortedRedeemCodes.length }} 条</span>
                <div class="flex items-center gap-2">
                  <button type="button" class="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-600 disabled:opacity-40" :disabled="redeemPage === 1" @click="redeemPage -= 1">
                    <ChevronLeft class="h-4 w-4" />
                  </button>
                  <span>第 {{ redeemPage }} / {{ redeemPageCount }} 页</span>
                  <button type="button" class="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-600 disabled:opacity-40" :disabled="redeemPage === redeemPageCount" @click="redeemPage += 1">
                    <ChevronRight class="h-4 w-4" />
                  </button>
                </div>
              </div>
            </article>
          </section>

          <section v-else-if="activeTab === 'announcements'" class="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
            <article class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div class="flex items-center gap-2">
                <BellRing class="h-4 w-4 text-slate-500" />
                <h3 class="text-lg font-semibold">全站公告</h3>
              </div>
              <div class="mt-4 grid gap-3">
                <label class="block">
                  <span class="mb-1 block text-sm text-slate-500">标题</span>
                  <input v-model="broadcastForm.title" class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-slate-400 focus:bg-white" />
                </label>
                <label class="block">
                  <span class="mb-1 block text-sm text-slate-500">内容</span>
                  <textarea v-model="broadcastForm.content" rows="6" class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-slate-400 focus:bg-white"></textarea>
                </label>
                <label class="block">
                  <span class="mb-1 block text-sm text-slate-500">优先级</span>
                  <input v-model.number="broadcastForm.priority" type="number" min="0" max="100" class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-slate-400 focus:bg-white" />
                </label>
                <div class="grid grid-cols-2 gap-3">
                  <label class="block">
                    <span class="mb-1 block text-sm text-slate-500">开始日期</span>
                    <div class="relative" data-admin-date-picker>
                      <button type="button" class="flex h-11 w-full items-center justify-between gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm outline-none transition hover:border-slate-300 hover:bg-white focus:border-slate-400 focus:bg-white" @click="toggleDatePicker('broadcast-start')">
                        <span :class="datePickerValue('broadcast-start') ? 'text-slate-900' : 'text-slate-400'">{{ displayDateOnly(datePickerValue('broadcast-start')) }}</span>
                        <CalendarDays class="h-4 w-4 shrink-0 text-slate-400" />
                      </button>
                      <div v-if="activeDatePicker === 'broadcast-start'" class="absolute left-0 top-full z-40 mt-2 w-full rounded-xl border border-slate-200 bg-white p-2 text-slate-900 shadow-[0_18px_45px_rgba(15,23,42,0.14)]">
                        <div class="flex items-center justify-between">
                          <button type="button" class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100" @click="shiftCalendarMonth('broadcast-start', -1)">
                            <ChevronLeft class="h-4 w-4" />
                          </button>
                          <p class="text-sm font-semibold">{{ calendarMonthLabel('broadcast-start') }}</p>
                          <button type="button" class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100" @click="shiftCalendarMonth('broadcast-start', 1)">
                            <ChevronRight class="h-4 w-4" />
                          </button>
                        </div>
                        <div class="mt-2 grid grid-cols-7 gap-0.5 text-center text-[11px] font-medium text-slate-400">
                          <span v-for="day in weekdayLabels" :key="day" class="py-1">{{ day }}</span>
                        </div>
                        <div class="grid grid-cols-7 gap-0.5">
                          <button v-for="day in calendarCells('broadcast-start')" :key="day.value" type="button" class="inline-flex h-7 items-center justify-center rounded-md text-xs font-medium transition" :class="day.selected ? 'bg-slate-900 text-white' : day.today ? 'border border-slate-300 text-slate-900' : day.inMonth ? 'text-slate-700 hover:bg-slate-100' : 'text-slate-300 hover:bg-slate-50'" @click="selectDate('broadcast-start', day.value)">
                            {{ day.label }}
                          </button>
                        </div>
                        <div class="mt-2 flex items-center justify-between border-t border-slate-100 pt-2 text-xs">
                          <button type="button" class="font-medium text-slate-500 hover:text-slate-900" @click="clearDate('broadcast-start')">清空</button>
                          <button type="button" class="font-medium text-slate-900 hover:text-slate-600" @click="selectDate('broadcast-start', toDateKey(new Date()))">今天</button>
                        </div>
                      </div>
                    </div>
                  </label>
                  <label class="block">
                    <span class="mb-1 block text-sm text-slate-500">结束日期</span>
                    <div class="relative" data-admin-date-picker>
                      <button type="button" class="flex h-11 w-full items-center justify-between gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm outline-none transition hover:border-slate-300 hover:bg-white focus:border-slate-400 focus:bg-white" @click="toggleDatePicker('broadcast-end')">
                        <span :class="datePickerValue('broadcast-end') ? 'text-slate-900' : 'text-slate-400'">{{ displayDateOnly(datePickerValue('broadcast-end')) }}</span>
                        <CalendarDays class="h-4 w-4 shrink-0 text-slate-400" />
                      </button>
                      <div v-if="activeDatePicker === 'broadcast-end'" class="absolute left-0 top-full z-40 mt-2 w-full rounded-xl border border-slate-200 bg-white p-2 text-slate-900 shadow-[0_18px_45px_rgba(15,23,42,0.14)]">
                        <div class="flex items-center justify-between">
                          <button type="button" class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100" @click="shiftCalendarMonth('broadcast-end', -1)">
                            <ChevronLeft class="h-4 w-4" />
                          </button>
                          <p class="text-sm font-semibold">{{ calendarMonthLabel('broadcast-end') }}</p>
                          <button type="button" class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100" @click="shiftCalendarMonth('broadcast-end', 1)">
                            <ChevronRight class="h-4 w-4" />
                          </button>
                        </div>
                        <div class="mt-2 grid grid-cols-7 gap-0.5 text-center text-[11px] font-medium text-slate-400">
                          <span v-for="day in weekdayLabels" :key="day" class="py-1">{{ day }}</span>
                        </div>
                        <div class="grid grid-cols-7 gap-0.5">
                          <button v-for="day in calendarCells('broadcast-end')" :key="day.value" type="button" class="inline-flex h-7 items-center justify-center rounded-md text-xs font-medium transition" :class="day.selected ? 'bg-slate-900 text-white' : day.today ? 'border border-slate-300 text-slate-900' : day.inMonth ? 'text-slate-700 hover:bg-slate-100' : 'text-slate-300 hover:bg-slate-50'" @click="selectDate('broadcast-end', day.value)">
                            {{ day.label }}
                          </button>
                        </div>
                        <div class="mt-2 flex items-center justify-between border-t border-slate-100 pt-2 text-xs">
                          <button type="button" class="font-medium text-slate-500 hover:text-slate-900" @click="clearDate('broadcast-end')">清空</button>
                          <button type="button" class="font-medium text-slate-900 hover:text-slate-600" @click="selectDate('broadcast-end', toDateKey(new Date()))">今天</button>
                        </div>
                      </div>
                    </div>
                  </label>
                </div>
              </div>

              <button type="button" :disabled="broadcastSaving" class="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:opacity-60" @click="createAnnouncement">
                <LoaderCircle v-if="broadcastSaving" class="h-4 w-4 animate-spin" />
                <Plus v-else class="h-4 w-4" />
                预览并发布
              </button>
            </article>

            <article class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-sm text-slate-500">公告列表</p>
                  <h3 class="mt-1 text-lg font-semibold">全站公告</h3>
                </div>
                <span class="text-sm text-slate-500">{{ filteredAnnouncements.length }} 条</span>
              </div>

              <div class="mt-4 grid gap-3">
                <div v-for="message in filteredAnnouncements" :key="message.id" class="rounded-lg border border-slate-200 px-4 py-4">
                  <div class="flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <p class="text-base font-medium">{{ message.title }}</p>
                      <p class="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-500">{{ message.content }}</p>
                    </div>
                    <span class="rounded-full border px-2.5 py-1 text-[11px] font-medium" :class="statusBadge(message.status)">{{ formatStatus(message.status) }}</span>
                  </div>
                  <div class="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-500">
                    <span>优先级：{{ message.priority }}</span>
                    <span>范围：全站</span>
                  </div>
                  <div class="mt-2 flex flex-wrap items-center gap-3 text-xs text-slate-500">
                    <span>开始：{{ formatDate(message.starts_at) }}</span>
                    <span>结束：{{ formatDate(message.ends_at) }}</span>
                  </div>
                  <div class="mt-3 flex justify-end">
                    <button type="button" class="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50" @click="toggleBroadcastState(message)">
                      <Check v-if="message.is_active" class="h-3.5 w-3.5" />
                      <Ban v-else class="h-3.5 w-3.5" />
                      {{ message.is_active ? '撤回' : '恢复' }}
                    </button>
                  </div>
                </div>
                <p v-if="!filteredAnnouncements.length" class="py-10 text-center text-sm text-slate-400">暂无公告。</p>
              </div>
            </article>
          </section>

          <section v-else-if="activeTab === 'popups'" class="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
            <article class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div class="flex items-center gap-2">
                <Megaphone class="h-4 w-4 text-slate-500" />
                <h3 class="text-lg font-semibold">弹窗投放</h3>
              </div>

              <div class="mt-4 grid gap-3">
                <label class="block">
                  <span class="mb-1 block text-sm text-slate-500">投放范围</span>
                  <div class="relative">
                    <select v-model="broadcastForm.scope" class="h-11 w-full appearance-none rounded-lg border border-slate-200 bg-slate-50 px-3 pr-10 text-sm outline-none focus:border-slate-400 focus:bg-white">
                      <option value="global">全站弹窗</option>
                      <option value="user">单用户弹窗</option>
                    </select>
                    <ChevronDown class="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  </div>
                </label>
                <label class="block" v-if="broadcastForm.scope === 'user'">
                  <span class="mb-1 block text-sm text-slate-500">目标用户</span>
                  <div ref="targetUserPickerRef" class="relative">
                    <button type="button" class="flex h-11 w-full items-center justify-between gap-3 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm leading-none text-slate-700 outline-none transition hover:border-slate-300 hover:bg-white" @click.stop="toggleTargetUserPicker">
                      <span class="min-w-0 truncate text-left">{{ selectedBroadcastTargetLabel }}</span>
                      <ChevronDown class="h-4 w-4 shrink-0 text-slate-400" />
                    </button>
                    <div v-if="targetUserPickerOpen" class="absolute left-0 right-0 top-full z-30 mt-2 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-[0_20px_50px_rgba(15,23,42,0.12)]">
                      <div class="border-b border-slate-100 p-2">
                        <div class="flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-2">
                          <Search class="h-4 w-4 text-slate-400" />
                          <input v-model="targetUserSearch" type="search" class="w-full bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400" placeholder="搜索用户名或邮箱" />
                        </div>
                      </div>
                      <div class="max-h-64 overflow-y-auto py-1">
                        <button v-for="user in filteredBroadcastTargetUsers" :key="user.id" type="button" class="flex w-full items-center justify-between gap-3 px-4 py-2.5 text-left text-sm transition hover:bg-slate-50" @click="selectTargetUser(user)">
                          <div class="min-w-0">
                            <p class="truncate text-sm font-medium text-slate-900">{{ user.username }}</p>
                            <p class="truncate text-xs text-slate-500">{{ user.email }}</p>
                          </div>
                          <Check v-if="broadcastForm.target_user_id === user.id" class="h-4 w-4 shrink-0 text-slate-900" />
                        </button>
                        <div v-if="!filteredBroadcastTargetUsers.length" class="px-4 py-8 text-center text-sm text-slate-400">没有匹配的用户。</div>
                      </div>
                    </div>
                  </div>
                </label>
                <label class="block">
                  <span class="mb-1 block text-sm text-slate-500">标题</span>
                  <input v-model="broadcastForm.title" class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-slate-400 focus:bg-white" />
                </label>
                <label class="block">
                  <span class="mb-1 block text-sm text-slate-500">内容</span>
                  <textarea v-model="broadcastForm.content" rows="6" class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-slate-400 focus:bg-white"></textarea>
                </label>
                <div class="grid grid-cols-2 gap-3">
                  <label class="block">
                    <span class="mb-1 block text-sm text-slate-500">优先级</span>
                    <input v-model.number="broadcastForm.priority" type="number" min="0" max="100" class="h-11 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
                  </label>
                  <label class="block">
                    <span class="mb-1 block text-sm text-slate-500">投放方式</span>
                    <div class="flex h-11 items-center rounded-lg border border-slate-200 bg-slate-100 px-3 text-sm text-slate-500">
                      {{ broadcastForm.scope === 'global' ? '全站弹窗' : '定向弹窗' }}
                    </div>
                  </label>
                </div>
                <div class="grid grid-cols-2 gap-3">
                  <label class="block">
                    <span class="mb-1 block text-sm text-slate-500">开始日期</span>
                    <div class="relative" data-admin-date-picker>
                      <button type="button" class="flex h-11 w-full items-center justify-between gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm outline-none transition hover:border-slate-300 hover:bg-white focus:border-slate-400 focus:bg-white" @click="toggleDatePicker('broadcast-start')">
                        <span :class="datePickerValue('broadcast-start') ? 'text-slate-900' : 'text-slate-400'">{{ displayDateOnly(datePickerValue('broadcast-start')) }}</span>
                        <CalendarDays class="h-4 w-4 shrink-0 text-slate-400" />
                      </button>
                      <div v-if="activeDatePicker === 'broadcast-start'" class="absolute left-0 top-full z-40 mt-2 w-full rounded-xl border border-slate-200 bg-white p-2 text-slate-900 shadow-[0_18px_45px_rgba(15,23,42,0.14)]">
                        <div class="flex items-center justify-between">
                          <button type="button" class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100" @click="shiftCalendarMonth('broadcast-start', -1)">
                            <ChevronLeft class="h-4 w-4" />
                          </button>
                          <p class="text-sm font-semibold">{{ calendarMonthLabel('broadcast-start') }}</p>
                          <button type="button" class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100" @click="shiftCalendarMonth('broadcast-start', 1)">
                            <ChevronRight class="h-4 w-4" />
                          </button>
                        </div>
                        <div class="mt-2 grid grid-cols-7 gap-0.5 text-center text-[11px] font-medium text-slate-400">
                          <span v-for="day in weekdayLabels" :key="day" class="py-1">{{ day }}</span>
                        </div>
                        <div class="grid grid-cols-7 gap-0.5">
                          <button v-for="day in calendarCells('broadcast-start')" :key="day.value" type="button" class="inline-flex h-7 items-center justify-center rounded-md text-xs font-medium transition" :class="day.selected ? 'bg-slate-900 text-white' : day.today ? 'border border-slate-300 text-slate-900' : day.inMonth ? 'text-slate-700 hover:bg-slate-100' : 'text-slate-300 hover:bg-slate-50'" @click="selectDate('broadcast-start', day.value)">
                            {{ day.label }}
                          </button>
                        </div>
                        <div class="mt-2 flex items-center justify-between border-t border-slate-100 pt-2 text-xs">
                          <button type="button" class="font-medium text-slate-500 hover:text-slate-900" @click="clearDate('broadcast-start')">清空</button>
                          <button type="button" class="font-medium text-slate-900 hover:text-slate-600" @click="selectDate('broadcast-start', toDateKey(new Date()))">今天</button>
                        </div>
                      </div>
                    </div>
                  </label>
                  <label class="block">
                    <span class="mb-1 block text-sm text-slate-500">结束日期</span>
                    <div class="relative" data-admin-date-picker>
                      <button type="button" class="flex h-11 w-full items-center justify-between gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm outline-none transition hover:border-slate-300 hover:bg-white focus:border-slate-400 focus:bg-white" @click="toggleDatePicker('broadcast-end')">
                        <span :class="datePickerValue('broadcast-end') ? 'text-slate-900' : 'text-slate-400'">{{ displayDateOnly(datePickerValue('broadcast-end')) }}</span>
                        <CalendarDays class="h-4 w-4 shrink-0 text-slate-400" />
                      </button>
                      <div v-if="activeDatePicker === 'broadcast-end'" class="absolute left-0 top-full z-40 mt-2 w-full rounded-xl border border-slate-200 bg-white p-2 text-slate-900 shadow-[0_18px_45px_rgba(15,23,42,0.14)]">
                        <div class="flex items-center justify-between">
                          <button type="button" class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100" @click="shiftCalendarMonth('broadcast-end', -1)">
                            <ChevronLeft class="h-4 w-4" />
                          </button>
                          <p class="text-sm font-semibold">{{ calendarMonthLabel('broadcast-end') }}</p>
                          <button type="button" class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100" @click="shiftCalendarMonth('broadcast-end', 1)">
                            <ChevronRight class="h-4 w-4" />
                          </button>
                        </div>
                        <div class="mt-2 grid grid-cols-7 gap-0.5 text-center text-[11px] font-medium text-slate-400">
                          <span v-for="day in weekdayLabels" :key="day" class="py-1">{{ day }}</span>
                        </div>
                        <div class="grid grid-cols-7 gap-0.5">
                          <button v-for="day in calendarCells('broadcast-end')" :key="day.value" type="button" class="inline-flex h-7 items-center justify-center rounded-md text-xs font-medium transition" :class="day.selected ? 'bg-slate-900 text-white' : day.today ? 'border border-slate-300 text-slate-900' : day.inMonth ? 'text-slate-700 hover:bg-slate-100' : 'text-slate-300 hover:bg-slate-50'" @click="selectDate('broadcast-end', day.value)">
                            {{ day.label }}
                          </button>
                        </div>
                        <div class="mt-2 flex items-center justify-between border-t border-slate-100 pt-2 text-xs">
                          <button type="button" class="font-medium text-slate-500 hover:text-slate-900" @click="clearDate('broadcast-end')">清空</button>
                          <button type="button" class="font-medium text-slate-900 hover:text-slate-600" @click="selectDate('broadcast-end', toDateKey(new Date()))">今天</button>
                        </div>
                      </div>
                    </div>
                  </label>
                </div>
              </div>

              <div class="mt-4 grid gap-2">
                <button type="button" :disabled="broadcastSaving" class="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:opacity-60" @click="createPopup">
                  <LoaderCircle v-if="broadcastSaving" class="h-4 w-4 animate-spin" />
                  <Plus v-else class="h-4 w-4" />
                  预览并发布
                </button>
                <button
                  type="button"
                  class="inline-flex w-full items-center justify-center gap-2 rounded-lg border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                  @click="broadcastForm.scope = 'global'"
                >
                  重置为全站弹窗
                </button>
              </div>
            </article>

            <article class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div class="grid gap-6 xl:grid-cols-2">
                <div>
                  <div class="flex items-center justify-between gap-3">
                    <div>
                      <p class="text-sm text-slate-500">全站弹窗</p>
                      <h3 class="mt-1 text-lg font-semibold">Global Popups</h3>
                    </div>
                    <span class="text-sm text-slate-500">{{ filteredGlobalPopups.length }} 条</span>
                  </div>
                  <div class="mt-4 grid gap-3">
                    <div v-for="message in filteredGlobalPopups" :key="message.id" class="rounded-lg border border-slate-200 px-4 py-4">
                      <div class="flex items-start justify-between gap-3">
                        <div class="min-w-0">
                          <p class="text-base font-medium">{{ message.title }}</p>
                          <p class="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-500">{{ message.content }}</p>
                        </div>
                        <span class="rounded-full border px-2.5 py-1 text-[11px] font-medium" :class="statusBadge(message.status)">{{ formatStatus(message.status) }}</span>
                      </div>
                      <div class="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-500">
                        <span>优先级：{{ message.priority }}</span>
                        <span>范围：全站</span>
                      </div>
                      <div class="mt-3 flex justify-end">
                        <button type="button" class="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50" @click="toggleBroadcastState(message)">
                          <Check v-if="message.is_active" class="h-3.5 w-3.5" />
                          <Ban v-else class="h-3.5 w-3.5" />
                          {{ message.is_active ? '撤回' : '恢复' }}
                        </button>
                      </div>
                    </div>
                    <p v-if="!filteredGlobalPopups.length" class="py-8 text-center text-sm text-slate-400">暂无全站弹窗。</p>
                  </div>
                </div>

                <div>
                  <div class="flex items-center justify-between gap-3">
                    <div>
                      <p class="text-sm text-slate-500">定向弹窗</p>
                      <h3 class="mt-1 text-lg font-semibold">User Popups</h3>
                    </div>
                    <span class="text-sm text-slate-500">{{ filteredDirectPopups.length }} 条</span>
                  </div>
                  <div class="mt-4 grid gap-3">
                    <div v-for="message in filteredDirectPopups" :key="message.id" class="rounded-lg border border-slate-200 px-4 py-4">
                      <div class="flex items-start justify-between gap-3">
                        <div class="min-w-0">
                          <p class="text-base font-medium">{{ message.title }}</p>
                          <p class="mt-1 text-xs text-slate-500">{{ broadcastTargetLabel(message.target_user_id) }}</p>
                          <p class="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-500">{{ message.content }}</p>
                        </div>
                        <span class="rounded-full border px-2.5 py-1 text-[11px] font-medium" :class="statusBadge(message.status)">{{ formatStatus(message.status) }}</span>
                      </div>
                      <div class="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-500">
                        <span>优先级：{{ message.priority }}</span>
                        <span>范围：单用户</span>
                      </div>
                      <div class="mt-3 flex justify-end">
                        <button type="button" class="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50" @click="toggleBroadcastState(message)">
                          <Check v-if="message.is_active" class="h-3.5 w-3.5" />
                          <Ban v-else class="h-3.5 w-3.5" />
                          {{ message.is_active ? '撤回' : '恢复' }}
                        </button>
                      </div>
                    </div>
                    <p v-if="!filteredDirectPopups.length" class="py-8 text-center text-sm text-slate-400">暂无定向弹窗。</p>
                  </div>
                </div>
              </div>
            </article>
          </section>

          <section v-else class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="text-sm text-slate-500">审计日志</p>
                <h3 class="mt-1 text-lg font-semibold">后台操作记录</h3>
              </div>
              <div class="flex items-center gap-3">
                <label class="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                  <Search class="h-4 w-4 text-slate-400" />
                  <input v-model="logQuery" type="search" class="w-56 bg-transparent text-sm outline-none" placeholder="搜索动作、资源、详情" />
                </label>
                <button
                  type="button"
                  class="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                  @click="exportDataset(`saveplan-audit-logs-${new Date().toISOString().slice(0, 10)}.csv`, ['动作', '资源', '详情', '时间'], logExportRows)"
                >
                  <Download class="h-4 w-4" />
                  导出
                </button>
                <span class="text-sm text-slate-500">{{ filteredLogs.length }} 条</span>
              </div>
            </div>
            <div class="mt-4 overflow-x-auto">
              <table class="min-w-full text-left">
                <thead>
                  <tr class="text-xs uppercase tracking-[0.2em] text-slate-400">
                    <th class="border-b border-slate-200 py-3 font-medium">动作</th>
                    <th class="border-b border-slate-200 py-3 font-medium">资源</th>
                    <th class="border-b border-slate-200 py-3 font-medium">详情</th>
                    <th class="border-b border-slate-200 py-3 font-medium">时间</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="log in paginatedLogs" :key="log.id" class="border-b border-slate-100">
                    <td class="py-4 pr-4 text-sm font-medium">{{ log.action }}</td>
                    <td class="py-4 pr-4 text-sm text-slate-600">{{ log.resource }}</td>
                    <td class="py-4 pr-4 text-sm text-slate-500">
                      <pre class="max-w-xl whitespace-pre-wrap font-sans">{{ JSON.stringify(log.detail, null, 2) }}</pre>
                    </td>
                    <td class="py-4 pr-4 text-sm text-slate-600">{{ formatDateTime(log.created_at) }}</td>
                  </tr>
                  <tr v-if="!paginatedLogs.length">
                    <td colspan="4" class="py-10 text-center text-sm text-slate-400">暂无日志。</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="mt-4 flex items-center justify-between text-sm text-slate-500">
              <span>共 {{ filteredLogs.length }} 条</span>
              <div class="flex items-center gap-2">
                <button type="button" class="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-600 disabled:opacity-40" :disabled="logPage === 1" @click="logPage -= 1">
                  <ChevronLeft class="h-4 w-4" />
                </button>
                <span>第 {{ logPage }} / {{ logPageCount }} 页</span>
                <button type="button" class="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-600 disabled:opacity-40" :disabled="logPage === logPageCount" @click="logPage += 1">
                  <ChevronRight class="h-4 w-4" />
                </button>
              </div>
            </div>
          </section>
        </div>
      </section>
    </div>

    <transition name="drawer">
      <div v-if="selectedUserPreview" class="fixed inset-0 z-50 bg-slate-950/30 backdrop-blur-sm" @click.self="selectedUser = null">
        <aside class="ml-auto flex h-full w-full max-w-xl flex-col border-l border-slate-200 bg-white shadow-[0_30px_80px_rgba(15,23,42,0.16)]">
          <div class="flex items-center justify-between border-b border-slate-200 px-6 py-5">
            <div>
              <p class="text-sm text-slate-500">用户详情</p>
              <h3 class="text-xl font-semibold">{{ selectedUserPreview.username }}</h3>
            </div>
            <button type="button" class="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50" @click="selectedUser = null">
              <X class="h-4 w-4" />
            </button>
          </div>

          <div class="flex-1 overflow-y-auto px-6 py-5">
            <div class="grid gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
              <div class="flex justify-between gap-4 text-sm">
                <span class="text-slate-500">邮箱</span>
                <span class="break-all text-right">{{ selectedUserPreview.email }}</span>
              </div>
              <div class="flex justify-between gap-4 text-sm">
                <span class="text-slate-500">身份</span>
                <span class="text-right">{{ selectedUserPreview.job || "未填写" }}</span>
              </div>
              <div class="flex justify-between gap-4 text-sm">
                <span class="text-slate-500">当前积分</span>
                <span class="text-right font-semibold">{{ selectedUserPreview.point_balance }}</span>
              </div>
              <div class="flex justify-between gap-4 text-sm">
                <span class="text-slate-500">注册时间</span>
                <span class="text-right">{{ formatDate(selectedUserPreview.created_at) }}</span>
              </div>
              <div class="flex justify-between gap-4 text-sm">
                <span class="text-slate-500">简介</span>
                <span class="max-w-[18rem] text-right text-slate-700">{{ selectedUserPreview.bio || "未填写" }}</span>
              </div>
            </div>

            <div class="mt-6">
              <h4 class="text-sm font-semibold text-slate-900">调整积分</h4>
              <div class="mt-3 grid gap-3">
                <label class="block">
                  <span class="mb-1 block text-sm text-slate-500">积分增减</span>
                  <input v-model.number="pointAmount" type="number" class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-slate-400 focus:bg-white" placeholder="可输入正数或负数" />
                </label>
                <label class="block">
                  <span class="mb-1 block text-sm text-slate-500">原因</span>
                  <textarea v-model="pointReason" rows="4" class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-slate-400 focus:bg-white"></textarea>
                </label>
              </div>
            </div>
          </div>

          <div class="border-t border-slate-200 px-6 py-4 grid gap-3">
            <button
              type="button"
              :disabled="userSaving"
              class="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:opacity-60"
              @click="saveUserPoints"
            >
              <LoaderCircle v-if="userSaving" class="h-4 w-4 animate-spin" />
              <span>{{ userSaving ? "保存中" : "提交调整" }}</span>
            </button>
            <button
              type="button"
              class="inline-flex w-full items-center justify-center gap-2 rounded-lg border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
              @click="openDirectPopupForUser(selectedUserPreview)"
            >
              <Megaphone class="h-4 w-4" />
              发送定向弹窗
            </button>
          </div>
        </aside>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="userEditorOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4 py-6 backdrop-blur-sm" @click.self="closeUserEditor">
        <section class="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white p-6 shadow-[0_30px_80px_rgba(15,23,42,0.18)]">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-sm text-slate-500">{{ userEditorMode === 'create' ? '新建用户' : '编辑用户' }}</p>
              <h3 class="text-xl font-semibold">{{ userEditorMode === 'create' ? '创建真实用户账号' : '修改用户资料' }}</h3>
            </div>
            <button type="button" class="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50" @click="closeUserEditor">
              <X class="h-4 w-4" />
            </button>
          </div>

          <div class="mt-5 grid gap-4 md:grid-cols-2">
            <label class="block">
              <span class="mb-1 block text-sm text-slate-500">用户名</span>
              <input v-model="userForm.username" class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </label>
            <label class="block">
              <span class="mb-1 block text-sm text-slate-500">邮箱</span>
              <input v-model="userForm.email" type="email" class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </label>
            <label class="block" v-if="userEditorMode === 'create'">
              <span class="mb-1 block text-sm text-slate-500">初始密码</span>
              <input v-model="userForm.password" type="password" class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </label>
            <label class="block">
              <span class="mb-1 block text-sm text-slate-500">身份</span>
              <input v-model="userForm.job" class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </label>
            <label class="block">
              <span class="mb-1 block text-sm text-slate-500">初始积分</span>
              <input v-model.number="userForm.point_balance" type="number" min="0" class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </label>
            <label class="block">
              <span class="mb-1 block text-sm text-slate-500">头像名</span>
              <input v-model="userForm.avatar_name" class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </label>
            <label class="block md:col-span-2">
              <span class="mb-1 block text-sm text-slate-500">简介</span>
              <textarea v-model="userForm.bio" rows="4" class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-slate-400 focus:bg-white"></textarea>
            </label>
            <label class="block md:col-span-2">
              <span class="mb-1 block text-sm text-slate-500">兴趣标签</span>
              <input v-model="userForm.interests" class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-slate-400 focus:bg-white" placeholder="多个标签用英文逗号分隔" />
            </label>
          </div>

          <div class="mt-6 flex items-center justify-end gap-3">
            <button type="button" class="inline-flex items-center rounded-lg border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50" @click="closeUserEditor">取消</button>
            <button type="button" :disabled="userSaving" class="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60" @click="submitUserForm">
              <LoaderCircle v-if="userSaving" class="h-4 w-4 animate-spin" />
              {{ userEditorMode === 'create' ? '创建用户' : '保存修改' }}
            </button>
          </div>
        </section>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="deleteTargetUser" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4 py-6 backdrop-blur-sm" @click.self="closeDeleteTarget">
        <section class="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-[0_30px_80px_rgba(15,23,42,0.18)]">
          <p class="text-sm text-rose-600">危险操作</p>
          <h3 class="mt-1 text-xl font-semibold">确认删除用户？</h3>
          <p class="mt-3 text-sm leading-6 text-slate-600">
            删除后将清理该用户的订单、转换、积分流水和密码重置记录，且无法恢复。
          </p>
          <div class="mt-5 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm">
            <p class="font-medium">{{ deleteTargetUser.username }}</p>
            <p class="mt-1 text-slate-500">{{ deleteTargetUser.email }}</p>
          </div>
          <label class="mt-4 block">
            <span class="mb-1 block text-sm text-slate-500">输入用户名确认</span>
            <input v-model="deleteConfirmationInput" type="text" class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-slate-400 focus:bg-white" :placeholder="deleteTargetUser.username" />
          </label>
          <div class="mt-6 flex items-center justify-end gap-3">
            <button type="button" class="inline-flex items-center rounded-lg border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50" @click="closeDeleteTarget">取消</button>
            <button
              type="button"
              :disabled="deleteConfirmationInput.trim() !== deleteTargetUser.username"
              class="inline-flex items-center rounded-lg bg-rose-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-rose-500 disabled:cursor-not-allowed disabled:opacity-50"
              @click="confirmDeleteUser"
            >
              删除
            </button>
          </div>
        </section>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="broadcastPreviewOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4 py-6 backdrop-blur-sm" @click.self="broadcastPreviewOpen = false">
        <section class="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white p-6 shadow-[0_30px_80px_rgba(15,23,42,0.18)]">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-sm text-slate-500">发布预览</p>
              <h3 class="text-xl font-semibold">{{ broadcastPreviewSummary.kind }}</h3>
            </div>
            <button type="button" class="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50" @click="broadcastPreviewOpen = false">
              <X class="h-4 w-4" />
            </button>
          </div>

          <div class="mt-5 grid gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
            <div class="flex justify-between gap-4 text-sm">
              <span class="text-slate-500">标题</span>
              <span class="max-w-[20rem] text-right font-medium">{{ broadcastPreviewSummary.title }}</span>
            </div>
            <div class="flex justify-between gap-4 text-sm">
              <span class="text-slate-500">目标</span>
              <span class="text-right">{{ broadcastPreviewSummary.target }}</span>
            </div>
            <div class="flex justify-between gap-4 text-sm">
              <span class="text-slate-500">开始</span>
              <span class="text-right">{{ broadcastPreviewSummary.startsAt }}</span>
            </div>
            <div class="flex justify-between gap-4 text-sm">
              <span class="text-slate-500">结束</span>
              <span class="text-right">{{ broadcastPreviewSummary.endsAt }}</span>
            </div>
            <div class="pt-2 text-sm leading-6 text-slate-700">
              {{ broadcastPreviewSummary.content }}
            </div>
          </div>

          <div class="mt-6 flex items-center justify-end gap-3">
            <button type="button" class="inline-flex items-center rounded-lg border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50" @click="broadcastPreviewOpen = false">取消</button>
            <button
              type="button"
              :disabled="broadcastSaving"
              class="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
              @click="confirmBroadcastPublish"
            >
              <LoaderCircle v-if="broadcastSaving" class="h-4 w-4 animate-spin" />
              确认发布
            </button>
          </div>
        </section>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="toasts.length" class="pointer-events-none fixed right-4 top-4 z-50 flex w-full max-w-sm flex-col gap-2">
        <div v-for="toast in toasts" :key="toast.id" class="pointer-events-auto rounded-xl border px-4 py-3 text-sm shadow-[0_20px_40px_rgba(15,23,42,0.12)]" :class="toast.tone === 'success' ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : toast.tone === 'error' ? 'border-rose-200 bg-rose-50 text-rose-700' : 'border-slate-200 bg-white text-slate-700'">
          <div class="flex items-start justify-between gap-3">
            <p class="leading-6">{{ toast.message }}</p>
            <button type="button" class="text-slate-400 transition hover:text-slate-700" @click="dismissToast(toast.id)">
              <X class="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </transition>
  </main>
</template>

<style scoped>
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 180ms ease;
}

.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}
</style>
