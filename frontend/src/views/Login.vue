<script setup lang="ts">
import { ref } from "vue"
import { useRoute, useRouter } from "@/router"
import AuthLayout from "@/components/AuthLayout.vue"
import AuthWaveInput from "@/components/AuthWaveInput.vue"
import ValidCode from "@/components/ValidCode.vue"
import { authClient, getAuthErrorMessage } from "@/services/authClient"
import { VIDEO_ASSETS } from "@/services/videoAssets"
import { Eye, EyeOff, Loader2, Lock, Mail, ShieldCheck } from "lucide-vue-next"

const loginVideo = VIDEO_ASSETS.login
const authPoster = VIDEO_ASSETS.loginPoster

const router = useRouter()
const route = useRoute()
const email = ref("")
const password = ref("")
const showPassword = ref(false)
const rememberMe = ref(false)
const validCode = ref("")
const generatedCode = ref("")
const validCodeRef = ref<InstanceType<typeof ValidCode> | null>(null)
const loading = ref(false)

const handleLogin = async () => {
  const normalizedEmail = email.value.trim()
  const normalizedValidCode = validCode.value.trim().toLowerCase()

  if (!normalizedEmail || !password.value) {
    window.alert("登录失败\n\n请输入邮箱和密码。")
    return
  }

  if (!normalizedValidCode) {
    window.alert("登录失败\n\n请输入验证码。")
    return
  }

  if (normalizedValidCode !== generatedCode.value.toLowerCase()) {
    window.alert("登录失败\n\n验证码错误，请重新输入。")
    validCode.value = ""
    validCodeRef.value?.refreshCode()
    return
  }

  try {
    loading.value = true
    const user = await authClient.login(normalizedEmail, password.value)
    window.alert(`登录成功\n\n欢迎回来，${user.username || user.email}。`)
    const redirectTo = typeof route.query.redirect === "string" ? route.query.redirect : "/"
    await router.push(redirectTo)
  } catch (error) {
    window.alert(`登录失败\n\n${getAuthErrorMessage(error)}`)
    validCode.value = ""
    validCodeRef.value?.refreshCode()
  } finally {
    loading.value = false
  }
}

const updateGeneratedCode = (code: string) => {
  generatedCode.value = code
}
</script>

<template>
  <AuthLayout
    :video-src="loginVideo"
    :poster-src="authPoster"
    media-position="88% center"
    media-eyebrow="WELCOME BACK"
    media-title="回到你的专注学习现场。"
    media-description="继续整理题库、校对资料，把复习节奏接回上一次的位置。"
    content-offset-class="md:translate-y-2"
  >
    <template #title>
      Welcome back
    </template>
    <template #subtitle>访问你的专属题库。</template>

    <form class="login-form" @submit.prevent="handleLogin">
      <AuthWaveInput
        id="email"
        v-model="email"
        name="email"
        type="email"
        label="请输入邮箱"
        autocomplete="email"
        autocapitalize="none"
        autocorrect="off"
        spellcheck="false"
        required
      >
        <template #leading>
          <Mail />
        </template>
      </AuthWaveInput>

      <div class="auth-password-block">
        <AuthWaveInput
          id="password"
          v-model="password"
          name="password"
          :type="showPassword ? 'text' : 'password'"
          label="请输入密码"
          autocomplete="current-password"
          required
        >
          <template #leading>
            <Lock />
          </template>
          <template #trailing>
            <button
              type="button"
              class="auth-link focus:outline-none"
              :aria-label="showPassword ? 'Hide password' : 'Show password'"
              @click="showPassword = !showPassword"
            >
              <EyeOff v-if="!showPassword" class="h-5 w-5" />
              <Eye v-else class="h-5 w-5" />
            </button>
          </template>
        </AuthWaveInput>
        <div class="forgot-password-row">
          <label class="remember-me-control">
            <input v-model="rememberMe" type="checkbox" name="remember" />
            <span>记住我</span>
          </label>
          <router-link to="/forgot-password" class="auth-link forgot-password-link">忘记密码？</router-link>
          <router-link to="/forgot-password" class="auth-link text-[0.62rem] font-semibold">忘记密码？</router-link>
        </div>
      </div>

      <div class="auth-captcha-block space-y-1">
        <div class="auth-code-row">
          <AuthWaveInput
            id="valid-code"
            v-model="validCode"
            name="valid-code"
            type="text"
            label="请输入验证码"
            autocomplete="off"
            inputmode="text"
            maxlength="4"
            required
          >
            <template #leading>
              <ShieldCheck />
            </template>
          </AuthWaveInput>
          <div class="auth-code-box">
            <ValidCode ref="validCodeRef" @update:value="updateGeneratedCode" />
          </div>
        </div>
      </div>

      <div class="forgot-password-row auth-login-options-row">
        <label class="remember-me-control">
          <input v-model="rememberMe" type="checkbox" name="remember" />
          <span>记住我</span>
        </label>
        <router-link to="/forgot-password" class="auth-link forgot-password-link">忘记密码？</router-link>
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="auth-button login-submit-button mt-4 px-4 py-3"
      >
        <Loader2 v-if="loading" class="mr-2 h-5 w-5 animate-spin" />
        {{ loading ? "登录中..." : "登录" }}
      </button>

      <div class="login-account-row mt-6 text-center text-[0.7rem] text-[rgba(226,218,194,0.34)]">
        <div>
          还没有账号？
          <router-link to="/register" class="auth-link font-semibold">
            创建账号
          </router-link>
        </div>
      </div>
    </form>
  </AuthLayout>
