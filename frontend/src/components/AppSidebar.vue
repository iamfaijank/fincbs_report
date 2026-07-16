<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Select, DatePicker } from 'frappe-ui'

const collapsed = ref(false)
const viewMode = ref('monthly')
const targetType = ref('monthly')
const numberFormat = ref('words')
const financialYear = ref('')
const asOfDate = ref('')
const asOfMonth = ref('6')
const zoneFilter = ref('all')
const regionFilter = ref('all')
const districtFilter = ref<string[]>([])
const showDistrictDropdown = ref(false)
const segmentSelect = ref('all')
const pctRange = ref(150)

const categories = ref([
  { name: 'Pinnacle', range: '>100%', color: '#4fffb0', count: 42, enabled: true },
  { name: 'Master', range: '80–100%', color: '#2dd4bf', count: 38, enabled: true },
  { name: 'Accelerator', range: '60–80%', color: '#0ea5e9', count: 61, enabled: true },
  { name: 'Starter', range: '40–60%', color: '#f59e0b', count: 47, enabled: true },
  { name: 'Learner', range: '20–40%', color: '#ef4444', count: 28, enabled: true },
  { name: 'Zero Level', range: '0–20%', color: '#dc2626', count: 13, enabled: true },
])

const monthOptions = [
  { label: 'April', value: '4' },
  { label: 'May', value: '5' },
  { label: 'June', value: '6' },
  { label: 'July', value: '7' },
  { label: 'August', value: '8' },
  { label: 'September', value: '9' },
  { label: 'October', value: '10' },
  { label: 'November', value: '11' },
  { label: 'December', value: '12' },
  { label: 'January', value: '1' },
  { label: 'February', value: '2' },
  { label: 'March', value: '3' },
]

const zoneFilterOptions = [
  { label: 'All', value: 'all' },
  { label: 'Z-1', value: 'z1' },
  { label: 'Z-2', value: 'z2' },
  { label: 'Z-3', value: 'z3' },
  { label: 'Z-4', value: 'z4' },
  { label: 'Z-5', value: 'z5' },
  { label: 'Z-6', value: 'z6' },
]

const regionFilterOptions = [
  { label: 'All', value: 'all' },
  { label: 'R1', value: 'r1' },
  { label: 'R2', value: 'r2' },
  { label: 'R3', value: 'r3' },
  { label: 'R4', value: 'r4' },
]

const districtOptions = [
  'Mumbai', 'Delhi', 'Bengaluru', 'Kolkata',
  'Chennai', 'Hyderabad', 'Pune', 'Ahmedabad',
]

const financialYearOptions = [
  { label: 'FY 26–27', value: 'fy2627' },
  { label: 'FY 25–26', value: 'fy2526' },
  { label: 'FY 24–25', value: 'fy2425' },
]

const segmentOptions = [
  { label: 'All Segments', value: 'all' },
  { label: 'Top 25%', value: 'top25' },
  { label: 'Next 25%', value: 'next25' },
  { label: 'Mid 25%', value: 'mid25' },
  { label: 'Bottom 25%', value: 'bottom25' },
]

const allDistrictsSelected = computed(() => districtFilter.value.length === districtOptions.length)

function toggleDistrict(d: string) {
  const idx = districtFilter.value.indexOf(d)
  if (idx >= 0) {
    districtFilter.value.splice(idx, 1)
  } else {
    districtFilter.value.push(d)
  }
}

function toggleAllDistricts() {
  if (allDistrictsSelected.value) {
    districtFilter.value = []
  } else {
    districtFilter.value = [...districtOptions]
  }
}

const districtLabel = computed(() => {
  if (allDistrictsSelected.value) return 'All Districts'
  if (districtFilter.value.length === 0) return 'No Districts Selected'
  return `${districtFilter.value.length} Districts Selected`
})

