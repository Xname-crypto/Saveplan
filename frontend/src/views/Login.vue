<script setup lang="ts">
import { ref } from "vue"
import { useRoute, useRouter } from "@/router"
import AuthLayout from "@/components/AuthLayout.vue"
import ValidCode from "@/components/ValidCode.vue"
import { authClient, getAuthErrorMessage } from "@/services/authClient"
import { Eye, EyeOff, Loader2 } from "lucide-vue-next"

const loginVideo = "/video/login-visual.mp4?v=auth-balanced-2"
const authPoster = "/video/auth-poster.jpeg"

const router = useRouter()
const route = useRoute()
const email = ref("")
const password = ref("")
const showPassword = ref(false)
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
  <AuthLayout :video-src="loginVideo" :poster-src="authPoster" content-offset-class="md:-translate-y-8">
    <template #title>
      欢迎回来
    </template>
    <template #subtitle>访问你的专属题库。</template>

    <form class="space-y-5" @submit.prevent="handleLogin">
      <div class="space-y-1">
        <label for="email" class="auth-label ml-1 text-xs font-semibold uppercase">邮箱地址</label>
        <input
          id="email"
          v-model="email"
          name="email"
          type="email"
          autocomplete="email"
          autocapitalize="none"
          autocorrect="off"
          spellcheck="false"
          placeholder="请输入邮箱"
          class="auth-input px-4 py-3"
          required
        />
      </div>

      <div class="space-y-1">
        <div class="ml-1 flex items-center justify-between">
          <label for="password" class="auth-label text-xs font-semibold uppercase">密码</label>
          <router-link to="/forgot-password" class="auth-link text-[0.62rem] font-semibold">忘记密码？</router-link>
        </div>
        <div class="relative">
          <input
            id="password"
            v-model="password"
            name="password"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="current-password"
            placeholder="请输入密码"
            class="auth-input px-4 py-3 pr-12"
            required
          />
          <button
            v-show="password"
            type="button"
            class="auth-link absolute right-3 top-1/2 -translate-y-1/2 focus:outline-none"
            :aria-label="showPassword ? 'Hide password' : 'Show password'"
            @click="showPassword = !showPassword"
          >
            <EyeOff v-if="!showPassword" class="h-5 w-5" />
            <Eye v-else class="h-5 w-5" />
          </button>
        </div>
      </div>

      <div class="space-y-1">
        <label for="valid-code" class="auth-label ml-1 text-xs font-semibold uppercase">验证码</label>
        <div class="auth-code-row">
          <input
            id="valid-code"
            v-model="validCode"
            name="valid-code"
            type="text"
            autocomplete="off"
            inputmode="text"
            maxlength="4"
            placeholder="请输入验证码"
            class="auth-input px-4 py-3"
            required
          />
          <div class="auth-code-box">
            <ValidCode ref="validCodeRef" @update:value="updateGeneratedCode" />
          </div>
        </div>
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="auth-button mt-4 px-4 py-3"
      >
        <Loader2 v-if="loading" class="mr-2 h-5 w-5 animate-spin" />
        {{ loading ? "登录中..." : "登录" }}
      </button>

      <div class="mt-6 text-center text-[0.7rem] text-[rgba(226,218,194,0.34)]">
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
.auth-code-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 8.25rem;
  gap: 0.75rem;
  align-items: center;
}

.auth-code-box {
  min-width: 0;
}

@media (max-width: 420px) {
  .auth-code-row {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
