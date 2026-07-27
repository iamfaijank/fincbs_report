import { ref, computed } from 'vue'

const zoneFilter = ref([])
const regionFilter = ref([])

const allZones = ref([])
const allRegions = ref([])

const zoneFilterOptions = ref([])
const regionFilterOptions = ref([])

function mapZoneName(name) {
  const match = name.match(/^Zone\s*-?\s*(.+)/i)
  if (match) return 'Z' + (match[1] ? '-' + match[1] : '')
  return name
}

function mapRegionName(name) {
  const match = name.match(/^Region\s*-?\s*(.+)/i)
  if (match) return 'R' + (match[1] ? '-' + match[1] : '')
  return name
}

export function useFilters() {
  function setZoneOptions(zones) {
    allZones.value = zones
    zoneFilterOptions.value = zones.map(z => ({ name: z, label: mapZoneName(z) }))
  }

  function setRegionOptions(regions) {
    allRegions.value = regions
    regionFilterOptions.value = regions.map(r => ({ name: r, label: mapRegionName(r) }))
  }

  function setZoneFilterOptions(zones) {
    zoneFilterOptions.value = zones.map(z => ({ name: z, label: mapZoneName(z) }))
  }

  function setRegionFilterOptions(regions) {
    regionFilterOptions.value = regions.map(r => ({ name: r, label: mapRegionName(r) }))
  }

  function setZoneFilter(zones) {
    zoneFilter.value = zones
  }

  function setRegionFilter(regions) {
    regionFilter.value = regions
  }

  const allZonesSelected = computed(() => zoneFilter.value.length === 0 || zoneFilter.value.length === zoneFilterOptions.value.length)
  const allRegionsSelected = computed(() => regionFilter.value.length === 0 || regionFilter.value.length === regionFilterOptions.value.length)

  function isZoneSelected(displayName) {
    if (zoneFilter.value.length === 0) return true
    return zoneFilter.value.some(apiName => mapZoneName(apiName) === displayName)
  }

  function isRegionSelected(displayName) {
    if (regionFilter.value.length === 0) return true
    return regionFilter.value.some(apiName => mapRegionName(apiName) === displayName)
  }

  return {
    zoneFilter,
    regionFilter,
    allZones,
    allRegions,
    zoneFilterOptions,
    regionFilterOptions,
    setZoneOptions,
    setRegionOptions,
    setZoneFilterOptions,
    setRegionFilterOptions,
    setZoneFilter,
    setRegionFilter,
    allZonesSelected,
    allRegionsSelected,
    isZoneSelected,
    isRegionSelected,
  }
}
