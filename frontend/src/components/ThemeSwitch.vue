<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue"

const props = defineProps<{
  checked: boolean
  ariaLabel: string
}>()

const emit = defineEmits<{
  change: []
}>()

const MAX_PULL_X = 118
const MIN_PULL_Y = -82
const MAX_PULL_Y = 74
const CLICK_PULL_Y = 34
const TOGGLE_PULL_Y = 22
const ROPE_BASE_PX = 86
const ROPE_ANCHOR_X = 120
const ROPE_ANCHOR_Y = 4
const SPRING_STIFFNESS = 0.052
const SPRING_DAMPING = 0.88
const FOLD_STIFFNESS = 0.075
const FOLD_DAMPING = 0.72

const isPulling = ref(false)
const isReleasing = ref(false)
const isSwitching = ref(false)
const pullX = ref(0)
const pullY = ref(0)
const foldX = ref(0)
const foldY = ref(0)

let activePointerId: number | null = null
let startX = 0
let startY = 0
let didDrag = false
let suppressNextClick = false
let releaseTimer: number | null = null
let switchFlashTimer: number | null = null
let animationFrameId: number | null = null
let velocityX = 0
let velocityY = 0
let velocityFoldX = 0
let velocityFoldY = 0
let releaseStartedAt = 0

const ropeEndY = computed(() => clamp(ROPE_BASE_PX + pullY.value, 8, ROPE_BASE_PX + MAX_PULL_Y))
const ropeEndX = computed(() => ROPE_ANCHOR_X + pullX.value)
const ropeVectorY = computed(() => Math.max(8, ropeEndY.value - ROPE_ANCHOR_Y))
const ropeLength = computed(() => Math.hypot(pullX.value, ropeVectorY.value))

const ropeExtra = computed(() => Math.max(0, ropeLength.value - (ROPE_BASE_PX - ROPE_ANCHOR_Y)))

const ropeTilt = computed(() => {
  if (Math.abs(pullX.value) <= 0.1 && Math.abs(pullY.value) <= 0.1) return 0

  return Math.atan2(pullX.value, ropeVectorY.value) * (180 / Math.PI)
})

const ropePath = computed(() => {
  const controlX = ROPE_ANCHOR_X + pullX.value * 0.48 + foldX.value
  const controlY = ROPE_ANCHOR_Y + ropeVectorY.value * 0.52 + foldY.value

  return `M ${ROPE_ANCHOR_X} ${ROPE_ANCHOR_Y} Q ${controlX.toFixed(2)} ${controlY.toFixed(2)} ${ropeEndX.value.toFixed(2)} ${ropeEndY.value.toFixed(2)}`
})

const switchStyle = computed(() => ({
  "--pull-x": `${pullX.value}px`,
  "--rope-end-x": `${ropeEndX.value}px`,
  "--rope-end-y": `${ropeEndY.value}px`,
  "--rope-extra": `${ropeExtra.value}px`,
  "--rope-tilt": `${ropeTilt.value}deg`,
  "--knot-rest-tilt": `${ropeTilt.value * 0.28 - 2}deg`,
  "--knot-hover-tilt": `${ropeTilt.value * 0.28 + 2}deg`,
  "--knot-pull-tilt": `${ropeTilt.value * 0.34 + 3}deg`,
}))

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

function clearReleaseTimer() {
  if (releaseTimer === null) return

  window.clearTimeout(releaseTimer)
  releaseTimer = null
}

function clearSwitchFlashTimer() {
  if (switchFlashTimer === null) return

  window.clearTimeout(switchFlashTimer)
  switchFlashTimer = null
}

function flashSwitch() {
  clearSwitchFlashTimer()
  isSwitching.value = true
  switchFlashTimer = window.setTimeout(() => {
    isSwitching.value = false
    switchFlashTimer = null
  }, 420)
}

function clearSwingAnimation() {
  if (animationFrameId === null) return

  window.cancelAnimationFrame(animationFrameId)
  animationFrameId = null
}

function prefersReducedMotion() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches
}

function finishRelease() {
  clearReleaseTimer()
  pullX.value = 0
  pullY.value = 0
  foldX.value = 0
  foldY.value = 0
  velocityX = 0
  velocityY = 0
  velocityFoldX = 0
  velocityFoldY = 0
  isPulling.value = false
  isReleasing.value = false
}

