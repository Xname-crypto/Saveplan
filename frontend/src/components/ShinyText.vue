<script setup lang="ts">
import { computed } from "vue"

interface ShinyTextProps {
  text: string
  color?: string
  shineColor?: string
  speed?: number
  delay?: number
  spread?: number
  direction?: "left" | "right"
  yoyo?: boolean
  pauseOnHover?: boolean
  disabled?: boolean
  className?: string
}

const props = withDefaults(defineProps<ShinyTextProps>(), {
  color: "#d8cfb4",
  shineColor: "#ffffff",
  speed: 2.6,
  delay: 0,
  spread: 120,
  direction: "left",
  yoyo: false,
  pauseOnHover: false,
  disabled: false,
  className: "",
})

const shinyStyle = computed(() => ({
  "--shiny-color": props.color,
  "--shiny-highlight": props.shineColor,
  "--shiny-speed": `${props.speed}s`,
  "--shiny-delay": `${props.delay}s`,
  "--shiny-spread": `${props.spread}deg`,
}))

const shinyClass = computed(() => [
  "shiny-text",
  `shiny-text--${props.direction}`,
  {
    "shiny-text--disabled": props.disabled,
    "shiny-text--yoyo": props.yoyo,
    "shiny-text--pause-hover": props.pauseOnHover,
  },
  props.className,
])
</script>

<template>
  <span :class="shinyClass" :style="shinyStyle" :data-text="props.text">
    {{ props.text }}
  </span>
</template>
