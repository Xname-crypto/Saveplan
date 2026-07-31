<script setup lang="ts">
import { onUnmounted, ref, watch, type CSSProperties, type ComponentPublicInstance } from "vue"

export type Falloff = "linear" | "smooth" | "sharp"

interface LineSidebarProps {
  items?: string[]
  accentColor?: string
  textColor?: string
  markerColor?: string
  showIndex?: boolean
  showMarker?: boolean
  proximityRadius?: number
  maxShift?: number
  falloff?: Falloff
  markerLength?: number
  markerGap?: number
  tickScale?: number
  scaleTick?: boolean
  itemGap?: number
  fontSize?: number
  smoothing?: number
  defaultActive?: number | null
  className?: string
}

const FALLOFF_CURVES: Record<Falloff, (progress: number) => number> = {
  linear: (progress) => progress,
  smooth: (progress) => progress * progress * (3 - 2 * progress),
  sharp: (progress) => progress * progress * progress,
}

const props = withDefaults(defineProps<LineSidebarProps>(), {
  items: () => ["Overview", "Components", "Animations", "Backgrounds", "Showcase"],
  accentColor: "#d6c58d",
  textColor: "rgba(235, 228, 207, 0.64)",
  markerColor: "rgba(235, 228, 207, 0.34)",
  showIndex: true,
  showMarker: true,
  proximityRadius: 100,
  maxShift: 26,
  falloff: "smooth",
  markerLength: 52,
  markerGap: 10,
  tickScale: 0.46,
  scaleTick: true,
  itemGap: 18,
  fontSize: 0.82,
  smoothing: 100,
  defaultActive: null,
  className: "",
})

const emit = defineEmits<{
  itemClick: [index: number, label: string]
}>()

const listRef = ref<HTMLUListElement | null>(null)
const itemRefs = ref<(HTMLLIElement | null)[]>([])
const activeIndex = ref<number | null>(props.defaultActive)

let targets: number[] = []
const current: number[] = []
let rafId: number | null = null
let last = 0

const rootStyle = (): CSSProperties => ({
  "--accent-color": props.accentColor,
  "--text-color": props.textColor,
  "--marker-color": props.markerColor,
  "--marker-length": `${props.markerLength}px`,
  "--marker-gap": `${props.markerGap}px`,
  "--tick-scale": String(props.tickScale),
  "--max-shift": `${props.maxShift}px`,
  "--item-gap": `${props.itemGap}px`,
  "--font-size": `${props.fontSize}rem`,
  "--smoothing": `${props.smoothing}ms`,
})

const setItemRef = (el: Element | ComponentPublicInstance | null, index: number) => {
  itemRefs.value[index] = el as HTMLLIElement | null
}

const runFrame = (now: number) => {
  const dt = Math.min((now - last) / 1000, 0.05)
  last = now
  const tau = Math.max(props.smoothing, 1) / 1000
  const k = 1 - Math.exp(-dt / tau)

  let moving = false
  const els = itemRefs.value
  for (let index = 0; index < els.length; index += 1) {
    const el = els[index]
    if (!el) continue

    const target = Math.max(targets[index] || 0, activeIndex.value === index ? 1 : 0)
    const cur = current[index] || 0
    const next = cur + (target - cur) * k
    const settled = Math.abs(target - next) < 0.0015
    const value = settled ? target : next

    current[index] = value
    el.style.setProperty("--effect", value.toFixed(4))
    if (!settled) moving = true
  }

  rafId = moving ? requestAnimationFrame(runFrame) : null
}

const startLoop = () => {
  if (rafId !== null) return
  last = performance.now()
  rafId = requestAnimationFrame(runFrame)
}

const handlePointerMove = (event: PointerEvent) => {
  const list = listRef.value
  if (!list) return

  const rect = list.getBoundingClientRect()
  const pointerY = event.clientY - rect.top
  const ease = FALLOFF_CURVES[props.falloff] ?? FALLOFF_CURVES.linear

  itemRefs.value.forEach((el, index) => {
    if (!el) return
    const center = el.offsetTop + el.offsetHeight / 2
    const distance = Math.abs(pointerY - center)
    targets[index] = ease(Math.max(0, 1 - distance / props.proximityRadius))
  })

  startLoop()
}

