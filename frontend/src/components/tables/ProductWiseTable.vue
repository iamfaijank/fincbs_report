<script setup>
import { ref, computed, onMounted } from 'vue'
import { frappeRequest } from 'frappe-ui'
import { useNumberFormat } from '@/composables/useNumberFormat.js'
import { useFilters } from '@/composables/useFilters.js'
import { useExpandableSet } from '@/composables/useExpandableSet.js'

const { formatNumber } = useNumberFormat()
const { isZoneSelected, isRegionSelected } = useFilters()
const { toggle: toggleZone, isExpanded: isZoneExpanded } = useExpandableSet()

const rawProductWise = ref([])
const allProducts = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const data = await frappeRequest({
      url: '/api/method/custom_report.www.drishti.get_product_wise_data',
      method: 'POST',
    }) || {}
    rawProductWise.value = data.product_wise || []
    allProducts.value = data.all_products || []
  } catch (e) {
    console.error('Failed to load product wise data', e)
  } finally {
    loading.value = false
  }
})

const filteredProductData = computed(() => {
  const zones = rawProductWise.value.filter(r => r.is_group && isZoneSelected(r.name))
  return zones.map(zone => {
    const regions = rawProductWise.value.filter(r => !r.is_group && r.parent === zone.name && isRegionSelected(r.name))
    return { ...zone, regions }
  }).filter(z => z.regions.length > 0 || z.is_group)
})

const grandTotal = computed(() => {
  const totals = {}
  allProducts.value.forEach(p => { totals[p] = 0 })
  totals._count = 0
  totals._amount = 0
  rawProductWise.value.filter(r => r.is_group).forEach(z => {
    totals._count += z.count || 0
    totals._amount += z.amount || 0
    allProducts.value.forEach(p => { totals[p] += z.products?.[p] || 0 })
  })
  return totals
})
</script>

<template>
  <div class="sb-card card-table">
    <div v-if="loading" class="p-8 text-center text-sm text-[var(--text3)]">Loading...</div>
    <div v-else>
      <table class="w-full">
        <thead>
          <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
            <th rowspan="2" class="border-r border-[var(--border)] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              Zone/Region
            </th>
            <th rowspan="2" class="border-r border-[var(--border)] px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              Count
            </th>
            <th
              v-for="product in allProducts"
              :key="product"
              class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]"
            >
              {{ product }}
            </th>
            <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
              Total
            </th>
          </tr>
        </thead>
        <tbody>
          <template v-for="zoneData in filteredProductData" :key="zoneData.name">
            <tr
              class="cursor-pointer border-b border-[var(--border)] bg-[var(--bg1)] font-semibold transition hover:bg-[var(--bg2)]"
              @click="toggleZone(zoneData.name)"
            >
              <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">
                <div class="flex items-center gap-2">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="transition-transform" :class="isZoneExpanded(zoneData.name) ? 'rotate-90' : ''">
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                  {{ zoneData.name }}
                </div>
              </td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-center font-mono text-sm text-[var(--text)]">{{ zoneData.count }}</td>
              <td
                v-for="product in allProducts"
                :key="product"
                class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]"
              >
                {{ formatNumber(zoneData.products?.[product] || 0) }}
              </td>
              <td class="px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">
                {{ formatNumber(zoneData.amount) }}
              </td>
            </tr>
            <template v-if="isZoneExpanded(zoneData.name)">
              <tr
                v-for="region in zoneData.regions"
                :key="`${zoneData.name}-${region.name}`"
                class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
              >
                <td class="border-r border-[var(--border)] px-4 py-3 pl-6 text-sm text-[var(--text2)]">
                  {{ region.name }}
                </td>
                <td class="border-r border-[var(--border)] px-4 py-3 text-center font-mono text-sm text-[var(--text)]">{{ region.count }}</td>
                <td
                  v-for="product in allProducts"
                  :key="product"
                  class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]"
                >
                  {{ formatNumber(region.products?.[product] || 0) }}
                </td>
                <td class="px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">
                  {{ formatNumber(region.amount) }}
                </td>
              </tr>
            </template>
          </template>
          <tr class="border-t-2 border-[var(--border)] bg-[var(--bg2)] font-semibold">
            <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">Total</td>
            <td class="border-r border-[var(--border)] px-4 py-3 text-center font-mono text-sm text-[var(--text)]">{{ grandTotal._count }}</td>
            <td
              v-for="product in allProducts"
              :key="product"
              class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]"
            >
              {{ formatNumber(grandTotal[product]) }}
            </td>
            <td class="px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">
              {{ formatNumber(grandTotal._amount) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
