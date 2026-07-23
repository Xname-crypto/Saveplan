<script setup lang="ts">
import { gsap } from "gsap"
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"

interface TargetCursorProps {
  targetSelector?: string
  spinDuration?: number
  hideDefaultCursor?: boolean
  hoverDuration?: number
  parallaxOn?: boolean
}

const props = withDefaults(defineProps<TargetCursorProps>(), {
  targetSelector: ".cursor-target",
  spinDuration: 2,
  hideDefaultCursor: true,
  hoverDuration: 0.2,
  parallaxOn: true,
})

const cursorRef = ref<HTMLDivElement | null>(null)
const dotRef = ref<HTMLDivElement | null>(null)
const cornersRef = ref<NodeListOf<HTMLDivElement> | null>(null)
const spinTl = ref<gsap.core.Timeline | null>(null)

const isActiveRef = ref(false)

const targetCornerPositionsRef = ref<{ x: number; y: number }[] | null>(null)
const tickerFnRef = ref<(() => void) | null>(null)
const activeStrengthRef = ref({ current: 0 })
const cursorEnabled = ref(true)
let setupFrame: number | null = null

const shouldUseCustomCursor = () => {
  if (typeof window === "undefined") return false
  if (window.innerWidth <= 768) return false

  const hasFinePointer = window.matchMedia?.("(pointer: fine)").matches
  const canHover = window.matchMedia?.("(hover: hover)").matches
  if (hasFinePointer || canHover) return true

  const hasCoarsePointer = window.matchMedia?.("(pointer: coarse)").matches
  const userAgent = navigator.userAgent || navigator.vendor
  const mobileRegex = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i
  const isMobileUserAgent = mobileRegex.test(userAgent.toLowerCase())

  return !(hasCoarsePointer || isMobileUserAgent || window.innerWidth <= 768)
}

const constants = {
  borderWidth: 3,
  cornerSize: 12,
}

const moveCursor = (x: number, y: number) => {
  if (!cursorRef.value) return

  gsap.to(cursorRef.value, {
    x,
    y,
    duration: 0.1,
    ease: "power3.out",
  })
}

