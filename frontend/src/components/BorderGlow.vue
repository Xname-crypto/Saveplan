<script setup lang="ts">
import { computed, ref, useTemplateRef, watch } from "vue"

type GlowClass = string | string[] | Record<string, boolean> | Array<string | Record<string, boolean>>

interface BorderGlowProps {
  as?: string
  className?: GlowClass
  edgeSensitivity?: number
  glowColor?: string
  backgroundColor?: string
  borderRadius?: number | null
  glowRadius?: number
  glowIntensity?: number
  coneSpread?: number
  animated?: boolean
  colors?: string[]
  fillOpacity?: number
}

function parseHSL(hslStr: string): { h: number; s: number; l: number } {
  const match = hslStr.match(/([\d.]+)\s*([\d.]+)%?\s*([\d.]+)%?/)
  if (!match) return { h: 40, s: 80, l: 80 }
  return { h: parseFloat(match[1]), s: parseFloat(match[2]), l: parseFloat(match[3]) }
}

function buildBoxShadow(glowColor: string, intensity: number): string {
  const { h, s, l } = parseHSL(glowColor)
  const base = `${h}deg ${s}% ${l}%`
  const layers: [number, number, number, number, number][] = [
    [0, 0, 2, 0, 90],
    [0, 0, 5, 0, 76],
    [0, 0, 11, 1, 58],
    [0, 0, 22, 2, 42],
    [0, 0, 38, 4, 28],
    [0, 0, 70, 8, 16],
  ]

  return layers
    .map(([x, y, blur, spread, alpha]) => {
      const a = Math.min(alpha * intensity, 100)
      return `${x}px ${y}px ${blur}px ${spread}px hsl(${base} / ${a}%)`
    })
    .join(", ")
}

function easeOutCubic(x: number) {
  return 1 - Math.pow(1 - x, 3)
}

function easeInCubic(x: number) {
  return x * x * x
}

function animateValue({
  start = 0,
  end = 100,
  duration = 1000,
  delay = 0,
  ease = easeOutCubic,
  onUpdate,
  onEnd,
}: {
  start?: number
  end?: number
  duration?: number
  delay?: number
  ease?: (t: number) => number
  onUpdate: (value: number) => void
  onEnd?: () => void
}) {
  const startTime = performance.now() + delay

  function tick() {
    const elapsed = performance.now() - startTime
    const t = Math.min(elapsed / duration, 1)
    onUpdate(start + (end - start) * ease(t))

    if (t < 1) {
      requestAnimationFrame(tick)
      return
    }

    onEnd?.()
  }

  window.setTimeout(() => requestAnimationFrame(tick), delay)
}

const props = withDefaults(defineProps<BorderGlowProps>(), {
  as: "div",
  className: "",
  edgeSensitivity: 16,
  glowColor: "46 88 78",
  backgroundColor: "#111",
  borderRadius: null,
  glowRadius: 58,
  glowIntensity: 1.75,
  coneSpread: 25,
  animated: false,
  colors: () => ["#c084fc", "#f472b6", "#38bdf8"],
  fillOpacity: 0.5,
})

const cardRef = useTemplateRef<HTMLElement>("cardRef")
const isHovered = ref(false)
const cursorAngle = ref(45)
const edgeProximity = ref(0)
const sweepActive = ref(false)

const getCenterOfElement = (el: HTMLElement) => {
  const { width, height } = el.getBoundingClientRect()
  return [width / 2, height / 2]
}

const getEdgeProximity = (el: HTMLElement, x: number, y: number) => {
  const [centerX, centerY] = getCenterOfElement(el)
  const dx = x - centerX
  const dy = y - centerY
  const edgeX = dx === 0 ? Infinity : centerX / Math.abs(dx)
  const edgeY = dy === 0 ? Infinity : centerY / Math.abs(dy)
  return Math.min(Math.max(1 / Math.min(edgeX, edgeY), 0), 1)
}

const getCursorAngle = (el: HTMLElement, x: number, y: number) => {
  const [centerX, centerY] = getCenterOfElement(el)
  const dx = x - centerX
  const dy = y - centerY
  if (dx === 0 && dy === 0) return 0

  let degrees = Math.atan2(dy, dx) * (180 / Math.PI) + 90
  if (degrees < 0) degrees += 360
  return degrees
}

const handlePointerMove = (event: PointerEvent) => {
  const card = cardRef.value
  if (!card) return

  const rect = card.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  edgeProximity.value = getEdgeProximity(card, x, y)
  cursorAngle.value = getCursorAngle(card, x, y)
}

