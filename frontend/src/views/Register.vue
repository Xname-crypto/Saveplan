<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue"
import { useRouter } from "@/router"
import AuthLayout from "@/components/AuthLayout.vue"
import AuthWaveInput from "@/components/AuthWaveInput.vue"
import { authClient, getAuthErrorMessage, saveAuthAvatarSource } from "@/services/authClient"
import { VIDEO_ASSETS } from "@/services/videoAssets"
import {
  ArrowRight,
  Briefcase,
  Camera,
  Check,
  CheckCircle2,
  Eye,
  EyeOff,
  Loader2,
  Lock,
  Mail,
  Sparkles,
  Upload,
  User,
  XCircle,
} from "lucide-vue-next"

const registerVideo = VIDEO_ASSETS.register
const authPoster = VIDEO_ASSETS.registerPoster

const router = useRouter()
const currentStep = ref(1)
const loading = ref(false)
const errorMsg = ref("")
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const identityChoiceRef = ref<HTMLElement | null>(null)
const isUsernameTouched = ref(false)
const isJobTouched = ref(false)

const presetAvatars = [
  { id: "lin", label: "Lin", src: "/stitch/avatar-lin.svg" },
  { id: "mia", label: "Mia", src: "/stitch/avatar-mia.svg" },
  { id: "chen", label: "Chen", src: "/stitch/avatar-chen.svg" },
  { id: "jason", label: "Jason", src: "/stitch/avatar-jason.svg" },
  { id: "zhou", label: "Zhou", src: "/stitch/avatar-zhou.svg" },
]

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
  avatarPreset: "",
})

const isUsernameValid = computed(() => formData.value.username.trim().length >= 3)
const identityOptions = ["学生", "教师", "备考用户"]

const selectIdentity = (identity: string) => {
  formData.value.job = identity
  isJobTouched.value = true
}

const handleWindowClick = (event: MouseEvent) => {
  if (currentStep.value !== 2 || !formData.value.job) return

  const target = event.target as Node | null
  if (target && identityChoiceRef.value?.contains(target)) return

  formData.value.job = ""
}

const triggerFileInputClick = () => {
  fileInput.value?.click()
}

const revokeUploadedAvatarPreview = () => {
  if (formData.value.avatarPreview.startsWith("blob:")) {
    URL.revokeObjectURL(formData.value.avatarPreview)
  }
}

const handleAvatarChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]

  if (!file) return

  revokeUploadedAvatarPreview()

  formData.value.avatarFile = file
  formData.value.avatarPreview = URL.createObjectURL(file)
  formData.value.avatarDataUrl = ""
  formData.value.avatarPreset = ""
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

