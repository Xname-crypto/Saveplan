<script setup lang="ts">
import { computed, ref } from "vue"
import { ShieldCheck, LoaderCircle, ArrowLeft } from "lucide-vue-next"
import { adminClient, getAdminErrorMessage } from "@/services/adminClient"
import { useRouter } from "@/router"

const router = useRouter()
const email = ref("")
const password = ref("")
const loading = ref(false)
const error = ref("")

const canSubmit = computed(() => email.value.trim().length > 2 && password.value.length > 0 && !loading.value)

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
  <main class="min-h-screen bg-[#f4f5f7] text-slate-900">
    <div class="mx-auto grid min-h-screen max-w-6xl gap-10 px-6 py-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
      <section class="space-y-6">
        <button
          type="button"
          class="inline-flex items-center gap-2 text-sm font-medium text-slate-500 transition hover:text-slate-900"
          @click="router.replace('/')"
        >
          <ArrowLeft class="h-4 w-4" />
          返回前台
        </button>

        <div class="max-w-2xl space-y-4">
          <div class="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600 shadow-sm">
            <ShieldCheck class="h-3.5 w-3.5" />
            管理员入口
          </div>
          <h1 class="text-4xl font-semibold tracking-tight text-slate-900 lg:text-5xl">Saveplan 管理后台</h1>
          <p class="max-w-xl text-base leading-8 text-slate-600">
            用于管理用户、调整积分、发放兑换码、发布公告和弹窗消息，并保留完整审计记录。
          </p>
        </div>

        <div class="grid gap-3 sm:grid-cols-3">
          <article class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <p class="text-sm text-slate-500">权限控制</p>
            <p class="mt-2 text-lg font-semibold">角色分级</p>
          </article>
          <article class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <p class="text-sm text-slate-500">审计记录</p>
            <p class="mt-2 text-lg font-semibold">可追溯</p>
          </article>
          <article class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <p class="text-sm text-slate-500">发布内容</p>
            <p class="mt-2 text-lg font-semibold">可回滚</p>
          </article>
        </div>
      </section>

      <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
        <form class="space-y-5" @submit.prevent="handleLogin">
          <div>
            <p class="text-sm font-medium text-slate-500">管理员登录</p>
            <h2 class="mt-1 text-2xl font-semibold text-slate-900">进入控制台</h2>
          </div>

          <label class="block">
            <span class="mb-2 block text-sm font-medium text-slate-600">邮箱</span>
            <input
              v-model="email"
              type="email"
              autocomplete="username"
              class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-slate-400 focus:bg-white"
              placeholder="admin@example.com"
            />
          </label>

          <label class="block">
            <span class="mb-2 block text-sm font-medium text-slate-600">密码</span>
            <input
              v-model="password"
              type="password"
              autocomplete="current-password"
              class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-slate-400 focus:bg-white"
              placeholder="请输入管理员密码"
            />
          </label>

          <div v-if="error" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
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
