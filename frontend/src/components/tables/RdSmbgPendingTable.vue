<script setup>
import { computed } from 'vue'
import { useFilters } from '@/composables/useFilters.js'
import { useExpandableSet } from '@/composables/useExpandableSet.js'
import { useNameFormat } from '@/composables/useNameFormat.js'
import SummaryCardGroup from '@/components/cards/SummaryCardGroup.vue'

const { isZoneSelected, isRegionSelected, zoneFilter, regionFilter } = useFilters()
const { toggle: toggleZone, isExpanded: isZoneExpanded } = useExpandableSet()
const { toggle: toggleRegion, isExpanded: isRegionExpanded } = useExpandableSet()
const { formatZone, formatRegion } = useNameFormat()

const isFilterApplied = computed(() => zoneFilter.value.length > 0 || regionFilter.value.length > 0)

const summaryCards = [
  { label: 'Total Accounts', value: '4,27,943' },
  { label: 'Total Collection', value: '₹233.95 Cr' },
  { label: 'Pending Accounts', value: '2,43,415' },
  { label: 'Pending Instalments', value: '13,75,432' },
  { label: 'Pending Amount', value: '₹401.21 Cr' },
]

const rawData = [
  {
    zone: 'Z-1',
    regions: [
      {
        region: 'R-1',
        branches: [
          { branch: 'ABD-1001', totalAccounts: 52340, totalCollection: 28.45, pendingAccounts: 28920, pendingInstalments: 165230, pendingAmount: 48.76 },
          { branch: 'ABD-1002', totalAccounts: 48120, totalCollection: 25.67, pendingAccounts: 24560, pendingInstalments: 142890, pendingAmount: 42.34 },
        ]
      },
      {
        region: 'R-2',
        branches: [
          { branch: 'JHD-1003', totalAccounts: 45670, totalCollection: 22.34, pendingAccounts: 22180, pendingInstalments: 128450, pendingAmount: 38.92 },
          { branch: 'JHD-1004', totalAccounts: 58900, totalCollection: 32.12, pendingAccounts: 31200, pendingInstalments: 178900, pendingAmount: 52.45 },
        ]
      },
    ]
  },
  {
    zone: 'Z-2',
    regions: [
      {
        region: 'R-3',
        branches: [
          { branch: 'PUN-1005', totalAccounts: 42340, totalCollection: 20.78, pendingAccounts: 19870, pendingInstalments: 112340, pendingAmount: 35.67 },
          { branch: 'PUN-1006', totalAccounts: 50230, totalCollection: 26.89, pendingAccounts: 26450, pendingInstalments: 152670, pendingAmount: 45.23 },
        ]
      },
      {
        region: 'R-4',
        branches: [
          { branch: 'MUM-1007', totalAccounts: 55000, totalCollection: 30.00, pendingAccounts: 30000, pendingInstalments: 170000, pendingAmount: 50.00 },
          { branch: 'MUM-1008', totalAccounts: 47500, totalCollection: 26.50, pendingAccounts: 25000, pendingInstalments: 145000, pendingAmount: 40.00 },
        ]
      },
    ]
  },
  {
    zone: 'Z-3',
    regions: [
      {
        region: 'R-5',
        branches: [
          { branch: 'DEL-1009', totalAccounts: 60000, totalCollection: 35.00, pendingAccounts: 32000, pendingInstalments: 185000, pendingAmount: 55.00 },
          { branch: 'DEL-1010', totalAccounts: 43000, totalCollection: 23.00, pendingAccounts: 21000, pendingInstalments: 120000, pendingAmount: 36.00 },
        ]
      },
      {
        region: 'R-6',
        branches: [
          { branch: 'CHN-1011', totalAccounts: 51000, totalCollection: 28.00, pendingAccounts: 27000, pendingInstalments: 155000, pendingAmount: 46.00 },
          { branch: 'CHN-1012', totalAccounts: 49000, totalCollection: 27.00, pendingAccounts: 26000, pendingInstalments: 148000, pendingAmount: 43.00 },
        ]
      },
    ]
  },
]

const filteredData = computed(() => {
  if (!isFilterApplied.value) return rawData
  return rawData
    .filter(z => isZoneSelected(z.zone))
    .map(z => ({ ...z, regions: z.regions.filter(r => isRegionSelected(r.region)) }))
    .filter(z => z.regions.length > 0)
})

const numCols = ['totalAccounts', 'totalCollection', 'pendingAccounts', 'pendingInstalments', 'pendingAmount']

function sumBranches(branches, field) {
  return branches.reduce((a, b) => a + b[field], 0)
}

function getRegionTotals(region) {
  const t = {}
  numCols.forEach(c => t[c] = sumBranches(region.branches, c))
  return t
}

