<script setup lang="ts">
import { computed } from "vue"
import { Quote } from "lucide-vue-next"

type MovingCard = {
  quote: string
  name: string
  title: string
  avatar?: string
}

const props = withDefaults(
  defineProps<{
    items: MovingCard[]
    direction?: "left" | "right"
    speed?: "fast" | "normal" | "slow"
    pauseOnHover?: boolean
    ariaLabel?: string
  }>(),
  {
    direction: "left",
    speed: "normal",
    pauseOnHover: true,
    ariaLabel: "Moving cards",
  },
)

const loopItems = computed(() => [...props.items, ...props.items])
const duration = computed(() => {
  if (props.speed === "fast") return "24s"
  if (props.speed === "slow") return "72s"
  return "44s"
})
</script>

<template>
  <div
    :class="[
      'infinite-moving-cards',
      {
        'infinite-moving-cards--reverse': direction === 'right',
        'infinite-moving-cards--pause': pauseOnHover,
      },
    ]"
    :style="{ '--infinite-moving-cards-duration': duration }"
    role="region"
    :aria-label="ariaLabel"
  >
    <ul class="infinite-moving-cards__track">
      <li
        v-for="(item, index) in loopItems"
        :key="`${item.name}-${index}`"
        class="infinite-moving-cards__item"
        :aria-hidden="index >= items.length"
      >
        <blockquote>
          <span class="infinite-moving-cards__quote-icon" aria-hidden="true">
            <Quote :size="13" :stroke-width="3" />
          </span>
          <p>{{ item.quote }}</p>
          <footer>
            <img
              v-if="item.avatar"
              class="infinite-moving-cards__avatar"
              :src="item.avatar"
              :alt="`${item.name} 头像`"
              loading="lazy"
            />
            <span v-else class="infinite-moving-cards__avatar" aria-hidden="true">
              {{ item.name.slice(0, 1) }}
            </span>
            <strong>{{ item.name }}</strong>
            <span class="infinite-moving-cards__meta">{{ item.title }}</span>
          </footer>
        </blockquote>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.infinite-moving-cards {
  position: relative;
  overflow: hidden;
  width: 100%;
  padding: 0.35rem 0;
  mask-image: linear-gradient(90deg, transparent, #000 11%, #000 89%, transparent);
}

.infinite-moving-cards__track {
  display: flex;
  width: max-content;
  min-width: 100%;
  gap: 1rem;
  margin: 0;
  padding: 0;
  list-style: none;
  animation: infinite-moving-cards-scroll var(--infinite-moving-cards-duration) linear infinite;
  will-change: transform;
}

.infinite-moving-cards--reverse .infinite-moving-cards__track {
  animation-direction: reverse;
}

.infinite-moving-cards--pause:hover .infinite-moving-cards__track {
  animation-play-state: paused;
}

.infinite-moving-cards__item {
  position: relative;
  flex: 0 0 min(19.75rem, calc(100vw - 2.5rem));
  overflow: hidden;
  border: 1px solid rgba(235, 228, 207, 0.14);
  border-radius: 0.85rem;
  background: #171717;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.035),
    0 18px 38px rgba(0, 0, 0, 0.2);
}

.infinite-moving-cards__item blockquote {
  display: flex;
  min-height: 14.1rem;
  flex-direction: column;
  margin: 0;
  padding: 1.05rem 1rem 1.15rem;
}

.infinite-moving-cards__quote-icon {
  display: inline-flex;
  width: 1.18rem;
  height: 1.18rem;
  align-items: center;
  justify-content: center;
  border: 1.5px solid rgba(241, 234, 213, 0.88);
  border-radius: 0.25rem;
  color: #f1ead5;
  line-height: 1;
}

.infinite-moving-cards__quote-icon svg {
  display: block;
  flex: 0 0 auto;
}

.infinite-moving-cards__item p {
  margin: 1.15rem 0 0;
  color: rgba(241, 241, 241, 0.92);
  font-size: 0.93rem;
  font-weight: 800;
  line-height: 1.75;
}

.infinite-moving-cards__item footer {
  display: grid;
  grid-template-columns: 2.45rem minmax(0, 1fr);
  align-items: center;
  gap: 0.75rem;
  margin-top: auto;
  border-top: 1px solid rgba(235, 228, 207, 0.08);
  padding-top: 1.05rem;
}

.infinite-moving-cards__avatar {
  display: inline-grid;
  width: 2.45rem;
  height: 2.45rem;
  place-items: center;
  overflow: hidden;
  border: 1px solid rgba(235, 228, 207, 0.18);
  border-radius: 50%;
  background:
    radial-gradient(circle at 35% 25%, rgba(255, 235, 190, 0.95), transparent 23%),
    linear-gradient(140deg, #6f7f57, #b8785e 54%, #2d2d2d);
  color: #f7ead1;
  font-size: 0.88rem;
  font-weight: 900;
  letter-spacing: 0;
}

img.infinite-moving-cards__avatar {
  display: block;
  object-fit: cover;
}

.infinite-moving-cards__item strong {
  color: #f5f5f5;
  font-size: 0.98rem;
  font-weight: 900;
  letter-spacing: 0;
}

.infinite-moving-cards__meta {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

@keyframes infinite-moving-cards-scroll {
  to {
    transform: translate3d(calc(-50% - 0.5rem), 0, 0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .infinite-moving-cards {
    overflow: visible;
    mask-image: none;
  }

  .infinite-moving-cards__track {
    flex-wrap: wrap;
    width: auto;
    animation: none;
  }
}
</style>
