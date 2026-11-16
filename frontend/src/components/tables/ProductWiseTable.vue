<script setup>
import { ref, computed, onMounted } from 'vue'
import { frappeRequest } from 'frappe-ui'
import { useNumberFormat } from '@/composables/useNumberFormat.js'
import { useFilters } from '@/composables/useFilters.js'
import { useExpandableSet } from '@/composables/useExpandableSet.js'
import { useNameFormat } from '@/composables/useNameFormat.js'
import ViewToggle from './ViewToggle.vue'

const { formatNumber } = useNumberFormat()
const { isZoneSelected, isRegionSelected } = useFilters()
const { toggle: toggleZone, isExpanded: isZoneExpanded } = useExpandableSet()
const { formatZone, formatRegion } = useNameFormat()

const rawProductWise = ref([])
const allProducts = ref([])
const loading = ref(true)
const viewMode = ref('table')

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

// Chart data for product-wise view
const productChartData = computed(() => {
  const productTotals = {}
  
  // Calculate totals for each product
  rawProductWise.value.filter(r => r.is_group && isZoneSelected(r.name)).forEach(zone => {
    allProducts.value.forEach(product => {
      if (!productTotals[product]) {
        productTotals[product] = {
          name: product,
          amount: 0,
          count: 0,
          zones: 0
        }
      }
      productTotals[product].amount += zone.products?.[product] || 0
    })
  })
  
  // Convert to array and sort by amount descending
  return Object.values(productTotals)
    .filter(item => item.amount > 0)
    .sort((a, b) => b.amount - a.amount)
})

const zoneChartData = computed(() => {
  const zones = rawProductWise.value.filter(r => r.is_group && isZoneSelected(r.name))
  
  return zones.map(zone => ({
    zone: formatZone(zone.name),
    amount: zone.amount,
    count: zone.count,
    products: allProducts.value.map(product => ({
      name: product,
      value: zone.products?.[product] || 0
    })).filter(p => p.value > 0)
  })).sort((a, b) => b.amount - a.amount)
})