</template>

<style scoped>
.auth-password-block {
  display: grid;
  gap: 0.82rem;
}

.auth-password-block > .forgot-password-row {
  display: none;
}

.forgot-password-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-top: -0.08rem;
  padding: 0 0.1rem;
  line-height: 1.2;
}

.auth-login-options-row {
  margin-top: -0.55rem;
  margin-bottom: -0.08rem;
}

.forgot-password-row > .auth-link:not(.forgot-password-link) {
  display: none;
}

.remember-me-control {
  display: inline-flex;
  align-items: center;
  gap: 0.42rem;
  color: rgba(226, 218, 194, 0.62);
  cursor: pointer;
  font-size: 0.86rem;
  font-weight: 800;
  line-height: 1;
}

.remember-me-control input {
  width: 0.78rem;
  height: 0.78rem;
  margin: 0;
  border: 1px solid rgba(226, 218, 194, 0.64);
  border-radius: 999px;
  appearance: none;
  background: transparent;
  cursor: pointer;
}

.remember-me-control input:checked {
  border-color: #9bd9ff;
  background:
    radial-gradient(circle, #9bd9ff 0 42%, transparent 46%),
    transparent;
}

.forgot-password-link {
  color: rgba(226, 218, 194, 0.78);
  font-size: 0.86rem !important;
  font-weight: 800 !important;
  line-height: 1;
}

.forgot-password-link:hover {
  color: #9bd9ff;
  text-shadow: 0 0 14px rgba(155, 217, 255, 0.22);
}

.auth-password-block + .auth-captcha-block {
  margin-top: 0.12rem !important;
}

.login-form {
  display: grid;
  gap: 1.02rem;
}

.auth-code-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 8.25rem;
  gap: 0.75rem;
  align-items: end;
}

.auth-code-box {
  min-width: 0;
  padding-bottom: 0.1rem;
}

.login-submit-button {
  margin-top: 0.35rem !important;
  font-size: 0.82rem;
}

.login-account-row {
  margin-top: 0.85rem !important;
  color: rgba(226, 218, 194, 0.38) !important;
  font-size: 0.7rem !important;
  font-weight: 800;
  line-height: 1.35;
}

.login-account-row > div {
  display: inline-flex;
  align-items: baseline;
  gap: 1.05rem;
}

.login-account-row .auth-link {
  color: rgba(226, 218, 194, 0.62);
  font-size: 0.7rem !important;
  font-weight: 900;
}

@media (max-width: 420px) {
  .auth-code-row {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
