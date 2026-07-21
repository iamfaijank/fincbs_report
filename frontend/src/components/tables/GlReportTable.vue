<script setup>
import { ref, computed } from 'vue'
import { useFilters } from '@/composables/useFilters.js'
import { useExpandableSet } from '@/composables/useExpandableSet.js'

const { isZoneSelected, isRegionSelected, allZonesSelected, allRegionsSelected } = useFilters()
const { toggle: toggleZone, isExpanded: isZoneExpanded } = useExpandableSet()
const { toggle: toggleRegion, isExpanded: isRegionExpanded } = useExpandableSet()
const { toggle: toggleDistrict, isExpanded: isDistrictExpanded } = useExpandableSet()

const isFilterApplied = computed(() => !allZonesSelected.value || !allRegionsSelected.value)

const glReportData = ref([
  {
    zone: 'Z-1',
    regions: [
      {
        region: 'R-1',
        districts: [
          {
            district: 'DIS-1',
            sols: [
              { sol: 'SOL001', dam: 125, dd: 45, fd: 32, rd: 18, jllRd: 5, smbg: 22, skbg: 8, taskSilver: 15, taskWealth: 6, savSil: 12, cuGold: 9, cuWealth: 4, share: 7, achievement: 308 },
              { sol: 'SOL002', dam: 98, dd: 38, fd: 28, rd: 15, jllRd: 4, smbg: 18, skbg: 6, taskSilver: 12, taskWealth: 5, savSil: 10, cuGold: 7, cuWealth: 3, share: 6, achievement: 250 },
            ]
          }
        ]
      },
      {
        region: 'R-2',
        districts: [
          {
            district: 'DIS-2',
            sols: [
              { sol: 'SOL003', dam: 112, dd: 42, fd: 30, rd: 16, jllRd: 5, smbg: 20, skbg: 7, taskSilver: 14, taskWealth: 5, savSil: 11, cuGold: 8, cuWealth: 4, share: 7, achievement: 281 },
              { sol: 'SOL004', dam: 88, dd: 35, fd: 25, rd: 14, jllRd: 3, smbg: 16, skbg: 5, taskSilver: 10, taskWealth: 4, savSil: 8, cuGold: 6, cuWealth: 3, share: 5, achievement: 222 },
            ]
          }
        ]
      },
    ]
  },
  {
    zone: 'Z-2',
    regions: [
      {
        region: 'R-3',
        districts: [
          {
            district: 'DIS-3',
            sols: [
              { sol: 'SOL005', dam: 140, dd: 52, fd: 38, rd: 22, jllRd: 6, smbg: 28, skbg: 10, taskSilver: 18, taskWealth: 7, savSil: 15, cuGold: 11, cuWealth: 5, share: 8, achievement: 360 },
              { sol: 'SOL006', dam: 105, dd: 40, fd: 30, rd: 17, jllRd: 4, smbg: 21, skbg: 7, taskSilver: 13, taskWealth: 5, savSil: 11, cuGold: 8, cuWealth: 3, share: 6, achievement: 270 },
            ]
          }
        ]
      },
      {
        region: 'R-4',
        districts: [
          {
            district: 'DIS-4',
            sols: [
              { sol: 'SOL007', dam: 132, dd: 48, fd: 35, rd: 20, jllRd: 6, smbg: 25, skbg: 9, taskSilver: 16, taskWealth: 6, savSil: 14, cuGold: 10, cuWealth: 4, share: 8, achievement: 333 },
              { sol: 'SOL008', dam: 95, dd: 36, fd: 26, rd: 14, jllRd: 4, smbg: 17, skbg: 6, taskSilver: 11, taskWealth: 4, savSil: 9, cuGold: 7, cuWealth: 3, share: 5, achievement: 237 },
            ]
          }
        ]
      },
    ]
  },
])

const filteredData = computed(() => {
  if (!isFilterApplied.value) return glReportData.value
  return glReportData.value
    .filter(z => isZoneSelected(z.zone))
    .map(z => ({ ...z, regions: z.regions.filter(r => isRegionSelected(r.region)) }))
    .filter(z => z.regions.length > 0)
})

const cols = ['dam','dd','fd','rd','jllRd','smbg','skbg','taskSilver','taskWealth','savSil','cuGold','cuWealth','share','achievement']

function sumField(items, field) { return items.reduce((a, b) => a + b[field], 0) }

function getSolTotals(sol) {
  const t = {}
  cols.forEach(c => t[c] = sol[c])
  return t
}

