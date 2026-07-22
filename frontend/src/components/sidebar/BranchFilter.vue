<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'

const branchFilter = ref([])
const showDropdown = ref(false)
const search = ref('')
const inputRef = ref(null)
const branchOptions = ref([])
const initialized = ref(false)

const filteredBranches = computed(() => {
  const q = search.value.toLowerCase()
  return branchOptions.value.filter(b => b.label.toLowerCase().includes(q))
})

const allBranchesSelected = computed(() => branchFilter.value.length === branchOptions.value.length)

function toggleBranch(val) {
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

const label = computed(() => {
  if (branchFilter.value.length === 0) return 'No Branches Selected'
  if (allBranchesSelected.value) return 'All Branches'
  const selected = branchOptions.value.filter(b => branchFilter.value.includes(b.value))
  return `${selected.length} Branches Selected`
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
  options: { type: Array, default: () => [] },
  initialValue: { type: Array, default: () => [] }
})

watch([() => props.options, () => props.initialValue], ([opts, pref]) => {
  branchOptions.value = opts
  if (!initialized.value) {
    if (pref && pref.length) {
      branchFilter.value = [...pref]
    } else {
      branchFilter.value = opts.map(b => b.value)
    }
    initialized.value = true
  }
}, { immediate: true })
</script>

<template>
  <div class="sb-section">
    <div class="sb-label">Branch</div>
    <div class="multiselect-dropdown ms-dropdown">
      <div class="multiselect-select" @click.stop="showDropdown = !showDropdown">
        <input
          v-if="showDropdown"
          ref="inputRef"
          v-model="search"
          type="text"
          class="ms-inline-input"
          placeholder="Search branch…"
          @click.stop
        />
        <span v-else>{{ label }}</span>
        <span class="z-arrow">▼</span>
      </div>
      <div class="multiselect-options" :class="{ open: showDropdown }">
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
</template>
