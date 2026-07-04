<script setup lang="ts">
import { computed, ref } from 'vue';
import type { Component } from 'vue';
import { Check } from 'lucide-vue-next';

interface InterestItem {
  id: string;
  label: string;
  icon: Component;
}

interface ChromaTheme {
  accent: string;
  glow: string;
  gradient: string;
}

const props = withDefaults(
  defineProps<{
    items: InterestItem[];
    selected: string[];
    maxSelected?: number;
  }>(),
  {
    maxSelected: 3,
  }
);

const emit = defineEmits<{
  toggle: [id: string];
}>();

const stageRef = ref<HTMLElement | null>(null);
const spotlightRef = ref<HTMLElement | null>(null);

const themeMap: Record<string, ChromaTheme> = {
  'question-bank': {
    accent: '#ded6bd',
    glow: 'rgba(222, 214, 189, 0.18)',
    gradient:
      'linear-gradient(155deg, rgba(78, 60, 42, 0.94) 0%, rgba(22, 21, 18, 0.96) 48%, rgba(10, 10, 9, 0.98) 100%)',
  },
  ocr: {
    accent: '#c9b982',
    glow: 'rgba(201, 185, 130, 0.18)',
    gradient:
      'linear-gradient(155deg, rgba(63, 54, 39, 0.94) 0%, rgba(20, 20, 18, 0.96) 52%, rgba(8, 9, 9, 0.98) 100%)',
  },
  focus: {
    accent: '#e7d7ac',
    glow: 'rgba(231, 215, 172, 0.18)',
    gradient:
      'linear-gradient(155deg, rgba(69, 47, 34, 0.92) 0%, rgba(22, 20, 17, 0.96) 50%, rgba(11, 10, 9, 0.99) 100%)',
  },
  planning: {
    accent: '#eee6ce',
    glow: 'rgba(238, 230, 206, 0.17)',
    gradient:
      'linear-gradient(155deg, rgba(74, 62, 45, 0.94) 0%, rgba(23, 22, 19, 0.96) 46%, rgba(9, 9, 8, 0.99) 100%)',
  },
  campus: {
    accent: '#d8c995',
    glow: 'rgba(216, 201, 149, 0.16)',
    gradient:
      'linear-gradient(155deg, rgba(55, 44, 34, 0.94) 0%, rgba(21, 20, 18, 0.96) 52%, rgba(8, 8, 8, 0.99) 100%)',
  },
  memory: {
    accent: '#cabd9b',
    glow: 'rgba(202, 189, 155, 0.16)',
    gradient:
      'linear-gradient(155deg, rgba(48, 43, 36, 0.94) 0%, rgba(20, 20, 18, 0.97) 50%, rgba(8, 8, 8, 0.99) 100%)',
  },
  challenge: {
    accent: '#f1dfb6',
    glow: 'rgba(241, 223, 182, 0.17)',
    gradient:
      'linear-gradient(155deg, rgba(76, 55, 38, 0.94) 0%, rgba(22, 20, 17, 0.97) 50%, rgba(8, 8, 8, 0.99) 100%)',
  },
};

const selectedSet = computed(() => new Set(props.selected));

const getTheme = (id: string): ChromaTheme =>
  themeMap[id] ?? {
    accent: '#ded6bd',
    glow: 'rgba(222, 214, 189, 0.18)',
    gradient:
      'linear-gradient(155deg, rgba(59, 48, 36, 0.94) 0%, rgba(22, 21, 18, 0.96) 50%, rgba(9, 9, 8, 0.99) 100%)',
  };

const isSelected = (id: string) => selectedSet.value.has(id);

const isLocked = (id: string) =>
  props.selected.length >= props.maxSelected && !isSelected(id);