function getDistrictTotals(district) {
  const t = {}
  cols.forEach(c => t[c] = sumField(district.sols, c))
  return t
}

function getRegionTotals(region) {
  const t = {}
  cols.forEach(c => t[c] = 0)
  region.districts.forEach(d => { const dt = getDistrictTotals(d); cols.forEach(k => t[k] += dt[k]) })
  return t
}

function getZoneTotals(zone) {
  const t = {}
  cols.forEach(c => t[c] = 0)
  zone.regions.forEach(r => { const rt = getRegionTotals(r); cols.forEach(k => t[k] += rt[k]) })
  return t
}
</script>

<template>
  <div class="sb-card card-table overflow-x-auto">
    <table class="w-full border-collapse text-sm">
      <thead>
        <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
          <th class="border-r border-[var(--border)] px-4 py-2.5 text-center text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)] w-12">SR</th>
          <th class="border-r border-[var(--border)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Z / R / DIS / SOL</th>
          <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">DAM</th>
          <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">DD</th>
          <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">FD</th>
          <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">RD</th>
          <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">JLL RD</th>
          <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">SMBG</th>
          <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">SKBG</th>
          <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">TASK SILVER</th>
          <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">TASK WEALTH</th>
          <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">SAV SIL</th>
          <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">CU GOLD</th>
          <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">CU WEALTH</th>
          <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">SHARE</th>
          <th class="px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">ACHIEVEMENT</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(zone, zi) in filteredData" :key="zone.zone">
          <tr class="cursor-pointer border-b border-[var(--border)] bg-[var(--bg2)] transition hover:bg-[var(--bg)]"
              @click="toggleZone(zone.zone)">
            <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm font-semibold text-[var(--text3)]">{{ zi + 1 }}</td>
            <td class="border-r border-[var(--border)] px-4 py-2.5 text-sm font-semibold text-[var(--text)]">
              <span class="mr-2 text-[var(--text3)]">{{ isZoneExpanded(zone.zone) ? '▼' : '▶' }}</span>
              {{ zone.zone }}
            </td>
            <td v-for="col in cols" :key="col" class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getZoneTotals(zone)[col] }}</td>
          </tr>
          <template v-if="isZoneExpanded(zone.zone)">
            <template v-for="(region, ri) in zone.regions" :key="region.region">
              <tr class="cursor-pointer border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
                  @click="toggleRegion(zone.zone + '-' + region.region)">
                <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm text-[var(--text3)]">{{ zi + 1 }}.{{ ri + 1 }}</td>
                <td class="border-r border-[var(--border)] px-4 py-2.5 pl-8 text-sm font-medium text-[var(--text)]">
                  <span class="mr-2 text-[var(--text3)]">{{ isRegionExpanded(zone.zone + '-' + region.region) ? '▼' : '▶' }}</span>
                  {{ region.region }}
                </td>
                <td v-for="col in cols" :key="col" class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getRegionTotals(region)[col] }}</td>
              </tr>
              <template v-if="isRegionExpanded(zone.zone + '-' + region.region)">
                <template v-for="(district, di) in region.districts" :key="district.district">
                  <tr class="cursor-pointer border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
                      @click="toggleDistrict(zone.zone + '-' + region.region + '-' + district.district)">
                    <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm text-[var(--text3)]">{{ zi + 1 }}.{{ ri + 1 }}.{{ di + 1 }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-2.5 pl-16 text-sm font-medium text-[var(--text)]">
                      <span class="mr-2 text-[var(--text3)]">{{ isDistrictExpanded(zone.zone + '-' + region.region + '-' + district.district) ? '▼' : '▶' }}</span>
                      {{ district.district }}
                    </td>
                    <td v-for="col in cols" :key="col" class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getDistrictTotals(district)[col] }}</td>
                  </tr>
                  <template v-if="isDistrictExpanded(zone.zone + '-' + region.region + '-' + district.district)">
                    <tr v-for="(sol, si) in district.sols" :key="sol.sol"
                        class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]">
                      <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-xs text-[var(--text3)]">{{ zi + 1 }}.{{ ri + 1 }}.{{ di + 1 }}.{{ si + 1 }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-2.5 pl-24 text-sm text-[var(--text)]">{{ sol.sol }}</td>
                      <td v-for="col in cols" :key="col" class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ sol[col] }}</td>
                    </tr>
                  </template>
                </template>
              </template>
            </template>
          </template>
        </template>
      </tbody>
    </table>
  </div>
</template>