function getZoneTotals(zone) {
  const t = {}
  numCols.forEach(c => t[c] = 0)
  zone.regions.forEach(r => {
    const rt = getRegionTotals(r)
    numCols.forEach(k => t[k] += rt[k])
  })
  return t
}

function getGrandTotals() {
  const t = {}
  numCols.forEach(c => t[c] = 0)
  filteredData.value.forEach(z => {
    const zt = getZoneTotals(z)
    numCols.forEach(k => t[k] += zt[k])
  })
  return t
}

function formatNum(val, field) {
  if (field === 'totalCollection' || field === 'pendingAmount') return '₹' + val.toFixed(2) + ' Cr'
  return val.toLocaleString('en-IN')
}
</script>

<template>
  <div>
    <SummaryCardGroup :cards="summaryCards" :cols="5" />

    <div class="sb-card card-table">
      <div>
        <table class="w-full">
          <thead>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="border-r border-[var(--border)] px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">SR</th>
              <th class="border-r border-[var(--border)] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">ZONE / REGION / BRANCH</th>
              <th class="border-r border-[var(--border)] px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">BRANCHES</th>
              <th class="border-r border-[var(--border)] px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">TOTAL ACCOUNTS</th>
              <th class="border-r border-[var(--border)] px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">TOTAL COLLECTION</th>
              <th class="border-r border-[var(--border)] px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">PENDING ACCOUNTS</th>
              <th class="border-r border-[var(--border)] px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">PENDING INSTALMENTS</th>
              <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">PENDING AMOUNT</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(zone, zi) in filteredData" :key="zone.zone">
              <tr class="cursor-pointer border-b border-[var(--border)] bg-[var(--bg2)] transition hover:bg-[var(--bg)]"
                  @click="toggleZone(zone.zone)">
                <td class="border-r border-[var(--border)] px-4 py-3 text-center font-mono text-sm font-semibold text-[var(--text3)]">{{ zi + 1 }}</td>
                <td class="border-r border-[var(--border)] px-4 py-3 text-sm font-semibold text-[var(--text)]">
                  <span class="mr-2 text-[var(--text3)]">{{ isZoneExpanded(zone.zone) ? '▼' : '▶' }}</span>
                  {{ formatZone(zone.zone) }}
                </td>
                <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ zone.regions.reduce((a, r) => a + r.branches.length, 0) }}</td>
                <td v-for="col in numCols" :key="col" class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ formatNum(getZoneTotals(zone)[col], col) }}</td>
              </tr>

              <template v-if="isZoneExpanded(zone.zone)">
                <template v-for="(region, ri) in zone.regions" :key="region.region">
                  <tr class="cursor-pointer border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
                      @click="toggleRegion(zone.zone + '-' + region.region)">
                    <td class="border-r border-[var(--border)] px-4 py-3 text-center font-mono text-sm text-[var(--text3)]">{{ zi + 1 }}.{{ ri + 1 }}</td>
                    <td class="border-r border-[var(--border)] pl-10 pr-4 py-3 text-sm font-medium text-[var(--text)]">
                      <span class="mr-2 text-[var(--text3)]">{{ isRegionExpanded(zone.zone + '-' + region.region) ? '▼' : '▶' }}</span>
                      {{ formatRegion(region.region) }}
                    </td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ region.branches.length }}</td>
                    <td v-for="col in numCols" :key="col" class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNum(getRegionTotals(region)[col], col) }}</td>
                  </tr>

                  <template v-if="isRegionExpanded(zone.zone + '-' + region.region)">
                    <tr v-for="(branch, bi) in region.branches" :key="branch.branch"
                        class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]">
                      <td class="border-r border-[var(--border)] px-4 py-3 text-center font-mono text-xs text-[var(--text3)]">{{ zi + 1 }}.{{ ri + 1 }}.{{ bi + 1 }}</td>
                      <td class="border-r border-[var(--border)] pl-16 pr-4 py-3 text-sm text-[var(--text)]">{{ branch.branch }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">1</td>
                      <td v-for="col in numCols" :key="col" class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNum(branch[col], col) }}</td>
                    </tr>
                  </template>
                </template>
              </template>
            </template>

            <tr class="border-t-2 border-[var(--border)] bg-[var(--bg2)] font-semibold">
              <td class="border-r border-[var(--border)] px-4 py-3 text-center text-sm text-[var(--text3)]"></td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">Total</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ filteredData.reduce((a, z) => a + z.regions.reduce((b, r) => b + r.branches.length, 0), 0) }}</td>
              <td v-for="col in numCols" :key="col" class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNum(getGrandTotals()[col], col) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
