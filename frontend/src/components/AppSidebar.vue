<script setup lang="ts">
import { ref, watch } from 'vue'
import { Select, DatePicker, frappeRequest } from 'frappe-ui'
import { useSidebar } from '@/composables/useSidebar.js'
import { useNumberFormat } from '@/composables/useNumberFormat.js'
import { useFilters } from '@/composables/useFilters.js'
import ZoneFilter from '@/components/sidebar/ZoneFilter.vue'
import RegionFilter from '@/components/sidebar/RegionFilter.vue'
import DistrictFilter from '@/components/sidebar/DistrictFilter.vue'
import BranchFilter from '@/components/sidebar/BranchFilter.vue'

const { collapsed, toggleSidebar } = useSidebar()
const { numberFormat } = useNumberFormat()
const { setZoneOptions, setRegionOptions, setZoneFilter, setRegionFilter } = useFilters()
const viewMode = ref('monthly')
const targetType = ref('monthly')
const financialYear = ref('')
const asOfDate = ref('')
const asOfMonth = ref('6')
const segmentSelect = ref('all')
const isDark = ref(false)

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

const districtOptions = ref([])
const branchOptions = ref([])
const prefDistricts = ref([])
const prefSolIds = ref([])

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

function toInitials(name: string): string {
  return name.split(/[\s_-]+/).filter(Boolean).map(w => w[0].toUpperCase()).join('')
}

function mapZoneName(name: string): string {
  const match = name.match(/^Zone\s*-?\s*(.+)/i)
  if (match) return 'Z' + (match[1] ? '-' + match[1] : '')
  return toInitials(name)
}

function mapRegionName(name: string): string {
  const match = name.match(/^Region\s*-?\s*(.+)/i)
  if (match) return 'R' + (match[1] ? '-' + match[1] : '')
  return toInitials(name)
}

function toggleTheme() {
  isDark.value = !isDark.value
  const theme = isDark.value ? 'dark' : 'light'
  localStorage.setItem('theme', theme)
  document.documentElement.setAttribute('data-theme', theme)
}

watch(viewMode, (val) => {
  localStorage.setItem('viewMode', val)
})

watch(targetType, (val) => {
  localStorage.setItem('targetType', val)
})

watch(asOfMonth, (val) => {
  localStorage.setItem('asOfMonth', val)
})

watch(numberFormat, (val) => {
  localStorage.setItem('numberFormat', val)
})

watch(financialYear, (val) => {
  localStorage.setItem('financialYear', val)
})

const PREFS_KEY = 'drishti_sidebar_prefs'

function loadPrefs() {
  try {
    const raw = localStorage.getItem(PREFS_KEY)
    if (raw) {
      const p = JSON.parse(raw)
      if (p.viewMode) viewMode.value = p.viewMode
      if (p.targetType) targetType.value = p.targetType
      if (p.financialYear) financialYear.value = p.financialYear
      if (p.asOfMonth) asOfMonth.value = p.asOfMonth
      if (p.numberFormat) numberFormat.value = p.numberFormat
    }
  } catch {}
}

function savePrefs() {
  try {
    localStorage.setItem(PREFS_KEY, JSON.stringify({
      viewMode: viewMode.value,
      targetType: targetType.value,
      financialYear: financialYear.value,
      asOfMonth: asOfMonth.value,
      numberFormat: numberFormat.value,
    }))
  } catch {}
}

loadPrefs()
watch([viewMode, targetType, financialYear, asOfMonth, numberFormat], savePrefs)

let allZones: string[] = []
let allRegions: string[] = []

const initFilters = async () => {
  let fetchedZones: string[] = []
  let fetchedRegions: string[] = []
  let fetchedDistricts: string[] = []
  let fetchedBranches: { label: string; value: string }[] = []

  try {
    const opts = await frappeRequest({
      url: '/api/method/custom_report.www.drishti.get_filter_options',
      method: 'POST',
    }) || {}
    fetchedZones = opts.zones || []
    fetchedRegions = opts.regions || []
    fetchedDistricts = opts.districts || []
    fetchedBranches = opts.branches || []
  } catch (e) {
    console.error('Failed to load filter options', e)
  }

  allZones = fetchedZones
  allRegions = fetchedRegions

  setZoneOptions(fetchedZones)
  setRegionOptions(fetchedRegions)

  districtOptions.value = fetchedDistricts.length ? fetchedDistricts : ['Mumbai', 'Delhi', 'Bengaluru', 'Kolkata', 'Chennai', 'Hyderabad', 'Pune', 'Ahmedabad']
  if (fetchedBranches.length) {
    branchOptions.value = fetchedBranches
  }

  try {
    const pref = await frappeRequest({
      url: '/api/method/custom_report.www.drishti.get_report_preference',
      method: 'POST',
    }) || {}

    if (pref.zone && pref.zone.length) {
      setZoneFilter(pref.zone)
    } else {
      setZoneFilter(fetchedZones)
    }

    if (pref.region && pref.region.length) {
      setRegionFilter(pref.region)
    } else {
      setRegionFilter(fetchedRegions)
    }

    prefDistricts.value = pref.district || []
    prefSolIds.value = pref.sol_id || []
  } catch (e) {
    setZoneFilter(fetchedZones)
    setRegionFilter(fetchedRegions)
  }
}

