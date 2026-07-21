<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { Select, DatePicker, frappeRequest } from 'frappe-ui'
import { useSidebar } from '@/composables/useSidebar.js'
import { useNumberFormat } from '@/composables/useNumberFormat.js'

const { collapsed, toggleSidebar } = useSidebar()
const { numberFormat } = useNumberFormat()
const viewMode = ref('monthly')
const targetType = ref('monthly')
const financialYear = ref('')
const asOfDate = ref('')
const asOfMonth = ref('6')
const segmentSelect = ref('all')
const isDark = ref(false)

// Zone Filter
const zoneFilter = ref<string[]>([])

// Region Filter
const regionFilter = ref<string[]>([])

// District Filter
const districtFilter = ref<string[]>([])
const showDistrictDropdown = ref(false)
const districtSearch = ref('')
const districtInputRef = ref<HTMLInputElement | null>(null)

// Branch Filter
const branchFilter = ref<string[]>([])
const showBranchDropdown = ref(false)
const branchSearch = ref('')
const branchInputRef = ref<HTMLInputElement | null>(null)

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

const zoneFilterOptions = ref<{ name: string; label: string }[]>([])

const regionFilterOptions = ref<{ name: string; label: string }[]>([])

const districtOptions = ref([
  'Mumbai', 'Delhi', 'Bengaluru', 'Kolkata',
  'Chennai', 'Hyderabad', 'Pune', 'Ahmedabad',
])

const branchOptions = ref([
  { label: 'ABD (1001)', value: 'abd1001' },
  { label: 'JHD (1002)', value: 'jhd1002' },
])

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

// District helpers
const filteredDistricts = computed(() => {
  const q = districtSearch.value.toLowerCase()
  return districtOptions.value.filter(d => d.toLowerCase().includes(q))
})

const allDistrictsSelected = computed(() => districtFilter.value.length === districtOptions.value.length)

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
    districtFilter.value = [...districtOptions.value]
  }
}

const districtLabel = computed(() => {
  if (districtFilter.value.length === 0) return 'No Districts Selected'
  if (allDistrictsSelected.value) return 'All Districts'
  return `${districtFilter.value.length} Districts Selected`
})

// Zone helpers
const allZonesSelected = computed(() => zoneFilter.value.length === zoneFilterOptions.value.length)

function toggleZone(name: string) {
  const idx = zoneFilter.value.indexOf(name)
  if (idx >= 0) {
    zoneFilter.value.splice(idx, 1)
  } else {
    zoneFilter.value.push(name)
  }
}

function toggleAllZones() {
  if (allZonesSelected.value) {
    zoneFilter.value = []
  } else {
    zoneFilter.value = zoneFilterOptions.value.map(z => z.name)
  }
}

// Region helpers
const allRegionsSelected = computed(() => regionFilter.value.length === regionFilterOptions.value.length)

function toggleRegion(name: string) {
  const idx = regionFilter.value.indexOf(name)
  if (idx >= 0) {
    regionFilter.value.splice(idx, 1)
  } else {
    regionFilter.value.push(name)
  }
}

function toggleAllRegions() {
  if (allRegionsSelected.value) {
    regionFilter.value = []
  } else {
    regionFilter.value = regionFilterOptions.value.map(r => r.name)
  }
}

// Branch helpers
const filteredBranches = computed(() => {
  const q = branchSearch.value.toLowerCase()
  return branchOptions.value.filter(b => b.label.toLowerCase().includes(q))
})

const allBranchesSelected = computed(() => branchFilter.value.length === branchOptions.value.length)

function toggleBranch(val: string) {
  const idx = branchFilter.value.indexOf(val)
  if (idx >= 0) {
    branchFilter.value.splice(idx, 1)
  } else {
    branchFilter.value.push(val)
  }
}

function toggleAllBranches() {
  if (allBranchesSelected.value) {
    branchFilter.value = []
  } else {
    branchFilter.value = branchOptions.value.map(b => b.value)
  }
}

const branchLabel = computed(() => {
  if (branchFilter.value.length === 0) return 'No Branches Selected'
  if (allBranchesSelected.value) return 'All Branches'
  const selected = branchOptions.value.filter(b => branchFilter.value.includes(b.value))
  return `${selected.length} Branches Selected`
})

// Click outside
function handleClickOutside(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.ms-dropdown-district')) {
    showDistrictDropdown.value = false
    districtSearch.value = ''
  }
  if (!target.closest('.ms-dropdown-branch')) {
    showBranchDropdown.value = false
    branchSearch.value = ''
  }
}

function toggleTheme() {
  isDark.value = !isDark.value
  const theme = isDark.value ? 'dark' : 'light'
  localStorage.setItem('theme', theme)
  document.documentElement.setAttribute('data-theme', theme)
}

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

