<script setup>
import { ref, inject } from 'vue'
import { useNumberFormat } from '@/composables/useNumberFormat.js'

const activeView = inject('activeView')
const { formatNumber } = useNumberFormat()
const activeTab = ref('zone')

const tabs = [
  { id: 'zone', label: 'Zone Wise', color: '#4fffb0' },
  { id: 'category', label: 'Category Wise', color: '#0ea5e9' },
  { id: 'product', label: 'Product Wise', color: '#a78bfa' },
  { id: 'agent', label: 'Agent Wise', color: '#2dd4bf' },
  { id: 'branch', label: 'Branch Wise', color: '#f59e0b' },
]

// Expanded zones tracker
const expandedZones = ref(new Set())

// Sample table data grouped by zones
const tableData = ref([
  {
    zone: 'Z-1',
    regions: [
      { region: 'R-1', branches: 42, target: 15678900, ach: 13456780, achPercent: 85.8 },
      { region: 'R-2', branches: 38, target: 14325000, ach: 13234500, achPercent: 92.4 },
      { region: 'R-3', branches: 35, target: 12890000, ach: 10234000, achPercent: 79.4 },
      { region: 'R-4', branches: 28, target: 11234000, ach: 9456000, achPercent: 84.2 },
    ]
  },
  {
    zone: 'Z-2',
    regions: [
      { region: 'R-1', branches: 35, target: 12890000, ach: 9876543, achPercent: 76.6 },
      { region: 'R-2', branches: 41, target: 16750000, ach: 15678900, achPercent: 93.6 },
      { region: 'R-3', branches: 32, target: 13450000, ach: 11234000, achPercent: 83.5 },
      { region: 'R-4', branches: 39, target: 15234000, ach: 13567000, achPercent: 89.1 },
    ]
  },
  {
    zone: 'Z-3',
    regions: [
      { region: 'R-1', branches: 29, target: 9845000, ach: 6734500, achPercent: 68.4 },
      { region: 'R-2', branches: 44, target: 18932000, ach: 16789000, achPercent: 88.7 },
      { region: 'R-3', branches: 31, target: 12567000, ach: 10234000, achPercent: 81.4 },
      { region: 'R-4', branches: 36, target: 14678000, ach: 13123000, achPercent: 89.4 },
    ]
  },
])

// Category table data
const categoryData = ref([
  { category: 'Pinnacle', performanceBand: '>100%', branchCount: 42, movement: '+5', movementDirection: 'up', healthStatus: 'excellent' },
  { category: 'Master', performanceBand: '80–100%', branchCount: 38, movement: '+3', movementDirection: 'up', healthStatus: 'good' },
  { category: 'Accelerator', performanceBand: '60–80%', branchCount: 61, movement: '-2', movementDirection: 'down', healthStatus: 'average' },
  { category: 'Starter', performanceBand: '40–60%', branchCount: 47, movement: '+1', movementDirection: 'up', healthStatus: 'average' },
  { category: 'Learner', performanceBand: '20–40%', branchCount: 28, movement: '-4', movementDirection: 'down', healthStatus: 'poor' },
  { category: 'Zero Level', performanceBand: '0–20%', branchCount: 13, movement: '0', movementDirection: 'neutral', healthStatus: 'critical' },
])


function toggleZone(zone) {
  if (expandedZones.value.has(zone)) {
    expandedZones.value.delete(zone)
  } else {
    expandedZones.value.add(zone)
  }
}

function isExpanded(zone) {
  return expandedZones.value.has(zone)
}

function getZoneTotals(zoneData) {
  const totals = zoneData.regions.reduce((acc, region) => {
    acc.branches += region.branches
    acc.target += region.target
    acc.ach += region.ach
    return acc
  }, { branches: 0, target: 0, ach: 0 })
  
  totals.achPercent = ((totals.ach / totals.target) * 100).toFixed(1)
  return totals
}

function getCategoryTotals() {
  const total = categoryData.value.reduce((acc, cat) => {
    acc.branchCount += cat.branchCount
    return acc
  }, { branchCount: 0 })
  return total
}
</script>

