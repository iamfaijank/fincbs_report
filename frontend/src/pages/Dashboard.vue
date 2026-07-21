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

// Product table data - hierarchical: Zone > Region > District/SOL
const productData = ref([
  {
    zone: 'Z-1',
    regions: [
      {
        region: 'R-1',
        sols: [
          { sol: 'DIS-1 / SOL-1001', casa: 15678900, dam: 2345678, dd: 890123, fd: 4567890, rd: 1234567, smbg: 567890, share: 8901234, achievement: 85.8 },
          { sol: 'DIS-1 / SOL-1002', casa: 14325000, dam: 2156789, dd: 789012, fd: 4321098, rd: 1123456, smbg: 456789, share: 8234567, achievement: 92.4 },
        ]
      },
      {
        region: 'R-2',
        sols: [
          { sol: 'DIS-2 / SOL-2001', casa: 12890000, dam: 1987654, dd: 678901, fd: 3987654, rd: 1012345, smbg: 345678, share: 7654321, achievement: 79.4 },
          { sol: 'DIS-2 / SOL-2002', casa: 11234000, dam: 1765432, dd: 567890, fd: 3543210, rd: 901234, smbg: 234567, share: 6543210, achievement: 84.2 },
        ]
      },
    ]
  },
  {
    zone: 'Z-2',
    regions: [
      {
        region: 'R-3',
        sols: [
          { sol: 'DIS-3 / SOL-3001', casa: 12890000, dam: 1654321, dd: 456789, fd: 3210987, rd: 890123, smbg: 123456, share: 5432109, achievement: 76.6 },
          { sol: 'DIS-3 / SOL-3002', casa: 16750000, dam: 2345678, dd: 890123, fd: 4567890, rd: 1345678, smbg: 678901, share: 9012345, achievement: 93.6 },
        ]
      },
    ]
  },
])

// Agent table data - hierarchical: Zone > Region
const agentData = ref([
  {
    zone: 'Z-1',
    regions: [
      { region: 'R-1', ssTarget: 500, ssAchievement: 425, ssShortfall: 75, ssActive: 38, ssInactive: 12, ddTarget: 300, ddAchievement: 270, ddShortfall: 30, ddActive: 28, ddInactive: 5 },
      { region: 'R-2', ssTarget: 450, ssAchievement: 405, ssShortfall: 45, ssActive: 35, ssInactive: 10, ddTarget: 280, ddAchievement: 252, ddShortfall: 28, ddActive: 25, ddInactive: 4 },
      { region: 'R-3', ssTarget: 380, ssAchievement: 304, ssShortfall: 76, ssActive: 30, ssInactive: 8, ddTarget: 220, ddAchievement: 187, ddShortfall: 33, ddActive: 20, ddInactive: 6 },
    ]
  },
  {
    zone: 'Z-2',
    regions: [
      { region: 'R-4', ssTarget: 520, ssAchievement: 494, ssShortfall: 26, ssActive: 42, ssInactive: 8, ddTarget: 310, ddAchievement: 294, ddShortfall: 16, ddActive: 30, ddInactive: 3 },
      { region: 'R-5', ssTarget: 400, ssAchievement: 340, ssShortfall: 60, ssActive: 32, ssInactive: 10, ddTarget: 250, ddAchievement: 212, ddShortfall: 38, ddActive: 22, ddInactive: 7 },
    ]
  },
])

// Branch table data
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

// Product table helpers
const expandedProductZones = ref(new Set())
const expandedProductRegions = ref(new Set())

function toggleProductZone(zone) {
  if (expandedProductZones.value.has(zone)) {
    expandedProductZones.value.delete(zone)
  } else {
    expandedProductZones.value.add(zone)
  }
}

function isProductZoneExpanded(zone) {
  return expandedProductZones.value.has(zone)
}

function toggleProductRegion(key) {
  if (expandedProductRegions.value.has(key)) {
    expandedProductRegions.value.delete(key)
  } else {
    expandedProductRegions.value.add(key)
  }
}

