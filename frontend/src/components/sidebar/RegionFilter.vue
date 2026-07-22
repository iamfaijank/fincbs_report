<script setup>
import { computed } from 'vue'
import { useFilters } from '@/composables/useFilters.js'

const { regionFilterOptions, regionFilter, setRegionFilter } = useFilters()

const allRegionsSelected = computed(() => regionFilter.value.length === 0 || regionFilter.value.length === regionFilterOptions.value.length)

function toggleRegion(name) {
  if (allRegionsSelected.value) {
    setRegionFilter([name])
  } else {
    const idx = regionFilter.value.indexOf(name)
    if (idx >= 0) {
      setRegionFilter(regionFilter.value.filter(r => r !== name))
    } else {
      setRegionFilter([...regionFilter.value, name])
    }
  }
}

function toggleAllRegions() {
  if (allRegionsSelected.value) {
    setRegionFilter([])
  } else {
    setRegionFilter([])
  }
}
</script>

<template>
  <div class="sb-section">
    <div class="sb-label">Region Filter</div>
    <div class="filter-chips">
      <div class="filter-chip" :class="{ active: allRegionsSelected }" @click="toggleAllRegions()">All</div>
      <div v-for="r in regionFilterOptions" :key="r.name" class="filter-chip" :class="{ active: regionFilter.includes(r.name) }" @click="toggleRegion(r.name)">
        {{ r.label }}
      </div>
    </div>
  </div>
</template>
