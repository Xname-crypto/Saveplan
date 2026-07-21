<script setup lang="ts">
import { computed, onMounted, ref, useAttrs } from "vue"

defineOptions({
  inheritAttrs: false,
})

const props = withDefaults(defineProps<{
  modelValue: string
  id?: string
  name?: string
  type?: string
  caption?: string
  label: string
  required?: boolean
  disabled?: boolean
}>(), {
  id: "",
  name: "",
  type: "text",
  caption: "",
  required: false,
  disabled: false,
})

const emit = defineEmits<{
  "update:modelValue": [value: string]
}>()

const attrs = useAttrs()
const inputRef = ref<HTMLInputElement | null>(null)
const autofillRepaint = ref(false)
const labelChars = computed(() => Array.from(props.label))
const hasValue = computed(() => props.modelValue.trim().length > 0)

function updateValue(event: Event) {
  emit("update:modelValue", (event.target as HTMLInputElement).value)
}

function syncNativeValue() {
  const value = inputRef.value?.value ?? ""
  if (value && value !== props.modelValue) {
    emit("update:modelValue", value)
  }

  if (value) {
    autofillRepaint.value = true
    window.requestAnimationFrame(() => {
      autofillRepaint.value = false
    })
  }
}

onMounted(() => {
  syncNativeValue()
  window.requestAnimationFrame(syncNativeValue)
  window.setTimeout(syncNativeValue, 120)
  window.setTimeout(syncNativeValue, 500)
  window.setTimeout(syncNativeValue, 1200)
})
</script>

<template>
  <div class="auth-wave-field">
    <div v-if="caption || $slots['caption-action']" class="auth-wave-field__top">
      <span>{{ caption }}</span>
      <slot name="caption-action" />
    </div>
    <div
      class="auth-wave-field__control"
      :class="{
        'has-leading': $slots.leading,
        'has-trailing': $slots.trailing,
        'has-value': hasValue,
        'is-autofill-repaint': autofillRepaint,
      }"
    >
      <span v-if="$slots.leading" class="auth-wave-field__leading" aria-hidden="true">
        <slot name="leading" />
      </span>
      <input
        ref="inputRef"
        v-bind="attrs"
        :id="id"
        :name="name"
        :type="type"
        :value="modelValue"
        :required="required"
        :disabled="disabled"
        placeholder=" "
        @animationstart="syncNativeValue"
        @change="updateValue"
        @input="updateValue"
      />
      <label :for="id">
        <span
          v-for="(char, index) in labelChars"
          :key="`${char}-${index}`"
          :style="{ transitionDelay: `${index * 45}ms` }"
        >
          {{ char }}
        </span>
      </label>
      <span v-if="$slots.trailing" class="auth-wave-field__trailing">
        <slot name="trailing" />
      </span>
    </div>
  </div>
</template>

<style scoped>
.auth-wave-field {
  display: grid;
  gap: 0.35rem;
}

.auth-wave-field__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  color: rgba(255, 255, 255, 0.42);
  font-size: 0.72rem;
  font-weight: 800;
}

.auth-wave-field__control {
  position: relative;
  --auth-wave-left: 0rem;
  --auth-wave-right: 0rem;
  padding-top: 1.55rem;
}

.auth-wave-field__control.has-leading {
  --auth-wave-left: 2.05rem;
}

.auth-wave-field__control.has-trailing {
  --auth-wave-right: 2.7rem;
}

.auth-wave-field__control input {
  display: block;
  width: 100%;
  border: 0;
  border-bottom: 2px solid rgba(255, 255, 255, 0.34);
  border-radius: 0;
  background-color: transparent;
  color: #fff !important;
  -webkit-text-fill-color: #fff !important;
  caret-color: #9bd9ff;
  padding: 0.25rem var(--auth-wave-right) 0.9rem var(--auth-wave-left);
  font-size: 1.08rem;
  font-weight: 800;
  line-height: 1.5rem;
  outline: 0;
  transition:
    border-bottom-color 220ms ease,
    box-shadow 220ms ease,
    padding-left 180ms ease;
}