function isProductRegionExpanded(key) {
  return expandedProductRegions.value.has(key)
}

function getProductZoneTotals(zoneData) {
  const totals = { casa: 0, dam: 0, dd: 0, fd: 0, rd: 0, smbg: 0, share: 0, totalAch: 0, totalTarget: 0 }
  zoneData.regions.forEach(region => {
    region.sols.forEach(sol => {
      totals.casa += sol.casa
      totals.dam += sol.dam
      totals.dd += sol.dd
      totals.fd += sol.fd
      totals.rd += sol.rd
      totals.smbg += sol.smbg
      totals.share += sol.share
      totals.totalAch += sol.casa * sol.achievement / 100
      totals.totalTarget += sol.casa
    })
  })
  totals.achievement = totals.totalTarget > 0 ? ((totals.totalAch / totals.totalTarget) * 100).toFixed(1) : 0
  return totals
}

function getProductRegionTotals(regionData) {
  const totals = { casa: 0, dam: 0, dd: 0, fd: 0, rd: 0, smbg: 0, share: 0, totalAch: 0, totalTarget: 0 }
  regionData.sols.forEach(sol => {
    totals.casa += sol.casa
    totals.dam += sol.dam
    totals.dd += sol.dd
    totals.fd += sol.fd
    totals.rd += sol.rd
    totals.smbg += sol.smbg
    totals.share += sol.share
    totals.totalAch += sol.casa * sol.achievement / 100
    totals.totalTarget += sol.casa
  })
  totals.achievement = totals.totalTarget > 0 ? ((totals.totalAch / totals.totalTarget) * 100).toFixed(1) : 0
  return totals
}

// Agent table helpers
const expandedAgentZones = ref(new Set())
const expandedAgentRegions = ref(new Set())

function toggleAgentZone(zone) {
  if (expandedAgentZones.value.has(zone)) {
    expandedAgentZones.value.delete(zone)
  } else {
    expandedAgentZones.value.add(zone)
  }
}

function isAgentZoneExpanded(zone) {
  return expandedAgentZones.value.has(zone)
}

function toggleAgentRegion(key) {
  if (expandedAgentRegions.value.has(key)) {
    expandedAgentRegions.value.delete(key)
  } else {
    expandedAgentRegions.value.add(key)
  }
}

function isAgentRegionExpanded(key) {
  return expandedAgentRegions.value.has(key)
}

function getAgentZoneTotals(zoneData) {
  const t = { ssTarget: 0, ssAchievement: 0, ssShortfall: 0, ssActive: 0, ssInactive: 0, ddTarget: 0, ddAchievement: 0, ddShortfall: 0, ddActive: 0, ddInactive: 0 }
  zoneData.regions.forEach(r => {
    t.ssTarget += r.ssTarget; t.ssAchievement += r.ssAchievement; t.ssShortfall += r.ssShortfall; t.ssActive += r.ssActive; t.ssInactive += r.ssInactive
    t.ddTarget += r.ddTarget; t.ddAchievement += r.ddAchievement; t.ddShortfall += r.ddShortfall; t.ddActive += r.ddActive; t.ddInactive += r.ddInactive
  })
  t.achPercent = t.ssTarget > 0 ? ((t.ssAchievement / t.ssTarget) * 100).toFixed(1) : 0
  return t
}

function getAgentRegionTotals(regionData) {
  const t = { ssTarget: regionData.ssTarget, ssAchievement: regionData.ssAchievement, ssShortfall: regionData.ssShortfall, ssActive: regionData.ssActive, ssInactive: regionData.ssInactive, ddTarget: regionData.ddTarget, ddAchievement: regionData.ddAchievement, ddShortfall: regionData.ddShortfall, ddActive: regionData.ddActive, ddInactive: regionData.ddInactive }
  t.achPercent = t.ssTarget > 0 ? ((t.ssAchievement / t.ssTarget) * 100).toFixed(1) : 0
  return t
}
</script>

