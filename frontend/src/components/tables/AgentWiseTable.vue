<script setup>
import { ref, computed, onMounted } from 'vue'
import { frappeRequest } from 'frappe-ui'
import { useNumberFormat } from '@/composables/useNumberFormat.js'
import { useFilters } from '@/composables/useFilters.js'
import { useExpandableSet } from '@/composables/useExpandableSet.js'
import { useNameFormat } from '@/composables/useNameFormat.js'
import AchievementBadge from './AchievementBadge.vue'
import ViewToggle from './ViewToggle.vue'

const { formatNumber } = useNumberFormat()
const { isZoneSelected, isRegionSelected } = useFilters()
const { toggle: toggleZone, isExpanded: isZoneExpanded } = useExpandableSet()
const { formatZone, formatRegion } = useNameFormat()

const rawAgentWise = ref([])
const loading = ref(true)
const viewMode = ref('table')

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

// Chart data for agent-wise view
const agentChartData = computed(() => {
  const zones = rawAgentWise.value.filter(r => isZoneSelected(r.zone) && isRegionSelected(r.region))
  
  // Group by zone for chart
  const zoneMap = {}
  zones.forEach(agent => {
    if (!zoneMap[agent.zone]) {
      zoneMap[agent.zone] = {
        zone: formatZone(agent.zone),
        ssTarget: 0,
        ssAchievement: 0,
        ssActive: 0,
        ssInactive: 0,
        agentTarget: 0,
        agentAchievement: 0,
        agentActive: 0,
        agentInactive: 0,
        achPercent: 0
      }
    }
    zoneMap[agent.zone].ssTarget += agent.ss_target || 0
    zoneMap[agent.zone].ssAchievement += agent.ss_achievement || 0
    zoneMap[agent.zone].ssActive += agent.ss_active || 0
    zoneMap[agent.zone].ssInactive += agent.ss_inactive || 0
    zoneMap[agent.zone].agentTarget += agent.target || 0
    zoneMap[agent.zone].agentAchievement += agent.achievement || 0
    zoneMap[agent.zone].agentActive += agent.active || 0
    zoneMap[agent.zone].agentInactive += agent.inactive || 0
  })
  
  // Calculate percentages
  Object.values(zoneMap).forEach(zone => {
    const totalTarget = zone.agentTarget
    zone.achPercent = totalTarget > 0 ? Math.round((zone.agentAchievement / totalTarget) * 100) : 0
    zone.totalActive = zone.ssActive + zone.agentActive
    zone.totalInactive = zone.ssInactive + zone.agentInactive
  })
  
  return Object.values(zoneMap).sort((a, b) => b.achPercent - a.achPercent)
})

const chartOptions = computed(() => {
  const maxTarget = Math.max(...agentChartData.value.map(d => Math.max(d.ssTarget, d.agentTarget)), 1)
  const maxAchievement = Math.max(...agentChartData.value.map(d => Math.max(d.ssAchievement, d.agentAchievement)), 1)
  
  return {
    maxTarget,
    maxAchievement,
    colors: {
      ss: '#3b82f6',
      agent: '#22c55e',
      active: '#10b981',
      inactive: '#ef4444'
    }
  }
})
</script>

