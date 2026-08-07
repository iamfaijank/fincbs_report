<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'

const branchFilter = ref([])
const showDropdown = ref(false)
const search = ref('')
const inputRef = ref(null)
const branchOptions = ref([])

const filteredBranches = computed(() => {
  const q = search.value.toLowerCase()
  const matched = branchOptions.value.filter(b => b.label.toLowerCase().includes(q))
  const selected = matched.filter(b => branchFilter.value.includes(String(b.value)))
  const unselected = matched.filter(b => !branchFilter.value.includes(String(b.value)))
  return [...selected, ...unselected]
})

const allBranchesSelected = computed(() => branchFilter.value.length === branchOptions.value.length)

function toggleBranch(val) {
  const v = String(val)
  const idx = branchFilter.value.indexOf(v)
  if (idx >= 0) {
    branchFilter.value.splice(idx, 1)
  } else {
    branchFilter.value.push(v)
  }
}

function toggleAllBranches() {
  if (allBranchesSelected.value) {
    branchFilter.value = []
  } else {
    branchFilter.value = branchOptions.value.map(b => String(b.value))
  }
}

const label = computed(() => {
  if (branchFilter.value.length === 0) return 'No Branches Selected'
  if (allBranchesSelected.value) return 'All Branches'
  const selected = branchOptions.value.filter(b => branchFilter.value.includes(String(b.value)))
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
  if (opts.length) {
    if (pref && pref.length) {
      branchFilter.value = pref.map(String)
    } else {
      branchFilter.value = opts.map(b => String(b.value))
    }
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
            <input type="checkbox" :value="String(b.value)" :checked="branchFilter.includes(String(b.value))" @change="toggleBranch(b.value)" />
            <span>{{ b.label }}</span>
          </label>
        </div>
        <div v-if="filteredBranches.length === 0" class="ms-empty">No results found</div>
      </div>
    </div>
  </div>
</template>
