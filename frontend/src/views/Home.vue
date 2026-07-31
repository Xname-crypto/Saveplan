<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue"
import {
  ArrowRight,
  BookOpenCheck,
  BrainCircuit,
  CheckCircle2,
  FileText,
  Layers3,
  PenLine,
  Sparkles,
  TimerReset,
  UploadCloud,
} from "lucide-vue-next"
import AppFooter from "@/components/AppFooter.vue"
import BorderGlow from "@/components/BorderGlow.vue"
import CinematicNav from "@/components/CinematicNav.vue"
import DecryptedText from "@/components/DecryptedText.vue"
import InfiniteMovingCards from "@/components/InfiniteMovingCards.vue"
import LineSidebar from "@/components/LineSidebar.vue"
import LightRays from "@/components/LightRays.vue"
import LogoLoop from "@/components/LogoLoop.vue"
import TiltedCard from "@/components/TiltedCard.vue"
import { useTheme } from "@/services/theme"
import { VIDEO_ASSETS } from "@/services/videoAssets"

const videoReady = ref(false)
const pageRoot = ref<HTMLElement | null>(null)
const revealRoot = ref<HTMLElement | null>(null)
const { theme } = useTheme()
let revealObserver: IntersectionObserver | null = null
let scrollFrame = 0
const heroVideoSrc = computed(() =>
  theme.value === "day" ? VIDEO_ASSETS.homeHeroDay : VIDEO_ASSETS.homeHero,
)
const heroPosterSrc = computed(() => (theme.value === "day" ? "" : VIDEO_ASSETS.homeHeroPoster))
const isDayTheme = computed(() => theme.value === "day")
const homeGlowColor = computed(() => (isDayTheme.value ? "204 54 39" : "46 88 78"))
const homeGlowIntensity = computed(() => (isDayTheme.value ? 1.1 : 1.75))
const homeGlowRadius = computed(() => (isDayTheme.value ? 42 : 58))
const aboutRayColor = computed(() => (isDayTheme.value ? "#345d75" : "#d6c58d"))
const aboutRayOpacity = computed(() => (isDayTheme.value ? 0.22 : 0.95))
const logoLoopFadeColor = computed(() => (isDayTheme.value ? "#f8faf7" : "#090909"))
const heroSidebarAccentColor = computed(() => (isDayTheme.value ? "#345d75" : "#d6c58d"))
const heroSidebarTextColor = computed(() =>
  isDayTheme.value ? "rgba(31, 41, 51, 0.64)" : "rgba(235, 228, 207, 0.58)",
)
const heroSidebarMarkerColor = computed(() =>
  isDayTheme.value ? "rgba(52, 93, 117, 0.28)" : "rgba(235, 228, 207, 0.28)",
)
const heroSidebarItems = ["上传资料", "AI 拆题", "校对修正", "导出复习"]

const aboutText =
  "无论是复杂排版、文字图片混合还是手写公式，我们都致力于为你带来前所未有的转换体验。上传你的文件，亲眼见证从混乱到有序的蜕变。无论是复杂排版、文字图片混合还是手写公式，我们都致力于为你带来前所未有的转换体验。上传你的文件，亲眼见证从混乱到有序的蜕变。无论是复杂排版、文字图片混合还是手写公式，我们都致力于为你带来前所未有的转换体验。上传你的文件，亲眼见证从混乱到有序的蜕变。"

const features = [
  {
    title: "智能转换 (01)",
    items: ["精准识别复杂公式", "支持多种文档格式", "AI 结构化排版", "保留原始逻辑结构"],
  },
  {
    title: "在线校对 (02)",
    items: ["双栏实时对比", "智能纠错建议", "一键批量修改", "云端自动保存"],
  },
  {
    title: "多端导出 (03)",
    items: ["Anki 卡片转换", "结构化 PDF 导出", "Markdown 格式支持", "适配刷题软件"],
  },
]

const steps = [
  {
    title: "上传资料",
    description: "拖入试卷、讲义、图片或 Word 文档，把混乱材料集中到一个转换工作台。",
    icon: UploadCloud,
  },
  {
    title: "AI 拆题",
    description: "自动拆分题干、选项、答案和解析，并把复杂排版整理成可编辑结构。",
    icon: Sparkles,
  },
  {
    title: "导出复习",
    description: "导出 Markdown、PDF 或记忆卡片格式，把时间还给真正的复习。",
    icon: FileText,
  },
]

const scenes = [
  {
    label: "INPUT",
    title: "混合资料",
    description: "试卷截图、讲义段落、手写公式和答案解析被集中到一个入口。",
    lines: ["IMG_2048.JPG", "线性代数 Week 08.pdf", "错题笔记.docx"],
  },
  {
    label: "PARSE",
    title: "结构识别",
    description: "AI 自动拆分题干、选项、答案与解析，并保留题目之间的层级。",
    lines: ["题干 12 条", "选项 48 项", "解析 9 段"],
  },
  {
    label: "OUTPUT",
    title: "复习资产",
    description: "把杂乱内容变成可编辑、可导出、可复用的学习材料。",
    lines: ["Markdown", "PDF", "Anki Cards"],
  },
]

