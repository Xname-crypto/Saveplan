<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue"
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

async function loadMessages() {
  if (route.path.startsWith("/admin")) {
    globalMessages.value = []
    userMessages.value = []
    return
  }

  loading.value = true
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
    loading.value = false
  }
}

function dismiss(messageId: string) {
  dismissedIds.value.add(messageId)
  persistDismissedIds()
  globalMessages.value = globalMessages.value.filter((message) => message.id !== messageId)
  userMessages.value = userMessages.value.filter((message) => message.id !== messageId)
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

onMounted(() => {
  dismissedIds.value = readDismissedIds()
  void loadMessages()
})
</script>

<template>
  <transition name="fade">
    <div
      v-if="!route.path.startsWith('/admin') && modalMessages.length"
      class="fixed inset-0 z-[90] flex items-center justify-center overflow-y-auto bg-slate-950/48 px-4 py-8 backdrop-blur-sm"
    >
      <div class="grid w-full max-w-2xl gap-4">
        <section
          v-for="message in modalMessages"
          :key="message.id"
          class="pointer-events-auto max-h-[calc(100vh-4rem)] min-h-[18rem] overflow-y-auto rounded-3xl border border-slate-200 bg-white p-7 text-slate-900 shadow-[0_34px_90px_rgba(15,23,42,0.24)] sm:p-8"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex items-start gap-3">
              <div class="mt-0.5 flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-700">
                <component :is="getMessageIcon(message)" class="h-5 w-5" />
              </div>
              <div class="min-w-0">
                <p class="text-xl font-semibold tracking-tight text-slate-950 sm:text-2xl">{{ message.title }}</p>
                <p class="mt-1 text-sm text-slate-500">{{ getMessageLabel(message) }}</p>
              </div>
            </div>
            <button
              type="button"
              class="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"
              @click="dismiss(message.id)"
            >
              <X class="h-4 w-4" />
            </button>
          </div>

          <p class="mt-7 whitespace-pre-wrap text-base leading-8 text-slate-600">
            {{ message.content }}
          </p>

          <div class="mt-8 flex justify-end">
            <button
              type="button"
              class="inline-flex min-h-11 items-center rounded-full bg-slate-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800"
              @click="dismiss(message.id)"
            >
              我知道了
            </button>
          </div>
        </section>
      </div>
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
