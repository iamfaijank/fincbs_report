<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: [Number, String], required: true },
})

const roundedValue = computed(() => {
  const n = parseFloat(props.value) || 0
  const decimal = n - Math.floor(n)
  if (decimal > 0.5) return Math.ceil(n)
  return Math.floor(n)
})

const barColor = computed(() => {
  const v = Number(props.value)
  if (v >= 90) return 'bg-green-500'
  if (v >= 75) return 'bg-amber-500'
  return 'bg-red-500'
})

const width = computed(() => {
  const v = Math.min(Number(props.value) || 0, 100)
  return v + '%'
})
</script>

<template>
  <div class="flex items-center gap-2 w-full">
    <div class="relative h-2 flex-1 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
      <div
        class="h-full rounded-full transition-all duration-700 ease-out"
        :class="barColor"
        :style="{ width }"
      ></div>
    </div>
    <span class="w-10 text-right text-xs font-medium text-[var(--text)]">{{ roundedValue }}%</span>
  </div>
</template>