watch(
  () => props.animated,
  () => {
    if (!props.animated || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return

    const angleStart = 110
    const angleEnd = 465
    sweepActive.value = true
    cursorAngle.value = angleStart

    animateValue({ duration: 500, onUpdate: (value) => (edgeProximity.value = value / 100) })
    animateValue({
      ease: easeInCubic,
      duration: 1500,
      end: 50,
      onUpdate: (value) => {
        cursorAngle.value = (angleEnd - angleStart) * (value / 100) + angleStart
      },
    })
    animateValue({
      ease: easeOutCubic,
      delay: 1500,
      duration: 2250,
      start: 50,
      end: 100,
      onUpdate: (value) => {
        cursorAngle.value = (angleEnd - angleStart) * (value / 100) + angleStart
      },
    })
    animateValue({
      ease: easeInCubic,
      delay: 2500,
      duration: 1500,
      start: 100,
      end: 0,
      onUpdate: (value) => (edgeProximity.value = value / 100),
      onEnd: () => (sweepActive.value = false),
    })
  },
  { immediate: true },
)

const isVisible = computed(() => isHovered.value || sweepActive.value)
const glowOpacity = computed(() =>
  isVisible.value
    ? Math.max(0, (edgeProximity.value * 100 - props.edgeSensitivity) / (100 - props.edgeSensitivity))
    : 0,
)

const angle = computed(() => `${cursorAngle.value.toFixed(3)}deg`)
const glowHsl = computed(() => {
  const { h, s, l } = parseHSL(props.glowColor)
  return `${h}deg ${s}% ${l}%`
})
const rimInset = computed(() => `${Math.max(2, Math.round(props.glowRadius * 0.045))}px`)
const radiusStyle = computed(() => (props.borderRadius === null ? undefined : `${props.borderRadius}px`))
</script>

<template>
  <component
    :is="props.as"
    ref="cardRef"
    :class="['border-glow-card', props.className]"
    :style="{
      background: props.backgroundColor,
      borderRadius: radiusStyle,
      transform: 'translate3d(0, 0, 0.01px)',
    }"
    @pointermove="handlePointerMove"
    @pointerenter="isHovered = true"
    @pointerleave="isHovered = false"
  >
    <span
      class="border-glow-card__rim"
      :style="{
        inset: `-${rimInset}`,
        padding: rimInset,
        background: `conic-gradient(from ${angle}, transparent 0deg, hsl(${glowHsl} / 0.92) 34deg, hsl(${glowHsl} / 0.78) 58deg, transparent 92deg, transparent 360deg)`,
        opacity: glowOpacity,
        transition: isVisible ? 'opacity 0.2s ease-out' : 'opacity 0.65s ease-in-out',
      }"
    />

    <span
      class="border-glow-card__outer"
      :style="{
        inset: `-${props.glowRadius}px`,
        padding: `${props.glowRadius}px`,
        maskImage: `conic-gradient(from ${angle} at center, black 2.5%, transparent 10%, transparent 90%, black 97.5%)`,
        WebkitMaskImage: `conic-gradient(from ${angle} at center, black 2.5%, transparent 10%, transparent 90%, black 97.5%)`,
        opacity: glowOpacity,
        mixBlendMode: 'plus-lighter',
        transition: isVisible ? 'opacity 0.25s ease-out' : 'opacity 0.75s ease-in-out',
      }"
    >
      <span
        class="border-glow-card__outer-clip"
        :style="{
          boxShadow: buildBoxShadow(props.glowColor, props.glowIntensity),
        }"
      >
        <span class="border-glow-card__outer-core" />
      </span>
    </span>

    <slot />
  </component>
</template>

<style scoped>
.border-glow-card {
  position: relative;
  overflow: visible;
  isolation: isolate;
}

.border-glow-card__outer,
.border-glow-card__rim,
.border-glow-card__outer-clip,
.border-glow-card__outer-core {
  position: absolute;
  border-radius: inherit;
  pointer-events: none;
}

.border-glow-card__rim {
  box-sizing: border-box;
  z-index: 0;
  -webkit-mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  mask-composite: exclude;
}

.border-glow-card__outer {
  box-sizing: border-box;
  z-index: 0;
}

.border-glow-card__outer-clip {
  inset: 0;
  box-sizing: border-box;
  -webkit-mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  mask-composite: exclude;
}

.border-glow-card__outer-core {
  inset: 0;
  z-index: 0;
}
</style>
