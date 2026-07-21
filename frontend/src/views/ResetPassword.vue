<script setup lang="ts">
import { computed, ref } from "vue"
import { useRoute, useRouter } from "@/router"
import AuthLayout from "@/components/AuthLayout.vue"
import AuthWaveInput from "@/components/AuthWaveInput.vue"
import { authClient, getAuthErrorMessage } from "@/services/authClient"
import { Loader2, Lock } from "lucide-vue-next"

const forgotPasswordVideo =
  "https://pub-4bd1febbb65843fbab89f795d612e480.r2.dev/%E3%80%90%E5%93%B2%E9%A3%8E%E5%A3%81%E7%BA%B8%E3%80%91%E4%B9%A6%E6%9C%AC-%E4%B9%A6%E6%A1%8C-%E4%BA%8C%E6%AC%A1%E5%85%83.mp4"
const authPoster = "/video/auth-poster.jpeg"

const route = useRoute()
const router = useRouter()
const password = ref("")
const confirmPassword = ref("")
const loading = ref(false)
const errorMsg = ref("")
const successMsg = ref("")

const resetToken = computed(() => {
  const queryToken = route.query.token
  return typeof queryToken === "string" ? queryToken : ""
})

const handleUpdatePassword = async () => {
  if (!resetToken.value) {
    errorMsg.value = "无效或过期的重置链接，请重新请求重置密码。"
    return
  }

  if (!password.value || !confirmPassword.value) {
    errorMsg.value = "请填写所有必填项。"
    return
  }

  if (password.value !== confirmPassword.value) {
    errorMsg.value = "两次输入的密码不一致。"
    return
  }

  if (password.value.length < 6) {
    errorMsg.value = "密码长度至少需要 6 位。"
    return
  }

  try {
    loading.value = true
    errorMsg.value = ""
    await authClient.resetPassword(resetToken.value, password.value)
    successMsg.value = "密码已成功修改，正在跳转到登录页..."

    window.setTimeout(() => {
      void router.push("/login")
    }, 1600)
  } catch (error) {
    errorMsg.value = getAuthErrorMessage(error)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthLayout
    :video-src="forgotPasswordVideo"
    :poster-src="authPoster"
    media-position="82% center"
    media-eyebrow="NEW PASSWORD"
    media-title="为账号设置新的安全凭证。"
    media-description="完成密码更新后，你可以继续回到专属复习工作区。"
    content-offset-class="md:-translate-y-8"
  >
    <template #title>New Password</template>
    <template #subtitle>为你的账号设置一个新密码。</template>

    <form class="space-y-5" @submit.prevent="handleUpdatePassword">
      <div v-if="!resetToken" class="auth-alert auth-alert--warning p-3 text-sm">
        当前链接缺少重置凭证，请先回到找回密码页面重新发送。
      </div>
      <div v-if="errorMsg" class="auth-alert auth-alert--error p-3 text-sm">
        {{ errorMsg }}
      </div>
      <div v-if="successMsg" class="auth-alert auth-alert--success p-3 text-sm">
        {{ successMsg }}
      </div>

      <AuthWaveInput
        id="password"
        v-model="password"
        name="password"
        type="password"
        autocomplete="new-password"
        label="请输入新密码"
        required
        :disabled="!!successMsg"
      >
        <template #leading>
          <Lock />
        </template>
      </AuthWaveInput>

      <AuthWaveInput
        id="confirmPassword"
        v-model="confirmPassword"
        name="confirmPassword"
        type="password"
        autocomplete="new-password"
        label="请再次输入新密码"
        required
        :disabled="!!successMsg"
      >
        <template #leading>
          <Lock />
        </template>
      </AuthWaveInput>

      <button
        type="submit"
        :disabled="loading || !!successMsg || !resetToken"
        class="auth-button mt-4 px-4 py-3"
      >
        <Loader2 v-if="loading" class="mr-2 h-5 w-5 animate-spin" />
        {{ loading ? "UPDATING..." : "UPDATE PASSWORD" }}
      </button>
    </form>
  </AuthLayout>
</template>
