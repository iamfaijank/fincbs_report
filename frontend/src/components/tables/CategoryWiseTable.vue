<script setup>
import { ref, computed } from 'vue'
import SummaryCardGroup from '@/components/cards/SummaryCardGroup.vue'

const categoryData = ref([
  { category: 'Pinnacle', performanceBand: '>100%', branchCount: 42, movement: '+5', movementDirection: 'up', healthStatus: 'excellent' },
  { category: 'Master', performanceBand: '80–100%', branchCount: 38, movement: '+3', movementDirection: 'up', healthStatus: 'good' },
  { category: 'Accelerator', performanceBand: '60–80%', branchCount: 61, movement: '-2', movementDirection: 'down', healthStatus: 'average' },
  { category: 'Starter', performanceBand: '40–60%', branchCount: 47, movement: '+1', movementDirection: 'up', healthStatus: 'average' },
  { category: 'Learner', performanceBand: '20–40%', branchCount: 28, movement: '-4', movementDirection: 'down', healthStatus: 'poor' },
  { category: 'Zero Level', performanceBand: '0–20%', branchCount: 13, movement: '0', movementDirection: 'neutral', healthStatus: 'critical' },
])

const totalBranchCount = computed(() => categoryData.value.reduce((sum, r) => sum + r.branchCount, 0))
</script>

<template>
  <div class="sb-card card-table">
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead>
          <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
            <th class="border-r border-[var(--border)] px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              Category
            </th>
            <th class="border-r border-[var(--border)] px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              Performance Band
            </th>
            <th class="border-r border-[var(--border)] px-5 py-3 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              Branch Count
            </th>
            <th class="border-r border-[var(--border)] px-5 py-3 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              Movement (vs Prev. Day)
            </th>
            <th class="px-5 py-3 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              Health Status
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, index) in categoryData"
            :key="index"
            class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
          >
            <td class="border-r border-[var(--border)] px-5 py-3 text-sm font-semibold text-[var(--text)]">
              {{ row.category }}
            </td>
            <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text)]">
              <span class="rounded bg-[var(--bg2)] px-2 py-1 font-mono text-xs">{{ row.performanceBand }}</span>
            </td>
            <td class="border-r border-[var(--border)] px-5 py-3 text-center font-mono text-sm text-[var(--text)]">
              {{ row.branchCount }}
            </td>
            <td class="border-r border-[var(--border)] px-5 py-3 text-center text-sm">
              <span
                class="inline-flex items-center gap-1 rounded px-2 py-0.5 font-mono text-xs font-medium"
                :class="
                  row.movementDirection === 'up'
                    ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                    : row.movementDirection === 'down'
                    ? 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'
                    : 'bg-gray-50 text-gray-600 dark:bg-gray-900/30 dark:text-gray-400'
                "
              >
                <svg
                  v-if="row.movementDirection === 'up'"
                  width="12"
                  height="12"
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
                  v-else-if="row.movementDirection === 'down'"
                  width="12"
                  height="12"
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
                  v-else
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
                {{ row.movement }}
              </span>
            </td>
            <td class="px-5 py-3 text-center">
              <span
                class="inline-block rounded-full px-3 py-1 text-xs font-medium"
                :class="
                  row.healthStatus === 'excellent'
                    ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                    : row.healthStatus === 'good'
                    ? 'bg-teal-50 text-teal-600 dark:bg-teal-900/30 dark:text-teal-400'
                    : row.healthStatus === 'average'
                    ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400'
                    : row.healthStatus === 'poor'
                    ? 'bg-orange-50 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400'
                    : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'
                "
              >
                {{ row.healthStatus.charAt(0).toUpperCase() + row.healthStatus.slice(1) }}
              </span>
            </td>
          </tr>
          <tr class="border-t-2 border-[var(--border)] bg-[var(--bg2)] font-semibold">
            <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text)]">
              Total
            </td>
            <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text3)]">
              —
            </td>
            <td class="border-r border-[var(--border)] px-5 py-3 text-center font-mono text-sm text-[var(--text)]">
              {{ totalBranchCount }}
            </td>
            <td class="border-r border-[var(--border)] px-5 py-3 text-center text-sm text-[var(--text3)]">
              —
            </td>
            <td class="px-5 py-3 text-center text-sm text-[var(--text3)]">
              —
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
