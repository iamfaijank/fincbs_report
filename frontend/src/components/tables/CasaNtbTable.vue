<script setup>
import { ref, computed } from 'vue'
import { useFilters } from '@/composables/useFilters.js'
import { useExpandableSet } from '@/composables/useExpandableSet.js'

const { isZoneSelected, isRegionSelected, zoneFilter, regionFilter } = useFilters()
const { toggle: toggleZone, isExpanded: isZoneExpanded } = useExpandableSet()
const { toggle: toggleRegion, isExpanded: isRegionExpanded } = useExpandableSet()

const isFilterApplied = computed(() => zoneFilter.value.length > 0 || regionFilter.value.length > 0)

const casaNtbData = ref([
  {
    zone: 'Z-1',
    regions: [
      {
        region: 'R-1',
        branches: [
          { branch: 'ABD-1001', ntb: 45, evr: 32, total: 77 },
          { branch: 'ABD-1002', ntb: 38, evr: 28, total: 66 },
        ]
      },
      {
        region: 'R-2',
        branches: [
          { branch: 'JHD-1001', ntb: 42, evr: 35, total: 77 },
          { branch: 'JHD-1002', ntb: 36, evr: 24, total: 60 },
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
          { branch: 'PUN-1001', ntb: 52, evr: 38, total: 90 },
          { branch: 'PUN-1002', ntb: 41, evr: 30, total: 71 },
        ]
      },
      {
        region: 'R-4',
        branches: [
          { branch: 'MUM-1001', ntb: 58, evr: 42, total: 100 },
          { branch: 'MUM-1002', ntb: 48, evr: 36, total: 84 },
        ]
      },
    ]
  },
])

const filteredData = computed(() => {
  if (!isFilterApplied.value) return casaNtbData.value
  return casaNtbData.value
    .filter(z => isZoneSelected(z.zone))
    .map(z => ({ ...z, regions: z.regions.filter(r => isRegionSelected(r.region)) }))
    .filter(z => z.regions.length > 0)
})

function getRegionTotals(regionData) {
  const b = regionData.branches
  const ntb = b.reduce((a, b) => a + b.ntb, 0)
  const evr = b.reduce((a, b) => a + b.evr, 0)
  return { ntb, evr, branches: b.length, total: ntb + evr }
}

function getZoneTotals(zoneData) {
  const t = { ntb: 0, evr: 0, branches: 0, total: 0 }
  zoneData.regions.forEach(r => {
    const rt = getRegionTotals(r)
    t.ntb += rt.ntb; t.evr += rt.evr; t.branches += rt.branches; t.total += rt.total
  })
  return t
}
</script>

<template>
  <div class="sb-card card-table overflow-x-auto">
    <table class="w-full border-collapse text-sm">
      <thead>
        <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
          <th class="border-r border-[var(--border)] px-4 py-2.5 text-center text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)] w-12">SR</th>
          <th class="border-r border-[var(--border)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">ZONE / REGION / BRANCH</th>
          <th class="border-r border-[var(--border)] px-4 py-2.5 text-center text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">BRANCHES</th>
          <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">NTB</th>
          <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">EVR</th>
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
              {{ zone.zone }}
            </td>
            <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm font-semibold text-[var(--text)]">{{ getZoneTotals(zone).branches }}</td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getZoneTotals(zone).ntb }}</td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getZoneTotals(zone).evr }}</td>
            <td class="px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getZoneTotals(zone).total }}</td>
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
                <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm text-[var(--text)]">{{ getRegionTotals(region).branches }}</td>
                <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getRegionTotals(region).ntb }}</td>
                <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getRegionTotals(region).evr }}</td>
                <td class="px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getRegionTotals(region).total }}</td>
              </tr>
              <template v-if="isRegionExpanded(zone.zone + '-' + region.region)">
                <tr v-for="(branch, bi) in region.branches" :key="branch.branch"
                    class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]">
                  <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-xs text-[var(--text3)]">{{ zi + 1 }}.{{ ri + 1 }}.{{ bi + 1 }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-2.5 pl-16 text-sm text-[var(--text)]">{{ branch.branch }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm text-[var(--text)]">1</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.ntb }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.evr }}</td>
                  <td class="px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.total }}</td>
                </tr>
              </template>
            </template>
          </template>
        </template>
      </tbody>
    </table>
  </div>
</template>