const selectPresetAvatar = (src: string) => {
  revokeUploadedAvatarPreview()
  formData.value.avatarFile = null
  formData.value.avatarPreview = src
  formData.value.avatarDataUrl = ""
  formData.value.avatarPreset = src

  if (fileInput.value) {
    fileInput.value.value = ""
  }
}

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
      formData.value.avatarPreset ||
      formData.value.avatarDataUrl ||
      (formData.value.avatarFile ? await createAvatarDataUrl(formData.value.avatarFile) : "")
    const avatarName = formData.value.avatarFile?.name || formData.value.avatarPreset.split("/").pop() || undefined

    const user = await authClient.register({
      email: formData.value.email.trim(),
      password: formData.value.password,
      username: formData.value.username.trim(),
      job: formData.value.job.trim(),
      bio: bio || undefined,
      avatar_name: avatarName,
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

onMounted(() => {
  window.addEventListener("click", handleWindowClick)
})

onBeforeUnmount(() => {
  window.removeEventListener("click", handleWindowClick)
  revokeUploadedAvatarPreview()
})
</script>

<template>
  <AuthLayout
    :video-src="registerVideo"
    :poster-src="authPoster"
    :show-back="currentStep > 1"
    media-position="88% center"
    media-eyebrow="START YOUR SPACE"
    media-title="创建你的专属复习工作区。"
    media-description="从账号开始，把题库、笔记和资料整理成更清晰的学习系统。"
    content-offset-class="md:translate-y-1"
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

      <form v-if="currentStep === 1" class="register-step-one animate-in duration-300 fade-in slide-in-from-right-4" @submit.prevent="handleStep1">
        <AuthWaveInput
          v-model="formData.email"
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

        <AuthWaveInput
          v-model="formData.password"
          :type="showPassword ? 'text' : 'password'"
          autocomplete="new-password"
          label="请输入密码"
          required
        >
          <template #leading>
            <Lock />
          </template>
          <template #trailing>
            <button
              v-show="formData.password"
              type="button"
              class="auth-link focus:outline-none"
              @click="showPassword = !showPassword"
            >
              <EyeOff v-if="!showPassword" class="h-5 w-5" />
              <Eye v-else class="h-5 w-5" />
            </button>
          </template>
        </AuthWaveInput>

        <AuthWaveInput
          v-model="formData.confirmPassword"
          :type="showConfirmPassword ? 'text' : 'password'"
          autocomplete="new-password"
          label="请确认密码"
          required
        >
          <template #leading>
            <Lock />
          </template>
          <template #trailing>
            <button
              v-show="formData.confirmPassword"
              type="button"
              class="auth-link focus:outline-none"
              @click="showConfirmPassword = !showConfirmPassword"
            >
              <EyeOff v-if="!showConfirmPassword" class="h-5 w-5" />
              <Eye v-else class="h-5 w-5" />
            </button>
          </template>
        </AuthWaveInput>

        <button
          type="submit"
          :disabled="loading"
          class="auth-button register-submit-button px-4 py-3.5"
        >
          <Loader2 v-if="loading" class="mr-2 h-5 w-5 animate-spin" />
          {{ loading ? "处理中..." : "继续" }}
          <ArrowRight v-if="!loading" class="ml-2 h-4 w-4" />
        </button>

        <div class="register-login-row text-center text-[0.7rem] text-[rgba(226,218,194,0.34)]">
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

        <div class="preset-avatar-block">
          <div class="preset-avatar-title">
            <span>选择已有头像</span>
            <small>也可以继续使用上方上传。</small>
          </div>
          <div class="preset-avatar-grid" role="radiogroup" aria-label="选择已有头像">
            <button
              v-for="avatar in presetAvatars"
              :key="avatar.id"
              type="button"
              class="preset-avatar-option"
              :class="{ 'is-selected': formData.avatarPreset === avatar.src }"
              :aria-checked="formData.avatarPreset === avatar.src"
              role="radio"
              @click="selectPresetAvatar(avatar.src)"
            >
              <img :src="avatar.src" :alt="`${avatar.label} 头像`" />
              <CheckCircle2 v-if="formData.avatarPreset === avatar.src" class="preset-avatar-check" />
            </button>
          </div>
        </div>

        <div class="space-y-1">
          <AuthWaveInput
            v-model="formData.username"
            type="text"
            autocomplete="nickname"
            label="请输入昵称"
            :class="[
              isUsernameValid
                ? 'border-green-400/60 focus:border-green-400'
                : isUsernameTouched && formData.username
                  ? 'border-red-400/70 focus:border-red-400'
                  : '',
            ]"
            @blur="isUsernameTouched = true"
          >
            <template #leading>
              <User />
            </template>
            <template #trailing>
              <CheckCircle2 v-if="isUsernameValid" class="h-5 w-5 text-[#c5f6d8]" />
              <XCircle v-else-if="isUsernameTouched && formData.username" class="h-5 w-5 text-[#ffc7c7]" />
            </template>
          </AuthWaveInput>
          <p v-if="isUsernameTouched && formData.username && !isUsernameValid" class="ml-1 text-xs font-medium text-[#ffc7c7]">
            昵称至少需要 3 个字符。
          </p>
        </div>

        <div
          ref="identityChoiceRef"
          class="identity-choice-block"
          :class="{ 'is-error': isJobTouched && !formData.job, 'is-selected': !!formData.job }"
        >
          <div class="identity-choice-title">
            <Briefcase class="h-5 w-5" />
            <span>选择身份</span>
          </div>
          <div class="identity-options" role="radiogroup" aria-label="选择身份">
            <button
              v-for="identity in identityOptions"
              :key="identity"
              type="button"
              class="identity-option"
              :class="{ 'is-selected': formData.job === identity }"
              :aria-checked="formData.job === identity"
              role="radio"
              @click="selectIdentity(identity)"
            >
              {{ identity }}
            </button>
          </div>
          <p v-if="isJobTouched && !formData.job" class="identity-choice-error">
            请选择学生、教师或备考用户。
          </p>
        </div>

        <button
          :disabled="loading"
          class="auth-button register-submit-button px-4 py-3.5"
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
          class="auth-button register-submit-button px-4 py-3.5"
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

.identity-choice-block {
  display: grid;
  gap: 0.72rem;
}

.preset-avatar-block {
  display: grid;
  gap: 0.72rem;
  margin-top: -0.8rem;
}

.preset-avatar-title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  color: rgba(238, 230, 206, 0.72);
}