function startSwingRelease(strength = 1) {
  clearReleaseTimer()
  clearSwingAnimation()

  if (prefersReducedMotion()) {
    finishRelease()
    return
  }

  isReleasing.value = true
  releaseStartedAt = performance.now()
  velocityX = clamp(velocityX * 0.35 - pullX.value * 0.32, -9, 9) * strength
  velocityY = clamp(velocityY * 0.15 - pullY.value * 0.2, -10, 2) * strength
  velocityFoldX = clamp(-pullX.value * 0.42 + velocityX * 1.8, -30, 30) * strength
  velocityFoldY = clamp(-Math.abs(pullX.value) * 0.12 - pullY.value * 0.16 + velocityY * 0.9, -22, 18) * strength

  const step = () => {
    const elapsed = performance.now() - releaseStartedAt

    velocityX = (velocityX - pullX.value * SPRING_STIFFNESS) * SPRING_DAMPING
    velocityY = (velocityY - pullY.value * SPRING_STIFFNESS) * SPRING_DAMPING
    velocityFoldX = (velocityFoldX - foldX.value * FOLD_STIFFNESS - pullX.value * 0.018) * FOLD_DAMPING
    velocityFoldY = (velocityFoldY - foldY.value * FOLD_STIFFNESS - pullY.value * 0.012) * FOLD_DAMPING
    pullX.value = clamp(pullX.value + velocityX, -MAX_PULL_X, MAX_PULL_X)
    pullY.value = clamp(pullY.value + velocityY, MIN_PULL_Y, MAX_PULL_Y)
    foldX.value = clamp(foldX.value + velocityFoldX, -44, 44)
    foldY.value = clamp(foldY.value + velocityFoldY, -28, 28)

    if (
      elapsed > 720 &&
      Math.abs(pullX.value) < 0.18 &&
      Math.abs(pullY.value) < 0.18 &&
      Math.abs(foldX.value) < 0.22 &&
      Math.abs(foldY.value) < 0.22 &&
      Math.abs(velocityX) < 0.14 &&
      Math.abs(velocityY) < 0.14 &&
      Math.abs(velocityFoldX) < 0.18 &&
      Math.abs(velocityFoldY) < 0.18
    ) {
      animationFrameId = null
      finishRelease()
      return
    }

    animationFrameId = window.requestAnimationFrame(step)
  }

  animationFrameId = window.requestAnimationFrame(step)
}

function removePointerListeners() {
  window.removeEventListener("pointermove", handlePointerMove)
  window.removeEventListener("pointerup", handlePointerUp)
  window.removeEventListener("pointercancel", handlePointerCancel)
}

function handlePointerDown(event: PointerEvent) {
  if (event.pointerType === "mouse" && event.button !== 0) return

  clearReleaseTimer()
  clearSwingAnimation()
  activePointerId = event.pointerId
  startX = event.clientX
  startY = event.clientY
  didDrag = false
  isPulling.value = true
  isReleasing.value = false
  velocityX = 0
  velocityY = 0
  velocityFoldX = 0
  velocityFoldY = 0
  pullX.value = 0
  pullY.value = 7
  foldX.value = 0
  foldY.value = 0

  window.addEventListener("pointermove", handlePointerMove)
  window.addEventListener("pointerup", handlePointerUp)
  window.addEventListener("pointercancel", handlePointerCancel)
}

function handlePointerMove(event: PointerEvent) {
  if (activePointerId !== event.pointerId) return

  const nextX = clamp((event.clientX - startX) * 0.62, -MAX_PULL_X, MAX_PULL_X)
  const nextY = clamp((event.clientY - startY) * 1.08, MIN_PULL_Y, MAX_PULL_Y)
  velocityX = (nextX - pullX.value) * 0.45
  velocityY = (nextY - pullY.value) * 0.32
  velocityFoldX = velocityX * -1.35
  velocityFoldY = velocityY * -0.75
  didDrag = didDrag || nextY > 5 || Math.abs(nextX) > 6
  pullX.value = nextX
  pullY.value = nextY
  foldX.value = clamp(-nextX * 0.16 + velocityFoldX, -30, 30)
  foldY.value = clamp(-Math.abs(nextX) * 0.035 + velocityFoldY, -18, 18)
}

function finishPointer(event: PointerEvent, shouldToggle: boolean) {
  if (activePointerId !== event.pointerId) return

  const shouldEmit = shouldToggle && didDrag && pullY.value >= TOGGLE_PULL_Y
  activePointerId = null
  removePointerListeners()

  if (shouldEmit) {
    suppressNextClick = true
    flashSwitch()
    emit("change")
  }

  startSwingRelease(shouldEmit ? 1.18 : 0.82)
}

