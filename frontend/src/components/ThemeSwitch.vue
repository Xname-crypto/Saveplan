<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue"

const props = defineProps<{
  checked: boolean
  ariaLabel: string
}>()

const emit = defineEmits<{
  change: []
}>()

const isPulling = ref(false)
const pullDistance = ref(0)

let activePointerId: number | null = null
let startY = 0
let didDrag = false
let suppressNextClick = false
let releaseTimer: number | null = null

const switchStyle = computed(() => ({
  "--pull-distance": `${pullDistance.value}px`,
}))

function clearReleaseTimer() {
  if (releaseTimer === null) return

  window.clearTimeout(releaseTimer)
  releaseTimer = null
}

function resetPull(delay = 120) {
  clearReleaseTimer()
  releaseTimer = window.setTimeout(() => {
    isPulling.value = false
    pullDistance.value = 0
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
  startY = event.clientY
  didDrag = false
  isPulling.value = true
  pullDistance.value = 5

  window.addEventListener("pointermove", handlePointerMove)
  window.addEventListener("pointerup", handlePointerUp)
  window.addEventListener("pointercancel", handlePointerCancel)
}

function handlePointerMove(event: PointerEvent) {
  if (activePointerId !== event.pointerId) return

  const nextDistance = Math.min(26, Math.max(0, event.clientY - startY))
  didDrag = didDrag || nextDistance > 4
  pullDistance.value = nextDistance
}

function finishPointer(event: PointerEvent, shouldToggle: boolean) {
  if (activePointerId !== event.pointerId) return

  const shouldEmit = shouldToggle && didDrag && pullDistance.value >= 13
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
  pullDistance.value = 18
  emit("change")
  resetPull(190)
}

onBeforeUnmount(() => {
  clearReleaseTimer()
  removePointerListeners()
})
</script>

<template>
  <button
    class="theme-pull-switch"
    :class="{ 'is-night': props.checked, 'is-pulling': isPulling }"
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
  --pull-distance: 0px;
  --rope-main: #9f7240;
  --rope-light: #d0a66f;
  --rope-dark: #5f3e20;
  --rope-shadow: rgba(28, 18, 8, 0.34);
  position: relative;
  display: inline-flex;
  width: 2.75rem;
  height: 3.35rem;
  flex: 0 0 auto;
  align-items: flex-start;
  justify-content: center;
  padding: 0;
  border: 0;
  background: transparent;
  color: #e8c06d;
  cursor: pointer;
  touch-action: none;
  transform: translateY(-0.08rem);
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
  height: calc(2.1rem + var(--pull-distance));
  border-radius: 999px;
  filter: drop-shadow(0 0.2rem 0.28rem var(--rope-shadow));
  transform: translateX(-50%);
  transform-origin: top center;
  transition: height 260ms cubic-bezier(0.2, 0.9, 0.26, 1.18);
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
  top: calc(2.18rem + var(--pull-distance));
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
  transform: translateX(-50%) rotate(-2deg);
  transition:
    top 260ms cubic-bezier(0.2, 0.9, 0.26, 1.18),
    transform 220ms ease,
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
  transform: translateX(-50%) translateY(0.08rem) rotate(2deg);
}

.theme-pull-switch.is-pulling .theme-pull-switch__rope {
  transition-duration: 70ms;
}

.theme-pull-switch.is-pulling .theme-pull-switch__knot {
  transform: translateX(-50%) translateY(0.08rem) rotate(5deg) scale(0.98);
  transition-duration: 70ms;
}

.theme-pull-switch.is-night {
  color: #d6c58d;
}

.theme-pull-switch.is-night .theme-pull-switch__ceiling {
  border-color: rgba(214, 197, 141, 0.4);
  background:
    linear-gradient(180deg, rgba(235, 228, 207, 0.18), rgba(52, 43, 28, 0.44)),
    rgba(13, 13, 13, 0.84);
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
