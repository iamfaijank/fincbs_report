<script setup>
import { ref } from 'vue'

const props = defineProps({
  viewMode: {
    type: String,
    default: 'table',
    validator: (value) => ['table', 'chart'].includes(value)
  },
  color: {
    type: String,
    default: '#346569'
  }
})

const emit = defineEmits(['update:viewMode'])

const localViewMode = ref(props.viewMode)

function toggleView(mode) {
  localViewMode.value = mode
  emit('update:viewMode', mode)
}
</script>

<template>
  <div 
    class="view-toggle btn-group" 
    role="group" 
    :style="{
      background: '#ffffff',
      padding: '2px',
      borderRadius: '6px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.15)',
      display: 'inline-flex',
      alignItems: 'center',
      gap: '2px'
    }"
  >
    <button
      type="button"
      class="toggle-btn"
      :class="{ active: localViewMode === 'chart' }"
      data-mode="chart"
      @click="toggleView('chart')"
      :style="{
        fontSize: '11px',
        padding: '2px 8px',
        borderRadius: '4px',
        border: 'none',
        fontWeight: '600',
        cursor: 'pointer',
        color: localViewMode === 'chart' ? '#ffffff' : '#475569',
        backgroundColor: localViewMode === 'chart' ? color : 'transparent',
        transition: 'all 0.2s ease',
        display: 'flex',
        alignItems: 'center',
        gap: '4px'
      }"
    >
      <svg
        width="12"
        height="12"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <line x1="18" y1="20" x2="18" y2="10"></line>
        <line x1="12" y1="20" x2="12" y2="4"></line>
        <line x1="6" y1="20" x2="6" y2="14"></line>
      </svg>
      Chart
    </button>
    <button
      type="button"
      class="toggle-btn"
      :class="{ active: localViewMode === 'table' }"
      data-mode="table"
      @click="toggleView('table')"
      :style="{
        fontSize: '11px',
        padding: '2px 8px',
        borderRadius: '4px',
        border: 'none',
        fontWeight: '600',
        cursor: 'pointer',
        color: localViewMode === 'table' ? '#ffffff' : '#475569',
        backgroundColor: localViewMode === 'table' ? color : 'transparent',
        transition: 'all 0.2s ease',
        display: 'flex',
        alignItems: 'center',
        gap: '4px'
      }"
    >
      <svg
        width="12"
        height="12"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"></path>
      </svg>
      Table
    </button>
  </div>
</template>

<style scoped>
.toggle-btn:hover:not(.active) {
  background-color: rgba(0, 0, 0, 0.05) !important;
}
</style>