<script setup lang="ts">
import { computed, ref } from "vue"
import AuthLayout from "@/components/AuthLayout.vue"
import AuthWaveInput from "@/components/AuthWaveInput.vue"
import { authClient, getAuthErrorMessage } from "@/services/authClient"
import { VIDEO_ASSETS } from "@/services/videoAssets"
import { Loader2, Mail } from "lucide-vue-next"

const forgotPasswordVideo = VIDEO_ASSETS.forgotPassword
const authPoster = VIDEO_ASSETS.forgotPasswordPoster

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
  <AuthLayout
    :video-src="forgotPasswordVideo"
    :poster-src="authPoster"
    media-position="88% center"
    media-eyebrow="RECOVER ACCESS"
    media-title="重新找回你的学习入口。"
    media-description="输入邮箱获取重置链接，恢复访问你的题库和复习资料。"
    content-offset-class="md:translate-y-4"
  >
    <template #title>重置访问权限</template>
    <template #subtitle>输入邮箱，接收密码重置链接。</template>

    <form class="forgot-form" @submit.prevent="handleReset">
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

      <AuthWaveInput
        id="email"
        v-model="email"
        name="email"
        type="email"
        autocomplete="email"
        autocapitalize="none"
        autocorrect="off"
        spellcheck="false"
        label="请输入邮箱"
        required
      >
        <template #leading>
          <Mail />
        </template>
      </AuthWaveInput>

      <button
        type="submit"
        :disabled="loading"
        class="auth-button forgot-submit-button px-4 py-3"
      >
        <Loader2 v-if="loading" class="mr-2 h-5 w-5 animate-spin" />
        {{ loading ? "发送中..." : "发送重置链接" }}
      </button>

      <div class="forgot-login-row text-center text-[0.7rem] text-[rgba(226,218,194,0.34)]">
        <router-link to="/login" class="auth-link inline-flex items-center font-semibold">
          返回登录
        </router-link>
      </div>
    </form>
  </AuthLayout>
</template>

<style scoped>
.forgot-form {
  display: grid;
  gap: 1.08rem;
}

.forgot-submit-button {
  margin-top: 0.45rem !important;
  font-size: 0.82rem;
}

.forgot-login-row {
  margin-top: 0.9rem !important;
  color: rgba(226, 218, 194, 0.38) !important;
  font-weight: 800;
}

:global(html[data-theme="day"]) .forgot-form .auth-wave-field__control input {
  border-bottom-color: rgba(104, 189, 240, 0.74) !important;
  color: #1f2933 !important;
  -webkit-text-fill-color: #1f2933 !important;
  caret-color: #345d75 !important;
  text-shadow: none !important;
}

:global(html[data-theme="day"]) .forgot-form .auth-wave-field__control label {
  color: rgba(52, 93, 117, 0.82) !important;
}

:global(html[data-theme="day"]) .forgot-form .auth-wave-field__control label span {
  color: inherit;
}

:global(html[data-theme="day"]) .forgot-form .auth-wave-field__leading,
:global(html[data-theme="day"]) .forgot-form .auth-wave-field__trailing {
  color: rgba(52, 93, 117, 0.72) !important;
}

:global(html[data-theme="day"]) .forgot-form .auth-wave-field__control input:focus,
:global(html[data-theme="day"]) .forgot-form .auth-wave-field__control input:not(:placeholder-shown),
:global(html[data-theme="day"]) .forgot-form .auth-wave-field__control input:-webkit-autofill,
:global(html[data-theme="day"]) .forgot-form .auth-wave-field__control.has-value input {
  border-bottom-color: #345d75 !important;
  box-shadow:
    0 1px 0 rgba(52, 93, 117, 0.62),
    0 10px 22px rgba(52, 93, 117, 0.08) !important;
}

:global(html[data-theme="day"]) .forgot-form .auth-wave-field__control input:focus + label span,
:global(html[data-theme="day"]) .forgot-form .auth-wave-field__control input:not(:placeholder-shown) + label span,
:global(html[data-theme="day"]) .forgot-form .auth-wave-field__control input:-webkit-autofill + label span,
:global(html[data-theme="day"]) .forgot-form .auth-wave-field__control.has-value label span,
:global(html[data-theme="day"]) .forgot-form .auth-wave-field__control:has(input:focus) .auth-wave-field__leading,
:global(html[data-theme="day"]) .forgot-form .auth-wave-field__control:has(input:not(:placeholder-shown)) .auth-wave-field__leading,
:global(html[data-theme="day"]) .forgot-form .auth-wave-field__control:has(input:-webkit-autofill) .auth-wave-field__leading,
:global(html[data-theme="day"]) .forgot-form .auth-wave-field__control.has-value .auth-wave-field__leading {
  color: #345d75 !important;
  filter: drop-shadow(0 0 8px rgba(52, 93, 117, 0.18));
}

:global(html[data-theme="day"]) .forgot-submit-button {
  box-shadow:
    0 18px 36px rgba(31, 41, 51, 0.18),
    0 0 0 1px rgba(31, 41, 51, 0.04) !important;
}

:global(html[data-theme="day"]) .forgot-login-row {
  color: rgba(31, 41, 51, 0.56) !important;
}

:global(html[data-theme="day"]) .forgot-login-row .auth-link {
  color: #345d75 !important;
}

:global(html[data-theme="day"]) .forgot-login-row .auth-link:hover {
  color: #1f2933 !important;
}
</style>
