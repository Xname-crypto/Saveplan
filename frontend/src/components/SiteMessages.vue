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
  <div
    v-if="!route.path.startsWith('/admin') && (banners.length || globalPopups.length || directPopups.length)"
    class="pointer-events-none fixed inset-x-0 top-[4.75rem] z-40 px-4 lg:top-[5.35rem]"
  >
    <div class="mx-auto flex w-full max-w-5xl flex-col gap-3">
      <section
        v-for="banner in banners"
        :key="banner.id"
        class="pointer-events-auto flex items-start gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-900 shadow-[0_12px_35px_rgba(15,23,42,0.08)]"
      >
        <div class="mt-0.5 flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-slate-700">
          <BellRing class="h-4 w-4" />
        </div>
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <p class="text-sm font-semibold">{{ banner.title }}</p>
            <span class="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-500">全站公告</span>
          </div>
          <p class="mt-1 whitespace-pre-wrap text-sm leading-6 text-slate-600">{{ banner.content }}</p>
        </div>
        <button
          type="button"
          class="inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"
          @click="dismiss(banner.id)"
        >
          <X class="h-4 w-4" />
        </button>
      </section>
    </div>
  </div>

  <transition name="fade">
    <div
      v-if="globalPopups.length || directPopups.length"
      class="fixed inset-0 z-[70] flex items-start justify-center overflow-y-auto bg-slate-950/40 px-4 py-6 pt-[5.75rem] backdrop-blur-sm sm:items-center sm:pt-6"
    >
      <div class="grid w-full max-w-5xl gap-4 lg:grid-cols-2">
        <section
          v-for="popup in globalPopups"
          :key="popup.id"
          class="pointer-events-auto rounded-2xl border border-slate-200 bg-white p-6 text-slate-900 shadow-[0_30px_80px_rgba(15,23,42,0.18)]"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex items-start gap-3">
              <div class="mt-0.5 flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-700">
                <Megaphone class="h-5 w-5" />
              </div>
              <div>
                <p class="text-lg font-semibold">{{ popup.title }}</p>
                <p class="mt-1 text-sm text-slate-500">全站弹窗</p>
              </div>
            </div>
            <button
              type="button"
              class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"
              @click="dismiss(popup.id)"
            >
              <X class="h-4 w-4" />
            </button>
          </div>

          <p class="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate-600">
            {{ popup.content }}
          </p>

          <div class="mt-6 flex justify-end">
            <button
              type="button"
              class="inline-flex items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800"
              @click="dismiss(popup.id)"
            >
              我知道了
            </button>
          </div>
        </section>

        <section
          v-for="popup in directPopups"
          :key="popup.id"
          class="pointer-events-auto rounded-2xl border border-slate-200 bg-white p-6 text-slate-900 shadow-[0_30px_80px_rgba(15,23,42,0.18)]"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex items-start gap-3">
              <div class="mt-0.5 flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-700">
                <Megaphone class="h-5 w-5" />
              </div>
              <div>
                <p class="text-lg font-semibold">{{ popup.title }}</p>
                <p class="mt-1 text-sm text-slate-500">定向弹窗</p>
              </div>
            </div>
            <button
              type="button"
              class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"
              @click="dismiss(popup.id)"
            >
              <X class="h-4 w-4" />
            </button>
          </div>

          <p class="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate-600">
            {{ popup.content }}
          </p>

          <div class="mt-6 flex justify-end">
            <button
              type="button"
              class="inline-flex items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800"
              @click="dismiss(popup.id)"
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