let cleanupFn: (() => void) | null = null
const setup = () => {
  if (!cursorEnabled.value || !cursorRef.value) return

  const originalCursor = document.body.style.cursor

  if (props.hideDefaultCursor) {
    document.body.style.cursor = "none"
  }

  const cursor = cursorRef.value
  cornersRef.value = cursor.querySelectorAll<HTMLDivElement>(".target-cursor-corner")

  let activeTarget: Element | null = null
  let currentLeaveHandler: (() => void) | null = null
  let resumeTimeout: ReturnType<typeof setTimeout> | null = null
  let targetResizeObserver: ResizeObserver | null = null
  let pageMutationObserver: MutationObserver | null = null

  const updateTargetCorners = (target: Element) => {
    const rect = target.getBoundingClientRect()
    const { borderWidth, cornerSize } = constants

    targetCornerPositionsRef.value = [
      {
        x: rect.left - borderWidth,
        y: rect.top - borderWidth,
      },
      {
        x: rect.right + borderWidth - cornerSize,
        y: rect.top - borderWidth,
      },
      {
        x: rect.right + borderWidth - cornerSize,
        y: rect.bottom + borderWidth - cornerSize,
      },
      {
        x: rect.left - borderWidth,
        y: rect.bottom + borderWidth - cornerSize,
      },
    ]
  }

  const cleanupTarget = (target: Element) => {
    if (currentLeaveHandler) {
      target.removeEventListener("mouseleave", currentLeaveHandler)
    }

    targetResizeObserver?.disconnect()
    targetResizeObserver = null
    currentLeaveHandler = null
  }

  gsap.set(cursor, {
    xPercent: -50,
    yPercent: -50,
    x: window.innerWidth / 2,
    y: window.innerHeight / 2,
  })

  const createSpinTimeline = () => {
    if (spinTl.value) {
      spinTl.value.kill()
    }

    spinTl.value = gsap.timeline({ repeat: -1 }).to(cursor, {
      rotation: "+=360",
      duration: props.spinDuration,
      ease: "none",
    })
  }

  createSpinTimeline()

  const tickerFn = () => {
    if (!targetCornerPositionsRef.value || !cursorRef.value || !cornersRef.value) {
      return
    }

    const strength = activeStrengthRef.value.current
    if (strength === 0) return

    const cursorX = gsap.getProperty(cursorRef.value, "x") as number
    const cursorY = gsap.getProperty(cursorRef.value, "y") as number
    const corners = Array.from(cornersRef.value)

    corners.forEach((corner, i) => {
      const currentX = gsap.getProperty(corner, "x") as number
      const currentY = gsap.getProperty(corner, "y") as number

      const targetX = targetCornerPositionsRef.value![i]!.x - cursorX
      const targetY = targetCornerPositionsRef.value![i]!.y - cursorY
      const finalX = currentX + (targetX - currentX) * strength
      const finalY = currentY + (targetY - currentY) * strength

      const duration = strength >= 0.99 ? (props.parallaxOn ? 0.2 : 0) : 0.05

      gsap.to(corner, {
        x: finalX,
        y: finalY,
        duration,
        ease: duration === 0 ? "none" : "power1.out",
        overwrite: "auto",
      })
    })
  }

  tickerFnRef.value = tickerFn

  const moveHandler = (e: MouseEvent) => moveCursor(e.clientX, e.clientY)

  window.addEventListener("mousemove", moveHandler)

  const scrollHandler = () => {
    if (!activeTarget || !cursorRef.value) return

    const mouseX = gsap.getProperty(cursorRef.value, "x") as number
    const mouseY = gsap.getProperty(cursorRef.value, "y") as number

    const elementUnderMouse = document.elementFromPoint(mouseX, mouseY)

    const isStillOverTarget =
      elementUnderMouse &&
      (elementUnderMouse === activeTarget || elementUnderMouse.closest(props.targetSelector) === activeTarget)
    if (!isStillOverTarget) {
      currentLeaveHandler?.()
    } else {
      updateTargetCorners(activeTarget)
    }
  }

  window.addEventListener("scroll", scrollHandler, {
    passive: true,
  })

  const resizeHandler = () => {
    if (activeTarget) {
      updateTargetCorners(activeTarget)
    }
  }

  window.addEventListener("resize", resizeHandler, {
    passive: true,
  })

  pageMutationObserver = new MutationObserver(() => {
    if (activeTarget && document.contains(activeTarget)) {
      updateTargetCorners(activeTarget)
      return
    }

    currentLeaveHandler?.()
  })

  pageMutationObserver.observe(document.body, {
    attributes: true,
    childList: true,
    subtree: true,
  })

  const mouseDownHandler = () => {
    if (!dotRef.value || !cursorRef.value) return
    if (activeTarget) updateTargetCorners(activeTarget)

    gsap.to(dotRef.value, {
      scale: 0.7,
      duration: 0.3,
    })
    gsap.to(cursorRef.value, {
      scale: 0.9,
      duration: 0.2,
    })
  }

  const mouseUpHandler = () => {
    if (!dotRef.value || !cursorRef.value) return
    if (activeTarget) updateTargetCorners(activeTarget)

    gsap.to(dotRef.value, {
      scale: 1,
      duration: 0.3,
    })
    gsap.to(cursorRef.value, {
      scale: 1,
      duration: 0.2,
    })
  }

  window.addEventListener("mousedown", mouseDownHandler)
  window.addEventListener("mouseup", mouseUpHandler)

  const enterHandler = (e: MouseEvent) => {
    const directTarget = e.target as Element
    const allTargets: Element[] = []
    let current: Element | null = directTarget

    while (current && current !== document.body) {
      if (current.matches(props.targetSelector)) {
        allTargets.push(current)
      }

      current = current.parentElement
    }

    const target = allTargets[0] || null
    if (!target || !cursorRef.value || !cornersRef.value) return
    if (activeTarget === target) return
    if (activeTarget) {
      cleanupTarget(activeTarget)
    }

    if (resumeTimeout) {
      clearTimeout(resumeTimeout)
      resumeTimeout = null
    }

    activeTarget = target

    const corners = Array.from(cornersRef.value)
    corners.forEach((corner) => gsap.killTweensOf(corner))

    gsap.killTweensOf(cursorRef.value, "rotation")

    spinTl.value?.pause()

    gsap.set(cursorRef.value, {
      rotation: 0,
    })

    const cursorX = gsap.getProperty(cursorRef.value, "x") as number
    const cursorY = gsap.getProperty(cursorRef.value, "y") as number
    updateTargetCorners(target)
    targetResizeObserver?.disconnect()
    targetResizeObserver = new ResizeObserver(() => {
      if (activeTarget) {
        updateTargetCorners(activeTarget)
      }
    })
    targetResizeObserver.observe(target)

    isActiveRef.value = true
    gsap.ticker.add(tickerFnRef.value!)

    gsap.to(activeStrengthRef.value, {
      current: 1,
      duration: props.hoverDuration,
      ease: "power2.out",
    })

    corners.forEach((corner, i) => {
      gsap.to(corner, {
        x: targetCornerPositionsRef.value![i]!.x - cursorX,
        y: targetCornerPositionsRef.value![i]!.y - cursorY,
        duration: 0.2,
        ease: "power2.out",
      })
    })

    const leaveHandler = () => {
      if (resumeTimeout) {
        clearTimeout(resumeTimeout)
        resumeTimeout = null
      }

      gsap.ticker.remove(tickerFnRef.value!)
      isActiveRef.value = false
      targetCornerPositionsRef.value = null
      gsap.set(activeStrengthRef.value, {
        current: 0,
        overwrite: true,
      })

      activeTarget = null

      if (cornersRef.value) {
        const corners = Array.from(cornersRef.value)
        gsap.killTweensOf(corners)

        const { cornerSize } = constants

        const positions = [
          {
            x: -cornerSize * 1.5,
            y: -cornerSize * 1.5,
          },
          {
            x: cornerSize * 0.5,
            y: -cornerSize * 1.5,
          },
          {
            x: cornerSize * 0.5,
            y: cornerSize * 0.5,
          },
          {
            x: -cornerSize * 1.5,
            y: cornerSize * 0.5,
          },
        ]

        const tl = gsap.timeline()

        corners.forEach((corner, index) => {
          tl.to(
            corner,
            {
              x: positions[index]!.x,
              y: positions[index]!.y,
              duration: 0.3,
              ease: "power3.out",
            },
            0,
          )
        })
      }

      resumeTimeout = setTimeout(() => {
        if (!activeTarget && cursorRef.value && spinTl.value) {
          const currentRotation = gsap.getProperty(cursorRef.value, "rotation") as number

          const normalizedRotation = currentRotation % 360

          spinTl.value.kill()

          spinTl.value = gsap.timeline({ repeat: -1 }).to(cursorRef.value, {
            rotation: "+=360",
            duration: props.spinDuration,
            ease: "none",
          })

          gsap.to(cursorRef.value, {
            rotation: normalizedRotation + 360,
            duration: props.spinDuration * (1 - normalizedRotation / 360),
            ease: "none",
            onComplete: () => {
              spinTl.value?.restart()
            },
          })
        }

        resumeTimeout = null
      }, 50)

      cleanupTarget(target)
    }

    currentLeaveHandler = leaveHandler

    target.addEventListener("mouseleave", leaveHandler)
  }

  window.addEventListener("mouseover", enterHandler as EventListener)

  cleanupFn = () => {
    if (tickerFnRef.value) {
      gsap.ticker.remove(tickerFnRef.value)
    }

    window.removeEventListener("mousemove", moveHandler)
    window.removeEventListener("mouseover", enterHandler as EventListener)
    window.removeEventListener("scroll", scrollHandler)
    window.removeEventListener("resize", resizeHandler)
    window.removeEventListener("mousedown", mouseDownHandler)
    window.removeEventListener("mouseup", mouseUpHandler)
    pageMutationObserver?.disconnect()
    pageMutationObserver = null

    if (resumeTimeout) {
      clearTimeout(resumeTimeout)
      resumeTimeout = null
    }

    if (activeTarget) {
      cleanupTarget(activeTarget)
    }

    spinTl.value?.kill()
    document.body.style.cursor = originalCursor
    isActiveRef.value = false
    targetCornerPositionsRef.value = null
    activeStrengthRef.value.current = 0
  }
}

