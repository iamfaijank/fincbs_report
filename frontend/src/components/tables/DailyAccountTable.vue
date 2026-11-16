<script setup>
import { ref, computed } from 'vue'
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
  { label: 'SA ACCOUNTS', value: '2,942' },
  { label: 'CA ACCOUNTS', value: '5' },
  { label: 'TASC ACCOUNTS', value: '10,443' },
  { label: 'RD ACCOUNTS', value: '6,442' },
  { label: 'SMBG ACCOUNTS', value: '5,389' },
  { label: 'DD ACCOUNTS', value: '3,122' },
  { label: 'FD ACCOUNTS', value: '8' },
  { label: 'TOTAL OPENED', value: '28,351' },
]

const dailyAccountData = ref([
  {
    zone: 'Z-1',
    regions: [
      {
        region: 'R-1',
        branches: [
          { branch: 'ABD-1001', ca: 120, sa: 850, tasc: 35, rd: 420, smbg: 180, dd: 95, fd: 65, totalOpened: 1765 },
          { branch: 'ABD-1002', ca: 95, sa: 720, tasc: 28, rd: 380, smbg: 150, dd: 82, fd: 55, totalOpened: 1510 },
        ]
      },
      {
        region: 'R-2',
        branches: [
          { branch: 'JHD-1001', ca: 110, sa: 780, tasc: 32, rd: 395, smbg: 165, dd: 88, fd: 60, totalOpened: 1630 },
          { branch: 'JHD-1002', ca: 88, sa: 690, tasc: 25, rd: 350, smbg: 140, dd: 75, fd: 48, totalOpened: 1416 },
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
          { branch: 'PUN-1001', ca: 135, sa: 920, tasc: 40, rd: 450, smbg: 195, dd: 102, fd: 72, totalOpened: 1914 },
          { branch: 'PUN-1002', ca: 105, sa: 810, tasc: 30, rd: 410, smbg: 170, dd: 90, fd: 58, totalOpened: 1673 },
        ]
      },
      {
        region: 'R-4',
        branches: [
          { branch: 'MUM-1001', ca: 150, sa: 980, tasc: 45, rd: 480, smbg: 210, dd: 110, fd: 78, totalOpened: 2053 },
          { branch: 'MUM-1002', ca: 125, sa: 890, tasc: 38, rd: 435, smbg: 185, dd: 98, fd: 68, totalOpened: 1839 },
        ]
      },
    ]
  },
])

const filteredData = computed(() => {
  if (!isFilterApplied.value) return dailyAccountData.value
  return dailyAccountData.value
    .filter(z => isZoneSelected(z.zone))
    .map(z => ({ ...z, regions: z.regions.filter(r => isRegionSelected(r.region)) }))
    .filter(z => z.regions.length > 0)
})

function sumBranches(branches, field) { return branches.reduce((a, b) => a + b[field], 0) }

function getRegionTotals(regionData) {
  const b = regionData.branches
  const ca = sumBranches(b, 'ca'), sa = sumBranches(b, 'sa'), tasc = sumBranches(b, 'tasc')
  const rd = sumBranches(b, 'rd'), smbg = sumBranches(b, 'smbg'), dd = sumBranches(b, 'dd'), fd = sumBranches(b, 'fd')
  return { ca, sa, tasc, rd, smbg, dd, fd, branches: b.length, caSaTasc: ca + sa + tasc, rdSmbgDdFd: rd + smbg + dd + fd, totalOpened: sumBranches(b, 'totalOpened') }
}

function getZoneTotals(zoneData) {
  const t = { ca: 0, sa: 0, tasc: 0, rd: 0, smbg: 0, dd: 0, fd: 0, branches: 0, totalOpened: 0 }
  zoneData.regions.forEach(r => {
    const rt = getRegionTotals(r)
    t.ca += rt.ca; t.sa += rt.sa; t.tasc += rt.tasc; t.rd += rt.rd; t.smbg += rt.smbg; t.dd += rt.dd; t.fd += rt.fd
    t.branches += rt.branches; t.totalOpened += rt.totalOpened
  })
  t.caSaTasc = t.ca + t.sa + t.tasc
  t.rdSmbgDdFd = t.rd + t.smbg + t.dd + t.fd
  return t
}
</script>

