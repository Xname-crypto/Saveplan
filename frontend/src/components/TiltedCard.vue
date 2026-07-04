<script setup lang="ts">
import { computed, ref, useTemplateRef } from "vue"

interface TiltedCardProps {
  rotateAmplitude?: number
  scaleOnHover?: number
}

const props = withDefaults(defineProps<TiltedCardProps>(), {
  rotateAmplitude: 10,
  scaleOnHover: 1.025,
})

const cardRef = useTemplateRef<HTMLElement>("cardRef")
const rotateX = ref(0)
const rotateY = ref(0)
const scale = ref(1)
const isActive = ref(false)

const prefersReducedMotion = () =>
  typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches

function handlePointerMove(event: PointerEvent) {
  if (!cardRef.value || prefersReducedMotion()) return

  const rect = cardRef.value.getBoundingClientRect()
  const offsetX = event.clientX - rect.left - rect.width / 2
  const offsetY = event.clientY - rect.top - rect.height / 2

  rotateX.value = (offsetY / (rect.height / 2)) * -props.rotateAmplitude
  rotateY.value = (offsetX / (rect.width / 2)) * props.rotateAmplitude
}

function handlePointerEnter() {
  if (prefersReducedMotion()) return
  isActive.value = true
  scale.value = props.scaleOnHover
}

function handlePointerLeave() {
  isActive.value = false
  rotateX.value = 0
  rotateY.value = 0
  scale.value = 1
}

const cardStyle = computed(() => ({
  transform: `rotateX(${rotateX.value.toFixed(2)}deg) rotateY(${rotateY.value.toFixed(
    2,
  )}deg) scale(${scale.value})`,
  transition: isActive.value
    ? "transform 90ms ease-out"
    : "transform 520ms cubic-bezier(0.22, 1, 0.36, 1)",
}))
</script>

<template>
  <div
    ref="cardRef"
    class="tilted-card"
    @pointermove="handlePointerMove"
    @pointerenter="handlePointerEnter"
    @pointerleave="handlePointerLeave"
  >
    <div class="tilted-card__body" :style="cardStyle">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.tilted-card {
  display: block;
  perspective: 800px;
}

.tilted-card__body {
  height: 100%;
  transform-style: preserve-3d;
  will-change: transform;
}

.tilted-card__body > :deep(*) {
  height: 100%;
  transform: translateZ(0);
}

@media (prefers-reduced-motion: reduce) {
  .tilted-card__body {
    transition: none !important;
    transform: none !important;
  }
}
</style>
