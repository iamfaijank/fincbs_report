<script setup>
import { ref, computed, onMounted } from 'vue'
import { frappeRequest } from 'frappe-ui'
import { useNumberFormat } from '@/composables/useNumberFormat.js'
import { useFilters } from '@/composables/useFilters.js'
import { useNameFormat } from '@/composables/useNameFormat.js'
import AchievementBadge from './AchievementBadge.vue'
import ViewToggle from './ViewToggle.vue'

const props = defineProps({
  searchQuery: { type: String, default: '' },
})

const emit = defineEmits(['select'])

const { formatNumber } = useNumberFormat()
const { isZoneSelected, isRegionSelected } = useFilters()
const { formatZone, formatRegion } = useNameFormat()

const branchWise = ref([])
const months = ref([])
const loading = ref(true)
const viewMode = ref('table')

const STATUS_META = {
  improved: { label: 'Improved', class: 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400', icon: 'up' },
  declined: { label: 'Declined', class: 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400', icon: 'down' },
  increased: { label: 'Increased', class: 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400', icon: 'up' },
  decreased: { label: 'Decreased', class: 'bg-orange-50 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400', icon: 'down' },
  unchanged: { label: 'Unchanged', class: 'bg-gray-50 text-gray-600 dark:bg-gray-900/30 dark:text-gray-400', icon: 'flat' },
  new: { label: 'New', class: 'bg-purple-50 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400', icon: 'new' },
}

const CATEGORY_COLORS = {
  Pinnacle: 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400',
  Master: 'bg-teal-50 text-teal-600 dark:bg-teal-900/30 dark:text-teal-400',
  Accelerator: 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
  Starter: 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400',
  Learner: 'bg-orange-50 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400',
  'Zero Level': 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400',
}

onMounted(async () => {
  try {
    const data = await frappeRequest({
      url: '/api/method/custom_report.www.drishti.get_branch_wise_data',
      method: 'POST',
    }) || {}
    branchWise.value = data.branch_wise || []
    months.value = data.months || []
  } catch (e) {
    console.error('Failed to load branch wise data', e)
  } finally {
    loading.value = false
  }
})

const activeMonth = computed(() => {
  if (months.value.length === 0) return null
  return months.value[months.value.length - 1]
})

const filteredBranchData = computed(() => {
  let data = branchWise.value.filter(b => isZoneSelected(b.zone) && isRegionSelected(b.region))
  if (props.searchQuery && props.searchQuery.trim()) {
    const q = props.searchQuery.trim().toLowerCase()
    data = data.filter(b => b.branch.toLowerCase().includes(q) || b.sol_id.toLowerCase().includes(q))
  }
  return data
})

function getMonthData(branch) {
  if (!activeMonth.value) return null
  return branch.months?.[activeMonth.value.key] || null
}

const totals = computed(() => {
  let target = 0, achievement = 0
  filteredBranchData.value.forEach(b => {
    const md = getMonthData(b)
    if (md) {
      target += md.target || 0
      achievement += md.achievement || 0
    }
  })
  return { target, achievement, percentage: target > 0 ? Math.round(achievement / target * 100) : 0 }
})

function selectBranch(row) {
  emit('select', row)
}

// Chart data for branch-wise view
const branchChartData = computed(() => {
  const branches = filteredBranchData.value.slice(0, 20) // Show top 20 branches
  
  return branches.map(branch => {
    const md = getMonthData(branch)
    return {
      solId: branch.sol_id,
      branch: branch.branch,
      zone: formatZone(branch.zone),
      region: formatRegion(branch.region),
      category: branch.category,
      target: md?.target || 0,
      achievement: md?.achievement || 0,
      percentage: md?.target > 0 ? Math.round((md.achievement / md.target) * 100) : 0,
      status: branch.status,
      movement: branch.movement
    }
  }).sort((a, b) => b.percentage - a.percentage)
})

const chartOptions = computed(() => {
  const maxTarget = Math.max(...branchChartData.value.map(d => d.target), 1)
  const maxAchievement = Math.max(...branchChartData.value.map(d => d.achievement), 1)
  
  return {
    maxTarget,
    maxAchievement,
    colors: {
      pinnacle: '#10b981',
      master: '#0ea5e9', 
      accelerator: '#3b82f6',
      starter: '#f59e0b',
      learner: '#ef4444',
      zeroLevel: '#dc2626'
    }
  }
})

function getCategoryColor(category) {
  const categoryMap = {
    'Pinnacle': chartOptions.colors.pinnacle,
    'Master': chartOptions.colors.master,
    'Accelerator': chartOptions.colors.accelerator,
    'Starter': chartOptions.colors.starter,
    'Learner': chartOptions.colors.learner,
    'Zero Level': chartOptions.colors.zeroLevel
  }
  return categoryMap[category] || '#6b7280'
}
</script>

<template>
  <div class="sb-card card-table">
    <div v-if="loading" class="p-8 text-center text-sm text-[var(--text3)]">Loading...</div>
    <div v-else>
      <!-- View Toggle Header -->
      <div class="flex items-center justify-between border-b border-[var(--border)] bg-[var(--bg2)] px-5 py-3">
        <div class="text-sm font-semibold text-[var(--text3)] uppercase tracking-wider">
          Branch Performance
        </div>
        <ViewToggle v-model:viewMode="viewMode" color="#92400e" />
      </div>
      
      <!-- Chart View -->
      <div v-if="viewMode === 'chart' && branchChartData.length > 0" class="p-6">
        <!-- Top Performing Branches -->
        <div class="mb-8">
          <h3 class="text-sm font-semibold text-[var(--text3)] mb-4">Top Performing Branches</h3>
          
          <div class="space-y-4">
            <div v-for="(branch, index) in branchChartData" :key="branch.solId" class="chart-item">
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center gap-3">
                  <span class="w-6 text-right text-xs font-medium text-[var(--text3)]">{{ index + 1 }}.</span>
                  <div>
                    <div class="text-sm font-medium text-[var(--text)]">{{ branch.branch }}</div>
                    <div class="text-xs text-[var(--text3)]">{{ branch.zone }} • {{ branch.region }}</div>
                  </div>
                  <span 
                    class="text-xs font-medium px-2 py-1 rounded-full"
                    :style="{
                      backgroundColor: getCategoryColor(branch.category) + '20',
                      color: getCategoryColor(branch.category)
                    }"
                  >
                    {{ branch.category }}
                  </span>
                </div>
                <AchievementBadge :value="branch.percentage" />
              </div>
              
              <!-- Performance Bar -->
              <div class="mb-3">
                <div class="relative h-4 bg-[var(--bg2)] rounded-full overflow-hidden mb-2">
                  <div 
                    class="absolute top-0 left-0 h-full rounded-full transition-all duration-500"
                    :style="{
                      width: `${Math.min(100, (branch.achievement / chartOptions.maxAchievement) * 100)}%`,
                      backgroundColor: getCategoryColor(branch.category)
                    }"
                  ></div>
                </div>
                <div class="flex justify-between text-xs">
                  <span class="text-[var(--text3)]">Ach: {{ formatNumber(branch.achievement) }}</span>
                  <span class="text-[var(--text3)]">Target: {{ formatNumber(branch.target) }}</span>
                </div>
              </div>
              
              <!-- Status and Movement -->
              <div class="flex gap-3">
                <div v-if="branch.status" class="flex-1">
                  <div class="text-xs text-[var(--text3)] mb-1">Status</div>
                  <span 
                    class="inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-medium"
                    :class="STATUS_META[branch.status]?.class || 'bg-gray-50 text-gray-600'"
                  >
                    <svg
                      v-if="STATUS_META[branch.status]?.icon === 'up'"
                      width="10"
                      height="10"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <polyline points="18 15 12 9 6 15"></polyline>
                    </svg>
                    <svg
                      v-else-if="STATUS_META[branch.status]?.icon === 'down'"
                      width="10"
                      height="10"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                    <svg
                      v-else-if="STATUS_META[branch.status]?.icon === 'new'"
                      width="10"
                      height="10"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <circle cx="12" cy="12" r="10"></circle>
                      <line x1="12" y1="8" x2="12" y2="16"></line>
                      <line x1="8" y1="12" x2="16" y2="12"></line>
                    </svg>
                    {{ STATUS_META[branch.status]?.label || branch.status }}
                  </span>
                </div>
                <div v-if="branch.movement" class="flex-1">
                  <div class="text-xs text-[var(--text3)] mb-1">Movement</div>
                  <span 
                    class="inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-medium"
                    :class="STATUS_META[branch.movement]?.class || 'bg-gray-50 text-gray-600'"
                  >
                    {{ STATUS_META[branch.movement]?.label || branch.movement }}
                  </span>
                </div>
              </div>
              
              <!-- View Details Button -->
              <div class="mt-3 pt-3 border-t border-[var(--border)]">
                <button 
                  @click="selectBranch(branch)"
                  class="w-full text-xs text-center text-[var(--text3)] hover:text-[var(--text)] transition-colors"
                >
                  View Branch Details →
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Summary Stats -->
        <div class="mt-8 pt-6 border-t border-[var(--border)] grid grid-cols-4 gap-4">
          <div class="text-center">
            <div class="text-xs text-[var(--text3)] mb-1">Total Branches</div>
            <div class="text-2xl font-bold text-[var(--text)]">{{ filteredBranchData.length }}</div>
          </div>
          <div class="text-center">
            <div class="text-xs text-[var(--text3)] mb-1">Avg. Achievement</div>
            <div class="text-2xl font-bold text-[var(--text)]">{{ totals.percentage }}%</div>
          </div>
          <div class="text-center">
            <div class="text-xs text-[var(--text3)] mb-1">Total Achievement</div>
            <div class="text-2xl font-bold text-[var(--text)]">{{ formatNumber(totals.achievement) }}</div>
          </div>
          <div class="text-center">
            <div class="text-xs text-[var(--text3)] mb-1">Total Target</div>
            <div class="text-2xl font-bold text-[var(--text)]">{{ formatNumber(totals.target) }}</div>
          </div>
        </div>
        
        <!-- Category Distribution -->
        <div v-if="branchChartData.length > 0" class="mt-8 pt-6 border-t border-[var(--border)]">
          <h3 class="text-sm font-semibold text-[var(--text3)] mb-4">Category Distribution</h3>
          <div class="grid grid-cols-3 gap-4">
            <div 
              v-for="category in ['Pinnacle', 'Master', 'Accelerator', 'Starter', 'Learner', 'Zero Level']" 
              :key="category"
              class="text-center p-3 border border-[var(--border)] rounded-lg"
            >
              <div class="text-xs text-[var(--text3)] mb-1">{{ category }}</div>
              <div class="text-2xl font-bold" :style="{ color: getCategoryColor(category) }">
                {{ branchChartData.filter(b => b.category === category).length }}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Table View -->
      <div v-else-if="viewMode === 'table'">
        <table class="w-full">
          <thead>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="border-r border-[var(--border)] px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                SR. NO.
            </th>
            <th class="border-r border-[var(--border)] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              BRANCH
            </th>
            <th class="border-r border-[var(--border)] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              ZONE
            </th>
            <th class="border-r border-[var(--border)] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              REGION
            </th>
            <th v-if="activeMonth" colspan="4" class="border-r border-[var(--border)] px-4 py-2 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              {{ activeMonth.display }}
            </th>
            <th class="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              STATUS
            </th>
          </tr>
          <tr v-if="activeMonth" class="border-b border-[var(--border)] bg-[var(--bg2)]">
            <th colspan="4" class="border-r border-[var(--border)] px-4 py-2"></th>
            <th class="border-r border-[var(--border)] px-4 py-2 text-center text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Category</th>
            <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Target</th>
            <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Ach</th>
            <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Ach %</th>
            <th class="px-4 py-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in filteredBranchData"
            :key="row.sol_id"
            class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)] cursor-pointer"
            @click="selectBranch(row)"
          >
            <td class="border-r border-[var(--border)] px-4 py-3 text-center font-mono text-sm text-[var(--text3)]">
              {{ row.sr_no }}
            </td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-sm font-semibold text-[var(--text)]">
              {{ row.branch }} ({{ row.sol_id }})
            </td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text2)]">
              {{ formatZone(row.zone) }}
            </td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text2)]">
              {{ formatRegion(row.region) }}
            </td>
            <template v-if="activeMonth && getMonthData(row)">
              <td class="border-r border-[var(--border)] px-4 py-3 text-center">
                <span class="inline-block rounded px-2 py-0.5 text-xs font-medium" :class="CATEGORY_COLORS[getMonthData(row).category] || ''">
                  {{ getMonthData(row).category }}
                </span>
              </td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">
                {{ formatNumber(getMonthData(row).target) }}
              </td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">
                {{ formatNumber(getMonthData(row).achievement) }}
              </td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm">
                <AchievementBadge :value="getMonthData(row).percentage" />
              </td>
            </template>
            <template v-else>
              <td colspan="4" class="border-r border-[var(--border)] px-4 py-3 text-center text-sm text-[var(--text3)]">—</td>
            </template>
            <td class="px-4 py-3 text-center">
              <span
                v-if="getMonthData(row)"
                class="inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium"
                :class="STATUS_META[getMonthData(row).status]?.class || ''"
              >
                <svg v-if="STATUS_META[getMonthData(row).status]?.icon === 'up'" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="18 15 12 9 6 15"></polyline>
                </svg>
                <svg v-else-if="STATUS_META[getMonthData(row).status]?.icon === 'down'" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
                <svg v-else width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
                {{ STATUS_META[getMonthData(row).status]?.label || getMonthData(row).status }}
              </span>
            </td>
          </tr>
          <tr class="border-t-2 border-[var(--border)] bg-[var(--bg2)] font-semibold">
            <td class="border-r border-[var(--border)] px-4 py-3 text-center text-sm text-[var(--text3)]"></td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]" colspan="3">Total</td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-center text-sm text-[var(--text3)]">—</td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(totals.target) }}</td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(totals.achievement) }}</td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ totals.percentage }}%</td>
            <td class="px-4 py-3 text-center text-sm text-[var(--text3)]">—</td>
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