<template>
  <div>
    <SummaryCardGroup :cards="summaryCards" :cols="4" />

    <div class="sb-card card-table">
      <table class="w-full border-collapse text-sm">
        <thead>
          <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
            <th class="border-r border-[var(--border)] px-4 py-2.5 text-center text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)] w-12">SR</th>
            <th class="border-r border-[var(--border)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">ZONE / REGION / BRANCH</th>
            <th class="border-r border-[var(--border)] px-4 py-2.5 text-center text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">BRANCHES</th>
            <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">CA</th>
            <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">SA</th>
            <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">TASC</th>
            <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">RD</th>
            <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">SMBG</th>
            <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">DD</th>
            <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">FD</th>
            <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">CA+SA+TASC</th>
            <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">RD+SMBG+DD+FD</th>
            <th class="px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">TOTAL</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="(zone, zi) in filteredData" :key="zone.zone">
            <tr class="cursor-pointer border-b border-[var(--border)] bg-[var(--bg2)] transition hover:bg-[var(--bg)]"
                @click="toggleZone(zone.zone)">
              <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm font-semibold text-[var(--text3)]">{{ zi + 1 }}</td>
              <td class="border-r border-[var(--border)] px-4 py-2.5 text-sm font-semibold text-[var(--text)]">
                <span class="mr-2 text-[var(--text3)]">{{ isZoneExpanded(zone.zone) ? '▼' : '▶' }}</span>
                {{ formatZone(zone.zone) }}
              </td>
              <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm font-semibold text-[var(--text)]">{{ getZoneTotals(zone).branches }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getZoneTotals(zone).ca.toLocaleString() }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getZoneTotals(zone).sa.toLocaleString() }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getZoneTotals(zone).tasc.toLocaleString() }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getZoneTotals(zone).rd.toLocaleString() }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getZoneTotals(zone).smbg.toLocaleString() }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getZoneTotals(zone).dd.toLocaleString() }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getZoneTotals(zone).fd.toLocaleString() }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getZoneTotals(zone).caSaTasc.toLocaleString() }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getZoneTotals(zone).rdSmbgDdFd.toLocaleString() }}</td>
              <td class="px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getZoneTotals(zone).totalOpened.toLocaleString() }}</td>
            </tr>
            <template v-if="isZoneExpanded(zone.zone)">
              <template v-for="(region, ri) in zone.regions" :key="region.region">
                <tr class="cursor-pointer border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
                    @click="toggleRegion(zone.zone + '-' + region.region)">
                  <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm text-[var(--text3)]">{{ zi + 1 }}.{{ ri + 1 }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-2.5 pl-8 text-sm font-medium text-[var(--text)]">
                    <span class="mr-2 text-[var(--text3)]">{{ isRegionExpanded(zone.zone + '-' + region.region) ? '▼' : '▶' }}</span>
                    {{ formatRegion(region.region) }}
                  </td>
                  <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm text-[var(--text)]">{{ getRegionTotals(region).branches }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getRegionTotals(region).ca.toLocaleString() }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getRegionTotals(region).sa.toLocaleString() }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getRegionTotals(region).tasc.toLocaleString() }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getRegionTotals(region).rd.toLocaleString() }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getRegionTotals(region).smbg.toLocaleString() }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getRegionTotals(region).dd.toLocaleString() }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getRegionTotals(region).fd.toLocaleString() }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getRegionTotals(region).caSaTasc.toLocaleString() }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getRegionTotals(region).rdSmbgDdFd.toLocaleString() }}</td>
                  <td class="px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getRegionTotals(region).totalOpened.toLocaleString() }}</td>
                </tr>
                <template v-if="isRegionExpanded(zone.zone + '-' + region.region)">
                  <tr v-for="(branch, bi) in region.branches" :key="branch.branch"
                      class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]">
                    <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-xs text-[var(--text3)]">{{ zi + 1 }}.{{ ri + 1 }}.{{ bi + 1 }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-2.5 pl-16 text-sm text-[var(--text)]">{{ branch.branch }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm text-[var(--text)]">1</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.ca.toLocaleString() }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.sa.toLocaleString() }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.tasc.toLocaleString() }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.rd.toLocaleString() }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.smbg.toLocaleString() }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.dd.toLocaleString() }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.fd.toLocaleString() }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ (branch.ca + branch.sa + branch.tasc).toLocaleString() }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ (branch.rd + branch.smbg + branch.dd + branch.fd).toLocaleString() }}</td>
                    <td class="px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.totalOpened.toLocaleString() }}</td>
                  </tr>
                </template>
              </template>
            </template>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>
