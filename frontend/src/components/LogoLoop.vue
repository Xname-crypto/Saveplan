<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch, type Component } from "vue"

export type LogoLoopItem =
  | string
  | {
      label: string
      icon?: Component
      title?: string
    }

const props = withDefaults(
  defineProps<{
    logos: LogoLoopItem[]
    speed?: number
    direction?: "left" | "right" | "up" | "down"
    logoHeight?: number
    gap?: number
    hoverSpeed?: number
    pauseOnHover?: boolean
    fadeOut?: boolean
    fadeOutColor?: string
    scaleOnHover?: boolean
    ariaLabel?: string
  }>(),
  {
    speed: 120,
    direction: "left",
    logoHeight: 28,
    gap: 32,
    hoverSpeed: undefined,
    pauseOnHover: undefined,
    fadeOut: false,
    fadeOutColor: "#090909",
    scaleOnHover: false,
    ariaLabel: "Partner logos",
  },
)

const minCopies = 2
const copyHeadroom = 2
const smoothTau = 0.25

const containerRef = ref<HTMLDivElement | null>(null)
const trackRef = ref<HTMLDivElement | null>(null)
const sequenceRef = ref<HTMLUListElement | null>(null)
const sequenceWidth = ref(0)
const sequenceHeight = ref(0)
const copyCount = ref(minCopies)
const isHovered = ref(false)

let animationFrame = 0
let lastTimestamp: number | null = null
let offset = 0
let velocity = 0
let resizeObserver: ResizeObserver | null = null

const isVertical = computed(() => props.direction === "up" || props.direction === "down")
const reverse = computed(() => props.direction === "right" || props.direction === "down")
const effectiveHoverSpeed = computed(() => {
  if (props.hoverSpeed !== undefined) return props.hoverSpeed
  if (props.pauseOnHover === false) return undefined
  return 0
})

const targetVelocity = computed(() => {
  const directionMultiplier = reverse.value ? -1 : 1
  const speedMultiplier = props.speed < 0 ? -1 : 1
  return Math.abs(props.speed) * directionMultiplier * speedMultiplier
})

const targetSpeed = computed(() =>
  isHovered.value && effectiveHoverSpeed.value !== undefined
    ? effectiveHoverSpeed.value * (reverse.value ? -1 : 1)
    : targetVelocity.value,
)

const rootStyle = computed(() => ({
  "--logo-loop-height": `${props.logoHeight}px`,
  "--logo-loop-gap": `${props.gap}px`,
  "--logo-loop-fade-color": props.fadeOutColor,
}))

function getLogoLabel(item: LogoLoopItem) {
  return typeof item === "string" ? item : item.label
}

function getLogoTitle(item: LogoLoopItem) {
  return typeof item === "string" ? item : item.title ?? item.label
}

function getLogoIcon(item: LogoLoopItem) {
  return typeof item === "string" ? undefined : item.icon
}

async function updateDimensions() {
  await nextTick()

  const container = containerRef.value
  const sequence = sequenceRef.value
  if (!container || !sequence) return

  const rect = sequence.getBoundingClientRect()
  const nextSequenceWidth = Math.ceil(rect.width)
  const nextSequenceHeight = Math.ceil(rect.height)

  if (isVertical.value && nextSequenceHeight > 0) {
    sequenceHeight.value = nextSequenceHeight
    copyCount.value = Math.max(minCopies, Math.ceil(container.clientHeight / nextSequenceHeight) + copyHeadroom)
  } else if (nextSequenceWidth > 0) {
    sequenceWidth.value = nextSequenceWidth
    copyCount.value = Math.max(minCopies, Math.ceil(container.clientWidth / nextSequenceWidth) + copyHeadroom)
  }
}

function applyTransform() {
  const track = trackRef.value
  if (!track) return

  track.style.transform = isVertical.value
    ? `translate3d(0, ${-offset}px, 0)`
    : `translate3d(${-offset}px, 0, 0)`
}

function tick(timestamp: number) {
  if (lastTimestamp === null) lastTimestamp = timestamp

  const delta = Math.min(0.05, Math.max(0, timestamp - lastTimestamp) / 1000)
  lastTimestamp = timestamp

  const sequenceSize = isVertical.value ? sequenceHeight.value : sequenceWidth.value
  if (sequenceSize > 0) {
    const easingFactor = 1 - Math.exp(-delta / smoothTau)
    velocity += (targetSpeed.value - velocity) * easingFactor
    offset = ((offset + velocity * delta) % sequenceSize + sequenceSize) % sequenceSize
    applyTransform()
  }

  animationFrame = window.requestAnimationFrame(tick)
}

function startLoop() {
  window.cancelAnimationFrame(animationFrame)
  lastTimestamp = null

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches
  if (reduceMotion) {
    offset = 0
    applyTransform()
    return
  }

  animationFrame = window.requestAnimationFrame(tick)
}

