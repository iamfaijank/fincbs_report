<script setup>
import { ref, inject, computed, watch, onMounted } from 'vue'
import { frappeRequest } from 'frappe-ui'
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
import ZoneProgressCard from '@/components/tables/ZoneProgressCard.vue'
import ZoneAchievementChart from '@/components/tables/ZoneAchievementChart.vue'
import BranchProfile from '@/components/tables/BranchProfile.vue'

const activeView = inject('activeView')
const searchQuery = inject('searchQuery')
const allTabIds = ['zone','category','product','agent','branch','rd_smbg','daily_acct','casa_ntb','casa_avg','gl_report']
const savedTab = sessionStorage.getItem('drishti-active-tab')
const activeTab = ref(allTabIds.includes(savedTab) ? savedTab : 'zone')

const drishtiTabs = [
  { id: 'zone', label: 'Zone Wise', color: '#065f46' },
  { id: 'category', label: 'Category Wise', color: '#1e40af' },
  { id: 'product', label: 'Product Wise', color: '#5b21b6' },
  { id: 'agent', label: 'Agent Wise', color: '#115e59' },
  { id: 'branch', label: 'Branch Wise', color: '#92400e' },
]

const misTabs = [
  { id: 'rd_smbg', label: 'RD & SMBG Pending', color: '#991b1b' },
  { id: 'daily_acct', label: 'Daily Account Opening', color: '#1e40af' },
  { id: 'casa_ntb', label: 'CASA NTB & EVR', color: '#065f46' },
  { id: 'casa_avg', label: 'CASA Cust Wise AVG Bal', color: '#5b21b6' },
  { id: 'gl_report', label: 'GL. Wise CH Report', color: '#92400e' },
]

const tabs = computed(() => activeView.value === 'drishti' ? drishtiTabs : misTabs)

watch(activeTab, (val) => {
  sessionStorage.setItem('drishti-active-tab', val)
})

watch(activeView, () => {
  const currentTabIds = tabs.value.map(t => t.id)
  if (!currentTabIds.includes(activeTab.value)) {
    activeTab.value = tabs.value[0].id
  }
})

watch(searchQuery, (val) => {
  if (val && val.trim()) {
    activeTab.value = 'branch'
  }
})

const zoneData = ref([])
const months = ref([])

onMounted(async () => {
  try {
    const data = await frappeRequest({
      url: '/api/method/custom_report.www.drishti.get_zone_wise_data',
      method: 'POST',
    }) || {}
    zoneData.value = data.zone_wise || []
    months.value = data.months || []
  } catch (e) {
    console.error('Failed to load zone wise data', e)
  }
})

const activeMonth = computed(() => {
  if (months.value.length === 0) return null
  return months.value[months.value.length - 1]
})

const summaryData = computed(() => {
  const activeKey = activeMonth.value?.key
  let totalBranches = 0
  let totalTarget = 0
  let totalAchievement = 0
  const zones = new Set()

  for (const row of zoneData.value) {
    const zone = row.zone
    if (zone === row.region) {
      zones.add(zone)
      const md = row.months?.[activeKey]
      if (md) {
        totalBranches += md.branches || 0
        totalTarget += md.target || 0
        totalAchievement += md.achievement || 0
      }
    }
  }

  const achPercent = totalTarget > 0 ? Math.round(totalAchievement / totalTarget * 100) : 0
  return { totalBranches, totalTarget, totalAchievement, achPercent, zoneCount: zones.size }
})

function formatCr(val) {
  if (val >= 10000000) return '₹' + (val / 10000000).toFixed(2) + ' Cr'
  if (val >= 100000) return '₹' + (val / 100000).toFixed(2) + ' L'
  return '₹' + val.toLocaleString()
}

const drishtiCards = computed(() => [
  { label: 'Total Branches', value: String(summaryData.value.totalBranches), tag: activeMonth.value?.display || '—', tagColor: 'green' },
  { label: 'Target (MTD)', value: formatCr(summaryData.value.totalTarget), tag: 'Monthly', tagColor: 'amber' },
  { label: 'Achievement', value: formatCr(summaryData.value.totalAchievement), tag: summaryData.value.achPercent + '%', tagColor: 'red' },
  { label: 'Active Zones', value: String(summaryData.value.zoneCount), tag: 'All live', tagColor: 'green' },
])

const selectedBranch = ref(null)

function selectBranch(branch) {
  selectedBranch.value = branch
}

function goBack() {
  selectedBranch.value = null
}
</script>

<template>
  <div class="flex flex-col h-full">
    <div v-if="!selectedBranch" class="flex-shrink-0">
      <SummaryCardGroup v-if="activeView === 'drishti'" :cards="drishtiCards" :cols="4" />

      <div class="mb-4 flex gap-2">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="rounded-lg px-4 py-2 text-xs font-medium transition"
          :class="activeTab === tab.id
            ? 'text-white shadow-sm'
            : 'bg-[var(--bg2)] text-[var(--text)] hover:bg-[var(--bg)]'"
          :style="activeTab === tab.id ? { backgroundColor: tab.color } : {}"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>
    </div>

    <div class="flex-1 min-h-0 overflow-auto">
      <template v-if="!selectedBranch">
        <div v-if="activeView === 'drishti' && activeTab === 'zone'" class="flex gap-4 h-full">
          <div class="flex-1 min-w-0 flex flex-col gap-4 h-full overflow-auto">
            <ZoneWiseTable :zoneData="zoneData" :months="months" />
            <ZoneAchievementChart :zoneData="zoneData" :months="months" />
          </div>
          <div class="flex-shrink-0 w-96 h-full">
            <ZoneProgressCard :zoneData="zoneData" :months="months" />
          </div>
        </div>
        <CategoryWiseTable v-if="activeView === 'drishti' && activeTab === 'category'" />
        <ProductWiseTable v-if="activeView === 'drishti' && activeTab === 'product'" />
        <AgentWiseTable v-if="activeView === 'drishti' && activeTab === 'agent'" />
        <BranchWiseTable v-if="activeView === 'drishti' && activeTab === 'branch'" :searchQuery="searchQuery" @select="selectBranch" />

        <RdSmbgPendingTable v-if="activeView === 'mis' && activeTab === 'rd_smbg'" />
        <DailyAccountTable v-if="activeView === 'mis' && activeTab === 'daily_acct'" />
        <CasaNtbTable v-if="activeView === 'mis' && activeTab === 'casa_ntb'" />
        <CasaAvgTable v-if="activeView === 'mis' && activeTab === 'casa_avg'" />
        <GlReportTable v-if="activeView === 'mis' && activeTab === 'gl_report'" />
      </template>

      <BranchProfile
        v-else
        :branch="selectedBranch"
        :months="months"
        @back="goBack"
      />
    </div>
  </div>
</template>
