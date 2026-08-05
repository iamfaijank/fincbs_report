<script setup>
import { useNumberFormat } from '@/composables/useNumberFormat.js'
import { useNameFormat } from '@/composables/useNameFormat.js'
import AchievementBadge from './AchievementBadge.vue'

const props = defineProps({
  branch: { type: Object, required: true },
  months: { type: Array, default: () => [] },
})

const emit = defineEmits(['back'])

const { formatNumber } = useNumberFormat()
const { formatZone, formatRegion } = useNameFormat()

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

    <!-- Branch Info -->
    <div class="px-5 py-4 border-b border-[var(--border)] bg-[var(--bg2)] flex-shrink-0">
      <div class="grid grid-cols-4 gap-4">
        <div>
          <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)] mb-1">Branch</div>
          <div class="text-sm font-semibold text-[var(--text)]">{{ branch.branch }}</div>
        </div>
        <div>
          <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)] mb-1">SOL ID</div>
          <div class="text-sm font-mono text-[var(--text)]">{{ branch.sol_id }}</div>
        </div>
        <div>
          <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)] mb-1">Zone</div>
          <div class="text-sm text-[var(--text2)]">{{ formatZone(branch.zone) }}</div>
        </div>
        <div>
          <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)] mb-1">Region</div>
          <div class="text-sm text-[var(--text2)]">{{ formatRegion(branch.region) }}</div>
        </div>
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
