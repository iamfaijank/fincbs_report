<script setup>
import { computed } from 'vue'
import { useNameFormat } from '@/composables/useNameFormat.js'

const { formatZone } = useNameFormat()

const props = defineProps({
  zoneData: { type: Array, default: () => [] },
  months: { type: Array, default: () => [] },
})

const zoneColors = ['#3b82f6', '#ef4444', '#f59e0b', '#22c55e', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316']

const zoneMap = computed(() => {
  const map = {}
  for (const row of props.zoneData) {
    if (row.zone === row.region) {
      map[row.zone] = row
    }
  }
  return map
})

const zoneNames = computed(() => {
  return Object.keys(zoneMap.value).sort((a, b) => a.localeCompare(b, undefined, { numeric: true }))
})

const chartData = computed(() => {
  return props.months.map(m => {
    const entry = { month: m.display, key: m.key }
    zoneNames.value.forEach(zone => {
      const row = zoneMap.value[zone]
      const md = row?.months?.[m.key]
      entry[zone] = md?.target > 0 ? Math.round((md.achievement / md.target) * 100) : 0
    })
    return entry
  })
})

const chartWidth = 600
const chartHeight = 220
const padding = { top: 20, right: 20, bottom: 40, left: 50 }
const plotWidth = chartWidth - padding.left - padding.right
const plotHeight = chartHeight - padding.top - padding.bottom

const maxVal = computed(() => {
  let max = 100
  chartData.value.forEach(d => {
    zoneNames.value.forEach(z => {
      if (d[z] > max) max = d[z]
    })
  })
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

function linePath(zone) {
  return chartData.value.map((d, i) => `${i === 0 ? 'M' : 'L'} ${x(i)} ${y(d[zone] || 0)}`).join(' ')
}

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
    <div class="px-5 py-3 border-b border-[var(--border)] flex items-center justify-between">
      <span class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">Zone Achievement Over Months</span>
      <div class="flex items-center gap-3">
        <div v-for="(zone, ci) in zoneNames" :key="zone" class="flex items-center gap-1">
          <span class="w-2.5 h-2.5 rounded-full" :style="{ background: zoneColors[ci % zoneColors.length] }"></span>
          <span class="text-[10px] text-[var(--text3)]">{{ formatZone(zone) }}</span>
        </div>
        <div class="flex items-center gap-1">
          <span class="w-4 border-t border-dashed border-green-500 opacity-60"></span>
          <span class="text-[10px] text-[var(--text3)]">Target</span>
        </div>
      </div>
    </div>
    <div class="p-4 overflow-x-auto">
      <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" class="w-full h-56">
        <!-- Y axis grid -->
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

        <!-- X axis labels -->
        <text
          v-for="(d, i) in chartData"
          :key="'x-' + i"
          :x="x(i)"
          :y="chartHeight - padding.bottom + 18"
          text-anchor="middle"
          class="fill-[var(--text3)] text-[9px]"
        >{{ d.month }}</text>

        <!-- Target line -->
        <line
          :x1="padding.left"
          :x2="chartWidth - padding.right"
          :y1="targetLineY"
          :y2="targetLineY"
          stroke="#22c55e"
          stroke-width="1.5"
          stroke-dasharray="6 3"
          opacity="0.5"
        />

        <!-- Zone lines -->
        <path
          v-for="(zone, ci) in zoneNames"
          :key="'line-' + zone"
          :d="linePath(zone)"
          fill="none"
          :stroke="zoneColors[ci % zoneColors.length]"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />

        <!-- Data points -->
        <template v-for="(d, i) in chartData" :key="'pts-' + i">
          <circle
            v-for="(zone, ci) in zoneNames"
            :key="'dot-' + zone + '-' + i"
            :cx="x(i)"
            :cy="y(d[zone] || 0)"
            r="3.5"
            fill="white"
            :stroke="zoneColors[ci % zoneColors.length]"
            stroke-width="2"
          />
        </template>
      </svg>
    </div>
  </div>
</template>
