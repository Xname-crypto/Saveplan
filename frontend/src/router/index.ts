import {
  computed,
  defineComponent,
  h,
  reactive,
  shallowRef,
  type App as VueApp,
  type Component,
} from "vue"
import { getStoredAuthUser } from "@/services/authClient"

type QueryValue = string | undefined

interface RouteState {
  path: string
  fullPath: string
  query: Record<string, QueryValue>
}

type RouteLoader = () => Promise<{ default: Component }>

const routeLoaders: Record<string, RouteLoader> = {
  "/": () => import("@/views/Home.vue"),
  "/convert": () => import("@/views/Convert.vue"),
  "/pricing": () => import("@/views/Pricing.vue"),
  "/profile": () => import("@/views/Profile.vue"),
  "/login": () => import("@/views/Login.vue"),
  "/register": () => import("@/views/Register.vue"),
  "/forgot-password": () => import("@/views/ForgotPassword.vue"),
  "/reset-password": () => import("@/views/ResetPassword.vue"),
}

const route = reactive<RouteState>({
  path: window.location.pathname || "/",
  fullPath: `${window.location.pathname}${window.location.search}${window.location.hash}`,
  query: parseQuery(window.location.search),
})

const activeComponent = shallowRef<Component | null>(null)
const protectedRoutes = new Set(["/convert"])

function parseQuery(search: string) {
  const params = new URLSearchParams(search)
  const query: Record<string, QueryValue> = {}

  params.forEach((value, key) => {
    query[key] = value
  })

  return query
}

function syncRoute() {
  const fallbackPath = routeLoaders[window.location.pathname] ? window.location.pathname : "/"

  if (!canEnterRoute(fallbackPath)) {
    redirectToLogin()
    return
  }

  route.path = fallbackPath
  route.fullPath = `${window.location.pathname}${window.location.search}${window.location.hash}`
  route.query = parseQuery(window.location.search)

  void loadRoute(fallbackPath)
}

async function loadRoute(path: string) {
  const loader = routeLoaders[path] ?? routeLoaders["/"]
  const module = await loader()
  activeComponent.value = module.default
}

function normalizeTarget(to: string) {
  if (to.startsWith("http")) {
    const url = new URL(to)
    return `${url.pathname}${url.search}${url.hash}`
  }

  return to || "/"
}

function getTargetPath(target: string) {
  return new URL(target, window.location.origin).pathname
}

function getCurrentFullPath() {
  return `${window.location.pathname}${window.location.search}${window.location.hash}` || "/"
}

function canEnterRoute(path: string) {
  return !protectedRoutes.has(path) || !!getStoredAuthUser()
}

function redirectToLogin(from = getCurrentFullPath()) {
  window.alert("请先登录后再使用转换功能。")
  window.history.replaceState(
    { from },
    "",
    `/login?redirect=${encodeURIComponent(from)}`,
  )
  route.path = "/login"
  route.fullPath = `${window.location.pathname}${window.location.search}${window.location.hash}`
  route.query = parseQuery(window.location.search)
  void loadRoute("/login")
}

export const router = {
  install(app: VueApp) {
    app.component("RouterView", RouterView)
    app.component("RouterLink", RouterLink)

    window.addEventListener("popstate", syncRoute)
    syncRoute()
  },

  async push(to: string) {
    const target = normalizeTarget(to)
    const targetPath = getTargetPath(target)
    const from = route.fullPath || `${window.location.pathname}${window.location.search}${window.location.hash}`

    if (!canEnterRoute(targetPath)) {
      redirectToLogin(target)
      await Promise.resolve()
      return
    }

    window.history.pushState({ from }, "", target)
    syncRoute()
    await Promise.resolve()
  },
}

export function useRouter() {
  return router
}

export function useRoute() {
  return route
}

export const RouterView = defineComponent({
  name: "RouterView",
  setup() {
    return () => (activeComponent.value ? h(activeComponent.value) : null)
  },
})

export const RouterLink = defineComponent({
  name: "RouterLink",
  props: {
    to: {
      type: String,
      required: true,
    },
  },
  setup(props, { slots, attrs }) {
    const href = computed(() => props.to)

    const navigate = (event: MouseEvent) => {
      const originalOnClick = attrs.onClick

      if (typeof originalOnClick === "function") {
        originalOnClick(event)
      } else if (Array.isArray(originalOnClick)) {
        originalOnClick.forEach((handler) => {
          if (typeof handler === "function") {
            handler(event)
          }
        })
      }

      if (event.defaultPrevented) return

      event.preventDefault()
      void router.push(props.to)
    }

    return () =>
      {
        const isActive = route.path === normalizeTarget(props.to)
        const classNames = [attrs.class, isActive ? "is-active" : null]

        return h(
          "a",
          {
            ...attrs,
            class: classNames,
            href: href.value,
            "aria-current": isActive ? "page" : undefined,
            onClick: navigate,
          },
          slots.default?.(),
        )
      }
  },
})
