<script setup>
import { ref, computed } from 'vue'
import { useNumberFormat } from '@/composables/useNumberFormat.js'
import { useFilters } from '@/composables/useFilters.js'
import { useExpandableSet } from '@/composables/useExpandableSet.js'
import AchievementBadge from './AchievementBadge.vue'

const { formatNumber } = useNumberFormat()
const { isZoneSelected, isRegionSelected, zoneFilter, regionFilter } = useFilters()
const { toggle: toggleZone, isExpanded: isZoneExpanded } = useExpandableSet()
const { toggle: toggleRegion, isExpanded: isRegionExpanded } = useExpandableSet()

const isFilterApplied = computed(() => zoneFilter.value.length > 0 || regionFilter.value.length > 0)

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

const filteredProductData = computed(() => {
  if (!isFilterApplied.value) return productData.value
  return productData.value
    .filter(z => isZoneSelected(z.zone))
    .map(z => ({ ...z, regions: z.regions.filter(r => isRegionSelected(r.region)) }))
    .filter(z => z.regions.length > 0)
})

function sumSolField(sols, field) { return sols.reduce((a, b) => a + b[field], 0) }

function getRegionTotals(region) {
  const s = region.sols
  return {
    casa: sumSolField(s, 'casa'), dam: sumSolField(s, 'dam'), dd: sumSolField(s, 'dd'),
    fd: sumSolField(s, 'fd'), rd: sumSolField(s, 'rd'), smbg: sumSolField(s, 'smbg'),
    share: sumSolField(s, 'share'), achievement: sumSolField(s, 'achievement'),
  }
}

function getZoneTotals(zone) {
  const t = { casa: 0, dam: 0, dd: 0, fd: 0, rd: 0, smbg: 0, share: 0, achievement: 0 }
  zone.regions.forEach(r => { const rt = getZoneRegionTotals(r); Object.keys(t).forEach(k => t[k] += rt[k]) })
  return t
}

function getZoneRegionTotals(region) {
  const t = { casa: 0, dam: 0, dd: 0, fd: 0, rd: 0, smbg: 0, share: 0, achievement: 0 }
  region.sols.forEach(s => { Object.keys(t).forEach(k => t[k] += s[k]) })
  return t
}
</script>

<template>
  <div class="sb-card card-table">
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
          <template v-for="zoneData in filteredProductData" :key="zoneData.zone">
            <tr
              class="cursor-pointer border-b border-[var(--border)] bg-[var(--bg1)] font-semibold transition hover:bg-[var(--bg2)]"
              @click="toggleZone(zoneData.zone)"
            >
              <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">
                <div class="flex items-center gap-2">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="transition-transform" :class="isZoneExpanded(zoneData.zone) ? 'rotate-90' : ''">
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                  {{ zoneData.zone }}
                </div>
              </td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).casa) }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).dam) }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).dd) }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).fd) }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).rd) }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).smbg) }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).casa + getZoneTotals(zoneData).dam + getZoneTotals(zoneData).dd + getZoneTotals(zoneData).fd + getZoneTotals(zoneData).rd + getZoneTotals(zoneData).smbg) }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneTotals(zoneData).share) }}</td>
              <td class="px-4 py-3 text-center font-mono text-sm">
                <AchievementBadge :value="getZoneTotals(zoneData).achievement" />
              </td>
            </tr>
            <template v-if="isZoneExpanded(zoneData.zone)">
              <template v-for="regionData in zoneData.regions" :key="`${zoneData.zone}-${regionData.region}`">
                <tr
                  class="cursor-pointer border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
                  @click="toggleRegion(`${zoneData.zone}-${regionData.region}`)"
                >
                  <td class="border-r border-[var(--border)] px-4 py-3 pl-12 text-sm text-[var(--text2)]">
                    <div class="flex items-center gap-2">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="transition-transform" :class="isRegionExpanded(`${zoneData.zone}-${regionData.region}`) ? 'rotate-90' : ''">
                        <polyline points="9 18 15 12 9 6"></polyline>
                      </svg>
                      {{ regionData.region }}
                    </div>
                  </td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneRegionTotals(regionData).casa) }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneRegionTotals(regionData).dam) }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneRegionTotals(regionData).dd) }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneRegionTotals(regionData).fd) }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneRegionTotals(regionData).rd) }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneRegionTotals(regionData).smbg) }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneRegionTotals(regionData).casa + getZoneRegionTotals(regionData).dam + getZoneRegionTotals(regionData).dd + getZoneRegionTotals(regionData).fd + getZoneRegionTotals(regionData).rd + getZoneRegionTotals(regionData).smbg) }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getZoneRegionTotals(regionData).share) }}</td>
                  <td class="px-4 py-3 text-center font-mono text-sm">
                    <AchievementBadge :value="getZoneRegionTotals(regionData).achievement" />
                  </td>
                </tr>
                <template v-if="isRegionExpanded(`${zoneData.zone}-${regionData.region}`)">
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
                      <AchievementBadge :value="sol.achievement" />
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
</template>