const outcomes = [
  {
    value: "72%",
    label: "整理时间下降",
    icon: TimerReset,
  },
  {
    value: "3.4x",
    label: "刷题准备提速",
    icon: BrainCircuit,
  },
  {
    value: "24h",
    label: "资料云端留存",
    icon: BookOpenCheck,
  },
]

const userComments = [
  {
    quote: "期末前两天把整本错题截图丢进去，题干和解析分得很清楚，我终于不用一张张图手动抄题了。",
    name: "林同学",
    title: "大二 / 高数复习",
    avatar: "/stitch/avatar-lin.svg",
  },
  {
    quote: "最有用的是导出 Markdown，老师发的 PDF 讲义可以快速整理成自己的复习提纲，后面补笔记很顺。",
    name: "Mia",
    title: "考研备考 / 专业课",
    avatar: "/stitch/avatar-mia.svg",
  },
  {
    quote: "以前整理 Anki 卡片要花一整晚，现在先让系统拆题，我只负责校对重点，节奏轻了很多。",
    name: "陈同学",
    title: "医学生 / 记忆卡片",
    avatar: "/stitch/avatar-chen.svg",
  },
  {
    quote: "手写公式识别比我预期稳定，至少不用再对着照片一点点排版，复习时间真的省出来了。",
    name: "Jason",
    title: "工科 / 公式资料",
    avatar: "/stitch/avatar-jason.svg",
  },
  {
    quote: "我最喜欢对照校对那一步，混乱的扫描件变成结构化内容后，漏掉的题目很容易被发现。",
    name: "周同学",
    title: "高中冲刺 / 试卷整理",
    avatar: "/stitch/avatar-zhou.svg",
  },
]

const logoLoopItems = [
  { label: "AI PARSE", icon: Sparkles },
  { label: "PDF", icon: FileText },
  { label: "MARKDOWN", icon: PenLine },
  { label: "ANKI", icon: BookOpenCheck },
  { label: "OCR", icon: Layers3 },
  { label: "FORMULA", icon: BrainCircuit },
  { label: "CLOUD SYNC", icon: UploadCloud },
]

function handleVideoReady() {
  videoReady.value = true
}

watch(heroVideoSrc, () => {
  videoReady.value = false
})

function updateScrollMotion() {
  scrollFrame = 0

  const root = pageRoot.value
  if (!root) return

  const maxScroll = Math.max(1, document.documentElement.scrollHeight - window.innerHeight)
  const progress = Math.min(1, Math.max(0, window.scrollY / maxScroll))
  const heroShift = Math.min(90, window.scrollY * 0.12)
  const studioShift = Math.sin(progress * Math.PI) * 28

  root.style.setProperty("--home-scroll-progress", progress.toFixed(4))
  root.style.setProperty("--home-hero-shift", `${heroShift.toFixed(2)}px`)
  root.style.setProperty("--home-studio-shift", `${studioShift.toFixed(2)}px`)
}

function requestScrollMotion() {
  if (scrollFrame) return
  scrollFrame = window.requestAnimationFrame(updateScrollMotion)
}

onMounted(() => {
  const revealItems = Array.from(
    revealRoot.value?.querySelectorAll<HTMLElement>(".stitch-reveal") ?? [],
  )

  if (!("IntersectionObserver" in window)) {
    revealItems.forEach((item) => item.classList.add("is-visible"))
  } else if (revealItems.length) {
    revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return
          entry.target.classList.add("is-visible")
          revealObserver?.unobserve(entry.target)
        })
      },
      {
        rootMargin: "0px 0px -14% 0px",
        threshold: 0.16,
      },
    )

    revealItems.forEach((item) => revealObserver?.observe(item))
  }

  updateScrollMotion()
  window.addEventListener("scroll", requestScrollMotion, { passive: true })
  window.addEventListener("resize", requestScrollMotion)
})

onBeforeUnmount(() => {
  revealObserver?.disconnect()
  revealObserver = null
  window.removeEventListener("scroll", requestScrollMotion)
  window.removeEventListener("resize", requestScrollMotion)

  if (scrollFrame) {
    window.cancelAnimationFrame(scrollFrame)
    scrollFrame = 0
  }
})
</script>

