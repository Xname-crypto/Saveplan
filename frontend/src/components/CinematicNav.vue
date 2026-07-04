<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue"
import { LogOut, Menu, UserRound } from "lucide-vue-next"
import ShinyText from "@/components/ShinyText.vue"
import { useRouter } from "@/router"
import {
  AUTH_SESSION_CHANGE_EVENT,
  authClient,
  getAuthAvatarInitial,
  getAuthAvatarSource,
  getStoredAuthUser,
  type AuthUser,
} from "@/services/authClient"

const links = [
  { label: "首页", to: "/" },
  { label: "转换", to: "/convert" },
  { label: "价格", to: "/pricing" },
  { label: "个人中心", to: "/profile" },
]

const router = useRouter()
const currentUser = ref<AuthUser | null>(getStoredAuthUser())
const avatarLoadFailed = ref(false)
const isUserMenuOpen = ref(false)
const userMenuRef = ref<HTMLElement | null>(null)
const isLoginPromptOpen = ref(false)

const avatarSrc = computed(() => (avatarLoadFailed.value ? "" : getAuthAvatarSource(currentUser.value)))
const avatarInitial = computed(() => getAuthAvatarInitial(currentUser.value))
const avatarLabel = computed(() => currentUser.value?.username || currentUser.value?.email || "个人中心")
const profileCredits = computed(() => {
  const userWithCredits = currentUser.value as (AuthUser & { credits?: number; points?: number }) | null
  const credits = userWithCredits?.credits ?? userWithCredits?.points ?? 0

  return new Intl.NumberFormat("zh-CN").format(credits)
})

const updateCurrentUser = (user: AuthUser | null) => {
  currentUser.value = user
  avatarLoadFailed.value = false

  if (!user) {
    isUserMenuOpen.value = false
  }
}

const handleAuthSessionChange = (event: Event) => {
  updateCurrentUser((event as CustomEvent<AuthUser | null>).detail)
}

const handleStorageChange = (event: StorageEvent) => {
  if (!event.key || event.key === "saveplan.auth.user" || event.key === "saveplan.auth.token") {
    updateCurrentUser(getStoredAuthUser())
  }
}

const handleAvatarError = () => {
  avatarLoadFailed.value = true
}

const closeUserMenu = () => {
  isUserMenuOpen.value = false
}

const toggleUserMenu = () => {
  isUserMenuOpen.value = !isUserMenuOpen.value
}

const goToProfile = () => {
  closeUserMenu()
  void router.push("/profile")
}

const handleLogout = () => {
  closeUserMenu()
  authClient.logout()
  void router.push("/")
}

const handleDocumentClick = (event: MouseEvent) => {
  if (!isUserMenuOpen.value) return

  const target = event.target
  if (target instanceof Node && userMenuRef.value?.contains(target)) return

  closeUserMenu()
}

const handleEscape = (event: KeyboardEvent) => {
  if (event.key === "Escape") {
    closeUserMenu()
  }
}

const handleNavLinkClick = (event: MouseEvent, link: (typeof links)[number]) => {
  if (link.to !== "/profile" || currentUser.value) return

  event.preventDefault()
  event.stopPropagation()
  event.stopImmediatePropagation()

  if (isLoginPromptOpen.value) return

  isLoginPromptOpen.value = true
  window.alert("请先登录后进入个人中心。")
  void router.push("/login?redirect=/profile")
  window.setTimeout(() => {
    isLoginPromptOpen.value = false
  }, 600)
}

onMounted(() => {
  updateCurrentUser(getStoredAuthUser())
  window.addEventListener(AUTH_SESSION_CHANGE_EVENT, handleAuthSessionChange)
  window.addEventListener("storage", handleStorageChange)
  document.addEventListener("click", handleDocumentClick)
  window.addEventListener("keydown", handleEscape)
})

onBeforeUnmount(() => {
  window.removeEventListener(AUTH_SESSION_CHANGE_EVENT, handleAuthSessionChange)
  window.removeEventListener("storage", handleStorageChange)
  document.removeEventListener("click", handleDocumentClick)
  window.removeEventListener("keydown", handleEscape)
})
</script>

<template>
  <header class="cinema-nav">
    <RouterLink class="cinema-nav__brand" to="/">
      <ShinyText
        text="Save Your Finals"
        :speed="1.85"
        :delay="0.15"
        :spread="100"
        color="#958b72"
        shine-color="#fffdf4"
        direction="left"
        pause-on-hover
        class-name="cinema-nav__brand-name"
      />
      <i />
      <small>题库导入助手</small>
    </RouterLink>

    <nav class="cinema-nav__links" aria-label="主要导航">
      <RouterLink
        v-for="link in links"
        :key="link.to"
        :to="link.to"
        @click="handleNavLinkClick($event, link)"
      >
        {{ link.label }}
      </RouterLink>
    </nav>

    <div class="cinema-nav__actions">
      <div v-if="currentUser" ref="userMenuRef" class="cinema-nav__user">
        <button
          class="cinema-nav__avatar"
          type="button"
          :title="avatarLabel"
          :aria-label="`${avatarLabel} 的账户菜单`"
          :aria-expanded="isUserMenuOpen"
          aria-haspopup="menu"
          @click.stop="toggleUserMenu"
        >
          <img v-if="avatarSrc" :src="avatarSrc" alt="" @error="handleAvatarError" />
          <span v-else>{{ avatarInitial }}</span>
        </button>

        <div v-if="isUserMenuOpen" class="cinema-nav__user-card" role="menu">
          <div class="cinema-nav__user-card-arrow" />
          <header>
            <strong>{{ avatarLabel }}</strong>
            <span>{{ currentUser.email }}</span>
          </header>
          <div class="cinema-nav__credits">
            <span>剩余积分</span>
            <strong>{{ profileCredits }}</strong>
          </div>
          <button type="button" role="menuitem" @click="goToProfile">
            <UserRound :size="16" />
            个人中心
          </button>
          <button type="button" role="menuitem" @click="handleLogout">
            <LogOut :size="16" />
            退出登录
          </button>
        </div>
      </div>
      <RouterLink v-else class="cinema-nav__login" to="/login">登录 / 注册</RouterLink>
      <button class="cinema-nav__menu" type="button" aria-label="打开菜单">
        <Menu :size="20" />
      </button>
    </div>
  </header>
</template>
