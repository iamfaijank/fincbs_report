<script setup>
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

const activeMonth = props.months.length > 0 ? props.months[props.months.length - 1] : null

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
</script>

<template>
  <div class="sb-card card-table h-full flex flex-col">
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
        <div class="grid grid-cols-2 gap-4">
          <div class="flex gap-2">
            <span class="text-[11px] font-medium text-[var(--text3)] w-20 shrink-0">Branch</span>
            <span class="text-[11px] text-[var(--text)]">{{ branch.branch }}</span>
          </div>
          <div class="flex gap-2">
            <span class="text-[11px] font-medium text-[var(--text3)] w-20 shrink-0">SOL ID</span>
            <span class="text-[11px] text-[var(--text)]">{{ branch.sol_id }}</span>
          </div>
          <div class="flex gap-2">
            <span class="text-[11px] font-medium text-[var(--text3)] w-20 shrink-0">Zone</span>
            <span class="text-[11px] text-[var(--text)]">{{ formatZone(branch.zone) }}</span>
          </div>
          <div class="flex gap-2">
            <span class="text-[11px] font-medium text-[var(--text3)] w-20 shrink-0">Region</span>
            <span class="text-[11px] text-[var(--text)]">{{ formatRegion(branch.region) }}</span>
          </div>
          <div class="flex gap-2">
            <span class="text-[11px] font-medium text-[var(--text3)] w-20 shrink-0">State</span>
            <span class="text-[11px] text-[var(--text)]">{{ branch.state || '—' }}</span>
          </div>
          <div class="flex gap-2">
            <span class="text-[11px] font-medium text-[var(--text3)] w-20 shrink-0">Email</span>
            <span class="text-[11px] text-[var(--text)]">{{ branch.email || '—' }}</span>
          </div>
          <div class="flex gap-2 col-span-2">
            <span class="text-[11px] font-medium text-[var(--text3)] w-20 shrink-0">Address</span>
            <span class="text-[11px] text-[var(--text)]">{{ branch.address || '—' }}</span>
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
          <div class="space-y-3">
            <div class="flex justify-between items-center">
              <span class="text-[11px] text-[var(--text3)]">BDO</span>
              <span class="text-[11px] font-medium text-[var(--text)]">{{ branchProfile?.bdo || '—' }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-[11px] text-[var(--text3)]">BDE</span>
              <span class="text-[11px] font-medium text-[var(--text)]">{{ branchProfile?.bde || '—' }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-[11px] text-[var(--text3)]">RO</span>
              <span class="text-[11px] font-medium text-[var(--text)]">{{ branchProfile?.ro || '—' }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-[11px] text-[var(--text3)]">Staff Count</span>
              <span class="text-[11px] font-medium text-[var(--text)]">{{ branchProfile?.staff_count || '—' }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-[11px] text-[var(--text3)]">Budget Staff</span>
              <span class="text-[11px] font-medium text-[var(--text)]">{{ branchProfile?.total_no_of_budgeted_staff || '—' }}</span>
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
          <div class="space-y-3">
            <div class="flex justify-between items-center">
              <span class="text-[11px] text-[var(--text3)]">Active SS Agent</span>
              <span class="text-[11px] font-medium text-[var(--text)]">{{ branchProfile?.total_active_ss_agent || '—' }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-[11px] text-[var(--text3)]">Total SS Agent</span>
              <span class="text-[11px] font-medium text-[var(--text)]">{{ branchProfile?.total_ss_agent || '—' }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-[11px] text-[var(--text3)]">Active DDS Agent</span>
              <span class="text-[11px] font-medium text-[var(--text)]">{{ branchProfile?.total_active_dds_agent || '—' }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-[11px] text-[var(--text3)]">Total DDS Agent</span>
              <span class="text-[11px] font-medium text-[var(--text)]">{{ branchProfile?.total_dds_agent || '—' }}</span>
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
          <div class="flex items-center justify-center">
            <span
              v-if="activeMonth && branch.months?.[activeMonth.key]"
              class="inline-block rounded px-3 py-1 text-sm font-medium"
              :class="CATEGORY_COLORS[branch.months[activeMonth.key].category] || ''"
            >
              {{ branch.months[activeMonth.key].category }}
            </span>
            <span v-else class="text-[11px] text-[var(--text3)]">—</span>
          </div>
          <div class="mt-4 space-y-3">
            <div class="flex justify-between items-center">
              <span class="text-[11px] text-[var(--text3)]">Target</span>
              <span class="text-[11px] font-medium text-[var(--text)]">{{ formatNumber(branch.months?.[activeMonth?.key]?.target || 0) }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-[11px] text-[var(--text3)]">Achievement</span>
              <span class="text-[11px] font-medium text-[var(--text)]">{{ formatNumber(branch.months?.[activeMonth?.key]?.achievement || 0) }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-[11px] text-[var(--text3)]">Ach %</span>
              <span class="text-[11px] font-medium text-[var(--text)]">{{ branch.months?.[activeMonth?.key]?.percentage || 0 }}%</span>
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
      <div class="px-4 py-3 border-b border-[var(--border)]">
        <div class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">Productivity Details</div>
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
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ branchProfile?.total_productivity || '—' }}</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">BDO Productivity</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ branchProfile?.bdo_productivity || '—' }}</td>
            </tr>
            <tr class="hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">BDE Productivity</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ branchProfile?.bde_productivity || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Manpower Details Card -->
    <div class="mx-5 mb-4 sb-card flex-shrink-0">
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