<template>
  <div ref="pageRoot" class="stitch-page home-page">
    <CinematicNav />
    <div class="stitch-noise" />
    <div class="home-scroll-progress" aria-hidden="true" />

    <section class="home-hero">
      <div class="home-hero__frame">
        <img
          v-if="heroPosterSrc"
          class="home-hero__poster"
          :src="heroPosterSrc"
          alt="电影感学习空间"
          fetchpriority="high"
        />
        <video
          :key="heroVideoSrc"
          aria-hidden="true"
          autoplay
          loop
          muted
          playsinline
          preload="metadata"
          :class="['home-hero__video', { 'is-ready': videoReady }]"
          :poster="heroPosterSrc"
          @canplay="handleVideoReady"
          @loadeddata="handleVideoReady"
          @playing="handleVideoReady"
        >
          <source :src="heroVideoSrc" type="video/mp4" />
        </video>
        <div class="home-hero__shade" />
        <LineSidebar
          class-name="home-hero__line-sidebar"
          :items="heroSidebarItems"
          :accent-color="heroSidebarAccentColor"
          :text-color="heroSidebarTextColor"
          :marker-color="heroSidebarMarkerColor"
          :default-active="1"
          :proximity-radius="96"
          :max-shift="22"
          :marker-length="58"
          :marker-gap="12"
          :item-gap="18"
          :font-size="0.76"
          falloff="smooth"
        />

        <div class="home-hero__content">
          <div>
            <p class="stitch-eyebrow">CINEMATIC AI STUDY FLOW</p>
            <h1>在方寸之间，<br />让效率起航。</h1>
          </div>
          <aside>
            <p>
              我们相信，每个备考的人都值得更高效的学习方式。海量试卷和资料不该成为负担，而应该成为你前进的燃料。
            </p>
            <RouterLink class="hero-cta" to="/convert">
              立即开始
              <ArrowRight :size="20" />
            </RouterLink>
          </aside>
        </div>
      </div>
    </section>

    <main ref="revealRoot">
      <section id="about" class="home-about">
        <div class="home-about__layout">
          <div class="home-about__panel stitch-reveal">
            <LightRays
              class="home-about__rays"
              rays-origin="top-center"
              :rays-color="aboutRayColor"
              :rays-speed="isDayTheme ? 0.38 : 0.62"
              :light-spread="isDayTheme ? 1.04 : 0.78"
              :ray-length="isDayTheme ? 1.05 : 1.45"
              :fade-distance="isDayTheme ? 0.84 : 1.1"
              :saturation="isDayTheme ? 0.48 : 0.86"
              :follow-mouse="true"
              :mouse-influence="isDayTheme ? 0.03 : 0.08"
              :noise-amount="isDayTheme ? 0 : 0.18"
              :distortion="isDayTheme ? 0.04 : 0.22"
              :style="{ opacity: aboutRayOpacity }"
              pulsating
            />
            <p class="stitch-eyebrow">ABOUT US</p>
            <h2>从混乱到有序，<span>重塑你的学习边界。</span></h2>
            <DecryptedText
              :text="aboutText"
              :speed="isDayTheme ? 16 : 28"
              :sequential="true"
              :use-original-chars-only="!isDayTheme"
              characters="学习效率转换题库AI0123456789"
              reveal-direction="start"
              animate-on="view"
              parent-class-name="home-about__copy"
              encrypted-class-name="home-about__copy-char--encrypted"
            />
          </div>

          <aside class="home-about__preview stitch-reveal stitch-delay-1">
            <div class="hero-preview-card hero-preview-card--about" aria-label="AI conversion preview">
              <span class="hero-preview-card__icon" aria-hidden="true">
                <FileText :size="34" />
                <Sparkles :size="16" />
              </span>

              <div class="hero-preview-card__body">
                <span class="hero-preview-card__status">
                  <i />
                  AI 正在整理
                </span>
                <h2>把混乱资料变成复习卡片</h2>
                <p>
                  上传试卷、截图或手写公式，自动拆分题干、选项、答案和解析。
                </p>

                <div class="hero-preview-card__flow" aria-hidden="true">
                  <span>PDF 试卷</span>
                  <span>OCR</span>
                  <span>Anki</span>
                </div>
              </div>

              <RouterLink class="hero-preview-card__link" to="/convert">查看转换流程</RouterLink>
              <RouterLink class="hero-preview-card__action" to="/convert">
                立即开始
                <ArrowRight :size="15" />
              </RouterLink>
            </div>
          </aside>
        </div>
      </section>

      <section class="home-process">
        <div class="home-section-heading stitch-reveal">
          <p class="stitch-eyebrow">WORKFLOW</p>
          <h2>三个步骤，重塑学习流。</h2>
        </div>

        <div class="home-process__grid">
          <TiltedCard
            v-for="(step, index) in steps"
            :key="step.title"
            :class="['stitch-reveal', `stitch-delay-${index + 1}`]"
            :rotate-amplitude="9"
            :scale-on-hover="1.025"
          >
            <article class="process-card">
              <component :is="step.icon" :size="30" />
              <span>0{{ index + 1 }}</span>
              <h3>{{ step.title }}</h3>
              <p>{{ step.description }}</p>
            </article>
          </TiltedCard>
        </div>
      </section>

      <section class="home-logo-loop stitch-reveal" aria-label="Supported study formats">
        <LogoLoop
          :logos="logoLoopItems"
          :speed="88"
          :logo-height="34"
          :gap="18"
          :hover-speed="18"
          fade-out
          :fade-out-color="logoLoopFadeColor"
          scale-on-hover
          aria-label="Supported study formats"
        />
      </section>

      <section class="home-features">
        <div class="home-section-heading stitch-reveal">
          <p class="stitch-eyebrow">CORE FUNCTIONS</p>
          <h2>专为高效学习者打造的智能工具。</h2>
        </div>

        <div class="feature-mosaic">
          <article class="feature-video stitch-reveal">
            <img src="/stitch/asset-01.jpg" alt="抽象电影感背景" loading="lazy" />
            <video autoplay loop muted playsinline preload="metadata">
              <source src="/stitch/asset-04.mp4" type="video/mp4" />
            </video>
            <span>极简上传，即刻解析。</span>
          </article>

          <BorderGlow
            v-for="(feature, index) in features"
            :key="feature.title"
            as="article"
            :class-name="['feature-card stitch-reveal', `stitch-delay-${index + 1}`]"
            :animated="true"
            :glow-color="homeGlowColor"
            :glow-intensity="homeGlowIntensity"
            :glow-radius="homeGlowRadius"
          >
            <PenLine :size="34" />
            <h3>{{ feature.title }}</h3>
            <ul>
              <li v-for="item in feature.items" :key="item">
                <CheckCircle2 :size="17" />
                {{ item }}
              </li>
            </ul>
            <span class="feature-card__link-spacer" aria-hidden="true">
              了解更多
              <ArrowRight :size="16" />
            </span>
          </BorderGlow>
        </div>
      </section>

      <section class="home-studio">
        <div class="home-section-heading stitch-reveal">
          <p class="stitch-eyebrow">LIVE CONVERSION</p>
          <h2>一次上传，看见资料被重新编排。</h2>
        </div>

        <div class="studio-board stitch-reveal stitch-delay-1">
          <div class="studio-board__rail" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>

          <article
            v-for="(scene, index) in scenes"
            :key="scene.label"
            :class="['studio-card', `studio-card--${index + 1}`]"
          >
            <p>{{ scene.label }}</p>
            <h3>{{ scene.title }}</h3>
            <span>{{ scene.description }}</span>
            <ul>
              <li v-for="line in scene.lines" :key="line">
                <Layers3 :size="15" />
                {{ line }}
              </li>
            </ul>
          </article>
        </div>
      </section>

      <section class="home-outcomes">
        <div class="home-section-heading home-outcomes__heading stitch-reveal">
          <p class="stitch-eyebrow">RESULTS</p>
          <h2>看得见的整理效率。</h2>
        </div>

        <BorderGlow
          as="div"
          class-name="outcome-copy stitch-reveal"
          :animated="true"
          :glow-color="homeGlowColor"
          :glow-intensity="homeGlowIntensity"
          :glow-radius="homeGlowRadius"
        >
          <p class="stitch-eyebrow">RESULTS</p>
          <h2>把零散时间，<br />还给真正的复习。</h2>
          <p>
            Save Your Finals 不只是把文件换一种格式，而是把备考流程里最耗神的整理、校对和导出拆掉，让你在截止日前保留清醒的节奏。
          </p>
          <RouterLink class="hero-cta" to="/convert">
            打开转换台
            <ArrowRight :size="20" />
          </RouterLink>
        </BorderGlow>

        <div class="outcome-grid">
          <BorderGlow
            v-for="(outcome, index) in outcomes"
            :key="outcome.label"
            as="article"
            :class-name="['outcome-card stitch-reveal', `stitch-delay-${index + 1}`]"
            :animated="true"
            :glow-color="homeGlowColor"
            :glow-intensity="homeGlowIntensity"
            :glow-radius="homeGlowRadius"
          >
            <component :is="outcome.icon" :size="28" />
            <strong>{{ outcome.value }}</strong>
            <span>{{ outcome.label }}</span>
          </BorderGlow>
        </div>
      </section>

      <section class="home-testimonials">
        <div class="home-section-heading home-testimonials__heading stitch-reveal">
          <p class="stitch-eyebrow">USER REVIEWS</p>
          <h2>使用后的真实反馈。</h2>
        </div>

        <div class="home-testimonials__marquee stitch-reveal stitch-delay-1">
          <InfiniteMovingCards
            :items="userComments"
            direction="left"
            speed="normal"
            aria-label="User comments"
          />
        </div>
      </section>
    </main>

    <AppFooter />
  </div>
</template>
