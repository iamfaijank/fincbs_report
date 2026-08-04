<script setup>
import { computed } from 'vue'
import { useNumberFormat } from '@/composables/useNumberFormat.js'
import { useNameFormat } from '@/composables/useNameFormat.js'

const { formatNumber } = useNumberFormat()
const { formatZone } = useNameFormat()

const props = defineProps({
  zoneData: { type: Array, default: () => [] },
  months: { type: Array, default: () => [] },
})

const activeMonth = computed(() => {
  if (props.months.length === 0) return null
  return props.months[props.months.length - 1]
})

const totals = computed(() => {
  let target = 0, achievement = 0
  for (const row of props.zoneData) {
    if (row.zone === row.region) {
      const md = row.months?.[activeMonth.value?.key]
      if (md) {
        target += md.target || 0
        achievement += md.achievement || 0
      }
    }
  }
  return { target, achievement }
})

const overallPct = computed(() => {
  return totals.value.target > 0 ? Math.round((totals.value.achievement / totals.value.target) * 100) : 0
})

const zoneProgress = computed(() => {
  const zoneMap = {}
  for (const row of props.zoneData) {
    if (row.zone === row.region) {
      zoneMap[row.zone] = row
    }
  }
  return Object.entries(zoneMap).map(([zone, data]) => {
    const md = data.months?.[activeMonth.value?.key] || { target: 0, achievement: 0, branches: 0 }
    const pct = md.target > 0 ? Math.round((md.achievement / md.target) * 100) : 0
    return { zone, target: md.target, achievement: md.achievement, branches: md.branches, pct }
  }).sort((a, b) => a.zone.localeCompare(b.zone, undefined, { numeric: true }))
})

const ringRadius = 46
const ringStroke = 8
const ringCircumference = 2 * Math.PI * ringRadius
const ringDashoffset = computed(() => ringCircumference - (ringCircumference * Math.min(overallPct.value, 100)) / 100)

const ringColor = computed(() => {
  if (overallPct.value >= 90) return '#22c55e'
  if (overallPct.value >= 75) return '#f59e0b'
  return '#ef4444'
})

const topZone = computed(() => {
  const sorted = [...zoneProgress.value].sort((a, b) => b.pct - a.pct)
  return sorted[0] || null
})

const bottomZone = computed(() => {
  const sorted = [...zoneProgress.value].sort((a, b) => a.pct - b.pct)
  return sorted[0] || null
})

const textColor = (pct) => {
  if (pct >= 90) return 'text-green-600 dark:text-green-400'
  if (pct >= 75) return 'text-amber-600 dark:text-amber-400'
  return 'text-red-600 dark:text-red-400'
}
</script>

<template>
  <div class="sb-card flex flex-col h-full">
    <div class="flex-shrink-0 border-b border-[var(--border)] px-4 py-4">
      <div class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)] mb-3">Overall Achievement</div>
      <div class="flex items-center gap-3">
        <div class="relative flex-shrink-0">
          <svg :width="ringRadius * 2 + ringStroke" :height="ringRadius * 2 + ringStroke" class="-rotate-90">
            <circle
              :cx="ringRadius + ringStroke / 2"
              :cy="ringRadius + ringStroke / 2"
              :r="ringRadius"
              fill="none"
              stroke="currentColor"
              :stroke-width="ringStroke"
              class="text-gray-200 dark:text-gray-700"
            />
            <circle
              :cx="ringRadius + ringStroke / 2"
              :cy="ringRadius + ringStroke / 2"
              :r="ringRadius"
              fill="none"
              :stroke="ringColor"
              :stroke-width="ringStroke"
              stroke-linecap="round"
              :stroke-dasharray="ringCircumference"
              :stroke-dashoffset="ringDashoffset"
              class="transition-all duration-1000 ease-out"
            />
          </svg>
          <div class="absolute inset-0 flex flex-col items-center justify-center">
            <span class="text-2xl font-bold font-mono" :class="textColor(overallPct)">{{ overallPct }}%</span>
            <span class="text-[10px] text-[var(--text3)]">achieved</span>
          </div>
        </div>
        <div class="flex flex-col gap-1.5 flex-1 min-w-0">
          <div class="rounded-md bg-[var(--bg2)] px-2.5 py-1.5 flex items-center justify-between">
            <span class="text-[10px] font-medium text-[var(--text3)]">Target</span>
            <span class="text-xs font-bold font-mono text-[var(--text)]">{{ formatNumber(totals.target) }}</span>
          </div>
          <div class="rounded-md bg-[var(--bg2)] px-2.5 py-1.5 flex items-center justify-between">
            <span class="text-[10px] font-medium text-[var(--text3)]">Achieved</span>
            <span class="text-xs font-bold font-mono text-green-600 dark:text-green-400">{{ formatNumber(totals.achievement) }}</span>
          </div>
          <div class="rounded-md bg-[var(--bg2)] px-2.5 py-1.5 flex items-center justify-between">
            <span class="text-[10px] font-medium text-[var(--text3)]">Gap</span>
            <span class="text-xs font-bold font-mono text-red-600 dark:text-red-400">{{ formatNumber(totals.target - totals.achievement) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-shrink-0 border-b border-[var(--border)] px-4 py-3">
      <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)] mb-2">Top & Bottom Zone</div>
      <div class="grid grid-cols-2 gap-2">
        <div class="rounded-md bg-green-50 dark:bg-green-900/20 px-3 py-2">
          <div class="text-[10px] font-semibold uppercase tracking-wider text-green-600 dark:text-green-400 mb-1">Top Zone</div>
          <div v-if="topZone" class="flex items-baseline justify-between">
            <span class="text-sm font-bold text-green-700 dark:text-green-300">{{ formatZone(topZone.zone) }}</span>
            <span class="text-sm font-mono font-bold text-green-600 dark:text-green-400">{{ topZone.pct }}%</span>
          </div>
        </div>
        <div class="rounded-md bg-red-50 dark:bg-red-900/20 px-3 py-2">
          <div class="text-[10px] font-semibold uppercase tracking-wider text-red-600 dark:text-red-400 mb-1">Bottom Zone</div>
          <div v-if="bottomZone" class="flex items-baseline justify-between">
            <span class="text-sm font-bold text-red-700 dark:text-red-300">{{ formatZone(bottomZone.zone) }}</span>
            <span class="text-sm font-mono font-bold text-red-600 dark:text-red-400">{{ bottomZone.pct }}%</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
