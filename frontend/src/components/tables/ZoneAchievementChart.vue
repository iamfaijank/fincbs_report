<script setup>
import { computed } from 'vue'
import { useNameFormat } from '@/composables/useNameFormat.js'

const { formatZone } = useNameFormat()

const props = defineProps({
  zoneData: { type: Array, default: () => [] },
  months: { type: Array, default: () => [] },
})

const activeMonth = computed(() => {
  if (props.months.length === 0) return null
  return props.months[props.months.length - 1]
})

const chartData = computed(() => {
  const zoneMap = {}
  for (const row of props.zoneData) {
    if (row.zone === row.region) {
      zoneMap[row.zone] = row
    }
  }
  return Object.entries(zoneMap)
    .map(([zone, data]) => {
      const md = data.months?.[activeMonth.value?.key] || { target: 0, achievement: 0 }
      const pct = md.target > 0 ? Math.round((md.achievement / md.target) * 100) : 0
      return { zone, pct, target: 100 }
    })
    .sort((a, b) => a.zone.localeCompare(b.zone, undefined, { numeric: true }))
})

const chartWidth = 600
const chartHeight = 200
const padding = { top: 20, right: 30, bottom: 40, left: 50 }
const plotWidth = chartWidth - padding.left - padding.right
const plotHeight = chartHeight - padding.top - padding.bottom

const maxVal = computed(() => {
  const max = Math.max(100, ...chartData.value.map(d => d.pct))
  return Math.ceil(max / 10) * 10
})

function x(i) {
  const n = chartData.value.length
  if (n <= 1) return padding.left + plotWidth / 2
  return padding.left + (i / (n - 1)) * plotWidth
}

function y(val) {
  return padding.top + plotHeight - (val / maxVal.value) * plotHeight
}

const achievementPath = computed(() => {
  return chartData.value.map((d, i) => `${i === 0 ? 'M' : 'L'} ${x(i)} ${y(d.pct)}`).join(' ')
})

const achievementAreaPath = computed(() => {
  const pts = chartData.value.map((d, i) => `${x(i)} ${y(d.pct)}`)
  if (pts.length === 0) return ''
  return `M ${x(0)} ${y(0)} ` + pts.map(p => `L ${p}`).join(' ') + ` L ${x(chartData.value.length - 1)} ${y(0)} Z`
})

const targetLineY = computed(() => y(100))

const yTicks = computed(() => {
  const max = maxVal.value
  const step = max <= 50 ? 10 : max <= 100 ? 20 : 25
  const ticks = []
  for (let v = 0; v <= max; v += step) ticks.push(v)
  return ticks
})
</script>

<template>
  <div class="sb-card card-table w-full">
    <div class="px-5 py-3 border-b border-[var(--border)]">
      <span class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">Zone Achievement ({{ activeMonth?.display || '—' }})</span>
    </div>
    <div class="p-4 overflow-x-auto">
      <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" class="w-full h-48">
        <!-- Y axis grid lines -->
        <g>
          <line
            v-for="tick in yTicks"
            :key="'grid-' + tick"
            :x1="padding.left"
            :x2="chartWidth - padding.right"
            :y1="y(tick)"
            :y2="y(tick)"
            stroke="currentColor"
            stroke-width="0.5"
            class="text-gray-200 dark:text-gray-700"
          />
          <text
            v-for="tick in yTicks"
            :key="'label-' + tick"
            :x="padding.left - 8"
            :y="y(tick) + 4"
            text-anchor="end"
            class="fill-[var(--text3)] text-[9px]"
          >{{ tick }}%</text>
        </g>

        <!-- Target line (100%) -->
        <line
          :x1="padding.left"
          :x2="chartWidth - padding.right"
          :y1="targetLineY"
          :y2="targetLineY"
          stroke="#22c55e"
          stroke-width="1.5"
          stroke-dasharray="6 3"
          opacity="0.6"
        />
        <text
          :x="chartWidth - padding.right + 4"
          :y="targetLineY + 3"
          class="fill-green-500 text-[9px] font-medium"
        >100%</text>

        <!-- Achievement area -->
        <path
          :d="achievementAreaPath"
          fill="url(#achGrad)"
          opacity="0.15"
        />

        <!-- Achievement line -->
        <path
          :d="achievementPath"
          fill="none"
          stroke="#3b82f6"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        />

        <!-- Data points -->
        <g v-for="(d, i) in chartData" :key="d.zone">
          <circle
            :cx="x(i)"
            :cy="y(d.pct)"
            r="5"
            fill="white"
            stroke="#3b82f6"
            stroke-width="2.5"
          />
          <text
            :x="x(i)"
            :y="y(d.pct) - 10"
            text-anchor="middle"
            class="fill-[var(--text)] text-[10px] font-semibold font-mono"
          >{{ d.pct }}%</text>
          <text
            :x="x(i)"
            :y="chartHeight - padding.bottom + 16"
            text-anchor="middle"
            class="fill-[var(--text3)] text-[10px]"
          >{{ formatZone(d.zone) }}</text>
        </g>

        <defs>
          <linearGradient id="achGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.4" />
            <stop offset="100%" stop-color="#3b82f6" stop-opacity="0" />
          </linearGradient>
        </defs>
      </svg>
    </div>
  </div>
</template>