<template>
  <div>
    <!-- Summary Cards - Only in Drishti mode -->
    <div v-if="activeView === 'drishti'" class="mb-4 grid grid-cols-4 gap-3">
      <div class="sb-card">
        <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
          Total Branches
        </div>
        <div class="font-mono text-lg font-semibold text-[var(--text)]">229</div>
        <div class="text-[10px] text-[var(--text3)]">
          <span class="rounded bg-green-50 px-1 py-0.5 text-[9px] font-medium text-green-600 dark:bg-green-900/30 dark:text-green-400">
            +3.2%
          </span>
          vs last month
        </div>
      </div>
      <div class="sb-card">
        <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
          Target (MTD)
        </div>
        <div class="font-mono text-lg font-semibold text-[var(--text)]">
          <span class="text-xs text-[var(--text3)]">₹</span>163<span class="text-xs text-[var(--text3)]">Cr</span>
        </div>
        <div class="text-[10px] text-[var(--text3)]">
          <span class="rounded bg-amber-50 px-1 py-0.5 text-[9px] font-medium text-amber-600 dark:bg-amber-900/30 dark:text-amber-400">
            Monthly
          </span>
          target set
        </div>
      </div>
      <div class="sb-card">
        <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
          Achievement
        </div>
        <div class="font-mono text-lg font-semibold text-[var(--text)]">
          <span class="text-xs text-[var(--text3)]">₹</span>91.4<span class="text-xs text-[var(--text3)]">Cr</span>
        </div>
        <div class="text-[10px] text-[var(--text3)]">
          <span class="rounded bg-red-50 px-1 py-0.5 text-[9px] font-medium text-red-600 dark:bg-red-900/30 dark:text-red-400">
            57.9%
          </span>
          achieved
        </div>
      </div>
      <div class="sb-card">
        <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
          Active Zones
        </div>
        <div class="font-mono text-lg font-semibold text-[var(--text)]">6</div>
        <div class="text-[10px] text-[var(--text3)]">
          <span class="rounded bg-green-50 px-1 py-0.5 text-[9px] font-medium text-green-600 dark:bg-green-900/30 dark:text-green-400">
            All live
          </span>
          operational
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="mb-4 flex items-center gap-0.5 border-b border-[var(--border)]">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="flex items-center gap-1.5 border-b-2 px-4 py-2.5 text-[13px] font-medium transition"
        :class="
          activeTab === tab.id
            ? 'border-green-500 text-green-600'
            : 'border-transparent text-[var(--text3)] hover:text-[var(--text)]'
        "
        @click="activeTab = tab.id"
      >
        <span class="size-1.5 rounded-full" :style="{ backgroundColor: tab.color }" />
        {{ tab.label }}
      </button>
      <div class="flex-1" />
    </div>

    <!-- Table - Only in Drishti mode -->
    <div v-if="activeView === 'drishti' && activeTab === 'zone'" class="sb-card">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-[var(--border)]">
              <th rowspan="2" class="border-r border-[var(--border)] bg-[var(--bg2)] px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Zone/Region
              </th>
              <th rowspan="2" class="border-r border-[var(--border)] bg-[var(--bg2)] px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Branches
              </th>
              <th colspan="3" class="border-b border-[var(--border)] bg-[var(--bg1)] px-5 py-2 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Jul-2026<br/>
                <span class="text-[10px] font-normal">SR % | 14 Working Days Left</span>
              </th>
            </tr>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="border-r border-[var(--border)] px-5 py-2 text-right text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Target
              </th>
              <th class="border-r border-[var(--border)] px-5 py-2 text-right text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Ach
              </th>
              <th class="px-5 py-2 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Ach %
              </th>
            </tr>
          </thead>
          <tbody>
            <template v-for="zoneData in tableData" :key="zoneData.zone">
              <!-- Zone Row (Collapsed shows totals) -->
              <tr
                class="cursor-pointer border-b border-[var(--border)] bg-[var(--bg1)] font-semibold transition hover:bg-[var(--bg2)]"
                @click="toggleZone(zoneData.zone)"
              >
                <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text)]">
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
                      :class="isExpanded(zoneData.zone) ? 'rotate-90' : ''"
                    >
                      <polyline points="9 18 15 12 9 6"></polyline>
                    </svg>
                    {{ zoneData.zone }}
                  </div>
                </td>
                <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text)]">
                  {{ getZoneTotals(zoneData).branches }}
                </td>
                <td class="border-r border-[var(--border)] px-5 py-3 text-right font-mono text-sm text-[var(--text)]">
                  {{ formatNumber(getZoneTotals(zoneData).target) }}
                </td>
                <td class="border-r border-[var(--border)] px-5 py-3 text-right font-mono text-sm text-[var(--text)]">
                  {{ formatNumber(getZoneTotals(zoneData).ach) }}
                </td>
                <td class="px-5 py-3 text-center font-mono text-sm text-[var(--text)]">
                  <span
                    class="inline-block rounded px-2 py-0.5 text-xs font-medium"
                    :class="
                      getZoneTotals(zoneData).achPercent >= 90
                        ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                        : getZoneTotals(zoneData).achPercent >= 75
                        ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400'
                        : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'
                    "
                  >
                    {{ getZoneTotals(zoneData).achPercent }}%
                  </span>
                </td>
              </tr>

              <!-- Region Rows (Expanded) -->
              <template v-if="isExpanded(zoneData.zone)">
                <tr
                  v-for="region in zoneData.regions"
                  :key="`${zoneData.zone}-${region.region}`"
                  class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
                >
                  <td class="border-r border-[var(--border)] px-5 py-3 pl-12 text-sm text-[var(--text3)]">
                    {{ region.region }}
                  </td>
                  <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text)]">
                    {{ region.branches }}
                  </td>
                  <td class="border-r border-[var(--border)] px-5 py-3 text-right font-mono text-sm text-[var(--text)]">
                    {{ formatNumber(region.target) }}
                  </td>
                  <td class="border-r border-[var(--border)] px-5 py-3 text-right font-mono text-sm text-[var(--text)]">
                    {{ formatNumber(region.ach) }}
                  </td>
                  <td class="px-5 py-3 text-center font-mono text-sm text-[var(--text)]">
                    <span
                      class="inline-block rounded px-2 py-0.5 text-xs font-medium"
                      :class="
                        region.achPercent >= 90
                          ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                          : region.achPercent >= 75
                          ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400'
                          : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'
                      "
                    >
                      {{ region.achPercent }}%
                    </span>
                  </td>
                </tr>
              </template>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Category Wise Table - Only in Drishti mode -->
    <div v-if="activeView === 'drishti' && activeTab === 'category'" class="sb-card">
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
            <!-- Total Row -->
            <tr class="border-t-2 border-[var(--border)] bg-[var(--bg2)] font-semibold">
              <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text)]">
                Total
              </td>
              <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text3)]">
                —
              </td>
              <td class="border-r border-[var(--border)] px-5 py-3 text-center font-mono text-sm text-[var(--text)]">
                {{ getCategoryTotals().branchCount }}
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
  </div>
</template>
