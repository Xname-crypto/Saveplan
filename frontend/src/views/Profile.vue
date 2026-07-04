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

type MaterialStatus = "已完成" | "处理中"
type StatusFilter = "all" | MaterialStatus

interface MaterialItem {
  id: number
  name: string
  date: string
  size: string
  status: MaterialStatus
  disabled: boolean
  type: string
}

const pageSize = 3
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
const profileError = ref("")

const filterOptions: Array<{ label: string; value: StatusFilter }> = [
  { label: "全部资料", value: "all" },
  { label: "已完成", value: "已完成" },
  { label: "处理中", value: "处理中" },
]

const filteredMaterials = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  const status = statusFilter.value

  return materials.value.filter((item) => {
    const matchesKeyword = !keyword || item.name.toLowerCase().includes(keyword)
    const matchesStatus = status === "all" || item.status === status

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
const profileCreatedAt = computed(() => {
  const createdAt = currentUser.value?.created_at
  if (!createdAt) return "暂无记录"

  const date = new Date(createdAt)
  if (Number.isNaN(date.getTime())) return createdAt

  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  })
})
const profileTags = computed(() => {
  const interests = currentUser.value?.interests?.map((item) => item.trim()).filter(Boolean) ?? []
  return interests.length ? interests : ["暂无兴趣标签"]
})
const profileCredits = computed(() => {
  const userWithCredits = currentUser.value as (AuthUser & { credits?: number; points?: number }) | null
  const credits = userWithCredits?.credits ?? userWithCredits?.points ?? 0

  return new Intl.NumberFormat("zh-CN").format(credits)
})
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

function selectFilter(value: StatusFilter) {
  statusFilter.value = value
  isFilterOpen.value = false
}

function goToPage(page: number) {
  currentPage.value = Math.min(Math.max(page, 1), totalPages.value)
}

function openPreview(item: MaterialItem) {
  if (item.disabled) return
  selectedMaterial.value = item
}

function closePreview() {
  selectedMaterial.value = null
}

function downloadMaterial(item: MaterialItem) {
  if (item.disabled) return

  const content = [
    `资料名称：${item.name}`,
    `文件类型：${item.type}`,
    `上传日期：${item.date}`,
    `文件大小：${item.size}`,
    `转换状态：${item.status}`,
  ].join("\n")
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")

  link.href = url
  link.download = `${item.name}.txt`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

function deleteMaterial(item: MaterialItem) {
  const confirmed = window.confirm(`确定删除「${item.name}」吗？`)
  if (!confirmed) return

  materials.value = materials.value.filter((material) => material.id !== item.id)

  if (selectedMaterial.value?.id === item.id) {
    closePreview()
  }
}

onMounted(() => {
  window.addEventListener(AUTH_SESSION_CHANGE_EVENT, handleAuthSessionChange)
  void loadProfile()
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
          <p v-if="currentUser">欢迎回来，{{ profileName }}。这里展示你的真实账户资料和转换记录。</p>
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
            <span v-for="tag in profileTags" :key="tag">{{ tag }}</span>
          </div>
        </div>
        <aside>
          <p>可用积分</p>
          <strong>{{ profileCredits }}</strong>
        </aside>
      </section>

      <section v-if="currentUser" class="history-panel stitch-reveal stitch-delay-1">
        <div class="history-panel__header">
          <h2>历史记录</h2>
          <div class="history-tools">
            <label>
              <Search :size="18" />
              <input v-model="query" type="search" placeholder="搜索资料..." />
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
              <p>Uploaded: {{ item.date }} · Size: {{ item.size }}</p>
            </div>
            <span :class="{ 'is-processing': item.status === '处理中' }">{{ item.status }}</span>
            <div class="material-row__actions">
              <button type="button" title="查看" aria-label="查看" :disabled="item.disabled" @click="openPreview(item)">
                <Eye :size="18" />
              </button>
              <button type="button" title="导出" aria-label="导出" :disabled="item.disabled" @click="downloadMaterial(item)">
                <Download :size="18" />
              </button>
              <button type="button" title="删除" aria-label="删除" @click="deleteMaterial(item)">
                <Trash2 :size="18" />
              </button>
            </div>
          </article>
          <div v-if="paginatedMaterials.length === 0" class="history-empty">
            <strong>暂无真实历史记录</strong>
            <span>接入真实转换记录接口后，这里会显示当前账户的资料。</span>
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
            <dt>上传日期</dt>
            <dd>{{ selectedMaterial.date }}</dd>
          </div>
          <div>
            <dt>文件大小</dt>
            <dd>{{ selectedMaterial.size }}</dd>
          </div>
          <div>
            <dt>转换状态</dt>
            <dd>{{ selectedMaterial.status }}</dd>
          </div>
        </dl>
        <button type="button" @click="downloadMaterial(selectedMaterial)">导出资料</button>
      </article>
    </div>
    <AppFooter />
  </div>
</template>