function handlePointerUp(event: PointerEvent) {
  finishPointer(event, true)
}

function handlePointerCancel(event: PointerEvent) {
  finishPointer(event, false)
}

function handleClick() {
  if (suppressNextClick) {
    suppressNextClick = false
    return
  }

  clearReleaseTimer()
  clearSwingAnimation()
  isPulling.value = true
  isReleasing.value = false
  velocityX = props.checked ? -2.2 : 2.2
  velocityY = 2.8
  velocityFoldX = props.checked ? 8 : -8
  velocityFoldY = -6
  pullX.value = props.checked ? -7 : 7
  pullY.value = CLICK_PULL_Y
  foldX.value = props.checked ? 12 : -12
  foldY.value = -8
  flashSwitch()
  emit("change")
  startSwingRelease(1)
}

onBeforeUnmount(() => {
  clearReleaseTimer()
  clearSwitchFlashTimer()
  clearSwingAnimation()
  removePointerListeners()
})
</script>

<template>
  <button
    class="theme-pull-switch"
    :class="{ 'is-night': props.checked, 'is-pulling': isPulling, 'is-releasing': isReleasing, 'is-switching': isSwitching }"
    type="button"
    :aria-label="ariaLabel"
    :aria-pressed="props.checked"
    :title="ariaLabel"
    :style="switchStyle"
    @click="handleClick"
    @pointerdown="handlePointerDown"
  >
    <span class="theme-pull-switch__ceiling" aria-hidden="true" />
    <span class="theme-pull-switch__hanger" aria-hidden="true">
      <svg class="theme-pull-switch__rope" viewBox="0 0 240 178" focusable="false">
        <path class="theme-pull-switch__rope-shadow" :d="ropePath" pathLength="1" />
        <path class="theme-pull-switch__rope-base" :d="ropePath" pathLength="1" />
        <path class="theme-pull-switch__rope-fiber theme-pull-switch__rope-fiber--light" :d="ropePath" pathLength="1" />
        <path class="theme-pull-switch__rope-fiber theme-pull-switch__rope-fiber--dark" :d="ropePath" pathLength="1" />
      </svg>
      <span class="theme-pull-switch__knot">
        <span class="theme-pull-switch__glyph" />
      </span>
    </span>
  </button>
</template>

<style scoped>
.theme-pull-switch {
  --pull-x: 0px;
  --rope-end-x: 120px;
  --rope-end-y: 86px;
  --rope-extra: 0px;
  --rope-tilt: 0deg;
  --knot-rest-tilt: -2deg;
  --knot-hover-tilt: 2deg;
  --knot-pull-tilt: 3deg;
  --glyph-tilt: 0deg;
  --rope-main: #9f7240;
  --rope-light: #d0a66f;
  --rope-dark: #5f3e20;
  --rope-shadow: rgba(28, 18, 8, 0.34);
  position: relative;
  display: inline-flex;
  width: 2.75rem;
  height: 5.2rem;
  flex: 0 0 auto;
  align-items: flex-start;
  justify-content: center;
  padding: 0;
  border: 0;
  background: transparent;
  color: #e8c06d;
  cursor: pointer;
  overflow: visible;
  touch-action: none;
}

.theme-pull-switch *,
.theme-pull-switch *::before,
.theme-pull-switch *::after {
  box-sizing: border-box;
}

.theme-pull-switch:focus-visible {
  outline: 2px solid rgba(235, 228, 207, 0.82);
  outline-offset: 0.2rem;
  border-radius: 999px;
}

.theme-pull-switch__ceiling {
  position: absolute;
  top: 0.05rem;
  left: 50%;
  z-index: 2;
  width: 1.08rem;
  height: 0.34rem;
  border: 1px solid rgba(159, 114, 64, 0.38);
  border-radius: 999px;
  background:
    linear-gradient(180deg, rgba(230, 202, 158, 0.28), rgba(88, 58, 30, 0.36)),
    rgba(34, 25, 15, 0.82);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.16),
    0 0.55rem 1.15rem rgba(0, 0, 0, 0.24);
  transform: translateX(-50%);
}

.theme-pull-switch__hanger {
  position: absolute;
  top: 0.24rem;
  left: 50%;
  z-index: 1;
  width: 15rem;
  height: 11.125rem;
  pointer-events: none;
  transform: translateX(-50%);
}

