<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  tag: { type: String, default: '' },
  tagColor: { type: String, default: 'green' },
})
</script>

<template>
  <div class="sb-card flex items-start justify-between">
    <div>
      <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">{{ label }}</div>
      <div v-if="tag" class="mt-1 text-[10px] text-[var(--text3)]">
        <span :class="[
          'rounded px-1 py-0.5 text-[9px] font-medium',
          tagColor === 'green' ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400' :
          tagColor === 'amber' ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400' :
          tagColor === 'red' ? 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400' :
          'bg-gray-50 text-gray-600 dark:bg-gray-900/30 dark:text-gray-400'
        ]">{{ tag }}</span>
      </div>
    </div>
    <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">{{ value }}</div>
  </div>
</template>
