<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'

const districtFilter = ref([])
const showDropdown = ref(false)
const search = ref('')
const inputRef = ref(null)
const districtOptions = ref([])

const filteredDistricts = computed(() => {
  const q = search.value.toLowerCase()
  return districtOptions.value.filter(d => d.toLowerCase().includes(q))
})

const allDistrictsSelected = computed(() => districtFilter.value.length === districtOptions.value.length)

function toggleDistrict(d) {
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

const label = computed(() => {
  if (districtFilter.value.length === 0) return 'No Districts Selected'
  if (allDistrictsSelected.value) return 'All Districts'
  return `${districtFilter.value.length} Districts Selected`
})

function handleClickOutside(e) {
  if (!e.target.closest('.ms-dropdown')) {
    showDropdown.value = false
    search.value = ''
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))

watch(showDropdown, (val) => {
  if (val) nextTick(() => inputRef.value?.focus())
})

const props = defineProps({
  options: { type: Array, default: () => [] }
})

watch(() => props.options, (val) => {
  districtOptions.value = val
  if (districtFilter.value.length === 0) {
    districtFilter.value = [...val]
  }
}, { immediate: true })
</script>

<template>
  <div class="sb-section">
    <div class="sb-label">District Filter</div>
    <div class="multiselect-dropdown ms-dropdown">
      <div class="multiselect-select" @click.stop="showDropdown = !showDropdown">
        <input
          v-if="showDropdown"
          ref="inputRef"
          v-model="search"
          type="text"
          class="ms-inline-input"
          placeholder="Search district…"
          @click.stop
        />
        <span v-else>{{ label }}</span>
        <span class="z-arrow">▼</span>
      </div>
      <div class="multiselect-options" :class="{ open: showDropdown }">
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
</template>