function handleMouseEnter() {
  if (effectiveHoverSpeed.value !== undefined) {
    isHovered.value = true
  }
}

function handleMouseLeave() {
  if (effectiveHoverSpeed.value !== undefined) {
    isHovered.value = false
  }
}

onMounted(async () => {
  await updateDimensions()

  resizeObserver = new ResizeObserver(() => {
    updateDimensions()
  })

  if (containerRef.value) resizeObserver.observe(containerRef.value)
  if (sequenceRef.value) resizeObserver.observe(sequenceRef.value)

  startLoop()
})

onBeforeUnmount(() => {
  window.cancelAnimationFrame(animationFrame)
  resizeObserver?.disconnect()
  resizeObserver = null
})

watch(
  () => [props.logos, props.gap, props.logoHeight, props.direction],
  async () => {
    await updateDimensions()
    const sequenceSize = isVertical.value ? sequenceHeight.value : sequenceWidth.value
    if (sequenceSize > 0) {
      offset = ((offset % sequenceSize) + sequenceSize) % sequenceSize
      applyTransform()
    }
  },
  { deep: true },
)
</script>

<template>
  <div
    ref="containerRef"
    :class="[
      'logo-loop',
      {
        'logo-loop--vertical': isVertical,
        'logo-loop--fade': fadeOut,
        'logo-loop--scale': scaleOnHover,
      },
    ]"
    :aria-label="ariaLabel"
    role="region"
    :style="rootStyle"
  >
    <div
      ref="trackRef"
      class="logo-loop__track"
      @mouseenter="handleMouseEnter"
      @mouseleave="handleMouseLeave"
    >
      <ul
        v-for="copyIndex in copyCount"
        :key="`copy-${copyIndex}`"
        :ref="(element) => {
          if (copyIndex === 1) sequenceRef = element as HTMLUListElement | null
        }"
        class="logo-loop__sequence"
        :aria-hidden="copyIndex > 1"
      >
        <li
          v-for="logo in logos"
          :key="`${copyIndex}-${getLogoLabel(logo)}`"
          class="logo-loop__item"
          :title="getLogoTitle(logo)"
        >
          <component
            :is="getLogoIcon(logo)"
            v-if="getLogoIcon(logo)"
            class="logo-loop__icon"
            :size="15"
            :stroke-width="2.2"
            aria-hidden="true"
          />
          <span>{{ getLogoLabel(logo) }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.logo-loop {
  position: relative;
  display: flex;
  width: 100%;
  overflow: hidden;
}

.logo-loop--vertical {
  height: calc(var(--logo-loop-height) * 5);
}

.logo-loop--fade {
  mask-image: linear-gradient(90deg, transparent, #000 15%, #000 85%, transparent);
}

.logo-loop--vertical.logo-loop--fade {
  mask-image: linear-gradient(180deg, transparent, #000 15%, #000 85%, transparent);
}

.logo-loop__track {
  position: relative;
  z-index: 0;
  display: flex;
  width: max-content;
  align-items: center;
  backface-visibility: hidden;
  transform: translate3d(0, 0, 0);
  will-change: transform;
}

.logo-loop--vertical .logo-loop__track,
.logo-loop--vertical .logo-loop__sequence {
  flex-direction: column;
  align-items: flex-start;
}

.logo-loop__sequence {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  margin: 0;
  padding: 0;
  list-style: none;
}

.logo-loop__item {
  display: inline-flex;
  flex: 0 0 auto;
  height: var(--logo-loop-height);
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  margin-right: var(--logo-loop-gap);
  border: 1px solid rgba(235, 228, 207, 0.12);
  border-radius: 999px;
  padding: 0 1rem;
  background: rgba(255, 255, 255, 0.035);
  color: rgba(235, 228, 207, 0.74);
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  line-height: 1;
  text-transform: uppercase;
  white-space: nowrap;
  transition:
    border-color 220ms ease,
    color 220ms ease,
    transform 220ms ease;
}

.logo-loop__icon {
  flex: 0 0 auto;
  color: rgba(214, 197, 141, 0.72);
  transition: color 220ms ease, transform 220ms ease;
}

.logo-loop--vertical .logo-loop__item {
  margin-right: 0;
  margin-bottom: var(--logo-loop-gap);
}

.logo-loop--scale .logo-loop__item:hover {
  border-color: rgba(214, 197, 141, 0.38);
  color: #f1ead5;
  transform: scale(1.06);
}

.logo-loop--scale .logo-loop__item:hover .logo-loop__icon {
  color: #f1ead5;
  transform: scale(1.08);
}

@media (prefers-reduced-motion: reduce) {
  .logo-loop {
    overflow: visible;
  }

  .logo-loop__track,
  .logo-loop__sequence {
    flex-wrap: wrap;
    width: auto;
    transform: none !important;
  }
}
</style>
