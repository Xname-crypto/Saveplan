<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue"
import { useRouter } from "@/router"
import AuthLayout from "@/components/AuthLayout.vue"
import { authClient, getAuthErrorMessage, saveAuthAvatarSource } from "@/services/authClient"
import {
  ArrowRight,
  Camera,
  Check,
  CheckCircle2,
  Eye,
  EyeOff,
  Loader2,
  Sparkles,
  Upload,
  XCircle,
} from "lucide-vue-next"

const registerVideo = "/video/register-visual.mp4?v=auth-balanced-2"
const authPoster = "/video/auth-poster.jpeg"

const router = useRouter()
const currentStep = ref(1)
const loading = ref(false)
const errorMsg = ref("")
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const isUsernameTouched = ref(false)
const isJobTouched = ref(false)

const formData = ref({
  email: "",
  password: "",
  confirmPassword: "",
  username: "",
  job: "",
  bio: "",
  avatarFile: null as File | null,
  avatarPreview: "",
  avatarDataUrl: "",
})

const isUsernameValid = computed(() => formData.value.username.trim().length >= 3)

const triggerFileInputClick = () => {
  fileInput.value?.click()
}

const handleAvatarChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]

  if (!file) return

  if (formData.value.avatarPreview) {
    URL.revokeObjectURL(formData.value.avatarPreview)
  }

  formData.value.avatarFile = file
  formData.value.avatarPreview = URL.createObjectURL(file)
  formData.value.avatarDataUrl = ""
  void createAvatarDataUrl(file).then((dataUrl) => {
    if (formData.value.avatarFile === file) {
      formData.value.avatarDataUrl = dataUrl
    }
  })
}

const createAvatarDataUrl = (file: File) =>
  new Promise<string>((resolve) => {
    const image = new Image()
    const url = URL.createObjectURL(file)

    image.onload = () => {
      const canvas = document.createElement("canvas")
      const size = 160
      const scale = Math.max(size / image.width, size / image.height)
      const width = image.width * scale
      const height = image.height * scale
      const x = (size - width) / 2
      const y = (size - height) / 2
      const context = canvas.getContext("2d")

      canvas.width = size
      canvas.height = size

      if (!context) {
        URL.revokeObjectURL(url)
        resolve("")
        return
      }

      context.drawImage(image, x, y, width, height)
      URL.revokeObjectURL(url)
      resolve(canvas.toDataURL("image/jpeg", 0.78))
    }

    image.onerror = () => {
      URL.revokeObjectURL(url)
      resolve("")
    }

    image.src = url
  })

const handleStep1 = () => {
  if (!formData.value.email || !formData.value.password || !formData.value.confirmPassword) {
    errorMsg.value = "请填写所有必填项。"
    return
  }

  if (formData.value.password !== formData.value.confirmPassword) {
    errorMsg.value = "两次输入的密码不一致。"
    return
  }

  if (formData.value.password.length < 6) {
    errorMsg.value = "密码长度至少需要 6 位。"
    return
  }

  errorMsg.value = ""
  currentStep.value = 2
}

const handleStep2 = async () => {
  isUsernameTouched.value = true
  isJobTouched.value = true

  const username = formData.value.username.trim()
  if (!username) {
    errorMsg.value = "请输入昵称。"
    return
  }

  if (username.length < 3) {
    errorMsg.value = "昵称至少需要 3 个字符。"
    return
  }

  if (!formData.value.job.trim()) {
    errorMsg.value = "请输入职业或身份。"
    return
  }

  formData.value.username = username
  formData.value.job = formData.value.job.trim()
  errorMsg.value = ""
  await handleRegistration()
}

const handleRegistration = async () => {
  try {
    loading.value = true
    errorMsg.value = ""

    const bio = formData.value.bio.trim()
    const avatarDataUrl =
      formData.value.avatarDataUrl ||
      (formData.value.avatarFile ? await createAvatarDataUrl(formData.value.avatarFile) : "")

    const user = await authClient.register({
      email: formData.value.email.trim(),
      password: formData.value.password,
      username: formData.value.username.trim(),
      job: formData.value.job.trim(),
      bio: bio || undefined,
      avatar_name: formData.value.avatarFile?.name,
    })

    if (avatarDataUrl) {
      saveAuthAvatarSource(user, avatarDataUrl)
    }

    currentStep.value = 3
  } catch (error) {
    errorMsg.value = getAuthErrorMessage(error)
  } finally {
    loading.value = false
  }
}

