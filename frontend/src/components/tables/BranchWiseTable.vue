<script setup>
import { ref, computed, onMounted } from 'vue'
import { frappeRequest } from 'frappe-ui'
import { useNumberFormat } from '@/composables/useNumberFormat.js'
import { useFilters } from '@/composables/useFilters.js'
import { useNameFormat } from '@/composables/useNameFormat.js'
import AchievementBadge from './AchievementBadge.vue'

const { formatNumber } = useNumberFormat()
const { isZoneSelected, isRegionSelected } = useFilters()
const { formatZone, formatRegion } = useNameFormat()

const branchWise = ref([])
const months = ref([])
const loading = ref(true)

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
  return branchWise.value.filter(b => isZoneSelected(b.zone) && isRegionSelected(b.region))
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
</script>

<template>
  <div class="sb-card card-table">
    <div v-if="loading" class="p-8 text-center text-sm text-[var(--text3)]">Loading...</div>
    <div v-else>
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
            class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
          >
            <td class="border-r border-[var(--border)] px-4 py-3 text-center font-mono text-sm text-[var(--text3)]">
              {{ row.sr_no }}
            </td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-sm font-semibold text-[var(--text)]">
              {{ row.branch }}
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
</template>
