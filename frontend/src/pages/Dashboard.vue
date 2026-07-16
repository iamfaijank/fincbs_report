<script setup>
import { ref } from 'vue'

const activeTab = ref('zone')

const tabs = [
  { id: 'zone', label: 'Zone Wise', color: '#4fffb0' },
  { id: 'category', label: 'Category Wise', color: '#0ea5e9' },
  { id: 'product', label: 'Product Wise', color: '#a78bfa' },
  { id: 'agent', label: 'Agent Wise', color: '#2dd4bf' },
  { id: 'branch', label: 'Branch Wise', color: '#f59e0b' },
]
</script>

<template>
  <div>
    <!-- Summary Cards -->
    <div class="mb-4 grid grid-cols-4 gap-3">
      <div class="rounded-lg border border-[var(--border)] bg-[var(--bg2)] px-3 py-2">
        <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
          Total Branches
        </div>
        <div class="font-mono text-lg font-semibold text-[var(--text)]">229</div>
        <div class="text-[10px] text-[var(--text3)]">
          <span class="rounded bg-green-50 px-1 py-0.5 text-[9px] font-medium text-green-600">
            +3.2%
          </span>
          vs last month
        </div>
      </div>
      <div class="rounded-lg border border-[var(--border)] bg-[var(--bg2)] px-3 py-2">
        <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
          Target (MTD)
        </div>
        <div class="font-mono text-lg font-semibold text-[var(--text)]">
          <span class="text-xs text-[var(--text3)]">₹</span>163<span class="text-xs text-[var(--text3)]">Cr</span>
        </div>
        <div class="text-[10px] text-[var(--text3)]">
          <span class="rounded bg-amber-50 px-1 py-0.5 text-[9px] font-medium text-amber-600">
            Monthly
          </span>
          target set
        </div>
      </div>
      <div class="rounded-lg border border-[var(--border)] bg-[var(--bg2)] px-3 py-2">
        <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
          Achievement
        </div>
        <div class="font-mono text-lg font-semibold text-[var(--text)]">
          <span class="text-xs text-[var(--text3)]">₹</span>91.4<span class="text-xs text-[var(--text3)]">Cr</span>
        </div>
        <div class="text-[10px] text-[var(--text3)]">
          <span class="rounded bg-red-50 px-1 py-0.5 text-[9px] font-medium text-red-600">
            57.9%
          </span>
          achieved
        </div>
      </div>
      <div class="rounded-lg border border-[var(--border)] bg-[var(--bg2)] px-3 py-2">
        <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
          Active Zones
        </div>
        <div class="font-mono text-lg font-semibold text-[var(--text)]">6</div>
        <div class="text-[10px] text-[var(--text3)]">
          <span class="rounded bg-green-50 px-1 py-0.5 text-[9px] font-medium text-green-600">
            All live
          </span>
          operational
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="mb-4 flex items-center gap-0.5 border-b border-gray-200">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="flex items-center gap-1.5 border-b-2 px-4 py-2.5 text-[13px] font-medium transition"
        :class="
          activeTab === tab.id
            ? 'border-green-500 text-green-600'
            : 'border-transparent text-gray-500 hover:text-gray-700'
        "
        @click="activeTab = tab.id"
      >
        <span class="size-1.5 rounded-full" :style="{ backgroundColor: tab.color }" />
        {{ tab.label }}
      </button>
      <div class="flex-1" />
      <button
        class="rounded-md border border-gray-200 bg-gray-50 px-3 py-1.5 text-xs text-gray-600 transition hover:bg-gray-100"
      >
        Export CSV
      </button>
    </div>

    <!-- Table Placeholder -->
    <div class="rounded-xl border border-gray-200 bg-white">
      <div class="flex items-center gap-3 border-b border-gray-200 px-5 py-3">
        <span class="text-sm font-semibold text-gray-800">Zone Performance</span>
        <span class="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] font-medium text-gray-500">
          6 zones
        </span>
        <div class="flex-1" />
        <button
          class="rounded-md border border-gray-200 px-3 py-1.5 text-xs text-gray-600 transition hover:bg-gray-50"
        >
          Export
        </button>
      </div>
      <div class="flex items-center justify-center py-16 text-sm text-gray-400">
        Select a space from the sidebar to view analytics
      </div>
    </div>
  </div>
</template>