<template>
  <div class="sb-card card-table">
    <div v-if="loading" class="p-8 text-center text-sm text-[var(--text3)]">Loading...</div>
    <div v-else-if="filteredAgentData.length === 0" class="p-8 text-center text-sm text-[var(--text3)]">No agent data available for the selected date.</div>
    <div v-else>
      <!-- View Toggle Header -->
      <div class="flex items-center justify-between border-b border-[var(--border)] bg-[var(--bg2)] px-5 py-3">
        <div class="text-sm font-semibold text-[var(--text3)] uppercase tracking-wider">
          Agent Performance
        </div>
        <ViewToggle v-model:viewMode="viewMode" color="#115e59" />
      </div>
      
      <!-- Chart View -->
      <div v-if="viewMode === 'chart' && agentChartData.length > 0" class="p-6">
        <!-- Zone Performance Overview -->
        <div class="mb-8">
          <h3 class="text-sm font-semibold text-[var(--text3)] mb-4">Zone-wise Agent Performance</h3>
          
          <div class="space-y-4">
            <div v-for="(zone, index) in agentChartData" :key="zone.zone" class="chart-item">
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center gap-3">
                  <span class="w-6 text-right text-xs font-medium text-[var(--text3)]">{{ index + 1 }}.</span>
                  <span class="text-sm font-medium text-[var(--text)]">{{ zone.zone }}</span>
                  <AchievementBadge :value="zone.achPercent" />
                </div>
                <div class="text-xs text-[var(--text3)]">
                  {{ zone.totalActive }} active / {{ zone.totalInactive }} inactive
                </div>
              </div>
              
              <!-- SS vs Agent Comparison -->
              <div class="mb-3">
                <div class="text-xs text-[var(--text3)] mb-2">SS Performance</div>
                <div class="relative h-3 bg-[var(--bg2)] rounded-full overflow-hidden mb-2">
                  <div 
                    class="absolute top-0 left-0 h-full rounded-full"
                    :style="{
                      width: `${Math.min(100, (zone.ssAchievement / chartOptions.maxAchievement) * 100)}%`,
                      backgroundColor: chartOptions.colors.ss
                    }"
                  ></div>
                </div>
                <div class="flex justify-between text-xs">
                  <span class="text-[var(--text3)]">Ach: {{ formatNumber(zone.ssAchievement) }}</span>
                  <span class="text-[var(--text3)]">Target: {{ formatNumber(zone.ssTarget) }}</span>
                </div>
              </div>
              
              <div>
                <div class="text-xs text-[var(--text3)] mb-2">Agent Performance</div>
                <div class="relative h-3 bg-[var(--bg2)] rounded-full overflow-hidden mb-2">
                  <div 
                    class="absolute top-0 left-0 h-full rounded-full"
                    :style="{
                      width: `${Math.min(100, (zone.agentAchievement / chartOptions.maxAchievement) * 100)}%`,
                      backgroundColor: chartOptions.colors.agent
                    }"
                  ></div>
                </div>
                <div class="flex justify-between text-xs">
                  <span class="text-[var(--text3)]">Ach: {{ formatNumber(zone.agentAchievement) }}</span>
                  <span class="text-[var(--text3)]">Target: {{ formatNumber(zone.agentTarget) }}</span>
                </div>
              </div>
              
              <!-- Active/Inactive Status -->
              <div class="mt-3 pt-3 border-t border-[var(--border)]">
                <div class="text-xs text-[var(--text3)] mb-2">Status Distribution</div>
                <div class="flex gap-2">
                  <div class="flex-1">
                    <div class="text-center mb-1">
                      <span class="text-xs font-medium" :style="{ color: chartOptions.colors.active }">Active</span>
                    </div>
                    <div class="relative h-3 bg-[var(--bg2)] rounded-full overflow-hidden">
                      <div 
                        class="absolute top-0 left-0 h-full rounded-full"
                        :style="{
                          width: `${Math.min(100, (zone.totalActive / (zone.totalActive + zone.totalInactive)) * 100)}%`,
                          backgroundColor: chartOptions.colors.active
                        }"
                      ></div>
                    </div>
                  </div>
                  <div class="flex-1">
                    <div class="text-center mb-1">
                      <span class="text-xs font-medium" :style="{ color: chartOptions.colors.inactive }">Inactive</span>
                    </div>
                    <div class="relative h-3 bg-[var(--bg2)] rounded-full overflow-hidden">
                      <div 
                        class="absolute top-0 left-0 h-full rounded-full"
                        :style="{
                          width: `${Math.min(100, (zone.totalInactive / (zone.totalActive + zone.totalInactive)) * 100)}%`,
                          backgroundColor: chartOptions.colors.inactive
                        }"
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Summary Stats -->
        <div class="mt-8 pt-6 border-t border-[var(--border)] grid grid-cols-4 gap-4">
          <div class="text-center">
            <div class="text-xs text-[var(--text3)] mb-1">Avg. Achievement</div>
            <div class="text-2xl font-bold text-[var(--text)]">
              {{ Math.round(agentChartData.reduce((sum, zone) => sum + zone.achPercent, 0) / agentChartData.length) }}%
            </div>
          </div>
          <div class="text-center">
            <div class="text-xs text-[var(--text3)] mb-1">Total Active</div>
            <div class="text-2xl font-bold text-[var(--text)]">
              {{ agentChartData.reduce((sum, zone) => sum + zone.totalActive, 0) }}
            </div>
          </div>
          <div class="text-center">
            <div class="text-xs text-[var(--text3)] mb-1">Total Inactive</div>
            <div class="text-2xl font-bold text-[var(--text)]">
              {{ agentChartData.reduce((sum, zone) => sum + zone.totalInactive, 0) }}
            </div>
          </div>
          <div class="text-center">
            <div class="text-xs text-[var(--text3)] mb-1">Total Zones</div>
            <div class="text-2xl font-bold text-[var(--text)]">{{ agentChartData.length }}</div>
          </div>
        </div>
      </div>
      
      <!-- Table View -->
      <div v-else-if="viewMode === 'table'">
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
                  {{ formatZone(zoneData.zone) }}
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
                <td class="border-r border-[var(--border)] px-4 py-3 pl-10 text-sm text-[var(--text2)]">
                  {{ formatRegion(region.region) }}
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
