<script setup lang="ts">
import { computed, ref } from "vue"
import AuthLayout from "@/components/AuthLayout.vue"
import { authClient, getAuthErrorMessage } from "@/services/authClient"
import { Loader2 } from "lucide-vue-next"

const forgotPasswordVideo = "/video/fp_v3.mp4?v=auth-balanced-2"
const authPoster = "/video/auth-poster.jpeg"

const email = ref("")
const loading = ref(false)
const errorMsg = ref("")
const successMsg = ref("")
const resetUrl = ref("")

const resetPath = computed(() => {
  if (!resetUrl.value) return ""

  try {
    const url = new URL(resetUrl.value)
    return `${url.pathname}${url.search}${url.hash}`
  } catch (_error) {
    return resetUrl.value
  }
})

const handleReset = async () => {
  const normalizedEmail = email.value.trim()

  if (!normalizedEmail) {
    errorMsg.value = "请输入您的电子邮箱。"
    return
  }

  try {
    loading.value = true
    errorMsg.value = ""
    successMsg.value = ""
    resetUrl.value = ""

    const response = await authClient.forgotPassword(normalizedEmail)
    successMsg.value = response.message
    resetUrl.value = response.reset_url || ""
    email.value = ""
  } catch (error) {
    errorMsg.value = getAuthErrorMessage(error)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthLayout :video-src="forgotPasswordVideo" :poster-src="authPoster" content-offset-class="md:-translate-y-8">
    <template #title>重置访问权限</template>
    <template #subtitle>输入邮箱，接收密码重置链接。</template>

    <form class="space-y-5" @submit.prevent="handleReset">
      <div v-if="errorMsg" class="auth-alert auth-alert--error p-3 text-sm">
        {{ errorMsg }}
      </div>
      <div v-if="successMsg" class="auth-alert auth-alert--success space-y-3 p-3 text-sm">
        <p>{{ successMsg }}</p>
        <router-link
          v-if="resetPath"
          :to="resetPath"
          class="auth-link inline-flex font-semibold"
        >
          开发环境直接打开重置链接
        </router-link>
      </div>

      <div class="space-y-1">
        <label for="email" class="auth-label ml-1 text-xs font-semibold uppercase">邮箱地址</label>
        <input
          id="email"
          v-model="email"
          name="email"
          type="email"
          autocomplete="email"
          placeholder="请输入邮箱"
          class="auth-input px-4 py-3"
          required
        />
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="auth-button mt-4 px-4 py-3"
      >
        <Loader2 v-if="loading" class="mr-2 h-5 w-5 animate-spin" />
        {{ loading ? "SENDING..." : "SEND RESET LINK" }}
      </button>

      <div class="mt-6 text-center text-[0.7rem] text-[rgba(226,218,194,0.34)]">
        <router-link to="/login" class="auth-link inline-flex items-center font-semibold">
          返回登录
        </router-link>
      </div>
    </form>
  </AuthLayout>
</template>