initFilters()
</script>

<template>
  <aside
    class="sidebar flex h-screen flex-col border-r transition-all duration-300"
    :class="collapsed ? 'sidebar-collapsed' : ''"
    :style="{ width: collapsed ? '52px' : 'var(--sidebar-w)' }"
  >
    <div class="sidebar-inner">
      <!-- Logo -->
      <div class="sidebar-logo" :class="{ 'logo-clickable': collapsed }" @click="collapsed ? toggleSidebar() : null" style="cursor: default;">
        <img src="/fav-icon.png" alt="Drishti" class="logo-mark" />
        <div v-if="!collapsed">
          <div class="logo-text">DRISHTI</div>
          <div class="logo-sub">Performance Intelligence</div>
        </div>
        <div style="flex:1" />
        <button class="collapse-btn" @click="toggleSidebar" :title="collapsed ? 'Expand' : 'Collapse'">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline v-if="!collapsed" points="11 17 6 12 11 7" />
            <polyline v-else points="13 7 18 12 13 17" />
          </svg>
        </button>
      </div>

      <template v-if="!collapsed">
      <!-- CONFIGURATION -->
      <div class="sb-section">
        <div class="sb-field">
          <div class="fg-title">Financial Year</div>
          <Select v-model="financialYear" placeholder="Select FY" :options="financialYearOptions" />
        </div>
        <div class="sb-field">
          <div class="fg-title">View Mode</div>
          <div class="config-row">
            <div class="config-btn" :class="{ active: viewMode === 'monthly' }" @click="viewMode = 'monthly'">Monthly</div>
            <div class="config-btn" :class="{ active: viewMode === 'quarterly' }" @click="viewMode = 'quarterly'">Quarterly</div>
            <div class="config-btn" :class="{ active: viewMode === 'yearly' }" @click="viewMode = 'yearly'">Yearly</div>
          </div>
        </div>
        <div class="sb-field">
          <div class="fg-title">Target Type</div>
          <div class="config-row">
            <div class="config-btn" :class="{ active: targetType === 'monthly' }" @click="targetType = 'monthly'">Monthly</div>
            <div class="config-btn" :class="{ active: targetType === 'ytd' }" @click="targetType = 'ytd'">YTD</div>
            <div class="config-btn" :class="{ active: targetType === 'yearly' }" @click="targetType = 'yearly'">Yearly</div>
          </div>
        </div>
        <div class="sb-field">
          <div class="fg-title">Number Format</div>
          <div class="config-row">
            <div class="config-btn" :class="{ active: numberFormat === 'words' }" @click="numberFormat = 'words'">Words</div>
            <div class="config-btn" :class="{ active: numberFormat === 'number' }" @click="numberFormat = 'number'">Numeric</div>
          </div>
        </div>
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

      <!-- FILTERS -->
      <ZoneFilter />
      <RegionFilter />
      <DistrictFilter :options="districtOptions" :initialValue="prefDistricts" />
      <BranchFilter :options="branchOptions" :initialValue="prefSolIds" />

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

      </template>

      <!-- Footer -->
      <div class="sb-footer">
        <div class="sb-footer-row">
          <button class="reset-btn" @click="$emit('reset')">↺ Reset All Filters</button>
          <button class="theme-toggle-btn-sm" @click="toggleTheme" title="Toggle light/dark theme">
            <svg v-if="isDark" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="5"></circle>
              <line x1="12" y1="1" x2="12" y2="3"></line>
              <line x1="12" y1="21" x2="12" y2="23"></line>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
              <line x1="1" y1="12" x2="3" y2="12"></line>
              <line x1="21" y1="12" x2="23" y2="12"></line>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
            </svg>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </aside>
</template>
