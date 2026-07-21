<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: [Number, String], required: true },
})

const colorClass = computed(() => {
  const v = Number(props.value)
  if (v >= 90) return 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400'
  if (v >= 75) return 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400'
  return 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'
})
</script>

<template>
  <span class="inline-block rounded px-2 py-0.5 text-xs font-medium" :class="colorClass">
    {{ value }}%
  </span>
</template>
