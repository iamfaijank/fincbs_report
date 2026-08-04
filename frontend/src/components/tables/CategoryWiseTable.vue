<script setup>
import { ref, computed, onMounted } from 'vue'
import { frappeRequest } from 'frappe-ui'
import { useExpandableSet } from '@/composables/useExpandableSet.js'
import { useFilters } from '@/composables/useFilters.js'

const { toggle, isExpanded } = useExpandableSet()
const { isZoneSelected, isRegionSelected } = useFilters()

const categoryWise = ref([])
const months = ref([])
const loading = ref(true)

const CATEGORY_META = {
  Pinnacle: { band: '>100%', color: '#4fffb0', health: 'excellent' },
  Master: { band: '80–100%', color: '#2dd4bf', health: 'good' },
  Accelerator: { band: '60–80%', color: '#0ea5e9', health: 'average' },
  Starter: { band: '40–60%', color: '#f59e0b', health: 'average' },
  Learner: { band: '20–40%', color: '#ef4444', health: 'poor' },
  'Zero Level': { band: '0–20%', color: '#dc2626', health: 'critical' },
}

onMounted(async () => {
  try {
    const data = await frappeRequest({
      url: '/api/method/custom_report.www.drishti.get_category_wise_data',
      method: 'POST',
    }) || {}
    categoryWise.value = data.category_wise || []
    months.value = data.months || []
  } catch (e) {
    console.error('Failed to load category wise data', e)
  } finally {
    loading.value = false
  }
})

const activeMonth = computed(() => {
  if (months.value.length === 0) return null
  return months.value[months.value.length - 1]
})

function getMonthData(cat) {
  if (!activeMonth.value) return null
  return cat.months?.[activeMonth.value.key] || null
}

const totalBranchCount = computed(() => {
  return categoryWise.value.reduce((sum, cat) => {
    const md = getMonthData(cat)
    return sum + (md?.count || 0)
  }, 0)
})

const totalMovement = computed(() => {
  let inc = 0, dec = 0
  categoryWise.value.forEach(cat => {
    const m = getMovement(cat)
    inc += m.increased
    dec += m.decreased
  })
  return { increased: inc, decreased: dec, total: inc - dec }
})

function getMovement(cat) {
  const md = getMonthData(cat)
  if (!md?.changes) return { increased: 0, decreased: 0, total: 0 }
  const inc = md.changes.increased?.length || 0
  const dec = md.changes.decreased?.length || 0
  return { increased: inc, decreased: dec, total: inc - dec }
}
</script>

<template>
  <div class="sb-card card-table">
    <div v-if="loading" class="p-8 text-center text-sm text-[var(--text3)]">Loading...</div>
    <div v-else>
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
              Zone Breakdown
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
          <template v-for="cat in categoryWise" :key="cat.category">
            <tr
              class="cursor-pointer border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
              @click="toggle(cat.category)"
            >
              <td class="border-r border-[var(--border)] px-5 py-3 text-sm font-semibold text-[var(--text)]">
                <div class="flex items-center gap-2">
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    class="transition-transform"
                    :class="isExpanded(cat.category) ? 'rotate-90' : ''"
                  >
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                  <span
                    class="inline-block h-2.5 w-2.5 rounded-full"
                    :style="{ background: CATEGORY_META[cat.category]?.color || '#888' }"
                  ></span>
                  {{ cat.category }}
                </div>
              </td>
              <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text)]">
                <span class="rounded bg-[var(--bg2)] px-2 py-1 font-mono text-xs">{{ CATEGORY_META[cat.category]?.band || '—' }}</span>
              </td>
              <td class="border-r border-[var(--border)] px-5 py-3 text-center font-mono text-sm text-[var(--text)]">
                {{ getMonthData(cat)?.count || 0 }}
              </td>
              <td class="border-r border-[var(--border)] px-5 py-3 text-center text-sm text-[var(--text)]">
                <span class="text-xs text-[var(--text3)]">{{ Object.keys(getMonthData(cat)?.zone_breakdown || {}).length }} zones</span>
              </td>
              <td class="border-r border-[var(--border)] px-5 py-3 text-center text-sm">
                <span
                  class="inline-flex items-center gap-1 rounded px-2 py-0.5 font-mono text-xs font-medium"
                  :class="
                    getMovement(cat).total > 0
                      ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                      : getMovement(cat).total < 0
                      ? 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'
                      : 'bg-gray-50 text-gray-600 dark:bg-gray-900/30 dark:text-gray-400'
                  "
                >
                  <svg
                    v-if="getMovement(cat).total > 0"
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
                    v-else-if="getMovement(cat).total < 0"
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
                  {{ getMovement(cat).total > 0 ? '+' : '' }}{{ getMovement(cat).total }}
                </span>
              </td>
              <td class="px-5 py-3 text-center">
                <span
                  class="inline-block rounded-full px-3 py-1 text-xs font-medium"
                  :class="
                    CATEGORY_META[cat.category]?.health === 'excellent'
                      ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                      : CATEGORY_META[cat.category]?.health === 'good'
                      ? 'bg-teal-50 text-teal-600 dark:bg-teal-900/30 dark:text-teal-400'
                      : CATEGORY_META[cat.category]?.health === 'average'
                      ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400'
                      : CATEGORY_META[cat.category]?.health === 'poor'
                      ? 'bg-orange-50 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400'
                      : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'
                  "
                >
                  {{ CATEGORY_META[cat.category]?.health?.charAt(0).toUpperCase() + (CATEGORY_META[cat.category]?.health?.slice(1) || '') }}
                </span>
              </td>
            </tr>
            <template v-if="isExpanded(cat.category)">
              <tr
                v-for="(zone, zi) in getMonthData(cat)?.zone_breakdown || {}"
                :key="`${cat.category}-${zi}`"
                class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
              >
                <td class="border-r border-[var(--border)] px-5 py-3 pl-6 text-sm text-[var(--text3)]">
                  {{ zi }}
                </td>
                <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text3)]">
                  —
                </td>
                <td class="border-r border-[var(--border)] px-5 py-3 text-center font-mono text-sm text-[var(--text)]">
                  {{ zone }}
                </td>
                <td class="border-r border-[var(--border)] px-5 py-3 text-center text-sm text-[var(--text3)]">
                  —
                </td>
                <td class="border-r border-[var(--border)] px-5 py-3 text-center text-sm text-[var(--text3)]">
                  —
                </td>
                <td class="px-5 py-3 text-center text-sm text-[var(--text3)]">
                  —
                </td>
              </tr>
            </template>
          </template>
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
            <td class="border-r border-[var(--border)] px-5 py-3 text-center text-sm">
              <span
                class="inline-flex items-center gap-1 rounded px-2 py-0.5 font-mono text-xs font-medium"
                :class="
                  totalMovement.total > 0
                    ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                    : totalMovement.total < 0
                    ? 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'
                    : 'bg-gray-50 text-gray-600 dark:bg-gray-900/30 dark:text-gray-400'
                "
              >
                <svg v-if="totalMovement.total > 0" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="18 15 12 9 6 15"></polyline>
                </svg>
                <svg v-else-if="totalMovement.total < 0" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
                <svg v-else width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
                {{ totalMovement.total > 0 ? '+' : '' }}{{ totalMovement.total }}
              </span>
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
