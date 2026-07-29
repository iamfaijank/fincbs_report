<script setup>
import { ref, inject, computed, watch } from 'vue'
import SummaryCardGroup from '@/components/cards/SummaryCardGroup.vue'
import ZoneWiseTable from '@/components/tables/ZoneWiseTable.vue'
import CategoryWiseTable from '@/components/tables/CategoryWiseTable.vue'
import ProductWiseTable from '@/components/tables/ProductWiseTable.vue'
import AgentWiseTable from '@/components/tables/AgentWiseTable.vue'
import BranchWiseTable from '@/components/tables/BranchWiseTable.vue'
import RdSmbgPendingTable from '@/components/tables/RdSmbgPendingTable.vue'
import DailyAccountTable from '@/components/tables/DailyAccountTable.vue'
import CasaNtbTable from '@/components/tables/CasaNtbTable.vue'
import CasaAvgTable from '@/components/tables/CasaAvgTable.vue'
import GlReportTable from '@/components/tables/GlReportTable.vue'

const activeView = inject('activeView')
const activeTab = ref('zone')

const drishtiTabs = [
  { id: 'zone', label: 'Zone Wise', color: '#4fffb0' },
  { id: 'category', label: 'Category Wise', color: '#0ea5e9' },
  { id: 'product', label: 'Product Wise', color: '#a78bfa' },
  { id: 'agent', label: 'Agent Wise', color: '#2dd4bf' },
  { id: 'branch', label: 'Branch Wise', color: '#f59e0b' },
]

const misTabs = [
  { id: 'rd_smbg', label: 'RD & SMBG Pending', color: '#ef4444' },
  { id: 'daily_acct', label: 'Daily Account Opening', color: '#0ea5e9' },
  { id: 'casa_ntb', label: 'CASA NTB & EVR', color: '#10b981' },
  { id: 'casa_avg', label: 'CASA Cust Wise AVG Bal', color: '#a78bfa' },
  { id: 'gl_report', label: 'GL. Wise CH Report', color: '#f59e0b' },
]

const tabs = computed(() => activeView.value === 'drishti' ? drishtiTabs : misTabs)

watch(activeView, () => {
  activeTab.value = tabs.value[0].id
})

const drishtiCards = [
  { label: 'Total Branches', value: '229', tag: '+3.2%', tagColor: 'green' },
  { label: 'Target (MTD)', value: '₹163 Cr', tag: 'Monthly', tagColor: 'amber' },
  { label: 'Achievement', value: '₹91.4 Cr', tag: '57.9%', tagColor: 'red' },
  { label: 'Active Zones', value: '6', tag: 'All live', tagColor: 'green' },
]
</script>

<template>
  <div>
    <SummaryCardGroup v-if="activeView === 'drishti'" :cards="drishtiCards" :cols="4" />

    <div class="mb-4 flex gap-2">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="rounded-lg px-4 py-2 text-xs font-medium transition"
        :class="activeTab === tab.id
          ? 'text-white shadow-sm'
          : 'bg-[var(--bg2)] text-[var(--text3)] hover:bg-[var(--bg)] hover:text-[var(--text)]'"
        :style="activeTab === tab.id ? { backgroundColor: tab.color } : {}"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <ZoneWiseTable v-if="activeView === 'drishti' && activeTab === 'zone'" />
    <CategoryWiseTable v-if="activeView === 'drishti' && activeTab === 'category'" />
    <ProductWiseTable v-if="activeView === 'drishti' && activeTab === 'product'" />
    <AgentWiseTable v-if="activeView === 'drishti' && activeTab === 'agent'" />
    <BranchWiseTable v-if="activeView === 'drishti' && activeTab === 'branch'" />

    <RdSmbgPendingTable v-if="activeView === 'mis' && activeTab === 'rd_smbg'" />
    <DailyAccountTable v-if="activeView === 'mis' && activeTab === 'daily_acct'" />
    <CasaNtbTable v-if="activeView === 'mis' && activeTab === 'casa_ntb'" />
    <CasaAvgTable v-if="activeView === 'mis' && activeTab === 'casa_avg'" />
    <GlReportTable v-if="activeView === 'mis' && activeTab === 'gl_report'" />
  </div>
</template>
