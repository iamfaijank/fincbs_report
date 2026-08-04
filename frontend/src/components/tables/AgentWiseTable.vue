<script setup>
import { ref, computed, onMounted } from 'vue'
import { frappeRequest } from 'frappe-ui'
import { useNumberFormat } from '@/composables/useNumberFormat.js'
import { useFilters } from '@/composables/useFilters.js'
import { useExpandableSet } from '@/composables/useExpandableSet.js'
import AchievementBadge from './AchievementBadge.vue'

const { formatNumber } = useNumberFormat()
const { isZoneSelected, isRegionSelected } = useFilters()
const { toggle: toggleZone, isExpanded: isZoneExpanded } = useExpandableSet()

const rawAgentWise = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const data = await frappeRequest({
      url: '/api/method/custom_report.www.drishti.get_agent_wise_data',
      method: 'POST',
    }) || {}
    rawAgentWise.value = data.agent_wise || []
  } catch (e) {
    console.error('Failed to load agent wise data', e)
  } finally {
    loading.value = false
  }
})

const filteredAgentData = computed(() => {
  const zoneMap = {}
  for (const row of rawAgentWise.value) {
    if (!isZoneSelected(row.zone)) continue
    if (!isRegionSelected(row.region)) continue
    if (!zoneMap[row.zone]) {
      zoneMap[row.zone] = { zone: row.zone, regions: [] }
    }
    zoneMap[row.zone].regions.push(row)
  }
  return Object.values(zoneMap).sort((a, b) => a.zone.localeCompare(b.zone, undefined, { numeric: true }))
})

function getZoneTotals(zoneData) {
  const t = { ssTarget: 0, ssAchievement: 0, ssShortfall: 0, ssActive: 0, ssInactive: 0, target: 0, achievement: 0, agentShortfall: 0, active: 0, inactive: 0 }
  zoneData.regions.forEach(r => {
    t.ssTarget += r.ss_target || 0
    t.ssAchievement += r.ss_achievement || 0
    t.ssShortfall += r.ss_shortfall || 0
    t.ssActive += r.ss_active || 0
    t.ssInactive += r.ss_inactive || 0
    t.target += r.target || 0
    t.achievement += r.achievement || 0
    t.agentShortfall += r.agent_shortfall || 0
    t.active += r.active || 0
    t.inactive += r.inactive || 0
  })
  t.achPercent = t.target > 0 ? Math.round((t.achievement / t.target) * 100) : 0
  return t
}
</script>

<template>
  <div class="sb-card card-table">
    <div v-if="loading" class="p-8 text-center text-sm text-[var(--text3)]">Loading...</div>
    <div v-else-if="filteredAgentData.length === 0" class="p-8 text-center text-sm text-[var(--text3)]">No agent data available for the selected date.</div>
    <div v-else>
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
              Agent
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
              <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).target) }}</td>
              <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).achievement) }}</td>
              <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).agentShortfall) }}</td>
              <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).active) }}</td>
              <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).inactive) }}</td>
              <td class="px-4 py-3 text-center font-mono text-sm">
                <AchievementBadge :value="getZoneTotals(zoneData).achPercent" />
              </td>
            </tr>
            <template v-if="isZoneExpanded(zoneData.zone)">
              <tr
                v-for="region in zoneData.regions"
                :key="`${zoneData.zone}-${region.region}`"
                class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
              >
                <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text2)]">
                  {{ region.region }}
                </td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(region.ss_target) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(region.ss_achievement) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(region.ss_shortfall) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(region.ss_active) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(region.ss_inactive) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(region.target) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(region.achievement) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(region.agent_shortfall) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(region.active) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(region.inactive) }}</td>
                <td class="px-4 py-3 text-center font-mono text-sm">
                  <AchievementBadge :value="region.target > 0 ? ((region.achievement / region.target) * 100).toFixed(1) : 0" />
                </td>
              </tr>
            </template>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>
