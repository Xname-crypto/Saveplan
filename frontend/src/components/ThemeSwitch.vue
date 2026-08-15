<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue"

const props = defineProps<{
  checked: boolean
  ariaLabel: string
}>()

const emit = defineEmits<{
  change: []
}>()

const MAX_PULL_X = 24
const MAX_PULL_Y = 56
const CLICK_PULL_Y = 34
const TOGGLE_PULL_Y = 22

const isPulling = ref(false)
const isReleasing = ref(false)
const pullX = ref(0)
const pullY = ref(0)

let activePointerId: number | null = null
let startX = 0
let startY = 0
let didDrag = false
let suppressNextClick = false
let releaseTimer: number | null = null

const ropeExtra = computed(() => Math.hypot(pullX.value * 0.58, pullY.value))
const ropeTilt = computed(() => {
  if (pullY.value <= 0 && Math.abs(pullX.value) <= 0) return 0

  return Math.max(-15, Math.min(15, pullX.value * 0.52))
})

const switchStyle = computed(() => ({
  "--pull-x": `${pullX.value}px`,
  "--pull-y": `${pullY.value}px`,
  "--rope-extra": `${ropeExtra.value}px`,
  "--rope-tilt": `${ropeTilt.value}deg`,
  "--knot-rest-tilt": `${ropeTilt.value * 0.72 - 2}deg`,
  "--knot-hover-tilt": `${ropeTilt.value * 0.72 + 2}deg`,
  "--knot-pull-tilt": `${ropeTilt.value * 0.9 + 3}deg`,
}))

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

function clearReleaseTimer() {
  if (releaseTimer === null) return

  window.clearTimeout(releaseTimer)
  releaseTimer = null
}

function resetPull(delay = 120) {
  clearReleaseTimer()
  isReleasing.value = true
  pullX.value = 0
  pullY.value = 0

  releaseTimer = window.setTimeout(() => {
    isPulling.value = false
    isReleasing.value = false
    releaseTimer = null
  }, delay)
}

function removePointerListeners() {
  window.removeEventListener("pointermove", handlePointerMove)
  window.removeEventListener("pointerup", handlePointerUp)
  window.removeEventListener("pointercancel", handlePointerCancel)
}

function handlePointerDown(event: PointerEvent) {
  if (event.pointerType === "mouse" && event.button !== 0) return

  clearReleaseTimer()
  activePointerId = event.pointerId
  startX = event.clientX
  startY = event.clientY
  didDrag = false
  isPulling.value = true
  isReleasing.value = false
  pullX.value = 0
  pullY.value = 7

  window.addEventListener("pointermove", handlePointerMove)
  window.addEventListener("pointerup", handlePointerUp)
  window.addEventListener("pointercancel", handlePointerCancel)
}

function handlePointerMove(event: PointerEvent) {
  if (activePointerId !== event.pointerId) return

  const nextX = clamp((event.clientX - startX) * 0.62, -MAX_PULL_X, MAX_PULL_X)
  const nextY = clamp((event.clientY - startY) * 1.08, 0, MAX_PULL_Y)
  didDrag = didDrag || nextY > 5 || Math.abs(nextX) > 6
  pullX.value = nextX
  pullY.value = nextY
}

function finishPointer(event: PointerEvent, shouldToggle: boolean) {
  if (activePointerId !== event.pointerId) return

  const shouldEmit = shouldToggle && didDrag && pullY.value >= TOGGLE_PULL_Y
  activePointerId = null
  removePointerListeners()

  if (shouldEmit) {
    suppressNextClick = true
    emit("change")
  }

  resetPull(shouldEmit ? 180 : 90)
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
  isPulling.value = true
  isReleasing.value = false
  pullX.value = props.checked ? -7 : 7
  pullY.value = CLICK_PULL_Y
  emit("change")
  resetPull(360)
}

onBeforeUnmount(() => {
  clearReleaseTimer()
  removePointerListeners()
})
</script>

<template>
  <button
    class="theme-pull-switch"
    :class="{ 'is-night': props.checked, 'is-pulling': isPulling, 'is-releasing': isReleasing }"
    type="button"
    :aria-label="ariaLabel"
    :aria-pressed="props.checked"
    :title="ariaLabel"
    :style="switchStyle"
    @click="handleClick"
    @pointerdown="handlePointerDown"
  >
    <span class="theme-pull-switch__ceiling" aria-hidden="true" />
    <span class="theme-pull-switch__rope" aria-hidden="true">
      <span class="theme-pull-switch__rope-core" />
    </span>
    <span class="theme-pull-switch__knot" aria-hidden="true">
      <span class="theme-pull-switch__glyph" />
    </span>
  </button>
