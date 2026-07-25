<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue"
import {
  ChevronLeft,
  ChevronRight,
  Download,
  Eye,
  FileText,
  Search,
  SlidersHorizontal,
  Trash2,
} from "lucide-vue-next"
import AppFooter from "@/components/AppFooter.vue"
import CinematicNav from "@/components/CinematicNav.vue"
import { useRouter } from "@/router"
import {
  AUTH_SESSION_CHANGE_EVENT,
  authClient,
  getAuthAvatarInitial,
  getAuthAvatarSource,
  getAuthErrorMessage,
  getStoredAuthUser,
  isAuthSessionInvalid,
  type AuthUser,
} from "@/services/authClient"
import {
  conversionClient,
  getConversionErrorMessage,
  isConversionAuthError,
  type ConversionSummary,
} from "@/services/conversionClient"

type StatusTone = "success" | "review" | "processing" | "attention"
type StatusFilter = "all" | "completed" | "review" | "processing" | "attention"

interface MaterialItem {
  id: string
  name: string
  date: string
  rawDate: string
  type: string
  status: string
  statusTone: StatusTone
  questionCount: number
  issueCount: number
  creditsSpent: number
  creditsAfter: number
  disabled: boolean
}

const pageSize = 4
const router = useRouter()
const materials = ref<MaterialItem[]>([])
const query = ref("")
const statusFilter = ref<StatusFilter>("all")
const isFilterOpen = ref(false)
const currentPage = ref(1)
const selectedMaterial = ref<MaterialItem | null>(null)
const currentUser = ref<AuthUser | null>(getStoredAuthUser())
const avatarLoadFailed = ref(false)
const isLoadingProfile = ref(true)
const isLoadingHistory = ref(false)
const deletingMaterialId = ref<string | null>(null)
const profileError = ref("")
const historyError = ref("")

const filterOptions: Array<{ label: string; value: StatusFilter }> = [
  { label: "全部记录", value: "all" },
  { label: "已完成", value: "completed" },
  { label: "待校对", value: "review" },
  { label: "处理中", value: "processing" },
  { label: "需处理", value: "attention" },
]

const filteredMaterials = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  const status = statusFilter.value

  return materials.value.filter((item) => {
    const matchesKeyword = !keyword || item.name.toLowerCase().includes(keyword)
    const matchesStatus =
      status === "all" ||
      (status === "completed" && item.statusTone === "success") ||
      (status === "review" && item.statusTone === "review") ||
      (status === "processing" && item.statusTone === "processing") ||
      (status === "attention" && item.statusTone === "attention")

    return matchesKeyword && matchesStatus
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredMaterials.value.length / pageSize)))
const paginatedMaterials = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredMaterials.value.slice(start, start + pageSize)
})
const visiblePages = computed(() => Array.from({ length: totalPages.value }, (_, index) => index + 1))
const profileName = computed(() => currentUser.value?.username?.trim() || currentUser.value?.email || "用户")
const profileRole = computed(() => currentUser.value?.job?.trim() || "未填写身份")
const profileSummary = computed(() => currentUser.value?.bio?.trim() || `${profileRole.value} · Save Your Finals`)
const profileCreatedAt = computed(() => formatDate(currentUser.value?.created_at))
const profileTags = computed(() => {
  const interests = currentUser.value?.interests?.map((item) => item.trim()).filter(Boolean) ?? []
  return interests.length ? interests : ["暂无兴趣标签"]
})
const profileCredits = computed(() => {
  const userWithCredits = currentUser.value as (AuthUser & { credits?: number; points?: number }) | null
  const credits = userWithCredits?.credits ?? userWithCredits?.points ?? 0

  return formatNumber(credits)
})
const usedCredits = computed(() =>
  formatNumber(materials.value.reduce((total, item) => total + item.creditsSpent, 0)),
)
const avatarSrc = computed(() => (avatarLoadFailed.value ? "" : getAuthAvatarSource(currentUser.value)))
const avatarInitial = computed(() => getAuthAvatarInitial(currentUser.value))