const handlePointerLeave = () => {
  targets = targets.map(() => 0)
  startLoop()
}

const handleClick = (index: number, label: string) => {
  activeIndex.value = index
  emit("itemClick", index, label)
}

watch(activeIndex, () => startLoop(), { immediate: true })

onUnmounted(() => {
  if (rafId !== null) cancelAnimationFrame(rafId)
})
</script>

<template>
  <nav
    :class="['line-sidebar', { 'line-sidebar--with-marker': showMarker }, className]"
    :style="rootStyle()"
    aria-label="Study flow"
  >
    <ul ref="listRef" class="line-sidebar__list" @pointermove="handlePointerMove" @pointerleave="handlePointerLeave">
      <li
        v-for="(label, index) in items"
        :key="`${label}-${index}`"
        :ref="(el) => setItemRef(el, index)"
        class="line-sidebar__item"
        :class="{ 'line-sidebar__item--active': activeIndex === index, 'line-sidebar__item--scaled-tick': scaleTick }"
        :aria-current="activeIndex === index ? 'true' : undefined"
        @click="handleClick(index, label)"
      >
        <span v-if="showMarker" class="line-sidebar__marker" aria-hidden="true" />
        <span class="line-sidebar__label">
          <span v-if="showIndex" class="line-sidebar__index">
            {{ String(index + 1).padStart(2, "0") }}
          </span>
          <span>{{ label }}</span>
        </span>
      </li>
    </ul>
  </nav>
</template>

<style scoped>
.line-sidebar {
  position: relative;
  display: flex;
  justify-content: flex-start;
  padding-left: 0;
}

.line-sidebar--with-marker {
  padding-left: calc(var(--marker-length) + var(--marker-gap));
}

.line-sidebar__list {
  display: flex;
  flex-direction: column;
  gap: var(--item-gap);
  margin: 0;
  padding: 1rem 0;
  list-style: none;
}

.line-sidebar__item {
  --effect: 0;
  position: relative;
  cursor: pointer;
}

.line-sidebar__item::before {
  position: absolute;
  inset: -0.38rem -3rem;
  content: "";
}

.line-sidebar__item::after {
  position: absolute;
  top: calc(100% + var(--item-gap) / 2);
  left: calc(-1 * var(--marker-length) - var(--marker-gap));
  width: calc(var(--marker-length) * var(--tick-scale));
  height: 1px;
  content: "";
  opacity: 0.5;
  background: var(--marker-color);
  transform: translateY(-50%) scaleX(calc(0.7 + var(--effect) * 0.6));
  transform-origin: left;
}

.line-sidebar__item:last-child::after {
  content: none;
}

.line-sidebar__item:not(.line-sidebar__item--scaled-tick)::after {
  transform: translateY(-50%);
}

.line-sidebar__marker {
  position: absolute;
  top: 50%;
  left: calc(-1 * var(--marker-length) - var(--marker-gap));
  width: var(--marker-length);
  height: 1px;
  background: color-mix(in srgb, var(--accent-color) calc(var(--effect) * 100%), var(--marker-color));
  transform: translateY(-50%) scaleX(calc(0.7 + var(--effect) * 0.5));
  transform-origin: left;
}

.line-sidebar__label {
  position: relative;
  display: inline-flex;
  align-items: baseline;
  color: color-mix(in srgb, var(--accent-color) calc(var(--effect) * 100%), var(--text-color));
  font-size: var(--font-size);
  font-weight: 800;
  letter-spacing: 0.1em;
  line-height: 1.2;
  text-transform: uppercase;
  transform: translateX(calc(var(--effect) * var(--max-shift)));
  transition: transform var(--smoothing) ease, color var(--smoothing) ease;
}

.line-sidebar__index {
  margin-right: 0.6rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.85em;
  opacity: calc(0.55 + var(--effect) * 0.45);
}
</style>
