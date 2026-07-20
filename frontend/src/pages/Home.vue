<script setup>
import { ref } from 'vue'
import { useSidebar } from '@/composables/useSidebar.js'

const { toggleSidebar } = useSidebar()
const searchQuery = ref('')

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
      <button class="collapse-btn" @click="toggleSidebar" title="Toggle Sidebar">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <path d="M9 3v18M16 15l-3-3 3-3"></path>
        </svg>
      </button>

      <div class="header-title-group">
        <div class="header-title">DRISHTI ANALYTICS</div>
        <div class="header-breadcrumb">Dashboard <span>›</span> Zone Wise</div>
      </div>

      <div class="header-spacer"></div>

      <div class="search-box">
        <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"></circle>
          <path d="m21 21-4.3-4.3"></path>
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search branch, zone, region…"
        />
      </div>

      <div class="header-date">{{ formattedDate }}</div>

      <button class="visualize-btn" title="Open analytics visualizations">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
          <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
          <line x1="12" y1="22.08" x2="12" y2="12"></line>
        </svg>
        Visualize
      </button>
    </header>

    <!-- Content -->
    <div class="content">
      <router-view />
    </div>
  </div>
</template>