.preset-avatar-title span {
  font-size: 0.82rem;
  font-weight: 900;
}

.preset-avatar-title small {
  color: rgba(226, 218, 194, 0.36);
  font-size: 0.68rem;
  font-weight: 800;
}

.preset-avatar-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.62rem;
}

.preset-avatar-option {
  position: relative;
  display: grid;
  aspect-ratio: 1;
  min-width: 0;
  place-items: center;
  overflow: hidden;
  border: 1px solid rgba(226, 218, 194, 0.18);
  border-radius: 999px;
  background:
    radial-gradient(circle at 34% 24%, rgba(255, 255, 255, 0.12), transparent 38%),
    rgba(226, 218, 194, 0.035);
  cursor: pointer;
  transition:
    border-color 180ms ease,
    box-shadow 180ms ease,
    transform 180ms ease;
}

.preset-avatar-option:hover,
.preset-avatar-option.is-selected {
  border-color: rgba(155, 217, 255, 0.74);
  box-shadow:
    0 0 0 2px rgba(155, 217, 255, 0.12),
    0 10px 24px rgba(0, 0, 0, 0.22);
  transform: translateY(-1px);
}

.preset-avatar-option img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preset-avatar-check {
  position: absolute;
  right: 0.1rem;
  bottom: 0.1rem;
  width: 1rem;
  height: 1rem;
  border-radius: 999px;
  background: #111;
  color: #9bd9ff;
}

.identity-choice-title {
  display: inline-flex;
  align-items: center;
  gap: 0.72rem;
  color: rgba(238, 230, 206, 0.72);
  font-size: 1.08rem;
  font-weight: 800;
  line-height: 1.5rem;
  transition: color 180ms ease;
}

.identity-choice-title svg {
  flex: 0 0 auto;
}

.identity-choice-block.is-selected .identity-choice-title {
  color: #9bd9ff;
}

.identity-options {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.58rem;
}

.identity-option {
  min-height: 2.75rem;
  border: 1px solid rgba(226, 218, 194, 0.2);
  border-radius: 0.62rem;
  background: rgba(226, 218, 194, 0.035);
  color: rgba(238, 230, 206, 0.72);
  cursor: pointer;
  font-size: 0.86rem;
  font-weight: 800;
  transition:
    background 180ms ease,
    border-color 180ms ease,
    color 180ms ease,
    transform 180ms ease;
}

.identity-option:hover {
  border-color: rgba(155, 217, 255, 0.48);
  color: #9bd9ff;
}

.identity-option.is-selected {
  border-color: #9bd9ff;
  background: rgba(155, 217, 255, 0.14);
  color: #9bd9ff;
  transform: translateY(-1px);
}

.identity-choice-block.is-error .identity-options {
  border-bottom: 2px solid rgba(255, 199, 199, 0.72);
  padding-bottom: 0.55rem;
}

.identity-choice-error {
  margin: 0;
  color: #ffc7c7;
  font-size: 0.72rem;
  font-weight: 700;
}

.register-step-one {
  display: grid;
  gap: 1.08rem;
}

.register-submit-button {
  margin-top: 0.45rem !important;
  font-size: 0.82rem;
}

.register-login-row {
  margin-top: 0.9rem !important;
  color: rgba(226, 218, 194, 0.38) !important;
  font-weight: 800;
}

@media (max-width: 760px) {
  .preset-avatar-block {
    gap: 0.58rem;
    margin-top: -0.35rem;
  }

  .preset-avatar-title {
    display: grid;
    gap: 0.25rem;
  }

  .preset-avatar-grid {
    display: flex;
    gap: 0.58rem;
    overflow-x: auto;
    padding-bottom: 0.15rem;
    scroll-snap-type: x proximity;
  }

  .preset-avatar-option {
    width: 3.25rem;
    min-width: 3.25rem;
    scroll-snap-align: start;
  }

  .identity-options {
    gap: 0.42rem;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    border: 1px solid rgba(226, 218, 194, 0.1);
    border-radius: 999px;
    padding: 0.28rem;
    background: rgba(226, 218, 194, 0.035);
  }

  .identity-option {
    min-height: 2.65rem;
    border-radius: 999px;
    padding: 0 0.35rem;
    font-size: 0.76rem;
    white-space: nowrap;
  }

  .identity-choice-block.is-error .identity-options {
    border-color: rgba(255, 199, 199, 0.42);
    border-bottom: 1px solid rgba(255, 199, 199, 0.42);
    padding: 0.28rem;
  }
}

@media (max-width: 420px) {
  .identity-options {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
</style>