.theme-pull-switch__rope {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 1;
  width: 15rem;
  height: 11.125rem;
  overflow: visible;
  filter: drop-shadow(0 0.2rem 0.28rem var(--rope-shadow));
}

.theme-pull-switch__rope path {
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
  vector-effect: non-scaling-stroke;
}

.theme-pull-switch__rope-shadow {
  stroke: rgba(34, 20, 8, 0.34);
  stroke-width: 8.5;
  transform: translate(0.65px, 1.15px);
}

.theme-pull-switch__rope-base {
  stroke: var(--rope-main);
  stroke-width: 7.2;
}

.theme-pull-switch__rope-fiber {
  stroke-dasharray: 0.035 0.045;
  stroke-width: 3;
  opacity: 0.9;
}

.theme-pull-switch__rope-fiber--light {
  stroke: var(--rope-light);
  stroke-dashoffset: 0.02;
}

.theme-pull-switch__rope-fiber--dark {
  stroke: var(--rope-dark);
  stroke-dashoffset: 0.06;
  stroke-width: 2.2;
  opacity: 0.64;
}

.theme-pull-switch__knot {
  position: absolute;
  top: var(--rope-end-y);
  left: var(--rope-end-x);
  z-index: 3;
  display: grid;
  width: 1.44rem;
  height: 1.24rem;
  place-items: center;
  border: 1px solid rgba(105, 69, 34, 0.44);
  border-radius: 48% 52% 54% 46% / 46% 48% 52% 54%;
  background:
    radial-gradient(circle at 34% 24%, rgba(246, 219, 172, 0.24), transparent 32%),
    repeating-linear-gradient(
      28deg,
      #765025 0 0.11rem,
      #a9793f 0.11rem 0.22rem,
      #c9975a 0.22rem 0.3rem,
      #855a2e 0.3rem 0.42rem
    );
  box-shadow:
    inset 0 1px 0 rgba(255, 236, 196, 0.24),
    inset 0 -0.14rem 0.2rem rgba(76, 45, 19, 0.38),
    0 0.65rem 1.15rem rgba(0, 0, 0, 0.28);
  transform: translate(-50%, -0.16rem) rotate(var(--knot-rest-tilt));
  will-change: top, transform;
  transition: box-shadow 220ms ease;
}

.theme-pull-switch__knot::before,
.theme-pull-switch__knot::after {
  content: "";
  position: absolute;
}

.theme-pull-switch__knot::before {
  inset: 0.2rem 0.12rem auto;
  height: 0.26rem;
  border-radius: 999px;
  background: rgba(80, 52, 25, 0.24);
}

.theme-pull-switch__knot::after {
  left: 50%;
  bottom: -0.32rem;
  width: 0.78rem;
  height: 0.44rem;
  border-radius: 0 0 999px 999px;
  background:
    repeating-linear-gradient(
      90deg,
      rgba(95, 62, 32, 0.9) 0 0.06rem,
      rgba(201, 151, 90, 0.92) 0.06rem 0.12rem,
      rgba(118, 80, 37, 0.92) 0.12rem 0.18rem
    );
  clip-path: polygon(4% 0, 96% 0, 86% 100%, 64% 62%, 49% 100%, 35% 62%, 16% 100%);
  transform: translateX(-50%);
}

.theme-pull-switch__glyph {
  position: relative;
  z-index: 1;
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 50%;
  background: #f4c84f;
  box-shadow:
    0 0 0 0.12rem rgba(255, 232, 154, 0.28),
    0 0 0.7rem rgba(244, 200, 79, 0.44);
  transition:
    background 260ms ease,
    box-shadow 260ms ease,
    transform 260ms ease;
}

.theme-pull-switch__glyph::before,
.theme-pull-switch__glyph::after {
  content: "";
  position: absolute;
  inset: 50% auto auto 50%;
  width: 0.12rem;
  height: 0.12rem;
  border-radius: 50%;
  background: rgba(69, 57, 37, 0);
  transform: translate(-50%, -50%);
  transition: background 260ms ease, box-shadow 260ms ease;
}

.theme-pull-switch:hover .theme-pull-switch__knot {
  transform: translate(-50%, -0.08rem) rotate(var(--knot-hover-tilt));
}

.theme-pull-switch.is-pulling .theme-pull-switch__knot {
  transform: translate(-50%, -0.08rem) rotate(var(--knot-pull-tilt)) scale(0.98);
  transition-duration: 0ms;
}

.theme-pull-switch.is-releasing .theme-pull-switch__knot {
  transition-duration: 0ms;
}