watch([query, statusFilter], () => {
  currentPage.value = 1
})

watch(totalPages, (pageCount) => {
  if (currentPage.value > pageCount) {
    currentPage.value = pageCount
  }
})

function formatNumber(value: number) {
  return new Intl.NumberFormat("zh-CN").format(value)
}

function formatDate(value?: string | null) {
  if (!value) return "暂无记录"

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function getFileType(filename: string) {
  const extension = filename.split(".").pop()?.toLowerCase()

  if (!extension || extension === filename.toLowerCase()) return "文本粘贴"
  if (extension === "pdf") return "PDF 文件"
  if (extension === "doc" || extension === "docx") return "Word 文件"
  if (extension === "txt") return "TXT 文件"
  return `${extension.toUpperCase()} 文件`
}

function getStatusMeta(status: string): { label: string; tone: StatusTone; disabled: boolean } {
  if (status === "reviewed" || status === "exported") {
    return { label: status === "exported" ? "已导出" : "已校对", tone: "success", disabled: false }
  }

  if (status === "needs_review") {
    return { label: "待校对", tone: "review", disabled: false }
  }

  if (status === "ocr_running") {
    return { label: "识别中", tone: "processing", disabled: true }
  }

  return { label: "需处理", tone: "attention", disabled: false }
}

function toMaterialItem(summary: ConversionSummary): MaterialItem {
  const statusMeta = getStatusMeta(summary.status)

  return {
    id: summary.id,
    name: summary.filename || "未命名试卷",
    date: formatDate(summary.created_at),
    rawDate: summary.created_at,
    type: getFileType(summary.filename || ""),
    status: statusMeta.label,
    statusTone: statusMeta.tone,
    questionCount: summary.question_count,
    issueCount: summary.issue_count,
    creditsSpent: summary.credits_spent,
    creditsAfter: summary.credits_after,
    disabled: statusMeta.disabled,
  }
}

function updateCurrentUser(user: AuthUser | null) {
  currentUser.value = user
  avatarLoadFailed.value = false
}

function redirectToLogin() {
  void router.push("/login?redirect=/profile")
}

function handleAuthSessionChange(event: Event) {
  const user = (event as CustomEvent<AuthUser | null>).detail
  updateCurrentUser(user)

  if (!user) {
    redirectToLogin()
  }
}

function handleAvatarError() {
  avatarLoadFailed.value = true
}

async function loadProfile() {
  isLoadingProfile.value = true
  profileError.value = ""

  try {
    const user = await authClient.me()
    updateCurrentUser(user)
  } catch (error) {
    profileError.value = getAuthErrorMessage(error)
    if (isAuthSessionInvalid(error)) {
      authClient.logout()
      redirectToLogin()
    }
  } finally {
    isLoadingProfile.value = false
  }
}

async function loadHistory() {
  isLoadingHistory.value = true
  historyError.value = ""

  try {
    const summaries = await conversionClient.list()
    materials.value = summaries.map(toMaterialItem)
  } catch (error) {
    historyError.value = getConversionErrorMessage(error)
    if (isConversionAuthError(error)) {
      authClient.logout()
      redirectToLogin()
    }
  } finally {
    isLoadingHistory.value = false
  }
}

async function initializeProfile() {
  await loadProfile()

  if (currentUser.value) {
    await loadHistory()
  }
}

function selectFilter(value: StatusFilter) {
  statusFilter.value = value
  isFilterOpen.value = false
}

function goToPage(page: number) {
  currentPage.value = Math.min(Math.max(page, 1), totalPages.value)
}

function openPreview(item: MaterialItem) {
  selectedMaterial.value = item
}

function closePreview() {
  selectedMaterial.value = null
}

function downloadMaterial(item: MaterialItem) {
  const content = [
    `资料名称：${item.name}`,
    `资料类型：${item.type}`,
    `上传时间：${item.date}`,
    `转换状态：${item.status}`,
    `识别题目：${item.questionCount} 题`,
    `待处理问题：${item.issueCount} 项`,
    `本次扣除：${item.creditsSpent} 积分`,
    `剩余积分：${item.creditsAfter} 积分`,
  ].join("\n")
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")

  link.href = url
  link.download = `${item.name}-转换记录.txt`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

async function deleteMaterial(item: MaterialItem) {
  const confirmed = window.confirm(`确定删除“${item.name}”这条转换历史吗？删除后无法恢复。`)
  if (!confirmed) return

  deletingMaterialId.value = item.id
  historyError.value = ""

  try {
    await conversionClient.delete(item.id)
    materials.value = materials.value.filter((material) => material.id !== item.id)

    if (selectedMaterial.value?.id === item.id) {
      closePreview()
    }
  } catch (error) {
    historyError.value = getConversionErrorMessage(error)
  } finally {
    deletingMaterialId.value = null
  }
}

onMounted(() => {
  window.addEventListener(AUTH_SESSION_CHANGE_EVENT, handleAuthSessionChange)
  void initializeProfile()
})

onBeforeUnmount(() => {
  window.removeEventListener(AUTH_SESSION_CHANGE_EVENT, handleAuthSessionChange)
})
</script>

<template>
  <div class="stitch-page profile-page">
    <CinematicNav />
    <div class="stitch-noise" />

    <main class="profile-shell">
      <header class="profile-topbar">
        <div>
          <p class="stitch-eyebrow">PRISMA SPACE</p>
          <h1>个人中心</h1>
          <p v-if="currentUser">欢迎回来，{{ profileName }}。这里展示你的账户资料、上传记录和积分消耗。</p>
          <p v-else-if="isLoadingProfile">正在读取账户信息...</p>
          <p v-else>{{ profileError || "请先登录后查看个人中心。" }}</p>
        </div>
      </header>

      <section v-if="currentUser" class="profile-card stitch-reveal">
        <div class="profile-avatar profile-card__avatar" aria-label="用户资料头像">
          <img v-if="avatarSrc" :src="avatarSrc" alt="用户资料头像" @error="handleAvatarError" />
          <span v-else>{{ avatarInitial }}</span>
        </div>
        <div>
          <h2>{{ profileName }}</h2>
          <p>{{ profileSummary }}</p>
          <div>
            <span>{{ currentUser.email }}</span>
            <span>{{ profileRole }}</span>
            <span>注册于 {{ profileCreatedAt }}</span>
            <span v-for="tag in profileTags" :key="tag">{{ tag }}</span>
          </div>
        </div>
        <aside>
          <p>可用积分</p>
          <strong>{{ profileCredits }}</strong>
          <span>已消耗 {{ usedCredits }} 积分</span>
        </aside>
      </section>

      <section v-if="currentUser" class="history-panel stitch-reveal stitch-delay-1">
        <div class="history-panel__header">
          <div class="history-panel__title">
            <h2>历史记录</h2>
            <p>{{ materials.length }} 条转换记录，包含上传文件、扣除积分和剩余积分。</p>
          </div>
          <div class="history-tools">
            <label>
              <Search :size="18" />
              <input v-model="query" type="search" placeholder="搜索文件名..." />
            </label>
            <div class="history-filter">
              <button
                :class="['history-filter__trigger', { 'is-active': statusFilter !== 'all' }]"
                type="button"
                :aria-expanded="isFilterOpen"
                aria-haspopup="menu"
                @click="isFilterOpen = !isFilterOpen"
              >
                <SlidersHorizontal :size="18" />筛选
              </button>
              <div v-if="isFilterOpen" class="history-filter__menu" role="menu">
                <button
                  v-for="option in filterOptions"
                  :key="option.value"
                  type="button"
                  :class="{ 'is-active': statusFilter === option.value }"
                  role="menuitemradio"
                  :aria-checked="statusFilter === option.value"
                  @click="selectFilter(option.value)"
                >
                  {{ option.label }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="material-list">
          <article v-for="item in paginatedMaterials" :key="item.id" class="material-row">
            <div class="material-row__icon"><FileText :size="22" /></div>
            <div class="material-row__meta">
              <h3>{{ item.name }}</h3>
              <p>{{ item.type }} · {{ item.date }} · {{ item.questionCount }} 题 · {{ item.issueCount }} 项待处理</p>
            </div>
            <div class="material-row__credits">
              <span>扣除 <strong>-{{ item.creditsSpent }}</strong></span>
              <span>剩余 <strong>{{ item.creditsAfter }}</strong></span>
            </div>
            <span :class="['material-row__status', `is-${item.statusTone}`]">{{ item.status }}</span>
            <div class="material-row__actions">
              <button type="button" title="查看" aria-label="查看" @click="openPreview(item)">
                <Eye :size="18" />
              </button>
              <button type="button" title="导出摘要" aria-label="导出摘要" @click="downloadMaterial(item)">
                <Download :size="18" />
              </button>
              <button
                type="button"
                title="删除"
                aria-label="删除"
                :disabled="deletingMaterialId === item.id"
                @click="deleteMaterial(item)"
              >
                <Trash2 :size="18" />
              </button>
            </div>
          </article>
          <div v-if="isLoadingHistory" class="history-empty">
            <strong>正在读取转换记录</strong>
            <span>稍等一下，正在同步你的上传文件和积分变化。</span>
          </div>
          <div v-else-if="historyError" class="history-empty history-empty--error">
            <strong>历史记录读取失败</strong>
            <span>{{ historyError }}</span>
          </div>
          <div v-else-if="paginatedMaterials.length === 0" class="history-empty">
            <strong>还没有转换记录</strong>
            <span>上传文件或粘贴试卷文本后，这里会显示扣除积分和剩余积分。</span>
          </div>
        </div>

        <div v-if="totalPages > 1" class="profile-pagination">
          <button type="button" :disabled="currentPage === 1" @click="goToPage(currentPage - 1)">
            <ChevronLeft :size="18" />
          </button>
          <button
            v-for="page in visiblePages"
            :key="page"
            :class="{ 'is-active': currentPage === page }"
            type="button"
            @click="goToPage(page)"
          >
            {{ page }}
          </button>
          <button type="button" :disabled="currentPage === totalPages" @click="goToPage(currentPage + 1)">
            <ChevronRight :size="18" />
          </button>
        </div>
      </section>
    </main>

    <div v-if="selectedMaterial" class="history-modal" role="dialog" aria-modal="true" @click.self="closePreview">
      <article class="history-modal__card">
        <header>
          <span>{{ selectedMaterial.type }}</span>
          <button type="button" aria-label="关闭详情" @click="closePreview">×</button>
        </header>
        <h2>{{ selectedMaterial.name }}</h2>
        <dl>
          <div>
            <dt>上传时间</dt>
            <dd>{{ selectedMaterial.date }}</dd>
          </div>
          <div>
            <dt>转换状态</dt>
            <dd>{{ selectedMaterial.status }}</dd>
          </div>
          <div>
            <dt>识别题目</dt>
            <dd>{{ selectedMaterial.questionCount }} 题</dd>
          </div>
          <div>
            <dt>本次扣除</dt>
            <dd>{{ selectedMaterial.creditsSpent }} 积分</dd>
          </div>
          <div>
            <dt>剩余积分</dt>
            <dd>{{ selectedMaterial.creditsAfter }} 积分</dd>
          </div>
        </dl>
        <button type="button" @click="downloadMaterial(selectedMaterial)">导出记录摘要</button>
      </article>
    </div>
    <AppFooter />
  </div>
</template>
