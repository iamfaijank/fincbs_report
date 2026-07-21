<script setup>
import { ref, computed } from 'vue'
import { useNumberFormat } from '@/composables/useNumberFormat.js'
import { useFilters } from '@/composables/useFilters.js'
import { useExpandableSet } from '@/composables/useExpandableSet.js'
import AchievementBadge from './AchievementBadge.vue'

const { formatNumber } = useNumberFormat()
const { isZoneSelected, isRegionSelected, allZonesSelected, allRegionsSelected } = useFilters()
const { toggle, isExpanded } = useExpandableSet()

const tableData = ref([
  {
    zone: 'Z-1',
    regions: [
      { region: 'R-1', branches: 42, target: 15678900, ach: 13456780, achPercent: 85.8 },
      { region: 'R-2', branches: 38, target: 14325000, ach: 13234500, achPercent: 92.4 },
      { region: 'R-3', branches: 35, target: 12890000, ach: 10234000, achPercent: 79.4 },
      { region: 'R-4', branches: 28, target: 11234000, ach: 9456000, achPercent: 84.2 },
    ]
  },
  {
    zone: 'Z-2',
    regions: [
      { region: 'R-1', branches: 35, target: 12890000, ach: 9876543, achPercent: 76.6 },
      { region: 'R-2', branches: 41, target: 16750000, ach: 15678900, achPercent: 93.6 },
      { region: 'R-3', branches: 32, target: 13450000, ach: 11234000, achPercent: 83.5 },
      { region: 'R-4', branches: 39, target: 15234000, ach: 13567000, achPercent: 89.1 },
    ]
  },
  {
    zone: 'Z-3',
    regions: [
      { region: 'R-1', branches: 29, target: 9845000, ach: 6734500, achPercent: 68.4 },
      { region: 'R-2', branches: 44, target: 18932000, ach: 16789000, achPercent: 88.7 },
      { region: 'R-3', branches: 31, target: 12567000, ach: 10234000, achPercent: 81.4 },
      { region: 'R-4', branches: 36, target: 14678000, ach: 13123000, achPercent: 89.4 },
    ]
  },
])

const isFilterApplied = computed(() => !allZonesSelected.value || !allRegionsSelected.value)

const filteredTableData = computed(() => {
  if (!isFilterApplied.value) return tableData.value
  return tableData.value
    .filter(zone => isZoneSelected(zone.zone))
    .map(zone => ({
      ...zone,
      regions: zone.regions.filter(region => isRegionSelected(region.region)),
    }))
    .filter(zone => zone.regions.length > 0)
})

function getZoneTotals(zoneData) {
  const totals = zoneData.regions.reduce(
    (acc, r) => ({
      branches: acc.branches + r.branches,
      target: acc.target + r.target,
      ach: acc.ach + r.ach,
    }),
    { branches: 0, target: 0, ach: 0 }
  )
  totals.achPercent = totals.target ? Math.round((totals.ach / totals.target) * 1000) / 10 : 0
  return totals
}
</script>

<template>
  <div class="sb-card card-table">
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead>
          <tr class="border-b border-[var(--border)]">
            <th rowspan="2" class="border-r border-[var(--border)] bg-[var(--bg2)] px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              Zone/Region
            </th>
            <th rowspan="2" class="border-r border-[var(--border)] bg-[var(--bg2)] px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              Branches
            </th>
            <th colspan="3" class="border-b border-[var(--border)] bg-[var(--bg1)] px-5 py-2 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              Jul-2026<br/>
              <span class="text-[10px] font-normal">SR % | 14 Working Days Left</span>
            </th>
          </tr>
          <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
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
                {{ getZoneTotals(zoneData).branches }}
              </td>
              <td class="border-r border-[var(--border)] px-5 py-3 text-right font-mono text-sm text-[var(--text)]">
                {{ formatNumber(getZoneTotals(zoneData).target) }}
              </td>
              <td class="border-r border-[var(--border)] px-5 py-3 text-right font-mono text-sm text-[var(--text)]">
                {{ formatNumber(getZoneTotals(zoneData).ach) }}
              </td>
              <td class="px-5 py-3 text-center font-mono text-sm text-[var(--text)]">
                <AchievementBadge :value="getZoneTotals(zoneData).achPercent" />
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
                  {{ region.branches }}
                </td>
                <td class="border-r border-[var(--border)] px-5 py-3 text-right font-mono text-sm text-[var(--text)]">
                  {{ formatNumber(region.target) }}
                </td>
                <td class="border-r border-[var(--border)] px-5 py-3 text-right font-mono text-sm text-[var(--text)]">
                  {{ formatNumber(region.ach) }}
                </td>
                <td class="px-5 py-3 text-center font-mono text-sm text-[var(--text)]">
                  <AchievementBadge :value="region.achPercent" />
                </td>
              </tr>
            </template>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>