</template>

<style scoped>
.theme-pull-switch {
  --pull-x: 0px;
  --pull-y: 0px;
  --rope-extra: 0px;
  --rope-tilt: 0deg;
  --knot-rest-tilt: -2deg;
  --knot-hover-tilt: 2deg;
  --knot-pull-tilt: 3deg;
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

.theme-pull-switch__rope {
  position: absolute;
  top: 0.24rem;
  left: 50%;
  z-index: 1;
  width: 0.42rem;
  height: calc(4.75rem + var(--rope-extra));
  border-radius: 999px;
  filter: drop-shadow(0 0.2rem 0.28rem var(--rope-shadow));
  transform: translateX(-50%) rotate(var(--rope-tilt));
  transform-origin: top center;
  transition:
    height 420ms cubic-bezier(0.18, 1.35, 0.28, 1),
    transform 420ms cubic-bezier(0.18, 1.35, 0.28, 1);
}

.theme-pull-switch__rope-core,
.theme-pull-switch__rope::before,
.theme-pull-switch__rope::after {
  position: absolute;
  inset: 0;
  border-radius: inherit;
}

.theme-pull-switch__rope-core {
  background:
    repeating-linear-gradient(
      34deg,
      var(--rope-dark) 0 0.08rem,
      var(--rope-main) 0.08rem 0.18rem,
      var(--rope-light) 0.18rem 0.24rem,
      var(--rope-main) 0.24rem 0.34rem
    );
  box-shadow:
    inset 0.08rem 0 0.09rem rgba(255, 246, 212, 0.22),
    inset -0.08rem 0 0.12rem rgba(72, 45, 18, 0.36);
}

.theme-pull-switch__rope::before,
.theme-pull-switch__rope::after {
  content: "";
  opacity: 0.72;
  mix-blend-mode: multiply;
}

.theme-pull-switch__rope::before {
  background: repeating-linear-gradient(
    -38deg,
    transparent 0 0.11rem,
    rgba(74, 48, 23, 0.42) 0.11rem 0.16rem,
    transparent 0.16rem 0.28rem
  );
}

.theme-pull-switch__rope::after {
  inset: 0 0.08rem;
  background: linear-gradient(90deg, rgba(255, 245, 205, 0.28), transparent 46%, rgba(44, 28, 12, 0.28));
}

.theme-pull-switch__knot {
  position: absolute;
  top: calc(4.82rem + var(--pull-y));
  left: 50%;
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
  transform: translateX(calc(-50% + var(--pull-x))) rotate(var(--knot-rest-tilt));
  transition:
    top 430ms cubic-bezier(0.16, 1.42, 0.28, 1),
    transform 430ms cubic-bezier(0.16, 1.42, 0.28, 1),
    box-shadow 220ms ease;
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
  transform: translateX(calc(-50% + var(--pull-x))) translateY(0.08rem) rotate(var(--knot-hover-tilt));
}

.theme-pull-switch.is-pulling .theme-pull-switch__rope {
  transition-duration: 42ms;
}

.theme-pull-switch.is-pulling .theme-pull-switch__knot {
  transform: translateX(calc(-50% + var(--pull-x))) translateY(0.08rem) rotate(var(--knot-pull-tilt)) scale(0.98);
  transition-duration: 42ms;
}

.theme-pull-switch.is-releasing .theme-pull-switch__rope {
  transition:
    height 560ms cubic-bezier(0.18, 1.55, 0.28, 1),
    transform 620ms cubic-bezier(0.16, 1.58, 0.3, 1);
}

.theme-pull-switch.is-releasing .theme-pull-switch__knot {
  transition:
    top 620ms cubic-bezier(0.16, 1.58, 0.3, 1),
    transform 680ms cubic-bezier(0.14, 1.62, 0.32, 1),
    box-shadow 220ms ease;
}

.theme-pull-switch.is-night {
  --rope-main: #d8d6cd;
  --rope-light: #fbfaf3;
  --rope-dark: #8e8c84;
  --rope-shadow: rgba(248, 246, 230, 0.18);
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
  transform: rotate(-16deg);
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
  }
}
</style>
