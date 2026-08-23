<script setup lang="ts">
import { computed, ref } from "vue"
import { ArrowLeft, LoaderCircle, ShieldCheck } from "lucide-vue-next"
import { adminClient, getAdminErrorMessage } from "@/services/adminClient"
import { useRouter } from "@/router"

const router = useRouter()
const email = ref("")
const password = ref("")
const loading = ref(false)
const error = ref("")

const canSubmit = computed(
  () => email.value.trim().length > 2 && password.value.length > 0 && !loading.value,
)

async function handleLogin() {
  if (!canSubmit.value) return

  loading.value = true
  error.value = ""
  try {
    await adminClient.login(email.value.trim(), password.value)
    await router.replace("/admin")
  } catch (loginError) {
    error.value = getAdminErrorMessage(loginError)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="min-h-screen bg-[#f5f6f8] px-6 py-8 text-slate-900">
    <div class="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-md flex-col justify-center">
      <button
        type="button"
        class="mb-6 inline-flex w-fit items-center gap-2 text-sm font-medium text-slate-500 transition hover:text-slate-900"
        @click="router.replace('/')"
      >
        <ArrowLeft class="h-4 w-4" />
        返回前台
      </button>

      <section class="rounded-3xl border border-slate-200 bg-white p-7 shadow-[0_24px_80px_rgba(15,23,42,0.08)] sm:p-8">
        <div class="flex items-center gap-2 text-xs font-medium text-slate-500">
          <ShieldCheck class="h-4 w-4" />
          管理员登录
        </div>

        <h1 class="mt-3 text-3xl font-semibold tracking-tight text-slate-900">进入控制台</h1>
        <p class="mt-2 text-sm leading-6 text-slate-500">仅用于管理员账号登录，不展示功能说明。</p>

        <form class="mt-7 space-y-4" @submit.prevent="handleLogin">
          <label class="block">
            <span class="mb-2 block text-sm font-medium text-slate-600">邮箱</span>
            <input
              v-model="email"
              type="email"
              autocomplete="username"
              placeholder="admin@example.com"
              class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-400 focus:bg-white"
            />
          </label>

          <label class="block">
            <span class="mb-2 block text-sm font-medium text-slate-600">密码</span>
            <input
              v-model="password"
              type="password"
              autocomplete="current-password"
              placeholder="请输入管理员密码"
              class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-400 focus:bg-white"
            />
          </label>

          <div
            v-if="error"
            class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm leading-6 text-rose-700"
          >
            {{ error }}
          </div>

          <button
            type="submit"
            :disabled="!canSubmit"
            class="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <LoaderCircle v-if="loading" class="h-4 w-4 animate-spin" />
            <span>{{ loading ? "登录中" : "登录后台" }}</span>
          </button>
        </form>
      </section>
    </div>
  </main>
</template>
