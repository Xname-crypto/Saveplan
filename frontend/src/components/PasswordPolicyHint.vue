<script setup lang="ts">
import { computed } from "vue"
import { getPasswordPolicyChecks, getPasswordStrengthLabel } from "@/services/passwordPolicy"

const props = defineProps<{
  password: string
}>()

const checks = computed(() => getPasswordPolicyChecks(props.password))
const strengthLabel = computed(() => getPasswordStrengthLabel(props.password))
const strengthClass = computed(() => {
  if (strengthLabel.value === "强") return "is-strong"
  if (strengthLabel.value === "中") return "is-medium"
  return "is-weak"
})
</script>

<template>
  <div class="password-policy-hint group relative inline-flex items-center">
    <button
      type="button"
      class="password-policy-hint__trigger"
      aria-label="查看密码要求"
      title="查看密码要求"
    >
      <span class="password-policy-hint__mark" aria-hidden="true">i</span>
    </button>

    <div class="password-policy-hint__panel" :class="strengthClass">
      <div class="password-policy-hint__head">
        <span>密码要求</span>
        <span class="password-policy-hint__strength">当前 {{ strengthLabel }}</span>
      </div>
      <ul class="password-policy-hint__list">
        <li v-for="check in checks" :key="check.key" :class="{ 'is-ok': check.ok }">
          <span class="password-policy-hint__dot" aria-hidden="true"></span>
          <span>{{ check.label }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.password-policy-hint {
  flex: 0 0 auto;
}

.password-policy-hint__trigger {
  display: grid;
  width: 1.35rem;
  height: 1.35rem;
  place-items: center;
  border: 1px solid rgba(226, 218, 194, 0.24);
  border-radius: 999px;
  background: rgba(226, 218, 194, 0.05);
  color: rgba(238, 230, 206, 0.72);
  cursor: help;
  transition:
    border-color 180ms ease,
    background-color 180ms ease,
    color 180ms ease,
    transform 180ms ease;
}

.password-policy-hint__mark {
  font-size: 0.78rem;
  font-weight: 900;
  line-height: 1;
}

.password-policy-hint:hover .password-policy-hint__trigger,
.password-policy-hint:focus-within .password-policy-hint__trigger {
  border-color: rgba(155, 217, 255, 0.72);
  background: rgba(155, 217, 255, 0.11);
  color: #9bd9ff;
  transform: translateY(-1px);
}

.password-policy-hint__panel {
  position: absolute;
  right: 0;
  bottom: calc(100% + 0.6rem);
  z-index: 20;
  width: min(15.75rem, calc(100vw - 2rem));
  border: 1px solid rgba(226, 218, 194, 0.14);
  border-radius: 0.72rem;
  background: rgba(14, 15, 18, 0.94);
  padding: 0.8rem 0.85rem 0.78rem;
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.28);
  opacity: 0;
  pointer-events: none;
  transform: translateY(0.22rem) scale(0.98);
  transform-origin: bottom right;
  transition:
    opacity 160ms ease,
    transform 160ms ease,
    border-color 160ms ease;
}

.password-policy-hint:hover .password-policy-hint__panel,
.password-policy-hint:focus-within .password-policy-hint__panel {
  opacity: 1;
  pointer-events: auto;
  transform: translateY(0) scale(1);
}

.password-policy-hint__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.8rem;
  color: #eee6ce;
  font-size: 0.74rem;
  font-weight: 900;
  letter-spacing: 0.02em;
}

.password-policy-hint__strength {
  color: rgba(238, 230, 206, 0.56);
  font-size: 0.68rem;
  font-weight: 800;
}

.password-policy-hint__panel.is-strong {
  border-color: rgba(123, 220, 171, 0.24);
}

.password-policy-hint__panel.is-medium {
  border-color: rgba(238, 206, 126, 0.26);
}

.password-policy-hint__panel.is-weak {
  border-color: rgba(255, 121, 121, 0.24);
}

.password-policy-hint__list {
  display: grid;
  gap: 0.46rem;
  margin: 0.72rem 0 0;
  padding: 0;
  list-style: none;
}

.password-policy-hint__list li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: rgba(226, 218, 194, 0.62);
  font-size: 0.72rem;
  font-weight: 700;
}

.password-policy-hint__list li.is-ok {
  color: #c5f6d8;
}

.password-policy-hint__dot {
  width: 0.42rem;
  height: 0.42rem;
  flex: 0 0 auto;
  border-radius: 999px;
  background: rgba(226, 218, 194, 0.34);
}

.password-policy-hint__list li.is-ok .password-policy-hint__dot {
  background: #7bdcab;
}

:global(html[data-theme="day"] .password-policy-hint__trigger) {
  border-color: rgba(52, 93, 117, 0.22);
  background: rgba(255, 255, 255, 0.8);
  color: #345d75;
}

:global(html[data-theme="day"] .password-policy-hint:hover .password-policy-hint__trigger),
:global(html[data-theme="day"] .password-policy-hint:focus-within .password-policy-hint__trigger) {
  border-color: rgba(52, 93, 117, 0.56);
  background: #345d75;
  color: #fff;
}

:global(html[data-theme="day"] .password-policy-hint__panel) {
  border-color: rgba(31, 41, 51, 0.12);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 16px 36px rgba(44, 64, 82, 0.14);
}

:global(html[data-theme="day"] .password-policy-hint__head) {
  color: #1f2933;
}

:global(html[data-theme="day"] .password-policy-hint__strength) {
  color: rgba(31, 41, 51, 0.52);
}

:global(html[data-theme="day"] .password-policy-hint__list li) {
  color: rgba(31, 41, 51, 0.72);
}

:global(html[data-theme="day"] .password-policy-hint__list li.is-ok) {
  color: #1f6b44;
}

:global(html[data-theme="day"] .password-policy-hint__dot) {
  background: rgba(31, 41, 51, 0.24);
}

:global(html[data-theme="day"] .password-policy-hint__list li.is-ok .password-policy-hint__dot) {
  background: #1f6b44;
}
</style>