function handleClickOutside(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.multiselect-dropdown')) {
    showDistrictDropdown.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  districtFilter.value = [...districtOptions]
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <aside
    class="sidebar flex h-screen flex-col border-r transition-all duration-300"
    :class="collapsed ? 'w-0 border-transparent' : ''"
    :style="!collapsed ? { width: 'var(--sidebar-w)' } : {}"
  >
    <div class="sidebar-inner">
      <!-- Logo -->
      <div class="sidebar-logo">
        <img src="/fav-icon.png" alt="Drishti" class="logo-mark" />
        <div>
          <div class="logo-text">DRISHTI</div>
          <div class="logo-sub">Performance Intelligence</div>
        </div>
      </div>

      <!-- CONFIGURATION -->
      <div class="sb-section">
        <!-- Financial Year -->
        <div class="sb-field">
          <div class="fg-title">Financial Year</div>
          <Select
            v-model="financialYear"
            placeholder="Select FY"
            :options="financialYearOptions"
          />
        </div>

        <!-- View Mode -->
        <div class="sb-field">
          <div class="fg-title">View Mode</div>
          <div class="config-row">
            <div class="config-btn" :class="{ active: viewMode === 'monthly' }" @click="viewMode = 'monthly'">Monthly</div>
            <div class="config-btn" :class="{ active: viewMode === 'quarterly' }" @click="viewMode = 'quarterly'">Quarterly</div>
            <div class="config-btn" :class="{ active: viewMode === 'yearly' }" @click="viewMode = 'yearly'">Yearly</div>
          </div>
        </div>

        <!-- Target Type -->
        <div class="sb-field">
          <div class="fg-title">Target Type</div>
          <div class="config-row">
            <div class="config-btn" :class="{ active: targetType === 'monthly' }" @click="targetType = 'monthly'">Monthly</div>
            <div class="config-btn" :class="{ active: targetType === 'ytd' }" @click="targetType = 'ytd'">YTD</div>
            <div class="config-btn" :class="{ active: targetType === 'yearly' }" @click="targetType = 'yearly'">Yearly</div>
          </div>
        </div>

        <!-- Number Format -->
        <div class="sb-field">
          <div class="fg-title">Number Format</div>
          <div class="config-row">
            <div class="config-btn" :class="{ active: numberFormat === 'words' }" @click="numberFormat = 'words'">Words</div>
            <div class="config-btn" :class="{ active: numberFormat === 'number' }" @click="numberFormat = 'number'">Numeric</div>
          </div>
        </div>

        <!-- As of Date & Month -->
        <div class="sb-field">
          <div class="fg-title">As of Date & Month</div>
          <div class="sb-row">
            <div class="sb-half">
              <DatePicker v-model="asOfDate" placeholder="Pick a date" format="MMM D, YYYY" />
            </div>
            <div class="sb-half">
              <Select v-model="asOfMonth" placeholder="Month" :options="monthOptions" />
            </div>
          </div>
        </div>
      </div>

      <!-- ZONE FILTER -->
      <div class="sb-section">
        <div class="sb-label">Zone Filter</div>
        <div class="filter-chips">
          <div
            v-for="opt in zoneFilterOptions"
            :key="opt.value"
            class="filter-chip"
            :class="{ active: zoneFilter === opt.value }"
            @click="zoneFilter = opt.value"
          >
            {{ opt.label }}
          </div>
        </div>
      </div>

      <!-- REGION FILTER -->
      <div class="sb-section">
        <div class="sb-label">Region Filter</div>
        <div class="filter-chips">
          <div
            v-for="opt in regionFilterOptions"
            :key="opt.value"
            class="filter-chip"
            :class="{ active: regionFilter === opt.value }"
            @click="regionFilter = opt.value"
          >
            {{ opt.label }}
          </div>
        </div>
      </div>

      <!-- DISTRICT FILTER -->
      <div class="sb-section">
        <div class="sb-label">District Filter</div>
        <div class="multiselect-dropdown">
          <div class="multiselect-select" @click.stop="showDistrictDropdown = !showDistrictDropdown">
            <span>{{ districtLabel }}</span>
            <span class="z-arrow">▼</span>
          </div>
          <div class="multiselect-options" :class="{ open: showDistrictDropdown }">
            <div class="multiselect-option">
              <label class="ms-label">
                <input type="checkbox" :checked="allDistrictsSelected" @change="toggleAllDistricts" />
                <span>Select All</span>
              </label>
            </div>
            <div v-for="d in districtOptions" :key="d" class="multiselect-option">
              <label class="ms-label">
                <input type="checkbox" :value="d" :checked="districtFilter.includes(d)" @change="toggleDistrict(d)" />
                <span>{{ d }}</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- CATEGORIES -->
      <div class="sb-section">
        <div class="sb-label">Categories</div>
        <div v-for="cat in categories" :key="cat.name" class="filter-row">
          <div class="filter-label">
            <div class="color-dot" :style="{ background: cat.color }"></div>
            {{ cat.name }}
            <span class="filter-range">{{ cat.range }}</span>
          </div>
          <div class="filter-right">
            <span class="filter-count">{{ cat.count }}</span>
            <label class="toggle">
              <input type="checkbox" v-model="cat.enabled" />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>
      </div>

      <!-- PERFORMANCE SEGMENT -->
      <div class="sb-section">
        <div class="sb-label">Performance Segment</div>
        <Select v-model="segmentSelect" placeholder="All Segments" :options="segmentOptions" />
      </div>

      <!-- ACH% RANGE -->
      <div class="sb-section">
        <div class="sb-label">Ach% Range</div>
        <div class="range-wrap">
          <input type="range" min="0" max="150" v-model.number="pctRange" />
          <div class="range-vals">
            <span>0%</span>
            <span>{{ pctRange }}%</span>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="sb-footer">
        <button class="reset-btn" @click="$emit('reset')">↺ Reset All Filters</button>
      </div>
    </div>
  </aside>
</template>
