<script setup>
import { ref, onMounted } from 'vue'
import { FormControl, TabButtons } from 'frappe-ui'

const searchQuery = ref('')
const activeTab = ref('drishti')
const isDark = ref(false)

const tabs = [
  { label: 'Drishti', value: 'drishti' },
  { label: 'MIS Report', value: 'mis-report' },
]

onMounted(() => {
  isDark.value = localStorage.getItem('theme') === 'dark'
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
})

function toggleTheme() {
  isDark.value = !isDark.value
  const theme = isDark.value ? 'dark' : 'light'
  localStorage.setItem('theme', theme)
  document.documentElement.setAttribute('data-theme', theme)
}

const formattedDate = new Date().toLocaleDateString('en-US', {
  month: 'short',
  day: '2-digit',
  year: 'numeric',
})
</script>

<template>
  <div style="display:flex;flex-direction:column;height:100%;">
    <!-- Header -->
    <header class="app-header">
      <div>
        <div class="header-title">DRISHTI ANALYTICS</div>
      </div>
      <div class="header-spacer"></div>
      <div class="search-box">
        <span class="search-icon">⌕</span>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search branch, zone, region…"
        />
      </div>
      <div class="header-date">{{ formattedDate }}</div>
      <button class="visualize-btn" title="Open analytics visualizations">
        <span style="font-size:15px;">◈</span> Visualize
      </button>
      <button class="theme-toggle-btn" @click="toggleTheme" title="Toggle light/dark theme">
        {{ isDark ? '☀️' : '🌙' }}
      </button>
    </header>

    <!-- Content -->
    <div class="content">
      <router-view />
    </div>
  </div>
</template>