const handleFinish = () => {
  void router.push("/")
}

const handleBack = () => {
  errorMsg.value = ""
  if (currentStep.value > 1) {
    currentStep.value -= 1
    return
  }

  void router.push("/login")
}

onBeforeUnmount(() => {
  if (formData.value.avatarPreview) {
    URL.revokeObjectURL(formData.value.avatarPreview)
  }
})
</script>

<template>
  <AuthLayout
    :video-src="registerVideo"
    :poster-src="authPoster"
    :show-back="currentStep > 1"
    content-offset-class="md:-translate-y-6"
    @back="handleBack"
  >
    <template #title>
      <div class="auth-register-head pr-12 md:pr-14">
        <h1 class="auth-register-title">
          <span v-if="currentStep === 1">创建账号</span>
          <span v-else-if="currentStep === 2">完善资料</span>
          <span v-else>注册成功</span>
        </h1>
        <p class="auth-register-subtitle">
          <span v-if="currentStep === 1">创建你的专属题库空间。</span>
          <span v-else-if="currentStep === 2">补充用于个性化工作区的信息。</span>
          <span v-else>账号已准备好，开始高效复习。</span>
        </p>
      </div>
    </template>

    <div class="relative">
      <div v-if="errorMsg" class="auth-alert auth-alert--error mb-5 p-3 text-sm font-medium">
        {{ errorMsg }}
      </div>

      <form v-if="currentStep === 1" class="animate-in space-y-5 duration-300 fade-in slide-in-from-right-4" @submit.prevent="handleStep1">
        <div class="space-y-1">
          <label class="auth-label ml-1 text-xs font-semibold uppercase">邮箱地址</label>
          <input
            v-model="formData.email"
            type="email"
            autocomplete="email"
            placeholder="请输入邮箱"
            class="auth-input px-4 py-3"
            required
          />
        </div>

        <div class="space-y-1">
          <label class="auth-label ml-1 text-xs font-semibold uppercase">密码</label>
          <div class="relative">
            <input
              v-model="formData.password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="••••••••"
              class="auth-input px-4 py-3 pr-12"
              required
            />
            <button
              v-show="formData.password"
              type="button"
              class="auth-link absolute right-3 top-1/2 -translate-y-1/2 focus:outline-none"
              @click="showPassword = !showPassword"
            >
              <EyeOff v-if="!showPassword" class="h-5 w-5" />
              <Eye v-else class="h-5 w-5" />
            </button>
          </div>
        </div>

        <div class="space-y-1">
          <label class="auth-label ml-1 text-xs font-semibold uppercase">确认密码</label>
          <div class="relative">
            <input
              v-model="formData.confirmPassword"
              :type="showConfirmPassword ? 'text' : 'password'"
              placeholder="••••••••"
              class="auth-input px-4 py-3 pr-12"
              required
            />
            <button
              v-show="formData.confirmPassword"
              type="button"
              class="auth-link absolute right-3 top-1/2 -translate-y-1/2 focus:outline-none"
              @click="showConfirmPassword = !showConfirmPassword"
            >
              <EyeOff v-if="!showConfirmPassword" class="h-5 w-5" />
              <Eye v-else class="h-5 w-5" />
            </button>
          </div>
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="auth-button mt-6 px-4 py-3.5"
        >
          <Loader2 v-if="loading" class="mr-2 h-5 w-5 animate-spin" />
          {{ loading ? "处理中..." : "继续" }}
          <ArrowRight v-if="!loading" class="ml-2 h-4 w-4" />
        </button>

        <div class="mt-6 text-center text-[0.7rem] text-[rgba(226,218,194,0.34)]">
          已经注册？
          <router-link to="/login" class="auth-link font-semibold">
            去登录
          </router-link>
        </div>
      </form>

      <div v-else-if="currentStep === 2" class="animate-in space-y-6 duration-300 fade-in slide-in-from-right-4">
        <div class="auth-avatar-row">
          <div class="group relative cursor-pointer" @click="triggerFileInputClick">
            <div class="auth-avatar-control">
              <img v-if="formData.avatarPreview" :src="formData.avatarPreview" class="h-full w-full object-cover" alt="" />
              <Camera v-else class="h-6 w-6 text-[rgba(226,218,194,0.42)] group-hover:text-[#eee6ce]" />
            </div>
            <div class="auth-avatar-upload">
              <Upload class="h-3.5 w-3.5" />
            </div>
            <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="handleAvatarChange" />
          </div>
          <div>
            <p>头像</p>
            <span>可选上传，用于完善你的工作区。</span>
          </div>
        </div>

        <div class="space-y-1">
          <label class="auth-label ml-1 text-xs font-semibold uppercase">显示名称</label>
          <div class="relative">
            <input
              v-model="formData.username"
              type="text"
              autocomplete="nickname"
              placeholder="请输入昵称"
              class="auth-input px-4 py-3 pr-10"
              :class="[
                isUsernameValid
                  ? 'border-green-400/60 focus:border-green-400'
                  : isUsernameTouched
                    ? 'border-red-400/70 focus:border-red-400'
                    : '',
              ]"
              @blur="isUsernameTouched = true"
            />
            <div class="absolute right-3 top-1/2 -translate-y-1/2">
              <CheckCircle2 v-if="isUsernameValid" class="h-5 w-5 text-[#c5f6d8]" />
              <XCircle v-else-if="isUsernameTouched" class="h-5 w-5 text-[#ffc7c7]" />
            </div>
          </div>
          <p v-if="isUsernameTouched && formData.username && !isUsernameValid" class="ml-1 text-xs font-medium text-[#ffc7c7]">
            昵称至少需要 3 个字符。
          </p>
        </div>

        <div class="space-y-1">
          <label class="auth-label ml-1 text-xs font-semibold uppercase">身份 / 状态</label>
          <div class="relative">
            <input
              v-model="formData.job"
              type="text"
              placeholder="学生、教师、备考用户"
              class="auth-input px-4 py-3 pr-10"
              :class="[
                formData.job
                  ? 'border-green-400/60 focus:border-green-400'
                  : isJobTouched
                    ? 'border-red-400/70 focus:border-red-400'
                    : '',
              ]"
              @blur="isJobTouched = true"
            />
            <div class="absolute right-3 top-1/2 -translate-y-1/2">
              <CheckCircle2 v-if="formData.job" class="h-5 w-5 text-[#c5f6d8]" />
              <XCircle v-else-if="isJobTouched" class="h-5 w-5 text-[#ffc7c7]" />
            </div>
          </div>
        </div>

        <button
          :disabled="loading"
          class="auth-button px-4 py-3.5"
          @click="handleStep2"
        >
          <Loader2 v-if="loading" class="mr-2 h-5 w-5 animate-spin" />
          {{ loading ? "创建中..." : "创建账号" }}
          <ArrowRight v-if="!loading" class="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
        </button>
      </div>

      <div v-else class="animate-in py-8 text-center duration-500 fade-in zoom-in-95">
        <div class="relative mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-full border border-[rgba(226,218,194,0.18)] bg-[rgba(226,218,194,0.06)] shadow-[0_20px_48px_rgba(0,0,0,0.24)]">
          <Sparkles class="absolute right-0 top-0 h-10 w-10 animate-bounce text-[#ded6bd]" style="animation-delay: 0.5s" />
          <Check class="h-12 w-12 text-[#eee6ce]" />
        </div>

        <h2 class="mb-2 text-2xl font-bold text-[#eee6ce]">账号已就绪</h2>
        <p class="mx-auto mb-8 max-w-xs text-[rgba(226,218,194,0.46)]">
          欢迎，<span class="font-semibold text-[#eee6ce]">{{ formData.username || "新朋友" }}</span>。<br />
          你的复习工作区已准备就绪。
        </p>

        <button
          class="auth-button px-4 py-3.5"
          @click="handleFinish"
        >
          开始使用
          <ArrowRight class="ml-2 h-5 w-5" />
        </button>
      </div>
    </div>
  </AuthLayout>
</template>

<style scoped>
input::-ms-reveal,
input::-ms-clear {
  display: none;
}
</style>