onMounted(async () => {
  document.addEventListener('click', handleClickOutside)
  isDark.value = localStorage.getItem('theme') === 'dark'
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')

  let allZones: string[] = []
  let allRegions: string[] = []
  let allDistricts: string[] = []
  let allSolIds: string[] = []

  try {
    const opts = await frappeRequest({
      url: '/api/method/custom_report.www.drishti.get_filter_options',
      method: 'POST',
    }) || {}
    allZones = opts.zones || []
    allRegions = opts.regions || []
    allDistricts = opts.districts || []
    allSolIds = opts.sol_ids || []
  } catch (e) {
    console.error('Failed to load filter options', e)
  }

  zoneFilterOptions.value = allZones.map(z => ({ name: z, label: mapZoneName(z) }))
  regionFilterOptions.value = allRegions.map(r => ({ name: r, label: mapRegionName(r) }))
  districtOptions.value = allDistricts.length ? allDistricts : ['Mumbai', 'Delhi', 'Bengaluru', 'Kolkata', 'Chennai', 'Hyderabad', 'Pune', 'Ahmedabad']
  if (allSolIds.length) {
    branchOptions.value = allSolIds.map(s => ({ label: s, value: s }))
  }

  try {
    const pref = await frappeRequest({
      url: '/api/method/custom_report.www.drishti.get_report_preference',
      method: 'POST',
    }) || {}

    if (pref.zone && pref.zone.length) {
      zoneFilter.value = pref.zone
    } else {
      zoneFilter.value = zoneFilterOptions.value.map(z => z.name)
    }

    if (pref.region && pref.region.length) {
      regionFilter.value = pref.region
    } else {
      regionFilter.value = regionFilterOptions.value.map(r => r.name)
    }

    if (pref.district && pref.district.length) {
      districtFilter.value = pref.district
    } else {
      districtFilter.value = [...districtOptions.value]
    }

    if (pref.sol_id && pref.sol_id.length) {
      branchFilter.value = pref.sol_id
    } else {
      branchFilter.value = branchOptions.value.map(b => b.value)
    }
  } catch (e) {
    zoneFilter.value = zoneFilterOptions.value.map(z => z.name)
    regionFilter.value = regionFilterOptions.value.map(r => r.name)
    districtFilter.value = [...districtOptions.value]
    branchFilter.value = branchOptions.value.map(b => b.value)
  }
})

watch(showDistrictDropdown, (val) => {
  if (val) nextTick(() => districtInputRef.value?.focus())
})

watch(showBranchDropdown, (val) => {
  if (val) nextTick(() => branchInputRef.value?.focus())
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <aside
    class="sidebar flex h-screen flex-col border-r transition-all duration-300"
    :class="collapsed ? 'sidebar-collapsed' : ''"
    :style="!collapsed ? { width: 'var(--sidebar-w)' } : {}"
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

      <!-- ZONE FILTER -->
      <div class="sb-section">
        <div class="sb-label">Zone Filter</div>
        <div class="filter-chips">
          <div class="filter-chip" :class="{ active: allZonesSelected }" @click="toggleAllZones()">All</div>
          <div v-for="z in zoneFilterOptions" :key="z.name" class="filter-chip" :class="{ active: zoneFilter.includes(z.name) }" @click="toggleZone(z.name)">
            {{ z.label }}
          </div>
        </div>
      </div>

      <!-- REGION FILTER -->
      <div class="sb-section">
        <div class="sb-label">Region Filter</div>
        <div class="filter-chips">
          <div class="filter-chip" :class="{ active: allRegionsSelected }" @click="toggleAllRegions()">All</div>
          <div v-for="r in regionFilterOptions" :key="r.name" class="filter-chip" :class="{ active: regionFilter.includes(r.name) }" @click="toggleRegion(r.name)">
            {{ r.label }}
          </div>
        </div>
      </div>

      <!-- DISTRICT FILTER -->
      <div class="sb-section">
        <div class="sb-label">District Filter</div>
        <div class="multiselect-dropdown ms-dropdown-district">
          <div class="multiselect-select" @click.stop="showDistrictDropdown = !showDistrictDropdown">
            <input
              v-if="showDistrictDropdown"
              ref="districtInputRef"
              v-model="districtSearch"
              type="text"
              class="ms-inline-input"
              placeholder="Search district…"
              @click.stop
            />
            <span v-else>{{ districtLabel }}</span>
            <span class="z-arrow">▼</span>
          </div>
          <div class="multiselect-options" :class="{ open: showDistrictDropdown }">
            <div class="ms-option">
              <label class="ms-label">
                <input type="checkbox" :checked="allDistrictsSelected" @change="toggleAllDistricts" />
                <span>Select All</span>
              </label>
            </div>
            <div v-for="d in filteredDistricts" :key="d" class="ms-option">
              <label class="ms-label">
                <input type="checkbox" :value="d" :checked="districtFilter.includes(d)" @change="toggleDistrict(d)" />
                <span>{{ d }}</span>
              </label>
            </div>
            <div v-if="filteredDistricts.length === 0" class="ms-empty">No results found</div>
          </div>
        </div>
      </div>

      <!-- BRANCH FILTER -->
      <div class="sb-section">
        <div class="sb-label">Branch</div>
        <div class="multiselect-dropdown ms-dropdown-branch">
          <div class="multiselect-select" @click.stop="showBranchDropdown = !showBranchDropdown">
            <input
              v-if="showBranchDropdown"
              ref="branchInputRef"
              v-model="branchSearch"
              type="text"
              class="ms-inline-input"
              placeholder="Search branch…"
              @click.stop
            />
            <span v-else>{{ branchLabel }}</span>
            <span class="z-arrow">▼</span>
          </div>
          <div class="multiselect-options" :class="{ open: showBranchDropdown }">
            <div class="ms-option">
              <label class="ms-label">
                <input type="checkbox" :checked="allBranchesSelected" @change="toggleAllBranches" />
                <span>Select All</span>
              </label>
            </div>
            <div v-for="b in filteredBranches" :key="b.value" class="ms-option">
              <label class="ms-label">
                <input type="checkbox" :value="b.value" :checked="branchFilter.includes(b.value)" @change="toggleBranch(b.value)" />
                <span>{{ b.label }}</span>
              </label>
            </div>
            <div v-if="filteredBranches.length === 0" class="ms-empty">No results found</div>
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
