<script setup>
import { computed, ref } from 'vue'
import { useNumberFormat } from '@/composables/useNumberFormat.js'
import { useFilters } from '@/composables/useFilters.js'
import { useExpandableSet } from '@/composables/useExpandableSet.js'
import { useNameFormat } from '@/composables/useNameFormat.js'
import ViewToggle from './ViewToggle.vue'

const { formatNumber } = useNumberFormat()
const { isZoneSelected, isRegionSelected } = useFilters()
const { toggle: toggleZone, isExpanded: isZoneExpanded } = useExpandableSet()
const { toggle: toggleRegion, isExpanded: isRegionExpanded } = useExpandableSet()
const { formatZone, formatRegion } = useNameFormat()

const props = defineProps({
  zoneData: { type: Array, default: () => [] },
  months: { type: Array, default: () => [] },
})

const rawZoneWise = computed(() => props.zoneData)
const months = computed(() => props.months)
const loading = computed(() => rawZoneWise.value.length === 0)
const viewMode = ref('table')

const filteredTableData = computed(() => {
  const zoneMap = {}
  for (const row of rawZoneWise.value) {
    const zone = row.zone
    const region = row.region
    if (zone === region) {
      zoneMap[zone] = { ...row, regions: [] }
    }
  }
  for (const row of rawZoneWise.value) {
    const zone = row.zone
    const region = row.region
    if (zone !== region && zoneMap[zone]) {
      zoneMap[zone].regions.push(row)
    }
  }
  return Object.values(zoneMap)
    .filter(z => isZoneSelected(z.zone))
    .map(z => ({
      ...z,
      regions: z.regions.filter(r => isRegionSelected(r.region)),
    }))
    .filter(z => z.regions.length > 0 || z.months)
})

const activeMonth = computed(() => {
  if (months.value.length === 0) return null
  return months.value[months.value.length - 1]
})

function getMonthData(row) {
  if (!activeMonth.value) return { branches: 0, target: 0, achievement: 0, percentage: 0 }
  return row.months?.[activeMonth.value.key] || { branches: 0, target: 0, achievement: 0, percentage: 0 }
}

const totals = computed(() => {
  let branches = 0, target = 0, achievement = 0
  filteredTableData.value.forEach(z => {
    const md = getMonthData(z)
    branches += md.branches || 0
    target += md.target || 0
    achievement += md.achievement || 0
  })
  return { branches, target, achievement, percentage: target > 0 ? Math.round(achievement / target * 100) : 0 }
})

// Chart data for zone-wise view
const chartData = computed(() => {
  const data = []
  
  filteredTableData.value.forEach(zone => {
    const md = getMonthData(zone)
    if (md.target > 0) {
      data.push({
        zone: formatZone(zone.zone),
        target: md.target,
        achievement: md.achievement,
        percentage: Math.round(md.percentage || 0),
        branches: md.branches
      })
    }
  })
  
  // Sort by percentage descending
  return data.sort((a, b) => b.percentage - a.percentage)
})

const chartOptions = computed(() => {
  const maxTarget = Math.max(...chartData.value.map(d => d.target), 1)
  const maxAchievement = Math.max(...chartData.value.map(d => d.achievement), 1)
  const maxValue = Math.max(maxTarget, maxAchievement)
  
  return {
    height: 400,
    colors: {
      target: '#3b82f6',
      achievement: '#22c55e',
      percentage: '#8b5cf6'
    },
    maxValue
  }
})
</script>

