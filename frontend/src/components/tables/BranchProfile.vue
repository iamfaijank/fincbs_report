<script setup>
import { computed, ref, onMounted } from 'vue'
import { frappeRequest } from 'frappe-ui'
import { useNumberFormat } from '@/composables/useNumberFormat.js'
import { useNameFormat } from '@/composables/useNameFormat.js'
import AchievementBadge from './AchievementBadge.vue'

const props = defineProps({
  branch: { type: Object, required: true },
  months: { type: Array, default: () => [] },
  branchProfile: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['back'])

const { formatNumber } = useNumberFormat()
const { formatZone, formatRegion } = useNameFormat()

const activeMonth = computed(() => props.months.length > 0 ? props.months[props.months.length - 1] : null)
const asOfMonth = computed(() => {
  if (activeMonth.value?.display) return activeMonth.value.display
  if (props.branchProfile?.month) return props.branchProfile.month
  if (props.months.length > 0) return props.months[props.months.length - 1]?.display || ''
  return ''
})

// Session user's Employee resignation status (Resign / Active)
const employeeStatus = ref('Active')
const employeeStatusClass = computed(() =>
  employeeStatus.value === 'Resign'
    ? 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'
    : 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400'
)
onMounted(async () => {
  try {
    const res = await frappeRequest({
      url: '/api/method/custom_report.www.drishti.get_current_user_employee_status',
      method: 'POST',
    })
    if (res && res.status) employeeStatus.value = res.status
  } catch (e) {
    console.error('Failed to load employee status', e)
  }
})

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

function scrollToManpowerDetails() {
  const element = document.getElementById('manpower-details')
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Header with Back Button -->
    <div class="px-5 py-3 border-b border-[var(--border)] flex items-center gap-3 flex-shrink-0">
      <button
        @click="emit('back')"
        class="flex items-center gap-1 text-sm text-[var(--text3)] hover:text-[var(--text)] transition"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"></polyline>
        </svg>
        Back
      </button>
      <span class="text-sm font-semibold text-[var(--text)]">{{ branch.branch }} ({{ branch.sol_id }})</span>
    </div>

    <!-- Branch Information Card -->
    <div class="mx-5 my-4 sb-card flex-shrink-0">
      <div class="px-4 py-3 border-b border-[var(--border)]">
        <div class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">Branch Information</div>
      </div>
      <div class="px-4 py-4">
        <div class="flex gap-4">
          <!-- Column 1: BM Badge -->
          <div class="flex-shrink-0">
            <span class="inline-flex items-center justify-center w-32 h-32 rounded bg-blue-100 text-blue-600 text-2xl font-bold dark:bg-blue-900/30 dark:text-blue-400">BM</span>
          </div>
          <!-- Column 2: 2 Rows -->
          <div class="flex-1 space-y-3">
            <!-- Row 1: Branch Manager Name -->
            <div>
              <span class="text-sm font-semibold text-[var(--text)]">Branch Manager</span>
              <span class="text-[11px] text-[var(--text3)] ml-2">{{ branchProfile?.bm_name || '—' }}</span>
              <span class="ml-2 inline-flex items-center rounded px-2 py-0.5 text-[10px] font-semibold" :class="employeeStatusClass">{{ employeeStatus }}</span>
            </div>
            <!-- Row 2: 3 Sub-columns -->
            <div class="grid grid-cols-3 gap-4">
              <!-- Sub-column 1: BM Details -->
              <div class="space-y-3">
                <div class="flex gap-2">
                  <span class="text-[11px] font-medium text-[var(--text3)] w-24 shrink-0">BM DOJ</span>
                  <span class="text-[11px] text-[var(--text)]">{{ branchProfile?.bm_doj || '—' }}</span>
                </div>
                <div class="flex gap-2">
                  <span class="text-[11px] font-medium text-[var(--text3)] w-24 shrink-0">BM Vintage</span>
                  <span class="text-[11px] text-[var(--text)]">{{ branchProfile?.bm_vintage || '—' }}</span>
                </div>
                <div class="flex gap-2">
                  <span class="text-[11px] font-medium text-[var(--text3)] w-24 shrink-0">BM Mobile</span>
                  <span class="text-[11px] text-[var(--text)]">{{ branchProfile?.bm_mob_no || '—' }}</span>
                </div>
              </div>
              <!-- Sub-column 2: Branch Details -->
              <div class="space-y-3">
                <div class="flex gap-2">
                  <span class="text-[11px] font-medium text-[var(--text3)] w-24 shrink-0">Branch Opening</span>
                  <span class="text-[11px] text-[var(--text)]">{{ branchProfile?.branch_opening_date || '—' }}</span>
                </div>
                <div class="flex gap-2">
                  <span class="text-[11px] font-medium text-[var(--text3)] w-24 shrink-0">Branch Vintage</span>
                  <span class="text-[11px] text-[var(--text)]">{{ branchProfile?.branch_vintage || '—' }}</span>
                </div>
                <div class="flex gap-2">
                  <span class="text-[11px] font-medium text-[var(--text3)] w-24 shrink-0">Branch Email</span>
                  <span class="text-[11px] text-[var(--text)]">{{ branch.email || branchProfile?.email || '—' }}</span>
                </div>
              </div>
              <!-- Sub-column 3: Reporting Person -->
              <div class="space-y-3">
                <div class="flex gap-2">
                  <span class="text-[11px] font-medium text-[var(--text3)] w-24 shrink-0">Reporting Person</span>
                  <span class="text-[11px] text-[var(--text)]">{{ branchProfile?.ch_name || '—' }}</span>
                </div>
                <div class="flex gap-2">
                  <span class="text-[11px] font-medium text-[var(--text3)] w-24 shrink-0">RP Mobile</span>
                  <span class="text-[11px] text-[var(--text)]">{{ branchProfile?.ch_mob_no || '—' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Three Cards Row -->
    <div class="mx-5 mb-4 grid grid-cols-3 gap-4 flex-shrink-0">
      <!-- Manpower Status Card -->
      <div class="sb-card">
        <div class="px-4 py-3 border-b border-[var(--border)]">
          <div class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">Manpower Status</div>
        </div>
        <div class="px-4 py-4">
          <!-- BDO, BDE, RO Cards in a Row -->
          <div class="grid grid-cols-3 gap-3 mb-4">
            <!-- BDO Card -->
            <div class="rounded border border-[var(--border)] bg-[var(--bg2)] p-3 text-center">
              <div class="text-[10px] font-medium text-[var(--text3)] mb-1">BDO</div>
              <div class="text-lg font-bold text-[var(--text)]">{{ branchProfile?.bdo || '—' }}</div>
            </div>
            <!-- BDE Card -->
            <div class="rounded border border-[var(--border)] bg-[var(--bg2)] p-3 text-center">
              <div class="text-[10px] font-medium text-[var(--text3)] mb-1">BDE</div>
              <div class="text-lg font-bold text-[var(--text)]">{{ branchProfile?.bde || '—' }}</div>
            </div>
            <!-- RO Card -->
            <div class="rounded border border-[var(--border)] bg-[var(--bg2)] p-3 text-center">
              <div class="text-[10px] font-medium text-[var(--text3)] mb-1">RO</div>
              <div class="text-lg font-bold text-[var(--text)]">{{ branchProfile?.ro || '—' }}</div>
            </div>
          </div>
          <!-- Staff Progress Bar -->
          <div>
            <div class="w-full bg-gray-200 rounded-full h-3 dark:bg-gray-700 mb-2">
              <div 
                class="h-3 rounded-full transition-all duration-300"
                :class="(branchProfile?.staff_count || 0) >= (branchProfile?.total_no_of_budgeted_staff || 1) ? 'bg-green-500' : 'bg-amber-500'"
                :style="{ width: Math.min(((branchProfile?.staff_count || 0) / (branchProfile?.total_no_of_budgeted_staff || 1)) * 100, 100) + '%' }"
              ></div>
            </div>
            <div class="flex justify-between items-center mb-2">
              <span class="text-[11px] font-medium text-[var(--text3)]">Budget Staff: {{ branchProfile?.total_no_of_budgeted_staff || '0' }}</span>
              <span class="text-[11px] font-medium text-[var(--text3)]">Staff Count: {{ branchProfile?.staff_count || '0' }}</span>
            </div>
            <div class="text-center">
              <a 
                href="#manpower-details" 
                @click.prevent="scrollToManpowerDetails"
                class="text-[11px] text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 cursor-pointer underline"
              >
                View Detailed Manpower Table
              </a>
            </div>
          </div>
        </div>
      </div>

      <!-- Agent Details Card -->
      <div class="sb-card">
        <div class="px-4 py-3 border-b border-[var(--border)]">
          <div class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">Agent Details</div>
        </div>
        <div class="px-4 py-4">
          <div class="space-y-4">
            <!-- DDS Agents Row -->
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <div class="text-sm font-semibold text-[var(--text)] mb-1">DDS Agents</div>
                <div class="text-[11px] text-[var(--text3)]">
                  Active: {{ branchProfile?.total_active_dds_agent || 0 }} / Total: {{ branchProfile?.total_dds_agent || 0 }}
                </div>
              </div>
              <div class="relative w-16 h-16 flex-shrink-0">
                <svg class="transform -rotate-90" width="64" height="64" viewBox="0 0 64 64">
                  <!-- Background circle -->
                  <circle cx="32" cy="32" r="28" fill="none" stroke="#e5e7eb" stroke-width="6"></circle>
                  <!-- Progress circle -->
                  <circle 
                    cx="32" cy="32" r="28" 
                    fill="none" 
                    stroke="#10b981" 
                    stroke-width="6"
                    stroke-linecap="round"
                    stroke-dasharray="176"
                    :stroke-dashoffset="176 - (176 * ((branchProfile?.total_active_dds_agent || 0) / Math.max(branchProfile?.total_dds_agent || 1, 1)))"
                    class="transition-all duration-300"
                  ></circle>
                </svg>
                <div class="absolute inset-0 flex items-center justify-center">
                  <span class="text-xs font-bold text-[var(--text)]">
                    {{ Math.round(((branchProfile?.total_active_dds_agent || 0) / Math.max(branchProfile?.total_dds_agent || 1, 1)) * 100) }}%
                  </span>
                </div>
              </div>
            </div>

            <!-- SS Agents Row -->
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <div class="text-sm font-semibold text-[var(--text)] mb-1">SS Agents</div>
                <div class="text-[11px] text-[var(--text3)]">
                  Active: {{ branchProfile?.total_active_ss_agent || 0 }} / Total: {{ branchProfile?.total_ss_agent || 0 }}
                </div>
              </div>
              <div class="relative w-16 h-16 flex-shrink-0">
                <svg class="transform -rotate-90" width="64" height="64" viewBox="0 0 64 64">
                  <!-- Background circle -->
                  <circle cx="32" cy="32" r="28" fill="none" stroke="#e5e7eb" stroke-width="6"></circle>
                  <!-- Progress circle -->
                  <circle 
                    cx="32" cy="32" r="28" 
                    fill="none" 
                    stroke="#3b82f6" 
                    stroke-width="6"
                    stroke-linecap="round"
                    stroke-dasharray="176"
                    :stroke-dashoffset="176 - (176 * ((branchProfile?.total_active_ss_agent || 0) / Math.max(branchProfile?.total_ss_agent || 1, 1)))"
                    class="transition-all duration-300"
                  ></circle>
                </svg>
                <div class="absolute inset-0 flex items-center justify-center">
                  <span class="text-xs font-bold text-[var(--text)]">
                    {{ Math.round(((branchProfile?.total_active_ss_agent || 0) / Math.max(branchProfile?.total_ss_agent || 1, 1)) * 100) }}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Category Card -->
      <div class="sb-card">
        <div class="px-4 py-3 border-b border-[var(--border)]">
          <div class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">Category</div>
        </div>
        <div class="px-4 py-4">
          <div class="space-y-2">
            <!-- PINNACLE -->
            <div class="flex items-center justify-between py-1.5 px-2 rounded bg-green-50 dark:bg-green-900/20">
              <span class="text-xs font-semibold text-green-700 dark:text-green-400">PINNACLE</span>
              <span class="text-xs font-medium text-green-600 dark:text-green-500">100%</span>
            </div>
            <!-- MASTER -->
            <div class="flex items-center justify-between py-1.5 px-2 rounded bg-teal-50 dark:bg-teal-900/20">
              <span class="text-xs font-semibold text-teal-700 dark:text-teal-400">MASTER</span>
              <span class="text-xs font-medium text-teal-600 dark:text-teal-500">80-100%</span>
            </div>
            <!-- ACCELERATOR -->
            <div class="flex items-center justify-between py-1.5 px-2 rounded bg-blue-50 dark:bg-blue-900/20">
              <span class="text-xs font-semibold text-blue-700 dark:text-blue-400">ACCELERATOR</span>
              <span class="text-xs font-medium text-blue-600 dark:text-blue-500">65-80%</span>
            </div>
            <!-- STARTER -->
            <div class="flex items-center justify-between py-1.5 px-2 rounded bg-amber-50 dark:bg-amber-900/20">
              <span class="text-xs font-semibold text-amber-700 dark:text-amber-400">STARTER</span>
              <span class="text-xs font-medium text-amber-600 dark:text-amber-500">40-65%</span>
            </div>
            <!-- LEARNER -->
            <div class="flex items-center justify-between py-1.5 px-2 rounded bg-orange-50 dark:bg-orange-900/20">
              <span class="text-xs font-semibold text-orange-700 dark:text-orange-400">LEARNER</span>
              <span class="text-xs font-medium text-orange-600 dark:text-orange-500">20-40%</span>
            </div>
            <!-- ZERO -->
            <div class="flex items-center justify-between py-1.5 px-2 rounded bg-red-50 dark:bg-red-900/20">
              <span class="text-xs font-semibold text-red-700 dark:text-red-400">ZERO</span>
              <span class="text-xs font-medium text-red-600 dark:text-red-500">0-20%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Deposit & Book Position Card -->
    <div class="mx-5 mb-4 sb-card flex-shrink-0">
      <div class="px-4 py-3 border-b border-[var(--border)]">
        <div class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">Deposit & Book Position</div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="px-4 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Account Type</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Book Position</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Composition</th>
            </tr>
          </thead>
          <tbody>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Savings Account (SA)</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.sa_book || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_book ? Math.round((branchProfile?.sa_book || 0) / branchProfile.total_book * 100) : 0 }}%</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Current Account (CA)</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.ca_book || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_book ? Math.round((branchProfile?.ca_book || 0) / branchProfile.total_book * 100) : 0 }}%</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Fixed Deposit (FD)</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.fd_book || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_book ? Math.round((branchProfile?.fd_book || 0) / branchProfile.total_book * 100) : 0 }}%</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Recurring Deposit (RD)</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.rd_book || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_book ? Math.round((branchProfile?.rd_book || 0) / branchProfile.total_book * 100) : 0 }}%</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Daily Deposit Scheme (DDS)</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.dds_book || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_book ? Math.round((branchProfile?.dds_book || 0) / branchProfile.total_book * 100) : 0 }}%</td>
            </tr>
            <tr class="hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">SMBG</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.smbg_book || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_book ? Math.round((branchProfile?.smbg_book || 0) / branchProfile.total_book * 100) : 0 }}%</td>
            </tr>
            <tr class="border-t-2 border-[var(--border)] bg-[var(--bg2)] font-semibold">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Total</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.total_book || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">100%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Account Details Card -->
    <div class="mx-5 mb-4 sb-card flex-shrink-0">
      <div class="px-4 py-3 border-b border-[var(--border)]">
        <div class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">Account Details</div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="px-4 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Category</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Account Count</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Composition</th>
            </tr>
          </thead>
          <tbody>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Savings Account (SA)</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.total_sa_no_of_customers || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_customers_id ? Math.round((branchProfile?.total_sa_no_of_customers || 0) / branchProfile.total_customers_id * 100) : 0 }}%</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Current Account (CA)</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.total_ca_no_of_customers || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_customers_id ? Math.round((branchProfile?.total_ca_no_of_customers || 0) / branchProfile.total_customers_id * 100) : 0 }}%</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Fixed Deposit (FD)</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.total_fd_no_of_customers || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_customers_id ? Math.round((branchProfile?.total_fd_no_of_customers || 0) / branchProfile.total_customers_id * 100) : 0 }}%</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Recurring Deposit (RD)</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.total_rd_no_of_customers || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_customers_id ? Math.round((branchProfile?.total_rd_no_of_customers || 0) / branchProfile.total_customers_id * 100) : 0 }}%</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Daily Deposit Scheme (DDS)</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.total_dds_no_of_customers || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_customers_id ? Math.round((branchProfile?.total_dds_no_of_customers || 0) / branchProfile.total_customers_id * 100) : 0 }}%</td>
            </tr>
            <tr class="hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">SMBG</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.total_smbg_no_of_customers || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_customers_id ? Math.round((branchProfile?.total_smbg_no_of_customers || 0) / branchProfile.total_customers_id * 100) : 0 }}%</td>
            </tr>
            <tr class="border-t-2 border-[var(--border)] bg-[var(--bg2)] font-semibold">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Total</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.total_customers_id || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">100%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Demand & Collection Performance Card -->
    <div class="mx-5 mb-4 sb-card flex-shrink-0">
      <div class="px-4 py-3 border-b border-[var(--border)]">
        <div class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">Demand & Collection Performance</div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="px-4 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Metric</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Performance</th>
            </tr>
          </thead>
          <tbody>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">DDS Demand</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.dds_demand || 0) }}</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">DDS Collection</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.dds_collection || 0) }}</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">DDS Demand vs Collection</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ branchProfile?.dds_demand_vs_collection || '—' }}</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">SMBG Demand</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.smbg_demand || 0) }}</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">SMBG Collection</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.smbg_collection || 0) }}</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">SMBG Demand vs Collection</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ branchProfile?.smbg_demand_vs_collection || '—' }}</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">RD Demand</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.rd_demand || 0) }}</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">RD Collection</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.rd_collection || 0) }}</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">RD SMBG Collection</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.rd_smbg_collection || 0) }}</td>
            </tr>
            <tr class="hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">RD SMBG Pending</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.rd_smbg_pending || 0) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Productivity Details Card -->
    <div class="mx-5 mb-4 sb-card flex-shrink-0">
      <div class="px-4 py-3 border-b border-[var(--border)] flex items-center justify-between">
        <div class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">Productivity Details</div>
        <div class="text-[11px] font-medium text-[var(--text3)]">As of: {{ asOfMonth || '—' }}</div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="px-4 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Metric</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Value</th>
            </tr>
          </thead>
          <tbody>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Total Productivity</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">-</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">BDO Productivity</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">-</td>
            </tr>
            <tr class="hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">BDE Productivity</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">-</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Manpower Details Card -->
    <div id="manpower-details" class="mx-5 mb-4 sb-card flex-shrink-0">
      <div class="px-4 py-3 border-b border-[var(--border)]">
        <div class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">Manpower Details</div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="px-4 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Employee ID</th>
              <th class="px-4 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Employee Name</th>
              <th class="px-4 py-2 text-center text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Vintage</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Total Leads</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Total Converted</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Conversion Ratio</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Monthly Business</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Yearly Business</th>
              <th class="px-4 py-2 text-center text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">PIP Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!branchProfile?.manpower_details || branchProfile.manpower_details.length === 0">
              <td colspan="9" class="px-4 py-3 text-center text-[11px] text-[var(--text3)]">No data available</td>
            </tr>
            <tr v-for="(emp, idx) in branchProfile?.manpower_details || []" :key="idx" class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-mono text-[var(--text)]">{{ emp.employee_id || '—' }}</td>
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">{{ emp.employee_name || '—' }}</td>
              <td class="px-4 py-3 text-center text-[11px] text-[var(--text)]">{{ emp.vintage || '—' }}</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ emp.total_leads || '—' }}</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ emp.total_converted || '—' }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ emp.conversion_ratio || '—' }}</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ emp.monthly_business || '—' }}</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ emp.yearly_business || '—' }}</td>
              <td class="px-4 py-3 text-center text-[11px] text-[var(--text)]">{{ emp.pip_status || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Monthly Data Table -->
    <div class="flex-1 overflow-auto">
      <table class="w-full">
        <thead class="sticky top-0 bg-[var(--bg2)]">
          <tr class="border-b border-[var(--border)]">
            <th class="border-r border-[var(--border)] px-4 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
              Month
            </th>
            <th class="border-r border-[var(--border)] px-4 py-2 text-center text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
              Category
            </th>
            <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
              Target
            </th>
            <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
              Achievement
            </th>
            <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
              Ach %
            </th>
            <th class="px-4 py-2 text-center text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
              Status
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="m in months"
            :key="m.key"
            class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
          >
            <td class="border-r border-[var(--border)] px-4 py-3 text-sm font-medium text-[var(--text)]">
              {{ m.display }}
            </td>
            <template v-if="branch.months?.[m.key]">
              <td class="border-r border-[var(--border)] px-4 py-3 text-center">
                <span class="inline-block rounded px-2 py-0.5 text-xs font-medium" :class="CATEGORY_COLORS[branch.months[m.key].category] || ''">
                  {{ branch.months[m.key].category }}
                </span>
              </td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">
                {{ formatNumber(branch.months[m.key].target) }}
              </td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">
                {{ formatNumber(branch.months[m.key].achievement) }}
              </td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm">
                <AchievementBadge :value="branch.months[m.key].percentage" />
              </td>
              <td class="px-4 py-3 text-center">
                <span
                  class="inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium"
                  :class="STATUS_META[branch.months[m.key].status]?.class || ''"
                >
                  <svg v-if="STATUS_META[branch.months[m.key].status]?.icon === 'up'" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="18 15 12 9 6 15"></polyline>
                  </svg>
                  <svg v-else-if="STATUS_META[branch.months[m.key].status]?.icon === 'down'" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="6 9 12 15 18 9"></polyline>
                  </svg>
                  <svg v-else width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                  </svg>
                  {{ STATUS_META[branch.months[m.key].status]?.label || branch.months[m.key].status }}
                </span>
              </td>
            </template>
            <template v-else>
              <td colspan="5" class="px-4 py-3 text-center text-sm text-[var(--text3)]">—</td>
            </template>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
