<script setup>
import { useFilters } from '@/composables/useFilters.js'

const { zoneFilterOptions, zoneFilter, setZoneFilter, selectAllZones, allZonesSelected } = useFilters()

function toggleZone(name) {
  if (allZonesSelected.value) {
    setZoneFilter([name])
  } else {
    const idx = zoneFilter.value.indexOf(name)
    if (idx >= 0) {
      setZoneFilter(zoneFilter.value.filter(z => z !== name))
    } else {
      setZoneFilter([...zoneFilter.value, name])
    }
  }
}

function toggleAllZones() {
  if (allZonesSelected.value) {
    setZoneFilter(zoneFilterOptions.value.map(z => z.name))
  } else {
    selectAllZones()
  }
}
</script>

<template>
  <div class="sb-section">
    <div class="sb-label">Zone Filter</div>
    <div class="filter-chips">
      <div class="filter-chip" :class="{ active: allZonesSelected }" @click="toggleAllZones()">All</div>
      <div v-for="z in zoneFilterOptions" :key="z.name" class="filter-chip" :class="{ active: !allZonesSelected && zoneFilter.includes(z.name) }" @click="toggleZone(z.name)">
        {{ z.label }}
      </div>
    </div>
  </div>
</template>