const chartOptions = computed(() => {
  const maxProductAmount = Math.max(...productChartData.value.map(d => d.amount), 1)
  const maxZoneAmount = Math.max(...zoneChartData.value.map(d => d.amount), 1)
  
  return {
    maxProductAmount,
    maxZoneAmount,
    colors: ['#3b82f6', '#ef4444', '#f59e0b', '#22c55e', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316']
  }
})
</script>

<template>
  <div class="sb-card card-table">
    <div v-if="loading" class="p-8 text-center text-sm text-[var(--text3)]">Loading...</div>
    <div v-else>
      <!-- View Toggle Header -->
      <div class="flex items-center justify-between border-b border-[var(--border)] bg-[var(--bg2)] px-5 py-3">
        <div class="text-sm font-semibold text-[var(--text3)] uppercase tracking-wider">
          Product Wise Collection
        </div>
        <ViewToggle v-model:viewMode="viewMode" color="#5b21b6" />
      </div>
      
      <!-- Chart View -->
      <div v-if="viewMode === 'chart'" class="p-6">
        <!-- Product Distribution Chart -->
        <div class="mb-8">
          <h3 class="text-sm font-semibold text-[var(--text3)] mb-4">Product Distribution</h3>
          
          <div class="space-y-4">
            <div v-for="(product, index) in productChartData" :key="product.name" class="chart-item">
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-3">
                  <span class="w-6 text-right text-xs font-medium text-[var(--text3)]">{{ index + 1 }}.</span>
                  <span class="text-sm font-medium text-[var(--text)]">{{ product.name }}</span>
                </div>
                <span class="text-sm font-semibold text-[var(--text)]">
                  {{ formatNumber(product.amount) }}
                </span>
              </div>
              
              <!-- Progress Bar -->
              <div class="relative h-3 bg-[var(--bg2)] rounded-full overflow-hidden">
                <div 
                  class="absolute top-0 left-0 h-full rounded-full transition-all duration-500"
                  :style="{
                    width: `${Math.min(100, (product.amount / chartOptions.maxProductAmount) * 100)}%`,
                    backgroundColor: chartOptions.colors[index % chartOptions.colors.length]
                  }"
                ></div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Zone-wise Product Performance -->
        <div>
          <h3 class="text-sm font-semibold text-[var(--text3)] mb-4">Zone-wise Collection</h3>
          
          <div class="space-y-4">
            <div v-for="(zone, index) in zoneChartData" :key="zone.zone" class="chart-item">
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center gap-3">
                  <span class="w-6 text-right text-xs font-medium text-[var(--text3)]">{{ index + 1 }}.</span>
                  <span class="text-sm font-medium text-[var(--text)]">{{ zone.zone }}</span>
                  <span class="text-xs text-[var(--text3)]">({{ zone.count }} transactions)</span>
                </div>
                <span class="text-sm font-semibold text-[var(--text)]">
                  {{ formatNumber(zone.amount) }}
                </span>
              </div>
              
              <!-- Product Breakdown -->
              <div class="text-xs text-[var(--text3)] mb-2">Product breakdown:</div>
              <div class="space-y-2">
                <div v-for="(product, pIndex) in zone.products.slice(0, 3)" :key="product.name" class="flex items-center gap-2">
                  <div class="w-16 text-xs text-[var(--text3)] truncate">{{ product.name }}</div>
                  <div class="flex-1">
                    <div class="relative h-2 bg-[var(--bg2)] rounded-full overflow-hidden">
                      <div 
                        class="absolute top-0 left-0 h-full rounded-full"
                        :style="{
                          width: `${Math.min(100, (product.value / zone.amount) * 100)}%`,
                          backgroundColor: chartOptions.colors[pIndex % chartOptions.colors.length]
                        }"
                      ></div>
                    </div>
                  </div>
                  <div class="w-16 text-right text-xs font-medium text-[var(--text)]">
                    {{ formatNumber(product.value) }}
                  </div>
                </div>
                <div v-if="zone.products.length > 3" class="text-xs text-[var(--text3)] text-center">
                  + {{ zone.products.length - 3 }} more products
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Summary Stats -->
        <div class="mt-8 pt-6 border-t border-[var(--border)] grid grid-cols-4 gap-4">
          <div class="text-center">
            <div class="text-xs text-[var(--text3)] mb-1">Total Products</div>
            <div class="text-2xl font-bold text-[var(--text)]">{{ productChartData.length }}</div>
          </div>
          <div class="text-center">
            <div class="text-xs text-[var(--text3)] mb-1">Total Collection</div>
            <div class="text-2xl font-bold text-[var(--text)]">{{ formatNumber(grandTotal._amount) }}</div>
          </div>
          <div class="text-center">
            <div class="text-xs text-[var(--text3)] mb-1">Total Transactions</div>
            <div class="text-2xl font-bold text-[var(--text)]">{{ grandTotal._count }}</div>
          </div>
          <div class="text-center">
            <div class="text-xs text-[var(--text3)] mb-1">Avg. per Zone</div>
            <div class="text-2xl font-bold text-[var(--text)]">{{ 
              zoneChartData.length > 0 ? formatNumber(grandTotal._amount / zoneChartData.length) : 0 
            }}</div>
          </div>
        </div>
      </div>
      
      <!-- Table View -->
      <div v-else-if="viewMode === 'table'">
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
                  {{ formatZone(zoneData.name) }}
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
                <td class="border-r border-[var(--border)] px-4 py-3 pl-10 text-sm text-[var(--text2)]">
                  {{ formatRegion(region.name) }}
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
  </div>
</template>

<style scoped>
.chart-item {
  @apply p-3 border border-[var(--border)] rounded-lg bg-[var(--bg1)];
}

.chart-item:not(:last-child) {
  @apply mb-3;
}
</style>