<template>
  <div class="sb-card card-table">
    <div v-if="loading" class="p-8 text-center text-sm text-[var(--text3)]">Loading...</div>
    <div v-else>
      <!-- View Toggle Header -->
      <div class="flex items-center justify-between border-b border-[var(--border)] bg-[var(--bg2)] px-5 py-3">
        <div class="text-sm font-semibold text-[var(--text3)] uppercase tracking-wider">
          Zone / Region / Branch
        </div>
        <ViewToggle v-model:viewMode="viewMode" color="#065f46" />
      </div>
      
      <!-- Chart View -->
      <div v-if="viewMode === 'chart' && chartData.length > 0" class="p-6">
        <div class="mb-6">
          <h3 class="text-sm font-semibold text-[var(--text3)] mb-4">Zone Performance Overview - {{ activeMonth?.display || 'Current Month' }}</h3>
          
          <!-- Zone Performance Chart -->
          <div class="space-y-4">
            <div v-for="(item, index) in chartData" :key="item.zone" class="chart-item">
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-3">
                  <span class="w-6 text-right text-xs font-medium text-[var(--text3)]">{{ index + 1 }}.</span>
                  <span class="text-sm font-medium text-[var(--text)]">{{ item.zone }}</span>
                  <span class="text-xs text-[var(--text3)]">({{ item.branches }} branches)</span>
                </div>
                <span class="text-sm font-semibold" :class="item.percentage >= 100 ? 'text-green-600' : item.percentage >= 80 ? 'text-blue-600' : item.percentage >= 60 ? 'text-amber-600' : 'text-red-600'">
                  {{ item.percentage }}%
                </span>
              </div>
              
              <!-- Progress Bar -->
              <div class="relative h-4 bg-[var(--bg2)] rounded-full overflow-hidden">
                <div 
                  class="absolute top-0 left-0 h-full rounded-full transition-all duration-500"
                  :style="{
                    width: `${Math.min(100, (item.achievement / chartOptions.maxValue) * 100)}%`,
                    backgroundColor: item.percentage >= 100 ? '#22c55e' : item.percentage >= 80 ? '#3b82f6' : item.percentage >= 60 ? '#f59e0b' : '#ef4444'
                  }"
                ></div>
              </div>
              
              <!-- Values -->
              <div class="flex justify-between mt-1 text-xs text-[var(--text3)]">
                <span>Ach: {{ formatNumber(item.achievement) }}</span>
                <span>Target: {{ formatNumber(item.target) }}</span>
              </div>
            </div>
          </div>
          
          <!-- Summary Stats -->
          <div class="mt-8 pt-6 border-t border-[var(--border)] grid grid-cols-3 gap-4">
            <div class="text-center">
              <div class="text-xs text-[var(--text3)] mb-1">Total Zones</div>
              <div class="text-2xl font-bold text-[var(--text)]">{{ chartData.length }}</div>
            </div>
            <div class="text-center">
              <div class="text-xs text-[var(--text3)] mb-1">Avg. Achievement</div>
              <div class="text-2xl font-bold text-[var(--text)]">
                {{ Math.round(chartData.reduce((sum, item) => sum + item.percentage, 0) / chartData.length) }}%
              </div>
            </div>
            <div class="text-center">
              <div class="text-xs text-[var(--text3)] mb-1">Total Branches</div>
              <div class="text-2xl font-bold text-[var(--text)]">{{ totals.branches }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Table View -->
      <div v-else-if="viewMode === 'table'">
        <table class="w-full">
          <thead>
            <tr class="border-b border-[var(--border)]">
              <th rowspan="2" class="border-r border-[var(--border)] bg-[var(--bg2)] px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Zone / Region / Branch
              </th>
              <th rowspan="2" class="border-r border-[var(--border)] bg-[var(--bg2)] px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Branches
              </th>
              <th colspan="3" v-if="activeMonth" class="border-b border-r border-[var(--border)] bg-[var(--bg1)] px-5 py-2 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                {{ activeMonth.display }}
              </th>
            </tr>
            <tr v-if="activeMonth" class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="border-r border-[var(--border)] px-5 py-2 text-right text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Target
              </th>
              <th class="border-r border-[var(--border)] px-5 py-2 text-right text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Ach
              </th>
              <th class="px-5 py-2 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Ach %
              </th>
            </tr>
          </thead>
        <tbody>
          <template v-for="zoneData in filteredTableData" :key="zoneData.zone">
            <!-- Zone row -->
            <tr
              class="cursor-pointer border-b border-[var(--border)] bg-[var(--bg1)] font-semibold transition hover:bg-[var(--bg2)]"
              @click="toggleZone(zoneData.zone)"
            >
              <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text)]">
                <div class="flex items-center gap-2">
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    class="transition-transform"
                    :class="isZoneExpanded(zoneData.zone) ? 'rotate-90' : ''"
                  >
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                  {{ formatZone(zoneData.zone) }}
                </div>
              </td>
              <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text)]">
                {{ getMonthData(zoneData).branches }}
              </td>
              <td v-if="activeMonth" class="border-r border-[var(--border)] px-5 py-3 text-right font-mono text-sm text-[var(--text)]">
                {{ formatNumber(getMonthData(zoneData).target) }}
              </td>
              <td v-if="activeMonth" class="border-r border-[var(--border)] px-5 py-3 text-right font-mono text-sm text-[var(--text)]">
                {{ formatNumber(getMonthData(zoneData).achievement) }}
              </td>
              <td v-if="activeMonth" class="px-5 py-3 text-center font-mono text-sm text-[var(--text)]">
                {{ Math.round(getMonthData(zoneData).percentage || 0) }}%
              </td>
            </tr>

            <!-- Region & Branch rows -->
            <template v-if="isZoneExpanded(zoneData.zone)">
              <template v-for="region in zoneData.regions" :key="`${zoneData.zone}-${region.region}`">
                <!-- Region row -->
                <tr
                  class="cursor-pointer border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
                  @click="toggleRegion(region.region)"
                >
                  <td class="border-r border-[var(--border)] px-5 py-3 pl-10 text-sm text-[var(--text3)]">
                    <div class="flex items-center gap-2">
                      <svg
                        width="12"
                        height="12"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        class="transition-transform flex-shrink-0"
                        :class="isRegionExpanded(region.region) ? 'rotate-90' : ''"
                      >
                        <polyline points="9 18 15 12 9 6"></polyline>
                      </svg>
                      {{ formatRegion(region.region) }}
                    </div>
                  </td>
                  <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text)]">
                    {{ getMonthData(region).branches }}
                  </td>
                  <td v-if="activeMonth" class="border-r border-[var(--border)] px-5 py-3 text-right font-mono text-sm text-[var(--text)]">
                    {{ formatNumber(getMonthData(region).target) }}
                  </td>
                  <td v-if="activeMonth" class="border-r border-[var(--border)] px-5 py-3 text-right font-mono text-sm text-[var(--text)]">
                    {{ formatNumber(getMonthData(region).achievement) }}
                  </td>
                  <td v-if="activeMonth" class="px-5 py-3 text-center font-mono text-sm text-[var(--text)]">
                    {{ Math.round(getMonthData(region).percentage || 0) }}%
                  </td>
                </tr>

                <!-- SOL/Branch rows -->
                <template v-if="isRegionExpanded(region.region)">
                  <tr
                    v-for="branch in (region.branches_list || [])"
                    :key="`${region.region}-${branch.sol_id}`"
                    class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
                  >
                    <td class="border-r border-[var(--border)] px-5 py-2 pl-16 text-xs text-[var(--text3)] font-mono">
                      {{ branch.branch || branch.sol_id }}
                    </td>
                    <td class="border-r border-[var(--border)] px-5 py-2 text-xs text-[var(--text)]">
                      1
                    </td>
                    <td v-if="activeMonth" class="border-r border-[var(--border)] px-5 py-2 text-right font-mono text-xs text-[var(--text)]">
                      {{ formatNumber(branch.months?.[activeMonth.key]?.target || 0) }}
                    </td>
                    <td v-if="activeMonth" class="border-r border-[var(--border)] px-5 py-2 text-right font-mono text-xs text-[var(--text)]">
                      {{ formatNumber(branch.months?.[activeMonth.key]?.achievement || 0) }}
                    </td>
                    <td v-if="activeMonth" class="px-5 py-2 text-center font-mono text-xs text-[var(--text)]">
                      {{ Math.round(branch.months?.[activeMonth.key]?.percentage || 0) }}%
                    </td>
                  </tr>
                </template>
              </template>
            </template>
          </template>

          <!-- Total row -->
          <tr class="border-t-2 border-[var(--border)] bg-[var(--bg2)] font-semibold">
            <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text)]">Total</td>
            <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text)]">{{ totals.branches }}</td>
            <td v-if="activeMonth" class="border-r border-[var(--border)] px-5 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(totals.target) }}</td>
            <td v-if="activeMonth" class="border-r border-[var(--border)] px-5 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(totals.achievement) }}</td>
            <td v-if="activeMonth" class="px-5 py-3 text-center font-mono text-sm text-[var(--text)]">{{ Math.round(totals.percentage || 0) }}%</td>
          </tr>
        </tbody>
      </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chart-item {
  @apply p-3 border border-[var(--border)] rounded-lg bg-[var(--bg1)];
}

.chart-item:not(:last-child) {
  @apply mb-3;
}
</style>