.auth-wave-field__control.has-value input,
.auth-wave-field__control.is-autofill-repaint input {
  font-family: inherit !important;
  font-size: 1.08rem !important;
  font-weight: 800 !important;
  line-height: 1.5rem !important;
  letter-spacing: 0 !important;
}

@keyframes auth-autofill-start {
  from {
    opacity: 0.999;
  }

  to {
    opacity: 1;
  }
}

.auth-wave-field__control.has-leading:has(input:focus) input,
.auth-wave-field__control.has-leading:has(input:not(:placeholder-shown)) input,
.auth-wave-field__control.has-leading:has(input:-webkit-autofill) input,
.auth-wave-field__control.has-leading.has-value input {
  padding-left: 0;
}

.auth-wave-field__control input::-ms-reveal,
.auth-wave-field__control input::-ms-clear {
  display: none;
}

.auth-wave-field__control input::-webkit-credentials-auto-fill-button,
.auth-wave-field__control input::-webkit-contacts-auto-fill-button {
  visibility: hidden;
  display: none !important;
  pointer-events: none;
}

.auth-wave-field__control input:focus,
.auth-wave-field__control input:not(:placeholder-shown),
.auth-wave-field__control input:-webkit-autofill,
.auth-wave-field__control.has-value input {
  border-bottom-color: #9bd9ff;
  box-shadow: 0 1px 0 rgba(155, 217, 255, 0.28);
}

.auth-wave-field__control input:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.auth-wave-field__control input:-webkit-autofill,
.auth-wave-field__control input:-webkit-autofill:hover,
.auth-wave-field__control input:-webkit-autofill:focus,
.auth-wave-field__control input:-webkit-autofill:active {
  color: #fff !important;
  -webkit-text-fill-color: #fff !important;
  -webkit-box-shadow: 0 0 0 1000px transparent inset;
  caret-color: #9bd9ff;
  font-family: inherit !important;
  font-size: 1.08rem !important;
  font-weight: 800 !important;
  line-height: 1.5rem !important;
  letter-spacing: 0 !important;
  appearance: none;
  -webkit-appearance: none;
  animation-name: auth-autofill-start;
  animation-duration: 1ms;
  transition: background-color 9999s ease-in-out 0s;
}

.auth-wave-field__control label {
  position: absolute;
  top: 1.8rem;
  left: var(--auth-wave-left);
  pointer-events: none;
  color: #fff;
  font-size: 1.08rem;
  font-weight: 800;
  line-height: 1.5rem;
}

.auth-wave-field__control label span {
  display: inline-block;
  min-width: 0.34rem;
  transition:
    color 300ms ease,
    transform 300ms cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.auth-wave-field__control input:focus + label span,
.auth-wave-field__control input:not(:placeholder-shown) + label span,
.auth-wave-field__control input:-webkit-autofill + label span,
.auth-wave-field__control.has-value label span {
  color: #9bd9ff;
  transform: translateY(-2.15rem);
}

.auth-wave-field__leading {
  position: absolute;
  left: 0.1rem;
  top: 1.96rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: rgba(226, 218, 194, 0.72);
  pointer-events: none;
  transition:
    color 300ms ease,
    transform 300ms cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.auth-wave-field__control:has(input:focus) .auth-wave-field__leading,
.auth-wave-field__control:has(input:not(:placeholder-shown)) .auth-wave-field__leading,
.auth-wave-field__control:has(input:-webkit-autofill) .auth-wave-field__leading,
.auth-wave-field__control.has-value .auth-wave-field__leading {
  color: #9bd9ff;
  transform: translateY(-2.16rem);
}

.auth-wave-field__leading :deep(svg) {
  width: 1.18rem;
  height: 1.18rem;
  stroke-width: 2.1;
}

.auth-wave-field__trailing {
  position: absolute;
  right: 0.15rem;
  top: 1.8rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: rgba(226, 218, 194, 0.72);
}

.auth-wave-field__trailing :deep(button) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: inherit;
  transform: none;
}

.auth-wave-field__trailing :deep(svg) {
  width: 1.18rem;
  height: 1.18rem;
}
</style>
