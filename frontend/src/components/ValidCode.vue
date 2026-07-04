<script setup lang="ts">
import { onMounted, ref } from "vue"

interface CodeItem {
  code: string
  color: string
  padding: string
  transform: string
}

const emit = defineEmits<{
  "update:value": [value: string]
}>()

const codeList = ref<CodeItem[]>([])
const chars = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz23456789"

function createCode() {
  const nextCode: CodeItem[] = []

  for (let index = 0; index < 4; index += 1) {
    const rgb = [
      Math.round(Math.random() * 80) + 90,
      Math.round(Math.random() * 80) + 90,
      Math.round(Math.random() * 60) + 70,
    ]

    nextCode.push({
      code: chars.charAt(Math.floor(Math.random() * chars.length)),
      color: `rgb(${rgb.join(",")})`,
      padding: `${Math.floor(Math.random() * 5)}px`,
      transform: `rotate(${Math.floor(Math.random() * 46) - 23}deg)`,
    })
  }

  codeList.value = nextCode
  emit("update:value", nextCode.map((item) => item.code).join(""))
}

function getStyle(item: CodeItem) {
  return {
    color: item.color,
    padding: item.padding,
    transform: item.transform,
  }
}

onMounted(createCode)

defineExpose({ refreshCode: createCode })
</script>

<template>
  <button class="valid-code" type="button" title="刷新验证码" aria-label="刷新验证码" @click="createCode">
    <span v-for="(item, index) in codeList" :key="`${item.code}-${index}`" :style="getStyle(item)">
      {{ item.code }}
    </span>
  </button>
</template>

<style scoped>
.valid-code {
  display: flex;
  min-height: 48px;
  width: 100%;
  align-items: center;
  justify-content: center;
  gap: 0.14rem;
  border: 1px solid rgba(226, 218, 194, 0.18);
  border-radius: 0.9rem;
  background:
    linear-gradient(135deg, rgba(226, 218, 194, 0.12), rgba(226, 218, 194, 0.035)),
    repeating-linear-gradient(45deg, rgba(226, 218, 194, 0.1) 0 1px, transparent 1px 7px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
  cursor: pointer;
  user-select: none;
}

.valid-code span {
  display: inline-block;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.15rem;
  font-weight: 800;
  line-height: 1;
  text-shadow: 0 1px 8px rgba(0, 0, 0, 0.35);
}
</style>
