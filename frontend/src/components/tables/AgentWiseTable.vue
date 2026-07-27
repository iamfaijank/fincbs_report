<script setup>
import { ref, computed } from 'vue'
import { useNumberFormat } from '@/composables/useNumberFormat.js'
import { useFilters } from '@/composables/useFilters.js'
import { useExpandableSet } from '@/composables/useExpandableSet.js'
import AchievementBadge from './AchievementBadge.vue'

const { formatNumber } = useNumberFormat()
const { isZoneSelected, isRegionSelected, zoneFilter, regionFilter } = useFilters()
const { toggle: toggleZone, isExpanded: isZoneExpanded } = useExpandableSet()

const isFilterApplied = computed(() => zoneFilter.value.length > 0 || regionFilter.value.length > 0)

const agentData = ref([
  {
    zone: 'Z-1',
    regions: [
      { region: 'R-1', ssTarget: 450, ssAchievement: 412, ssShortfall: 38, ssActive: 35, ssInactive: 5, ddTarget: 280, ddAchievement: 264, ddShortfall: 16, ddActive: 25, ddInactive: 2 },
      { region: 'R-2', ssTarget: 380, ssAchievement: 325, ssShortfall: 55, ssActive: 28, ssInactive: 8, ddTarget: 220, ddAchievement: 198, ddShortfall: 22, ddActive: 18, ddInactive: 4 },
    ]
  },
  {
    zone: 'Z-2',
    regions: [
      { region: 'R-3', ssTarget: 520, ssAchievement: 494, ssShortfall: 26, ssActive: 42, ssInactive: 3, ddTarget: 310, ddAchievement: 294, ddShortfall: 16, ddActive: 30, ddInactive: 1 },
      { region: 'R-4', ssTarget: 400, ssAchievement: 340, ssShortfall: 60, ssActive: 32, ssInactive: 10, ddTarget: 250, ddAchievement: 212, ddShortfall: 38, ddActive: 22, ddInactive: 7 },
    ]
  },
])

const filteredAgentData = computed(() => {
  if (!isFilterApplied.value) return agentData.value
  return agentData.value
    .filter(z => isZoneSelected(z.zone))
    .map(z => ({ ...z, regions: z.regions.filter(r => isRegionSelected(r.region)) }))
    .filter(z => z.regions.length > 0)
})

function getZoneTotals(zoneData) {
  const t = { ssTarget: 0, ssAchievement: 0, ssShortfall: 0, ssActive: 0, ssInactive: 0, ddTarget: 0, ddAchievement: 0, ddShortfall: 0, ddActive: 0, ddInactive: 0 }
  zoneData.regions.forEach(r => {
    t.ssTarget += r.ssTarget; t.ssAchievement += r.ssAchievement; t.ssShortfall += r.ssShortfall; t.ssActive += r.ssActive; t.ssInactive += r.ssInactive
    t.ddTarget += r.ddTarget; t.ddAchievement += r.ddAchievement; t.ddShortfall += r.ddShortfall; t.ddActive += r.ddActive; t.ddInactive += r.ddInactive
  })
  t.achPercent = t.ssTarget > 0 ? ((t.ssAchievement / t.ssTarget) * 100).toFixed(1) : 0
  return t
}

function getRegionTotals(regionData) {
  const t = { ssTarget: regionData.ssTarget, ssAchievement: regionData.ssAchievement, ssShortfall: regionData.ssShortfall, ssActive: regionData.ssActive, ssInactive: regionData.ssInactive, ddTarget: regionData.ddTarget, ddAchievement: regionData.ddAchievement, ddShortfall: regionData.ddShortfall, ddActive: regionData.ddActive, ddInactive: regionData.ddInactive }
  t.achPercent = t.ssTarget > 0 ? ((t.ssAchievement / t.ssTarget) * 100).toFixed(1) : 0
  return t
}
</script>

<template>
  <div class="sb-card card-table">
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead>
          <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
            <th rowspan="2" class="border-r border-[var(--border)] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              ZONE/REGION
            </th>
            <th colspan="5" class="border-b border-r border-[var(--border)] px-4 py-2 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              SS
            </th>
            <th colspan="5" class="border-b border-r border-[var(--border)] px-4 py-2 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              DD
            </th>
            <th rowspan="2" class="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              ACH %
            </th>
          </tr>
          <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
            <th class="border-r border-[var(--border)] px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Target</th>
            <th class="border-r border-[var(--border)] px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Ach</th>
            <th class="border-r border-[var(--border)] px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Shortfall</th>
            <th class="border-r border-[var(--border)] px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Active</th>
            <th class="border-r border-[var(--border)] px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Inactive</th>
            <th class="border-r border-[var(--border)] px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Target</th>
            <th class="border-r border-[var(--border)] px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Ach</th>
            <th class="border-r border-[var(--border)] px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Shortfall</th>
            <th class="border-r border-[var(--border)] px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Active</th>
            <th class="border-r border-[var(--border)] px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Inactive</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="zoneData in filteredAgentData" :key="zoneData.zone">
            <tr
              class="cursor-pointer border-b border-[var(--border)] bg-[var(--bg1)] font-semibold transition hover:bg-[var(--bg2)]"
              @click="toggleZone(zoneData.zone)"
            >
              <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">
                <div class="flex items-center gap-2">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="transition-transform" :class="isZoneExpanded(zoneData.zone) ? 'rotate-90' : ''">
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                  {{ zoneData.zone }}
                </div>
              </td>
              <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).ssTarget) }}</td>
              <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).ssAchievement) }}</td>
              <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).ssShortfall) }}</td>
              <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).ssActive) }}</td>
              <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).ssInactive) }}</td>
              <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).ddTarget) }}</td>
              <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).ddAchievement) }}</td>
              <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).ddShortfall) }}</td>
              <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).ddActive) }}</td>
              <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).ddInactive) }}</td>
              <td class="px-4 py-3 text-center font-mono text-sm">
                <AchievementBadge :value="getZoneTotals(zoneData).achPercent" />
              </td>
            </tr>
            <template v-if="isZoneExpanded(zoneData.zone)">
              <tr
                v-for="regionData in zoneData.regions"
                :key="`${zoneData.zone}-${regionData.region}`"
                class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
              >
                <td class="border-r border-[var(--border)] px-4 py-3 pl-12 text-sm text-[var(--text2)]">
                  {{ regionData.region }}
                </td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ssTarget) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ssAchievement) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ssShortfall) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ssActive) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ssInactive) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ddTarget) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ddAchievement) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ddShortfall) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ddActive) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ddInactive) }}</td>
                <td class="px-4 py-3 text-center font-mono text-sm">
                  <AchievementBadge :value="getRegionTotals(regionData).achPercent" />
                </td>
              </tr>
            </template>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>