const updateSpotlight = (event: PointerEvent) => {
  const stage = stageRef.value;
  const spotlight = spotlightRef.value;

  if (!stage || !spotlight) {
    return;
  }

  const rect = stage.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;

  spotlight.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%)`;
  spotlight.style.opacity = '1';
  stage.style.setProperty('--grid-x', `${x}px`);
  stage.style.setProperty('--grid-y', `${y}px`);
};

const hideSpotlight = () => {
  if (spotlightRef.value) {
    spotlightRef.value.style.opacity = '0';
  }
};

const updateCardGlow = (event: MouseEvent) => {
  const card = event.currentTarget as HTMLElement;
  const rect = card.getBoundingClientRect();
  card.style.setProperty('--pointer-x', `${event.clientX - rect.left}px`);
  card.style.setProperty('--pointer-y', `${event.clientY - rect.top}px`);
};

const resetCardGlow = (event: MouseEvent) => {
  const card = event.currentTarget as HTMLElement;
  card.style.setProperty('--pointer-x', '50%');
  card.style.setProperty('--pointer-y', '50%');
};

const handleCardClick = (id: string, event: MouseEvent) => {
  const card = event.currentTarget as HTMLElement;
  const icon = card.querySelector('.interest-chroma__icon-shell') as HTMLElement | null;
  const wave = card.querySelector('.interest-chroma__tap-wave') as HTMLElement | null;
  const willSelect = !isSelected(id);

  emit('toggle', id);

  card.animate(
    [
      { transform: 'translateY(0) scale(1)' },
      { transform: 'translateY(1px) scale(0.97)' },
      { transform: willSelect ? 'translateY(-6px) scale(1.035)' : 'translateY(-3px) scale(1.01)' },
      { transform: 'translateY(0) scale(1)' },
    ],
    {
      duration: 420,
      easing: 'cubic-bezier(0.22, 1, 0.36, 1)',
    }
  );

  icon?.animate(
    [
      { transform: 'scale(1)', offset: 0 },
      { transform: 'scale(0.92)', offset: 0.22 },
      { transform: 'scale(1.12)', offset: 0.55 },
      { transform: 'scale(1)', offset: 1 },
    ],
    {
      duration: 420,
      easing: 'cubic-bezier(0.22, 1, 0.36, 1)',
    }
  );

  wave?.animate(
    [
      { opacity: 0, transform: 'scale(0.4)' },
      { opacity: willSelect ? 0.5 : 0.32, transform: 'scale(1)' },
      { opacity: 0, transform: 'scale(1.85)' },
    ],
    {
      duration: 520,
      easing: 'cubic-bezier(0.16, 1, 0.3, 1)',
    }
  );
};

const cardStyle = (item: InterestItem, index: number) => {
  const theme = getTheme(item.id);

  return {
    '--card-accent': theme.accent,
    '--card-glow': theme.glow,
    '--card-gradient': theme.gradient,
    animationDelay: `${index * 120}ms`,
  } as Record<string, string>;
};
</script>

<template>
  <div class="interest-chroma">
    <div class="interest-chroma__toolbar">
      <span class="interest-chroma__eyebrow">CHROMA</span>
      <span class="interest-chroma__counter">{{ selected.length }}/{{ maxSelected }}</span>
    </div>

    <div
      ref="stageRef"
      class="interest-chroma__stage"
      @pointermove="updateSpotlight"
      @pointerleave="hideSpotlight"
    >
      <div ref="spotlightRef" class="interest-chroma__spotlight"></div>

      <div class="interest-chroma__grid">
        <button
          v-for="(item, index) in items"
          :key="item.id"
          type="button"
          class="interest-chroma__card"
          :class="{
            'is-selected': isSelected(item.id),
            'is-locked': isLocked(item.id),
          }"
          :style="cardStyle(item, index)"
          :aria-pressed="isSelected(item.id)"
          :disabled="isLocked(item.id)"
          @click="handleCardClick(item.id, $event)"
          @mousemove="updateCardGlow"
          @mouseleave="resetCardGlow"
        >
          <span class="interest-chroma__tap-wave"></span>
          <span class="interest-chroma__card-shine"></span>

          <span class="interest-chroma__card-content">
            <span class="interest-chroma__icon-shell">
              <component :is="item.icon" class="h-5 w-5" />
            </span>
            <span class="interest-chroma__label">{{ item.label }}</span>
          </span>

          <span class="interest-chroma__check">
            <Check class="h-3.5 w-3.5" />
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.interest-chroma {
  position: relative;
}

.interest-chroma__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0 0.25rem 0.35rem;
}

.interest-chroma__eyebrow {
  font-size: 0.64rem;
  font-weight: 700;
  letter-spacing: 0.36em;
  color: rgba(226, 218, 194, 0.4);
}

.interest-chroma__counter {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2.75rem;
  border-radius: 999px;
  border: 1px solid rgba(226, 218, 194, 0.16);
  background: rgba(226, 218, 194, 0.055);
  padding: 0.34rem 0.72rem;
  font-size: 0.72rem;
  font-weight: 700;
  color: rgba(226, 218, 194, 0.64);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.interest-chroma__stage {
  --grid-x: 50%;
  --grid-y: 50%;
  position: relative;
  overflow: visible;
  padding: 0.15rem 0 0.3rem;
}

.interest-chroma__stage::before {
  content: '';
  position: absolute;
  inset: 0.15rem -0.35rem -0.2rem;
  z-index: 0;
  background:
    radial-gradient(circle at 14% 18%, rgba(226, 218, 194, 0.12), transparent 30%),
    radial-gradient(circle at 84% 88%, rgba(154, 116, 77, 0.12), transparent 32%),
    radial-gradient(circle at var(--grid-x) var(--grid-y), rgba(226, 218, 194, 0.08), transparent 36%);
  filter: blur(18px);
  opacity: 0.78;
  pointer-events: none;
}

.interest-chroma__stage::after {
  content: none;
}

.interest-chroma__spotlight {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 0;
  width: 240px;
  height: 240px;
  border-radius: 999px;
  pointer-events: none;
  opacity: 0;
  background:
    radial-gradient(circle, rgba(226, 218, 194, 0.26) 0%, rgba(226, 218, 194, 0.12) 30%, rgba(154, 116, 77, 0.08) 56%, transparent 76%);
  filter: blur(20px);
  transition:
    transform 320ms cubic-bezier(0.22, 1, 0.36, 1),
    opacity 240ms ease;
  transform: translate(-50%, -50%);
}

.interest-chroma__grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.9rem;
}

.interest-chroma__card {
  --pointer-x: 50%;
  --pointer-y: 50%;
  position: relative;
  isolation: isolate;
  display: block;
  aspect-ratio: 1 / 1;
  overflow: hidden;
  border: 1px solid rgba(226, 218, 194, 0.1);
  border-radius: 0.55rem;
  background:
    linear-gradient(180deg, rgba(226, 218, 194, 0.06) 0%, rgba(226, 218, 194, 0.025) 48%, rgba(0, 0, 0, 0.05) 100%),
    var(--card-gradient);
  background-size: 160% 160%;
  padding: 0.85rem 0.55rem 0.7rem;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.07),
    0 12px 26px rgba(0, 0, 0, 0.18);
  transition:
    transform 360ms cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 320ms ease,
    opacity 240ms ease,
    filter 240ms ease;
  animation: chroma-drift 11s ease-in-out infinite alternate;
}

.interest-chroma__card::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  background:
    radial-gradient(circle at var(--pointer-x) var(--pointer-y), rgba(226, 218, 194, 0.16), transparent 42%),
    radial-gradient(circle at 50% 100%, rgba(226, 218, 194, 0.08), transparent 60%);
  opacity: 0;
  transition: opacity 240ms ease;
}

.interest-chroma__card::after {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  background:
    radial-gradient(circle at top left, var(--card-glow) 0%, transparent 54%),
    linear-gradient(180deg, rgba(226, 218, 194, 0.06) 0%, transparent 64%);
  opacity: 0.75;
  pointer-events: none;
}

.interest-chroma__card:hover,
.interest-chroma__card:focus-visible,
.interest-chroma__card.is-selected {
  transform: translateY(-5px) scale(1.025);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.1),
    0 18px 32px rgba(0, 0, 0, 0.3),
    0 0 22px var(--card-glow);
}

.interest-chroma__card:hover::before,
.interest-chroma__card:focus-visible::before,
.interest-chroma__card.is-selected::before {
  opacity: 1;
}

.interest-chroma__card.is-selected {
  border-color: rgba(226, 218, 194, 0.36);
  background:
    linear-gradient(180deg, rgba(226, 218, 194, 0.16) 0%, rgba(226, 218, 194, 0.07) 48%, rgba(0, 0, 0, 0.02) 100%),
    var(--card-gradient);
}

.interest-chroma__card.is-locked {
  opacity: 0.5;
  filter: saturate(0.74) grayscale(0.08);
  cursor: not-allowed;
}

.interest-chroma__tap-wave,
.interest-chroma__card-shine {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
}

.interest-chroma__tap-wave {
  z-index: 1;
  opacity: 0;
  background:
    radial-gradient(circle at var(--pointer-x) var(--pointer-y), rgba(226, 218, 194, 0.3) 0%, var(--card-glow) 24%, transparent 52%);
  transform: scale(0.4);
}

.interest-chroma__card-shine {
  z-index: 1;
  background: linear-gradient(180deg, rgba(226, 218, 194, 0.12), transparent 42%);
  opacity: 0.5;
}

.interest-chroma__card-content {
  position: relative;
  z-index: 2;
  display: flex;
  height: 100%;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.7rem;
}

.interest-chroma__icon-shell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  height: 3rem;
  border: 1px solid rgba(226, 218, 194, 0.12);
  border-radius: 999px;
  color: var(--card-accent);
  background:
    radial-gradient(circle at 30% 30%, rgba(226, 218, 194, 0.16) 0%, rgba(226, 218, 194, 0.07) 44%, rgba(0, 0, 0, 0.08) 100%),
    radial-gradient(circle at 72% 76%, var(--card-glow) 0%, transparent 72%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    0 10px 18px rgba(0, 0, 0, 0.18),
    0 0 18px var(--card-glow);
}

.interest-chroma__label {
  font-size: 0.8rem;
  font-weight: 700;
  line-height: 1.1;
  color: rgba(238, 230, 206, 0.74);
  letter-spacing: 0.08em;
  text-shadow: none;
}

.interest-chroma__card.is-selected .interest-chroma__label {
  color: #eee6ce;
}

.interest-chroma__check {
  position: absolute;
  top: 0.55rem;
  right: 0.55rem;
  z-index: 3;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.55rem;
  height: 1.55rem;
  border-radius: 999px;
  background: #ded6bd;
  color: #171611;
  backdrop-filter: blur(8px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.24);
  opacity: 0;
  transform: scale(0.72);
  transition:
    opacity 220ms ease,
    transform 280ms cubic-bezier(0.22, 1, 0.36, 1);
}

.interest-chroma__card.is-selected .interest-chroma__check {
  opacity: 1;
  transform: scale(1);
}

@keyframes chroma-drift {
  0% {
    background-position: 0% 12%;
  }

  100% {
    background-position: 100% 88%;
  }
}

@media (max-width: 420px) {
  .interest-chroma__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
