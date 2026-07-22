export const VIDEO_ASSETS = {
  homeHero:
    "https://pub-4bd1febbb65843fbab89f795d612e480.r2.dev/%E5%9B%BE%E7%89%87%E4%B8%AD%E7%9A%84%E4%BA%BA%E7%89%A9%E5%9C%A8%E5%86%99%E5%AD%97%E5%AD%A6%E4%B9%A0%EF%BC%8C%E5%9B%BA%E5%AE%9A%E6%9C%BA%E4%BD%8D%EF%BC%8C%E5%9B%BA%E5%AE%9A%E9%95%9C%E5%A4%B4%EF%BC%8C%E4%B8%8D%E8%A6%81%E8%BF%90%E5%8A%A8%E7%9B%B8%E6%9C%BA%EF%BC%8C%E9%AB%98%E8%B4%A8%E9%87%8F_202605250305.mp4",
  login:
    "https://pub-4bd1febbb65843fbab89f795d612e480.r2.dev/%E9%87%8D%E6%96%B0%E5%BC%80%E5%A7%8B2.mp4",
  register:
    "https://pub-4bd1febbb65843fbab89f795d612e480.r2.dev/%E3%80%90%E5%93%B2%E9%A3%8E%E5%A3%81%E7%BA%B8%E3%80%91%E4%BA%8C%E6%AC%A1%E5%85%83-%E5%8A%A8%E6%BC%AB.mp4",
  forgotPassword:
    "https://pub-4bd1febbb65843fbab89f795d612e480.r2.dev/%E3%80%90%E5%93%B2%E9%A3%8E%E5%A3%81%E7%BA%B8%E3%80%91%E4%B9%A6%E6%9C%AC-%E4%B9%A6%E6%A1%8C-%E4%BA%8C%E6%AC%A1%E5%85%83.mp4",
  homeHeroPoster: "/video/home-hero-poster.jpg",
  loginPoster: "/video/login-poster.jpg",
  registerPoster: "/video/register-poster.jpg",
  forgotPasswordPoster: "/video/forgot-password-poster.jpg",
  authPoster: "/video/auth-poster.jpeg",
} as const

const IMAGE_PRELOAD_ORDER = [
  VIDEO_ASSETS.homeHeroPoster,
  VIDEO_ASSETS.loginPoster,
  VIDEO_ASSETS.registerPoster,
  VIDEO_ASSETS.forgotPasswordPoster,
] as const

const VIDEO_PRELOAD_ORDER = [
  VIDEO_ASSETS.homeHero,
  VIDEO_ASSETS.login,
  VIDEO_ASSETS.register,
  VIDEO_ASSETS.forgotPassword,
] as const

const imagePreloadCache = new Map<string, Promise<void>>()
const preloadCache = new Map<string, Promise<void>>()
let queueStarted = false

function preloadImage(src: string): Promise<void> {
  if (!src || typeof window === "undefined") return Promise.resolve()

  const cached = imagePreloadCache.get(src)
  if (cached) return cached

  const promise = new Promise<void>((resolve) => {
    const image = new Image()
    image.onload = () => resolve()
    image.onerror = () => resolve()
    image.src = src
  })

  imagePreloadCache.set(src, promise)
  return promise
}

function preloadVideo(src: string, timeoutMs = 12000): Promise<void> {
  if (!src || typeof document === "undefined") return Promise.resolve()

  const cached = preloadCache.get(src)
  if (cached) return cached

  const promise = new Promise<void>((resolve) => {
    const video = document.createElement("video")
    let settled = false

    const finish = () => {
      if (settled) return
      settled = true
      video.removeAttribute("src")
      video.load()
      resolve()
    }

    window.setTimeout(finish, timeoutMs)
    video.muted = true
    video.playsInline = true
    video.preload = "auto"
    video.addEventListener("loadeddata", finish, { once: true })
    video.addEventListener("canplaythrough", finish, { once: true })
    video.addEventListener("error", finish, { once: true })
    video.src = src
    video.load()
  })

  preloadCache.set(src, promise)
  return promise
}

function scheduleIdle(callback: () => void) {
  if ("requestIdleCallback" in window) {
    window.requestIdleCallback(callback, { timeout: 3000 })
    return
  }

  globalThis.setTimeout(callback, 1200)
}

export function startVideoPreloadQueue() {
  if (queueStarted || typeof window === "undefined") return
  queueStarted = true

  scheduleIdle(() => {
    void Promise.all(IMAGE_PRELOAD_ORDER.map((src) => preloadImage(src))).finally(() => {
      void VIDEO_PRELOAD_ORDER.reduce(
        (previous, src) => previous.then(() => preloadVideo(src)),
        Promise.resolve(),
      )
    })
  })
}
