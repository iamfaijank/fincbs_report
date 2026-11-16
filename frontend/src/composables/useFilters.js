import { ref, computed } from 'vue'

const zoneFilter = ref([])
const regionFilter = ref([])

const allZones = ref([])
const allRegions = ref([])

const zoneFilterOptions = ref([])
const regionFilterOptions = ref([])

function mapZoneName(name) {
  const match = name.match(/^ZONE-?\s*(.+)/i)
  if (match) return 'Z-' + (match[1] || '')
  const match2 = name.match(/^Zone\s*-?\s*(.+)/i)
  if (match2) return 'Z-' + (match2[1] || '')
  return name
}

function mapRegionName(name) {
  const match = name.match(/^REGION-?\s*(.+)/i)
  if (match) return 'R-' + (match[1] || '')
  const match2 = name.match(/^Region\s*-?\s*(.+)/i)
  if (match2) return 'R-' + (match2[1] || '')
  return name
}

export function useFilters() {
  function setZoneOptions(zones) {
    allZones.value = zones
    zoneFilterOptions.value = zones.map(z => ({ name: z, label: mapZoneName(z) }))
    zoneFilter.value = zones.map(z => z)
  }

  function setRegionOptions(regions) {
    allRegions.value = regions
    regionFilterOptions.value = regions.map(r => ({ name: r, label: mapRegionName(r) }))
    regionFilter.value = regions.map(r => r)
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

  function selectAllZones() {
    zoneFilter.value = zoneFilterOptions.value.map(z => z.name)
  }

  function selectAllRegions() {
    regionFilter.value = regionFilterOptions.value.map(r => r.name)
  }

  const allZonesSelected = computed(() => zoneFilter.value.length === zoneFilterOptions.value.length)
  const allRegionsSelected = computed(() => regionFilter.value.length === regionFilterOptions.value.length)

  function isZoneSelected(displayName) {
    return zoneFilter.value.includes(displayName)
  }

  function isRegionSelected(displayName) {
    return regionFilter.value.includes(displayName)
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
    selectAllZones,
    selectAllRegions,
    allZonesSelected,
    allRegionsSelected,
    isZoneSelected,
    isRegionSelected,
  }
}
