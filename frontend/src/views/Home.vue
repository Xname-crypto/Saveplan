<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue"
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
import LightRays from "@/components/LightRays.vue"
import LogoLoop from "@/components/LogoLoop.vue"
import TiltedCard from "@/components/TiltedCard.vue"

const videoReady = ref(false)
const pageRoot = ref<HTMLElement | null>(null)
const revealRoot = ref<HTMLElement | null>(null)
let revealObserver: IntersectionObserver | null = null
let scrollFrame = 0
const heroVideoSrc = "/stitch/home-study-writing.mp4"

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
          class="home-hero__poster"
          src="/stitch/asset-02.jpg"
          alt="电影感学习空间"
          fetchpriority="high"
        />
        <video
          aria-hidden="true"
          autoplay
          loop
          muted
          playsinline
          preload="metadata"
          :class="['home-hero__video', { 'is-ready': videoReady }]"
          poster="/stitch/asset-02.jpg"
          @canplay="handleVideoReady"
          @loadeddata="handleVideoReady"
          @playing="handleVideoReady"
        >
          <source :src="heroVideoSrc" type="video/mp4" />
        </video>
        <div class="home-hero__shade" />

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
        <div class="home-about__panel stitch-reveal">
          <LightRays
            class="home-about__rays"
            rays-origin="top-center"
            rays-color="#d6c58d"
            :rays-speed="0.62"
            :light-spread="0.78"
            :ray-length="1.45"
            :fade-distance="1.1"
            :saturation="0.86"
            :follow-mouse="true"
            :mouse-influence="0.08"
            :noise-amount="0.18"
            :distortion="0.22"
            pulsating
          />
          <p class="stitch-eyebrow">ABOUT US</p>
          <h2>从混乱到有序，<span>重塑你的学习边界。</span></h2>
          <DecryptedText
            :text="aboutText"
            :speed="28"
            :sequential="true"
            :use-original-chars-only="true"
            reveal-direction="start"
            animate-on="view"
            parent-class-name="home-about__copy"
            encrypted-class-name="home-about__copy-char--encrypted"
          />
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
          fade-out-color="#090909"
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