onMounted(() => {
  cursorEnabled.value = shouldUseCustomCursor()

  void nextTick(() => {
    setupFrame = window.requestAnimationFrame(() => {
      setupFrame = null
      setup()
    })
  })
})

onBeforeUnmount(() => {
  if (setupFrame !== null) {
    window.cancelAnimationFrame(setupFrame)
    setupFrame = null
  }
  cleanupFn?.()
})

watch(
  () => [props.targetSelector, props.spinDuration, props.hideDefaultCursor, props.hoverDuration, props.parallaxOn],
  () => {
    cleanupFn?.()
    void nextTick(() => setup())
  },
)

watch(
  () => props.spinDuration,
  () => {
    if (!cursorEnabled.value || !cursorRef.value || !spinTl.value) {
      return
    }

    if (spinTl.value.isActive()) {
      spinTl.value.kill()

      spinTl.value = gsap.timeline({ repeat: -1 }).to(cursorRef.value, {
        rotation: "+=360",
        duration: props.spinDuration,
        ease: "none",
      })
    }
  },
)
</script>

<template>
  <div
    v-if="cursorEnabled"
    ref="cursorRef"
    class="target-cursor"
    :style="{ willChange: 'transform' }"
  >
    <div
      ref="dotRef"
      class="target-cursor-dot"
      :style="{ willChange: 'transform' }"
    />

    <div
      class="target-cursor-corner target-cursor-corner--tl"
      :style="{ willChange: 'transform' }"
    />

    <div
      class="target-cursor-corner target-cursor-corner--tr"
      :style="{ willChange: 'transform' }"
    />

    <div
      class="target-cursor-corner target-cursor-corner--br"
      :style="{ willChange: 'transform' }"
    />

    <div
      class="target-cursor-corner target-cursor-corner--bl"
      :style="{ willChange: 'transform' }"
    />
  </div>
</template>

<style scoped>
.target-cursor,
.target-cursor * {
  pointer-events: none;
}

.target-cursor {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 9999;
  width: 0;
  height: 0;
  color: #ffffff;
  mix-blend-mode: difference;
}

.target-cursor-dot,
.target-cursor-corner {
  position: absolute;
  top: 50%;
  left: 50%;
}

.target-cursor-dot {
  width: 4px;
  height: 4px;
  border-radius: 999px;
  background: currentColor;
  transform: translate(-50%, -50%);
}

.target-cursor-corner {
  width: 12px;
  height: 12px;
  border-color: currentColor;
  border-style: solid;
  border-width: 3px;
}

.target-cursor-corner--tl {
  border-right: 0;
  border-bottom: 0;
  transform: translate(-150%, -150%);
}

.target-cursor-corner--tr {
  border-bottom: 0;
  border-left: 0;
  transform: translate(50%, -150%);
}

.target-cursor-corner--br {
  border-top: 0;
  border-left: 0;
  transform: translate(50%, 50%);
}

.target-cursor-corner--bl {
  border-top: 0;
  border-right: 0;
  transform: translate(-150%, 50%);
}
</style>
