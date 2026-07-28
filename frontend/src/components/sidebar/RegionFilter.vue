<script setup>
import { useFilters } from '@/composables/useFilters.js'

const { regionFilterOptions, regionFilter, setRegionFilter, selectAllRegions, allRegionsSelected } = useFilters()

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
    setRegionFilter(regionFilterOptions.value.map(r => r.name))
  } else {
    selectAllRegions()
  }
}
</script>

<template>
  <div class="sb-section">
    <div class="sb-label">Region Filter</div>
    <div class="filter-chips">
      <div class="filter-chip" :class="{ active: allRegionsSelected }" @click="toggleAllRegions()">All</div>
      <div v-for="r in regionFilterOptions" :key="r.name" class="filter-chip" :class="{ active: !allRegionsSelected && regionFilter.includes(r.name) }" @click="toggleRegion(r.name)">
        {{ r.label }}
      </div>
    </div>
  </div>
</template>
