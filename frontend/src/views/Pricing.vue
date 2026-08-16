<script setup lang="ts">
import { computed, ref } from "vue"
import { CheckCircle2, ChevronUp } from "lucide-vue-next"
import AppFooter from "@/components/AppFooter.vue"
import BorderGlow from "@/components/BorderGlow.vue"
import CinematicNav from "@/components/CinematicNav.vue"
import TargetCursor from "@/components/TargetCursor.vue"
import { useRouter } from "@/router"
import { plans, type PlanDefinition } from "@/services/planCatalog"
import { useTheme } from "@/services/theme"

const faqs = [
  {
    q: "支持哪些格式的试卷上传？",
    a: "支持 PDF、Word、高清图片和扫描件。系统会自动处理倾斜、阴影和分页。",
  },
  {
    q: "解析后的题库可以直接导出吗？",
    a: "可以导出为 Markdown、结构化 PDF 或 Anki 友好格式，后续也能继续扩展到更多刷题 App。",
  },
  {
    q: "我的试卷资料会不会泄露？",
    a: "正式接入支付和订单后，用户资料会继续沿用已有的数据库与存储权限控制。",
  },
  {
    q: "套餐可以随时升级或取消吗？",
    a: "可以。你可以根据备考强度调整套餐，升级后立即解锁对应额度和功能。",
  },
  {
    q: "免费额度用完后怎么办？",
    a: "免费额度用完后可以等待次日刷新，也可以升级到更高套餐获得更多转换次数和导出能力。",
  },
  {
    q: "导出的内容可以继续编辑吗？",
    a: "可以。导出的 Markdown、结构化 PDF 和 Anki 友好格式都保留清晰层级，方便继续整理、标注和复习。",
  },
]

const router = useRouter()
const selectedPlan = ref<string | null>(null)
const openFaqIndex = ref<number | null>(null)
const { theme } = useTheme()
const isDayTheme = computed(() => theme.value === "day")
const quoteImageSrc = computed(() =>
  isDayTheme.value ? "/stitch/format-comparison.png" : "/stitch/asset-05.jpg",
)
const quoteImageAlt = computed(() =>
  isDayTheme.value ? "结构化转换界面预览" : "午夜图书馆学习场景",
)

function getPlanClasses(plan: PlanDefinition, index: number) {
  return [
    "pricing-card",
    "stitch-reveal",
    "cursor-target",
    `stitch-delay-${index + 1}`,
    plan.featured ? "is-featured" : "",
    selectedPlan.value === plan.id ? "is-selected" : "",
  ].filter(Boolean)
}

function getFeaturedPlanProps(plan: PlanDefinition, index: number) {
  const isSelected = selectedPlan.value === plan.id

  return {
    className: getPlanClasses(plan, index),
    animated: true,
    backgroundColor: isDayTheme.value
      ? isSelected
        ? "linear-gradient(145deg, rgba(238, 247, 246, 0.98), #ffffff)"
        : "linear-gradient(145deg, rgba(255, 255, 255, 0.96), rgba(247, 251, 250, 0.9))"
      : isSelected
        ? "rgba(45, 42, 36, 0.9)"
        : "#111",
    glowColor: isDayTheme.value ? "204 54 39" : "46 88 78",
    glowIntensity: isDayTheme.value ? 1.08 : 1.75,
    glowRadius: isDayTheme.value ? 44 : 58,
  }
}

function selectPlan(planId: string) {
  selectedPlan.value = planId
}

function clearSelectedPlan() {
  selectedPlan.value = null
}

function continueWithPlan(plan: PlanDefinition) {
  if (!plan.purchasable) {
    void router.push("/convert")
    return
  }

  void router.push(`/checkout?plan=${encodeURIComponent(plan.id)}`)
}

function toggleFaq(index: number) {
  openFaqIndex.value = openFaqIndex.value === index ? null : index
}
</script>

<template>
  <div class="stitch-page pricing-page" @click="clearSelectedPlan">
    <CinematicNav />
    <div class="stitch-noise" />
    <TargetCursor
      target-selector=".pricing-page .cursor-target"
      :spin-duration="2"
      :hover-duration="0.18"
      :hide-default-cursor="true"
      :parallax-on="true"
    />

    <main class="pricing-shell">
      <section class="pricing-hero stitch-reveal">
        <p class="stitch-eyebrow">CINEMATIC PRICING</p>
        <h1>选择你的抢救方案</h1>
        <p>
          为不同阶段的备考者量身定制。从临时整理资料，到高频刷题复盘，让期末不再是一场混乱的追赶。
        </p>
      </section>

      <section class="pricing-grid">
        <component
          :is="plan.featured ? BorderGlow : 'article'"
          v-for="(plan, index) in plans"
          :key="plan.id"
          as="article"
          v-bind="plan.featured
            ? getFeaturedPlanProps(plan, index)
            : {
                class: getPlanClasses(plan, index),
              }"
          @click.stop="selectPlan(plan.id)"
        >
          <span v-if="plan.featured" class="pricing-card__badge">推荐</span>
          <p>{{ plan.label }}</p>
          <h2>{{ plan.name }}</h2>
          <div class="pricing-card__price">
            <strong>{{ plan.price }}</strong>
            <span>{{ plan.period }}</span>
          </div>
          <ul>
            <li v-for="feature in plan.features" :key="feature">
              <CheckCircle2 :size="18" />
              {{ feature }}
            </li>
          </ul>
          <button type="button" class="cursor-target" @click.stop="continueWithPlan(plan)">
            {{ plan.cta }}
          </button>
        </component>
      </section>

      <section class="pricing-faq stitch-reveal stitch-delay-2">
        <div class="pricing-faq__header">
          <p class="stitch-eyebrow">CINEMATIC FAQ</p>
          <h2>常见问题解答</h2>
          <p>
            我们随时准备解答你的任何问题。如果找不到所需资料，请通过
            <a href="mailto:support@example.com">support@example.com</a>
            联系我们。
          </p>
        </div>
        <div class="pricing-faq__list">
          <article
            v-for="(item, index) in faqs"
            :key="item.q"
            :class="['cursor-target', { 'is-open': openFaqIndex === index }]"
          >
            <button
              type="button"
              class="pricing-faq__question"
              :aria-expanded="openFaqIndex === index"
              @click.stop="toggleFaq(index)"
            >
              <ChevronUp :size="19" stroke-width="2.4" />
              <span>{{ item.q }}</span>
            </button>
            <p v-show="openFaqIndex === index">{{ item.a }}</p>
          </article>
        </div>
      </section>

      <section class="pricing-quote">
        <img :src="quoteImageSrc" :alt="quoteImageAlt" loading="lazy" />
        <div />
        <p>“在最后的时限到来之前，为你的学术理想注入最后一束光。”</p>
      </section>
    </main>
    <AppFooter />
  </div>
</template>
