<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue"
import { BellRing, Megaphone, X } from "lucide-vue-next"
import { useRoute } from "@/router"
import { messageClient, type BroadcastMessage } from "@/services/messageClient"
import { getStoredAuthUser } from "@/services/authClient"

const route = useRoute()
const globalMessages = ref<BroadcastMessage[]>([])
const userMessages = ref<BroadcastMessage[]>([])
const loading = ref(false)
const error = ref("")
const dismissedKey = "saveplan.broadcast.dismissed"
const dismissedIds = ref<Set<string>>(new Set())
const activeMessageId = ref<string | null>(null)
const refreshIntervalMs = 15000
let refreshTimer: number | undefined

function readDismissedIds() {
  try {
    const raw = localStorage.getItem(dismissedKey)
    if (!raw) return new Set<string>()
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return new Set<string>()
    return new Set(parsed.filter((item) => typeof item === "string"))
  } catch (_error) {
    return new Set<string>()
  }
}

function persistDismissedIds() {
  localStorage.setItem(dismissedKey, JSON.stringify(Array.from(dismissedIds.value)))
}

async function loadMessages(options: { silent?: boolean } = {}) {
  if (route.path.startsWith("/admin")) {
    globalMessages.value = []
    userMessages.value = []
    return
  }

  if (!options.silent) {
    loading.value = true
  }
  error.value = ""
  try {
    const [globalResult, userResult] = await Promise.all([
      messageClient.listActiveBroadcasts(),
      getStoredAuthUser() ? messageClient.listMyMessages() : Promise.resolve([] as BroadcastMessage[]),
    ])
    dismissedIds.value = readDismissedIds()
    globalMessages.value = globalResult.filter((item) => !dismissedIds.value.has(item.id))
    userMessages.value = userResult.filter((item) => !dismissedIds.value.has(item.id))
  } catch (loadError) {
    error.value = loadError instanceof Error ? loadError.message : "消息加载失败"
    globalMessages.value = []
    userMessages.value = []
  } finally {
    if (!options.silent) {
      loading.value = false
    }
  }
}

function dismiss(messageId: string) {
  dismissedIds.value.add(messageId)
  persistDismissedIds()
  globalMessages.value = globalMessages.value.filter((message) => message.id !== messageId)
  userMessages.value = userMessages.value.filter((message) => message.id !== messageId)
  if (activeMessageId.value === messageId) {
    activeMessageId.value = modalMessages.value[0]?.id ?? null
  }
}

const banners = computed(() =>
  globalMessages.value.filter((item) => item.channel === "announcement" && item.scope === "global"),
)
const globalPopups = computed(() =>
  globalMessages.value.filter((item) => item.channel === "popup" && item.scope === "global"),
)
const directPopups = computed(() =>
  userMessages.value.filter((item) => item.channel === "popup" && item.scope === "user"),
)
const modalMessages = computed(() => [
  ...banners.value,
  ...globalPopups.value,
  ...directPopups.value,
])
const activeMessage = computed(() =>
  modalMessages.value.find((message) => message.id === activeMessageId.value) ?? modalMessages.value[0] ?? null,
)

function selectMessage(messageId: string) {
  activeMessageId.value = messageId
}

function getMessageIcon(message: BroadcastMessage) {
  return message.channel === "announcement" ? BellRing : Megaphone
}

function getMessageLabel(message: BroadcastMessage) {
  if (message.channel === "announcement") return "全站公告"
  return message.scope === "user" ? "定向弹窗" : "全站弹窗"
}

watch(
  () => route.path,
  () => {
    void loadMessages()
  },
)

watch(
  modalMessages,
  (messages) => {
    if (!messages.length) {
      activeMessageId.value = null
      return
    }
    if (!activeMessageId.value || !messages.some((message) => message.id === activeMessageId.value)) {
      activeMessageId.value = messages[0].id
    }
  },
  { immediate: true },
)

function handleVisibilityChange() {
  if (document.visibilityState === "visible") {
    void loadMessages({ silent: true })
  }
}