<template>
  <div>
    <!-- Summary Cards - Only in Drishti mode -->
    <div v-if="activeView === 'drishti'" class="mb-4 grid grid-cols-4 gap-3">
      <div class="sb-card">
        <div class="flex items-center justify-between w-full">
          <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
            Total Branches
          </div>
          <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">229</div>
        </div>
        <div class="text-[10px] text-[var(--text3)] flex items-center gap-1">
          <span class="rounded bg-green-50 px-1 py-0.5 text-[9px] font-medium text-green-600 dark:bg-green-900/30 dark:text-green-400">
            +3.2%
          </span>
          <span>vs last month</span>
        </div>
      </div>
      <div class="sb-card">
        <div class="flex items-center justify-between w-full">
          <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
            Target (MTD)
          </div>
          <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">
            <span class="text-xs text-[var(--text3)]">₹</span>163<span class="text-xs text-[var(--text3)]">Cr</span>
          </div>
        </div>
        <div class="text-[10px] text-[var(--text3)] flex items-center gap-1">
          <span class="rounded bg-amber-50 px-1 py-0.5 text-[9px] font-medium text-amber-600 dark:bg-amber-900/30 dark:text-amber-400">
            Monthly
          </span>
          <span>target set</span>
        </div>
      </div>
      <div class="sb-card">
        <div class="flex items-center justify-between w-full">
          <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
            Achievement
          </div>
          <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">
            <span class="text-xs text-[var(--text3)]">₹</span>91.4<span class="text-xs text-[var(--text3)]">Cr</span>
          </div>
        </div>
        <div class="text-[10px] text-[var(--text3)] flex items-center gap-1">
          <span class="rounded bg-red-50 px-1 py-0.5 text-[9px] font-medium text-red-600 dark:bg-red-900/30 dark:text-red-400">
            57.9%
          </span>
          <span>achieved</span>
        </div>
      </div>
      <div class="sb-card">
        <div class="flex items-center justify-between w-full">
          <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
            Active Zones
          </div>
          <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">6</div>
        </div>
        <div class="text-[10px] text-[var(--text3)] flex items-center gap-1">
          <span class="rounded bg-green-50 px-1 py-0.5 text-[9px] font-medium text-green-600 dark:bg-green-900/30 dark:text-green-400">
            All live
          </span>
          <span>operational</span>
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
    <div v-if="activeView === 'drishti' && activeTab === 'zone'" class="sb-card card-table">
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
    <div v-if="activeView === 'drishti' && activeTab === 'category'" class="sb-card card-table">
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

    <!-- Product Wise Table - Only in Drishti mode -->
    <div v-if="activeView === 'drishti' && activeTab === 'product'" class="sb-card card-table">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th rowspan="2" class="border-r border-[var(--border)] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Z/R/DIS/SOL
              </th>
              <th colspan="7" class="border-b border-r border-[var(--border)] px-4 py-2 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Product Values
              </th>
              <th rowspan="2" class="border-r border-[var(--border)] px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                SHARE
              </th>
              <th rowspan="2" class="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                ACHIEVEMENT
              </th>
            </tr>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">CASA</th>
              <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">DAM</th>
              <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">DD</th>
              <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">FD</th>
              <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">RD</th>
              <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">SMBG</th>
              <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Total</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="zoneData in productData" :key="zoneData.zone">
              <!-- Zone Row -->
              <tr
                class="cursor-pointer border-b border-[var(--border)] bg-[var(--bg1)] font-semibold transition hover:bg-[var(--bg2)]"
                @click="toggleProductZone(zoneData.zone)"
              >
                <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">
                  <div class="flex items-center gap-2">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="transition-transform" :class="isProductZoneExpanded(zoneData.zone) ? 'rotate-90' : ''">
                      <polyline points="9 18 15 12 9 6"></polyline>
                    </svg>
                    {{ zoneData.zone }}
                  </div>
                </td>
                <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductZoneTotals(zoneData).casa) }}</td>
                <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductZoneTotals(zoneData).dam) }}</td>
                <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductZoneTotals(zoneData).dd) }}</td>
                <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductZoneTotals(zoneData).fd) }}</td>
                <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductZoneTotals(zoneData).rd) }}</td>
                <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductZoneTotals(zoneData).smbg) }}</td>
                <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductZoneTotals(zoneData).casa + getProductZoneTotals(zoneData).dam + getProductZoneTotals(zoneData).dd + getProductZoneTotals(zoneData).fd + getProductZoneTotals(zoneData).rd + getProductZoneTotals(zoneData).smbg) }}</td>
                <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductZoneTotals(zoneData).share) }}</td>
                <td class="px-4 py-3 text-center font-mono text-sm">
                  <span class="inline-block rounded px-2 py-0.5 text-xs font-medium" :class="getProductZoneTotals(zoneData).achievement >= 90 ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400' : getProductZoneTotals(zoneData).achievement >= 75 ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400' : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'">
                    {{ getProductZoneTotals(zoneData).achievement }}%
                  </span>
                </td>
              </tr>

              <!-- Region Rows -->
              <template v-if="isProductZoneExpanded(zoneData.zone)">
                <template v-for="regionData in zoneData.regions" :key="`${zoneData.zone}-${regionData.region}`">
                  <tr
                    class="cursor-pointer border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
                    @click="toggleProductRegion(`${zoneData.zone}-${regionData.region}`)"
                  >
                    <td class="border-r border-[var(--border)] px-4 py-3 pl-12 text-sm text-[var(--text2)]">
                      <div class="flex items-center gap-2">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="transition-transform" :class="isProductRegionExpanded(`${zoneData.zone}-${regionData.region}`) ? 'rotate-90' : ''">
                          <polyline points="9 18 15 12 9 6"></polyline>
                        </svg>
                        {{ regionData.region }}
                      </div>
                    </td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductRegionTotals(regionData).casa) }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductRegionTotals(regionData).dam) }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductRegionTotals(regionData).dd) }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductRegionTotals(regionData).fd) }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductRegionTotals(regionData).rd) }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductRegionTotals(regionData).smbg) }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductRegionTotals(regionData).casa + getProductRegionTotals(regionData).dam + getProductRegionTotals(regionData).dd + getProductRegionTotals(regionData).fd + getProductRegionTotals(regionData).rd + getProductRegionTotals(regionData).smbg) }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductRegionTotals(regionData).share) }}</td>
                    <td class="px-4 py-3 text-center font-mono text-sm">
                      <span class="inline-block rounded px-2 py-0.5 text-xs font-medium" :class="getProductRegionTotals(regionData).achievement >= 90 ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400' : getProductRegionTotals(regionData).achievement >= 75 ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400' : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'">
                        {{ getProductRegionTotals(regionData).achievement }}%
                      </span>
                    </td>
                  </tr>

                  <!-- SOL Rows -->
                  <template v-if="isProductRegionExpanded(`${zoneData.zone}-${regionData.region}`)">
                    <tr
                      v-for="(sol, solIdx) in regionData.sols"
                      :key="solIdx"
                      class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
                    >
                      <td class="border-r border-[var(--border)] px-4 py-3 pl-20 text-sm text-[var(--text3)]">
                        {{ sol.sol }}
                      </td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(sol.casa) }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(sol.dam) }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(sol.dd) }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(sol.fd) }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(sol.rd) }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(sol.smbg) }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(sol.casa + sol.dam + sol.dd + sol.fd + sol.rd + sol.smbg) }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(sol.share) }}</td>
                      <td class="px-4 py-3 text-center font-mono text-sm">
                        <span class="inline-block rounded px-2 py-0.5 text-xs font-medium" :class="sol.achievement >= 90 ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400' : sol.achievement >= 75 ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400' : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'">
                          {{ sol.achievement }}%
                        </span>
                      </td>
                    </tr>
                  </template>
                </template>
              </template>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Agent Wise Table - Only in Drishti mode -->
    <div v-if="activeView === 'drishti' && activeTab === 'agent'" class="sb-card card-table">
      <div class="overflow-x-auto">
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
                DD
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
            <template v-for="zoneData in agentData" :key="zoneData.zone">
              <!-- Zone Row -->
              <tr
                class="cursor-pointer border-b border-[var(--border)] bg-[var(--bg1)] font-semibold transition hover:bg-[var(--bg2)]"
                @click="toggleAgentZone(zoneData.zone)"
              >
                <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">
                  <div class="flex items-center gap-2">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="transition-transform" :class="isAgentZoneExpanded(zoneData.zone) ? 'rotate-90' : ''">
                      <polyline points="9 18 15 12 9 6"></polyline>
                    </svg>
                    {{ zoneData.zone }}
                  </div>
                </td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getAgentZoneTotals(zoneData).ssTarget) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getAgentZoneTotals(zoneData).ssAchievement) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getAgentZoneTotals(zoneData).ssShortfall) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getAgentZoneTotals(zoneData).ssActive) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getAgentZoneTotals(zoneData).ssInactive) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getAgentZoneTotals(zoneData).ddTarget) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getAgentZoneTotals(zoneData).ddAchievement) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getAgentZoneTotals(zoneData).ddShortfall) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getAgentZoneTotals(zoneData).ddActive) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getAgentZoneTotals(zoneData).ddInactive) }}</td>
                <td class="px-4 py-3 text-center font-mono text-sm">
                  <span class="inline-block rounded px-2 py-0.5 text-xs font-medium" :class="getAgentZoneTotals(zoneData).achPercent >= 90 ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400' : getAgentZoneTotals(zoneData).achPercent >= 75 ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400' : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'">
                    {{ getAgentZoneTotals(zoneData).achPercent }}%
                  </span>
                </td>
              </tr>

              <!-- Region Rows -->
              <template v-if="isAgentZoneExpanded(zoneData.zone)">
                <tr
                  v-for="regionData in zoneData.regions"
                  :key="`${zoneData.zone}-${regionData.region}`"
                  class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
                >
                  <td class="border-r border-[var(--border)] px-4 py-3 pl-12 text-sm text-[var(--text2)]">
                    {{ regionData.region }}
                  </td>
                  <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ssTarget) }}</td>
                  <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ssAchievement) }}</td>
                  <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ssShortfall) }}</td>
                  <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ssActive) }}</td>
                  <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ssInactive) }}</td>
                  <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ddTarget) }}</td>
                  <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ddAchievement) }}</td>
                  <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ddShortfall) }}</td>
                  <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ddActive) }}</td>
                  <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ddInactive) }}</td>
                  <td class="px-4 py-3 text-center font-mono text-sm">
                    <span class="inline-block rounded px-2 py-0.5 text-xs font-medium" :class="getAgentRegionTotals(regionData).achPercent >= 90 ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400' : getAgentRegionTotals(regionData).achPercent >= 75 ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400' : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'">
                      {{ getAgentRegionTotals(regionData).achPercent }}%
                    </span>
                  </td>
                </tr>
              </template>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Branch Wise Table - Only in Drishti mode -->
    <div v-if="activeView === 'drishti' && activeTab === 'branch'" class="sb-card card-table">
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
                <span class="inline-block rounded px-2 py-0.5 text-xs font-medium"
                  :class="
                    row.achPercent >= 90 ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                    : row.achPercent >= 75 ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400'
                    : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'
                  "
                >
                  {{ row.achPercent }}%
                </span>
              </td>
            </tr>
            <!-- Total Row -->
            <tr class="border-t-2 border-[var(--border)] bg-[var(--bg2)] font-semibold">
              <td class="border-r border-[var(--border)] px-4 py-3 text-center text-sm text-[var(--text3)]"></td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">Total</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text3)]">—</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-center text-sm text-[var(--text3)]">—</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(branchData.reduce((a, r) => a + r.target, 0)) }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(branchData.reduce((a, r) => a + r.ach, 0)) }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ (branchData.reduce((a, r) => a + r.ach, 0) / branchData.reduce((a, r) => a + r.target, 0) * 100).toFixed(1) }}%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
