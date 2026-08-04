<script setup>
import { computed } from 'vue'
import { useNumberFormat } from '@/composables/useNumberFormat.js'
import { useFilters } from '@/composables/useFilters.js'
import { useExpandableSet } from '@/composables/useExpandableSet.js'
import AchievementBadge from './AchievementBadge.vue'

const { formatNumber } = useNumberFormat()
const { isZoneSelected, isRegionSelected } = useFilters()
const { toggle, isExpanded } = useExpandableSet()

const props = defineProps({
  zoneData: { type: Array, default: () => [] },
  months: { type: Array, default: () => [] },
})

const rawZoneWise = computed(() => props.zoneData)
const months = computed(() => props.months)
const loading = computed(() => rawZoneWise.value.length === 0)

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
</script>

<template>
  <div class="sb-card card-table">
    <div v-if="loading" class="p-8 text-center text-sm text-[var(--text3)]">Loading...</div>
    <div v-else>
      <table class="w-full">
        <thead>
          <tr class="border-b border-[var(--border)]">
            <th rowspan="2" class="border-r border-[var(--border)] bg-[var(--bg2)] px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              Zone/Region
            </th>
            <th rowspan="2" class="border-r border-[var(--border)] bg-[var(--bg2)] px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              Branches
            </th>
            <th colspan="3" v-if="activeMonth" class="border-b border-[var(--border)] bg-[var(--bg1)] px-5 py-2 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
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
            <tr
              class="cursor-pointer border-b border-[var(--border)] bg-[var(--bg1)] font-semibold transition hover:bg-[var(--bg2)]"
              @click="toggle(zoneData.zone)"
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
                    :class="isExpanded(zoneData.zone) ? 'rotate-90' : ''"
                  >
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                  {{ zoneData.zone }}
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
                <AchievementBadge :value="getMonthData(zoneData).percentage" />
              </td>
            </tr>
            <template v-if="isExpanded(zoneData.zone)">
              <tr
                v-for="region in zoneData.regions"
                :key="`${zoneData.zone}-${region.region}`"
                class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
              >
                <td class="border-r border-[var(--border)] px-5 py-3 pl-12 text-sm text-[var(--text3)]">
                  {{ region.region }}
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
                  <AchievementBadge :value="getMonthData(region).percentage" />
                </td>
              </tr>
            </template>
          </template>
          <tr class="border-t-2 border-[var(--border)] bg-[var(--bg2)] font-semibold">
            <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text)]">Total</td>
            <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text)]">{{ totals.branches }}</td>
            <td v-if="activeMonth" class="border-r border-[var(--border)] px-5 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(totals.target) }}</td>
            <td v-if="activeMonth" class="border-r border-[var(--border)] px-5 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(totals.achievement) }}</td>
            <td v-if="activeMonth" class="px-5 py-3 text-center font-mono text-sm text-[var(--text)]">{{ totals.percentage }}%</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
