<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, useTemplateRef, watch } from "vue"

interface DecryptedTextProps {
  text: string
  speed?: number
  maxIterations?: number
  sequential?: boolean
  revealDirection?: "start" | "end" | "center"
  useOriginalCharsOnly?: boolean
  characters?: string
  className?: string
  encryptedClassName?: string
  parentClassName?: string
  animateOn?: "view" | "hover"
}

const props = withDefaults(defineProps<DecryptedTextProps>(), {
  text: "",
  speed: 42,
  maxIterations: 10,
  sequential: false,
  revealDirection: "start",
  useOriginalCharsOnly: false,
  characters: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{};:,.<>?",
  className: "",
  encryptedClassName: "",
  parentClassName: "",
  animateOn: "hover",
})

const emit = defineEmits<{
  animationComplete: []
}>()

const containerRef = useTemplateRef<HTMLSpanElement>("containerRef")
const displayText = ref(props.text)
const isActive = ref(false)
const isScrambling = ref(false)
const revealedIndices = ref(new Set<number>())
const hasAnimated = ref(false)

let interval: ReturnType<typeof setInterval> | null = null
let intersectionObserver: IntersectionObserver | null = null

const displayChars = computed(() => Array.from(displayText.value))

function clearScramble() {
  if (interval) {
    clearInterval(interval)
    interval = null
  }
}

function getNextIndex(revealedSet: Set<number>) {
  const textLength = Array.from(props.text).length

  switch (props.revealDirection) {
    case "end":
      return textLength - 1 - revealedSet.size
    case "center": {
      const middle = Math.floor(textLength / 2)
      const offset = Math.floor(revealedSet.size / 2)
      const nextIndex = revealedSet.size % 2 === 0 ? middle + offset : middle - offset - 1

      if (nextIndex >= 0 && nextIndex < textLength && !revealedSet.has(nextIndex)) {
        return nextIndex
      }

      for (let i = 0; i < textLength; i += 1) {
        if (!revealedSet.has(i)) return i
      }

      return 0
    }
    case "start":
    default:
      return revealedSet.size
  }
}

function getAvailableCharacters() {
  if (!props.useOriginalCharsOnly) return Array.from(props.characters)

  return Array.from(new Set(Array.from(props.text))).filter((char) => !/\s/.test(char))
}

function shuffleText(originalText: string, currentRevealed: Set<number>) {
  const originalChars = Array.from(originalText)
  const availableChars = getAvailableCharacters()

  if (!availableChars.length) return originalText

  if (props.useOriginalCharsOnly) {
    const positions = originalChars.map((char, index) => ({
      char,
      index,
      isSpace: /\s/.test(char),
      isRevealed: currentRevealed.has(index),
    }))
    const unrevealedChars = positions
      .filter((position) => !position.isSpace && !position.isRevealed)
      .map((position) => position.char)

    for (let i = unrevealedChars.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[unrevealedChars[i], unrevealedChars[j]] = [unrevealedChars[j], unrevealedChars[i]]
    }

    let charIndex = 0
    return positions
      .map((position) => {
        if (position.isSpace) return position.char
        if (position.isRevealed) return originalChars[position.index]
        return unrevealedChars[charIndex++]
      })
      .join("")
  }

  return originalChars
    .map((char, index) => {
      if (/\s/.test(char)) return char
      if (currentRevealed.has(index)) return originalChars[index]
      return availableChars[Math.floor(Math.random() * availableChars.length)]
    })
    .join("")
}

function runScramble() {
  clearScramble()

  if (!isActive.value) {
    displayText.value = props.text
    revealedIndices.value = new Set()
    isScrambling.value = false
    return
  }

  let currentIteration = 0
  isScrambling.value = true
  displayText.value = shuffleText(props.text, revealedIndices.value)

  interval = setInterval(() => {
    if (props.sequential) {
      if (revealedIndices.value.size < Array.from(props.text).length) {
        const nextIndex = getNextIndex(revealedIndices.value)
        const nextRevealed = new Set(revealedIndices.value)
        nextRevealed.add(nextIndex)
        revealedIndices.value = nextRevealed
        displayText.value = shuffleText(props.text, nextRevealed)
        return
      }
    } else if (currentIteration < props.maxIterations) {
      displayText.value = shuffleText(props.text, revealedIndices.value)
      currentIteration += 1
      return
    }

    clearScramble()
    displayText.value = props.text
    isScrambling.value = false
    emit("animationComplete")
  }, props.speed)
}

function handleMouseEnter() {
  if (props.animateOn === "hover") {
    isActive.value = true
  }
}

function handleMouseLeave() {
  if (props.animateOn === "hover") {
    isActive.value = false
  }
}

watch(
  [
    () => isActive.value,
    () => props.text,
    () => props.speed,
    () => props.maxIterations,
    () => props.sequential,
    () => props.revealDirection,
    () => props.characters,
    () => props.useOriginalCharsOnly,
  ],
  runScramble,
)

onMounted(async () => {
  if (props.animateOn !== "view") return

  await nextTick()

  if (!("IntersectionObserver" in window)) {
    isActive.value = true
    hasAnimated.value = true
    return
  }

  intersectionObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting || hasAnimated.value) return
        isActive.value = true
        hasAnimated.value = true
        intersectionObserver?.disconnect()
      })
    },
    {
      rootMargin: "0px 0px -10% 0px",
      threshold: 0.15,
    },
  )

  if (containerRef.value) {
    intersectionObserver.observe(containerRef.value)
  }
})

onUnmounted(() => {
  clearScramble()
  intersectionObserver?.disconnect()
})
</script>

<template>
  <span
    ref="containerRef"
    :aria-label="props.text"
    :class="['decrypted-text', props.parentClassName]"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
    <span aria-hidden="true">
      <span
        v-for="(char, index) in displayChars"
        :key="`${char}-${index}`"
        :class="
          revealedIndices.has(index) || !isScrambling || !isActive
            ? props.className
            : props.encryptedClassName
        "
      >
        {{ char }}
      </span>
    </span>
  </span>
</template>