onMounted(() => {
  dismissedIds.value = readDismissedIds()
  void loadMessages()
  refreshTimer = window.setInterval(() => {
    void loadMessages({ silent: true })
  }, refreshIntervalMs)
  document.addEventListener("visibilitychange", handleVisibilityChange)
})

onBeforeUnmount(() => {
  if (refreshTimer !== undefined) {
    window.clearInterval(refreshTimer)
  }
  document.removeEventListener("visibilitychange", handleVisibilityChange)
})
</script>

<template>
  <transition name="fade">
    <div
      v-if="!route.path.startsWith('/admin') && modalMessages.length && activeMessage"
      class="fixed inset-0 z-[90] flex items-center justify-center overflow-y-auto bg-slate-950/48 px-4 py-8 backdrop-blur-sm"
    >
      <section class="pointer-events-auto grid w-full max-w-4xl overflow-hidden rounded-3xl border border-slate-200 bg-white text-slate-900 shadow-[0_34px_90px_rgba(15,23,42,0.24)] lg:grid-cols-[230px_minmax(0,1fr)]">
        <aside class="border-b border-slate-200 bg-slate-50/80 p-3 lg:border-b-0 lg:border-r">
          <div class="flex items-center justify-between px-2 py-2">
            <p class="text-sm font-medium text-slate-900">消息</p>
            <span class="text-xs text-slate-400">{{ modalMessages.length }} 条</span>
          </div>
          <div class="mt-2 flex gap-2 overflow-x-auto pb-1 lg:block lg:max-h-[28rem] lg:space-y-1 lg:overflow-y-auto lg:pb-0">
            <button
              v-for="(message, index) in modalMessages"
              :key="message.id"
              type="button"
              class="flex min-w-44 items-center gap-3 rounded-xl border px-3 py-2.5 text-left transition lg:w-full lg:min-w-0"
              :class="activeMessage.id === message.id ? 'border-slate-900 bg-white text-slate-950 shadow-sm' : 'border-transparent text-slate-500 hover:bg-white hover:text-slate-900'"
              @click="selectMessage(message.id)"
            >
              <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white text-xs font-semibold text-slate-500 ring-1 ring-slate-200">
                {{ index + 1 }}
              </span>
              <span class="min-w-0">
                <span class="block truncate text-sm font-medium">{{ message.title }}</span>
                <span class="mt-0.5 block text-xs text-slate-400">{{ getMessageLabel(message) }}</span>
              </span>
            </button>
          </div>
        </aside>

        <div class="max-h-[calc(100vh-4rem)] min-h-[22rem] overflow-y-auto p-7 sm:p-8">
          <div class="flex items-start justify-between gap-4">
            <div class="flex min-w-0 items-start gap-3">
              <div class="mt-0.5 flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-700">
                <component :is="getMessageIcon(activeMessage)" class="h-5 w-5" />
              </div>
              <div class="min-w-0">
                <p class="text-xl font-semibold tracking-tight text-slate-950 sm:text-2xl">{{ activeMessage.title }}</p>
                <p class="mt-1 text-sm text-slate-500">{{ getMessageLabel(activeMessage) }}</p>
              </div>
            </div>
            <button
              type="button"
              class="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"
              @click="dismiss(activeMessage.id)"
            >
              <X class="h-4 w-4" />
            </button>
          </div>

          <p class="mt-7 whitespace-pre-wrap text-base leading-8 text-slate-600">
            {{ activeMessage.content }}
          </p>

          <div class="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p class="text-xs text-slate-400">第 {{ modalMessages.findIndex((message) => message.id === activeMessage?.id) + 1 }} / {{ modalMessages.length }} 条</p>
            <button
              type="button"
              class="inline-flex min-h-11 items-center rounded-full bg-slate-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800"
              @click="dismiss(activeMessage.id)"
            >
              我知道了
            </button>
          </div>
        </div>
      </section>
    </div>
  </transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition:
    opacity 180ms ease,
    transform 180ms ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
