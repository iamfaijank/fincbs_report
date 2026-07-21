<script setup>
import { ref, computed } from 'vue'
import { useNumberFormat } from '@/composables/useNumberFormat.js'
import AchievementBadge from './AchievementBadge.vue'

const { formatNumber } = useNumberFormat()

const branchData = ref([
  { sr: 1, branch: 'ABD-1001', segments: 'SB/CA/ND', category: 'Pinnacle', target: 1567890, julTarget: 522630, ach: 456789, achPercent: 87.4 },
  { sr: 2, branch: 'JHD-1002', segments: 'SB/CA', category: 'Master', target: 1432500, julTarget: 477500, ach: 423456, achPercent: 88.7 },
  { sr: 3, branch: 'PUN-1003', segments: 'SB/CA/FD', category: 'Accelerator', target: 1289000, julTarget: 429667, ach: 345678, achPercent: 80.5 },
  { sr: 4, branch: 'MUM-1004', segments: 'SB/CA/ND/RD', category: 'Pinnacle', target: 1890000, julTarget: 630000, ach: 598765, achPercent: 95.0 },
  { sr: 5, branch: 'DEL-1005', segments: 'SB/CA', category: 'Starter', target: 987650, julTarget: 329217, ach: 234567, achPercent: 71.3 },
  { sr: 6, branch: 'CHN-1006', segments: 'SB/CA/FD/RD', category: 'Master', target: 1654300, julTarget: 551433, ach: 498765, achPercent: 90.6 },
  { sr: 7, branch: 'HYD-1007', segments: 'SB/CA', category: 'Learner', target: 756000, julTarget: 252000, ach: 156789, achPercent: 62.4 },
  { sr: 8, branch: 'KOL-1008', segments: 'SB/CA/ND', category: 'Accelerator', target: 1123400, julTarget: 374467, ach: 298765, achPercent: 79.2 },
])

const totalTarget = computed(() => branchData.value.reduce((a, r) => a + r.target, 0))
const totalAch = computed(() => branchData.value.reduce((a, r) => a + r.ach, 0))
const totalAchPercent = computed(() => totalTarget.value > 0 ? (totalAch.value / totalTarget.value * 100).toFixed(1) : 0)
</script>

<template>
  <div class="sb-card card-table">
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead>
          <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
            <th rowspan="2" class="border-r border-[var(--border)] px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              SR. NO.
            </th>
            <th rowspan="2" class="border-r border-[var(--border)] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              BRANCH
            </th>
            <th rowspan="2" class="border-r border-[var(--border)] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              SEGMENTS
            </th>
            <th colspan="4" class="border-b border-r border-[var(--border)] px-4 py-2 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              JUL-2026<br/>
              <span class="text-[10px] font-normal">10 WORKING DAYS LEFT</span>
            </th>
          </tr>
          <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
            <th class="border-r border-[var(--border)] px-4 py-2 text-center text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">CATEGORY</th>
            <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">TARGET</th>
            <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">ACH</th>
            <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">ACH %</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in branchData"
            :key="row.sr"
            class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
          >
            <td class="border-r border-[var(--border)] px-4 py-3 text-center font-mono text-sm text-[var(--text3)]">
              {{ row.sr }}
            </td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-sm font-semibold text-[var(--text)]">
              {{ row.branch }}
            </td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text2)]">
              {{ row.segments }}
            </td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-center">
              <span class="inline-block rounded px-2 py-0.5 text-xs font-medium"
                :class="
                  row.category === 'Pinnacle' ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                  : row.category === 'Master' ? 'bg-teal-50 text-teal-600 dark:bg-teal-900/30 dark:text-teal-400'
                  : row.category === 'Accelerator' ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400'
                  : row.category === 'Starter' ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400'
                  : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'
                "
              >
                {{ row.category }}
              </span>
            </td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">
              {{ formatNumber(row.target) }}
            </td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">
              {{ formatNumber(row.ach) }}
            </td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm">
              <AchievementBadge :value="row.achPercent" />
            </td>
          </tr>
          <tr class="border-t-2 border-[var(--border)] bg-[var(--bg2)] font-semibold">
            <td class="border-r border-[var(--border)] px-4 py-3 text-center text-sm text-[var(--text3)]"></td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">Total</td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text3)]">—</td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-center text-sm text-[var(--text3)]">—</td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(totalTarget) }}</td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(totalAch) }}</td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ totalAchPercent }}%</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