.theme-pull-switch.is-switching .theme-pull-switch__glyph {
  animation: theme-pull-switch-flash 420ms ease-out;
}

.theme-pull-switch.is-night {
  --rope-main: #d8d6cd;
  --rope-light: #fbfaf3;
  --rope-dark: #8e8c84;
  --rope-shadow: rgba(248, 246, 230, 0.18);
  --glyph-tilt: -16deg;
  color: #d6c58d;
}

.theme-pull-switch.is-night .theme-pull-switch__ceiling {
  border-color: rgba(238, 236, 222, 0.5);
  background:
    linear-gradient(180deg, rgba(255, 255, 248, 0.28), rgba(132, 130, 119, 0.34)),
    rgba(24, 24, 22, 0.84);
}

.theme-pull-switch.is-night .theme-pull-switch__knot {
  border-color: rgba(238, 236, 222, 0.42);
  background:
    radial-gradient(circle at 34% 24%, rgba(255, 255, 248, 0.38), transparent 34%),
    repeating-linear-gradient(
      28deg,
      #8e8c84 0 0.11rem,
      #d8d6cd 0.11rem 0.22rem,
      #fbfaf3 0.22rem 0.3rem,
      #aaa79d 0.3rem 0.42rem
    );
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.34),
    inset 0 -0.14rem 0.2rem rgba(67, 66, 61, 0.3),
    0 0.65rem 1.15rem rgba(0, 0, 0, 0.28),
    0 0 0.65rem rgba(255, 252, 232, 0.16);
}

.theme-pull-switch.is-night .theme-pull-switch__knot::before {
  background: rgba(84, 83, 78, 0.18);
}

.theme-pull-switch.is-night .theme-pull-switch__knot::after {
  background:
    repeating-linear-gradient(
      90deg,
      rgba(142, 140, 132, 0.95) 0 0.06rem,
      rgba(251, 250, 243, 0.95) 0.06rem 0.12rem,
      rgba(170, 167, 157, 0.95) 0.12rem 0.18rem
    );
}

.theme-pull-switch.is-night .theme-pull-switch__glyph {
  background: #d6c58d;
  box-shadow:
    inset -0.16rem 0 0 #8f8664,
    0 0 0 0.12rem rgba(214, 197, 141, 0.24),
    0 0 0.8rem rgba(214, 197, 141, 0.48);
  transform: rotate(var(--glyph-tilt));
}

.theme-pull-switch.is-night .theme-pull-switch__glyph::before {
  background: rgba(93, 86, 63, 0.55);
  box-shadow:
    -0.14rem -0.06rem 0 -0.02rem rgba(93, 86, 63, 0.42),
    0.16rem 0.12rem 0 -0.03rem rgba(93, 86, 63, 0.38);
}

html[data-theme="day"] .theme-pull-switch:focus-visible {
  outline-color: rgba(52, 93, 117, 0.64);
}

html[data-theme="day"] .theme-pull-switch__ceiling {
  border-color: rgba(112, 79, 38, 0.28);
  background:
    linear-gradient(180deg, rgba(244, 226, 192, 0.8), rgba(173, 128, 72, 0.54)),
    #dfbf86;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    0 0.55rem 1.05rem rgba(52, 93, 117, 0.16);
}

html[data-theme="day"] .theme-pull-switch__knot {
  border-color: rgba(112, 79, 38, 0.32);
  box-shadow:
    inset 0 1px 0 rgba(255, 236, 196, 0.28),
    inset 0 -0.14rem 0.2rem rgba(84, 52, 21, 0.22),
    0 0.65rem 1rem rgba(52, 93, 117, 0.15);
}

@media (prefers-reduced-motion: reduce) {
  .theme-pull-switch,
  .theme-pull-switch *,
  .theme-pull-switch *::before,
  .theme-pull-switch *::after {
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
  }
}

@keyframes theme-pull-switch-flash {
  0% {
    transform: rotate(var(--glyph-tilt)) scale(0.9);
    box-shadow:
      0 0 0 0.08rem rgba(255, 232, 154, 0.42),
      0 0 0.4rem rgba(244, 200, 79, 0.4);
  }

  42% {
    transform: rotate(var(--glyph-tilt)) scale(1.16);
    box-shadow:
      0 0 0 0.2rem rgba(255, 232, 154, 0.38),
      0 0 1.25rem rgba(244, 200, 79, 0.72);
  }

  100% {
    transform: rotate(var(--glyph-tilt)) scale(1);
  }
}
</style>
