<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import { frappeRequest } from 'frappe-ui'
import { useNumberFormat } from '@/composables/useNumberFormat.js'
import { useNameFormat } from '@/composables/useNameFormat.js'
import AchievementBadge from './AchievementBadge.vue'

const props = defineProps({
  branch: { type: Object, required: true },
  months: { type: Array, default: () => [] },
  branchProfile: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['back', 'daily-planning-sheet'])

const { formatNumber } = useNumberFormat()
const { formatZone, formatRegion } = useNameFormat()

const activeMonth = computed(() => props.months.length > 0 ? props.months[props.months.length - 1] : null)
const asOfMonth = computed(() => {
  if (activeMonth.value?.display) return activeMonth.value.display
  if (props.branchProfile?.month) return props.branchProfile.month
  if (props.months.length > 0) return props.months[props.months.length - 1]?.display || ''
  return ''
})

const dailyPlanningSheetUrl = computed(() => {
  const empId = props.branchProfile?.bm_employee_id || props.branchProfile?.bm_id || ''
  const solId = props.branch?.sol_id || props.branchProfile?.sol_id || ''
  const today = new Date().toISOString().split('T')[0]
  const params = new URLSearchParams()
  if (empId) params.set('bm_employee_id', empId)
  if (solId) params.set('sol_id', solId)
  params.set('date', today)
  return `/app/bm-checklist/new-bm-checklist-tcthxsxvlh?${params.toString()}`
})

const currentWeekWorkingDays = computed(() => {
  const now = new Date()
  const currentDay = now.getDay() // 0 = Sun, 1 = Mon, ..., 6 = Sat
  const diffToMonday = currentDay === 0 ? -6 : 1 - currentDay
  const monday = new Date(now)
  monday.setDate(now.getDate() + diffToMonday)

  const days = []
  const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

  for (let i = 0; i < 6; i++) {
    const d = new Date(monday)
    d.setDate(monday.getDate() + i)

    const dayNum = String(d.getDate()).padStart(2, '0')
    const monthStr = monthNames[d.getMonth()]
    const yyyy = d.getFullYear()
    const mm = String(d.getMonth() + 1).padStart(2, '0')
    const isoDate = `${yyyy}-${mm}-${dayNum}`

    const isToday = d.toDateString() === now.toDateString()

    days.push({
      dayName: dayNames[i],
      dateNum: dayNum,
      month: monthStr,
      displayDate: `${dayNames[i]} ${dayNum}`,
      fullDisplay: `${dayNames[i]} ${dayNum} ${monthStr}`,
      isoDate: isoDate,
      isToday: isToday,
    })
  }

  return days
})

const showPlanningModal = ref(false)
const activeView = ref('profile') // 'profile' | 'planning'
const isPlanningLoading = ref(false)
const isPlanningSaving = ref(false)
const planningFeedback = ref({ message: '', type: '' })
const isNewChecklist = ref(true)
const checklistDoc = ref({
  name: '',
  bm_employee_id: '',
  name1: '',
  designation: '',
  sol_id: '',
  date: '',
  table_lqft: []
})
const checklistStatusMap = ref({})

function backToProfile() {
  activeView.value = 'profile'
  fetchChecklistStatus()
}

const completedTasksCount = computed(() => (checklistDoc.value.table_lqft || []).filter(t => t.is_completed).length)
const totalTasksCount = computed(() => (checklistDoc.value.table_lqft || []).length)
const completionProgress = computed(() => totalTasksCount.value > 0 ? Math.round((completedTasksCount.value / totalTasksCount.value) * 100) : 0)

async function fetchChecklistStatus() {
  const empId = props.branchProfile?.bm_employee_id || props.branchProfile?.bm_id || props.branch?.bm_employee_id || ''
  const solId = props.branch?.sol_id || props.branchProfile?.sol_id || ''
  if (!empId && !solId) return

  const week = currentWeekWorkingDays.value
  if (!week || week.length === 0) return
  const startDate = week[0].isoDate
  const endDate = week[week.length - 1].isoDate

  try {
    const res = await fetch(`/api/method/custom_report.custom_report.doctype.bm_checklist.bm_checklist.get_bm_checklist_status_for_week?sol_id=${encodeURIComponent(solId)}&employee_id=${encodeURIComponent(empId)}&start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}`)
      .then(r => r.json())
    const map = (res && res.message) ? res.message : (res || {})
    checklistStatusMap.value = map
  } catch (e) {
    console.error('Failed to fetch checklist status', e)
  }
}

function getDayChipStyle(d) {
  const todayStr = new Date().toISOString().split('T')[0]
  const recordInfo = checklistStatusMap.value[d.isoDate]
  const empId = props.branchProfile?.bm_employee_id || props.branchProfile?.bm_id || props.branch?.bm_employee_id || ''
  const hasRecord = !!(recordInfo?.exists && (!empId || !recordInfo.bm_employee_id || recordInfo.bm_employee_id === empId))

  if (hasRecord) {
    return {
      containerClass: 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 ring-1 ring-inset ring-emerald-500/40 hover:bg-emerald-100 dark:hover:bg-emerald-900/60',
      dayTextClass: 'text-emerald-700 dark:text-emerald-400 font-bold',
      dateTextClass: 'text-emerald-800 dark:text-emerald-200 font-extrabold',
      statusText: 'Completed'
    }
  }

  if (d.isoDate <= todayStr) {
    return {
      containerClass: 'bg-rose-50 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 ring-1 ring-inset ring-rose-500/40 hover:bg-rose-100 dark:hover:bg-rose-900/60',
      dayTextClass: 'text-rose-700 dark:text-rose-400 font-bold',
      dateTextClass: 'text-rose-800 dark:text-rose-200 font-extrabold',
      statusText: 'Pending'
    }
  }

  return {
    containerClass: 'bg-slate-50/60 text-slate-400 dark:bg-slate-900/30 dark:text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800/50',
    dayTextClass: 'text-slate-400 dark:text-slate-500 font-semibold',
    dateTextClass: 'text-slate-500 dark:text-slate-400 font-bold',
    statusText: 'Upcoming'
  }
}

async function loadChecklistDoc(specificDate) {
  const targetDate = specificDate || new Date().toISOString().split('T')[0]
  const empId = props.branchProfile?.bm_employee_id || props.branchProfile?.bm_id || props.branch?.bm_employee_id || ''
  const solId = props.branch?.sol_id || props.branchProfile?.sol_id || ''
  const recordInfo = checklistStatusMap.value[targetDate]
  const recordName = (recordInfo && recordInfo.exists && (!empId || recordInfo.bm_employee_id === empId)) ? recordInfo.name : ''

  isPlanningLoading.value = true
  planningFeedback.value = { message: '', type: '' }

  try {
    const url = `/api/method/custom_report.custom_report.doctype.bm_checklist.bm_checklist.get_bm_checklist_details?name=${encodeURIComponent(recordName)}&employee_id=${encodeURIComponent(empId)}&date=${encodeURIComponent(targetDate)}&sol_id=${encodeURIComponent(solId)}`
    const res = await fetch(url).then(r => r.json())
    const data = res.message || res
    if (data && data.doc) {
      checklistDoc.value = {
        name: data.doc.name || '',
        bm_employee_id: data.doc.bm_employee_id || empId,
        name1: data.doc.name1 || props.branchProfile?.bm_name || '',
        designation: data.doc.designation || props.branchProfile?.bm_designation || 'BRANCH MANAGER',
        sol_id: data.doc.sol_id || solId,
        date: data.doc.date || targetDate,
        table_lqft: (data.doc.table_lqft || []).map(row => ({
          name: row.name || '',
          task: row.task || '',
          is_completed: Boolean(row.is_completed == 1 || row.is_completed === true),
          remark: row.remark || ''
        }))
      }
      isNewChecklist.value = Boolean(data.is_new)
    }
  } catch (e) {
    console.error('Failed to load checklist details', e)
    planningFeedback.value = { message: 'Failed to load checklist details.', type: 'error' }
  } finally {
    isPlanningLoading.value = false
  }
}

async function handleDailyPlanningClick(e, specificDate) {
  if (e) e.preventDefault()
  const targetDate = specificDate || new Date().toISOString().split('T')[0]
  const isInPopup = typeof window !== 'undefined' && (
    window.self !== window.top ||
    window.opener != null ||
    new URLSearchParams(window.location.search).get('popup') === '1'
  )

  if (isInPopup) {
    activeView.value = 'planning'
    await loadChecklistDoc(targetDate)
  } else {
    showPlanningModal.value = true
    await loadChecklistDoc(targetDate)
  }
}

function addTaskRow() {
  checklistDoc.value.table_lqft.push({
    name: '',
    task: '',
    is_completed: false,
    remark: ''
  })
}

function removeTaskRow(idx) {
  checklistDoc.value.table_lqft.splice(idx, 1)
}

async function saveChecklistDoc() {
  isPlanningSaving.value = true
  planningFeedback.value = { message: '', type: '' }

  const payload = {
    name: checklistDoc.value.name,
    bm_employee_id: checklistDoc.value.bm_employee_id,
    name1: checklistDoc.value.name1,
    designation: checklistDoc.value.designation,
    sol_id: checklistDoc.value.sol_id,
    date: checklistDoc.value.date,
    table_lqft: checklistDoc.value.table_lqft.map(t => ({
      name: t.name,
      task: t.task,
      is_completed: t.is_completed ? 1 : 0,
      remark: t.remark
    }))
  }

  try {
    const res = await fetch('/api/method/custom_report.custom_report.doctype.bm_checklist.bm_checklist.save_bm_checklist_doc', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Frappe-CSRF-Token': (window.frappe && window.frappe.csrf_token) || ''
      },
      body: JSON.stringify({ data: payload })
    }).then(r => r.json())

    const data = res.message || res
    if (data && data.status === 'success') {
      checklistDoc.value.name = data.doc.name
      isNewChecklist.value = false
      planningFeedback.value = { message: data.message || 'Saved successfully!', type: 'success' }
      await fetchChecklistStatus()
      setTimeout(() => {
        planningFeedback.value = { message: '', type: '' }
      }, 4000)
    } else {
      planningFeedback.value = { message: data.message || 'Failed to save checklist.', type: 'error' }
    }
  } catch (e) {
    console.error('Save checklist error', e)
    planningFeedback.value = { message: 'Network error while saving checklist.', type: 'error' }
  } finally {
    isPlanningSaving.value = false
  }
}

// Session user's Employee resignation status (Resign / Active)
const employeeStatus = ref('Active')
const relievingInDays = ref(null)
const employeeStatusLabel = computed(() => {
  if (employeeStatus.value === 'Resign' && typeof relievingInDays.value === 'number' && relievingInDays.value > 0) {
    return `Resign (relieving in ${relievingInDays.value} days)`
  }
  return employeeStatus.value
})
const employeeStatusClass = computed(() =>
  employeeStatus.value === 'Resign'
    ? 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'
    : 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400'
)
onMounted(async () => {
  fetchChecklistStatus()
  try {
    const res = await frappeRequest({
      url: '/api/method/custom_report.www.drishti.get_current_user_employee_status',
      method: 'POST',
    })
    if (res && res.status) employeeStatus.value = res.status
    if (res && res.relieving_in_days !== undefined) relievingInDays.value = res.relieving_in_days
  } catch (e) {
    console.error('Failed to load employee status', e)
  }
})

watch(() => [props.branchProfile, props.branch], () => {
  fetchChecklistStatus()
}, { deep: true })

const STATUS_META = {
  improved: { label: 'Improved', class: 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400', icon: 'up' },
  declined: { label: 'Declined', class: 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400', icon: 'down' },
  increased: { label: 'Increased', class: 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400', icon: 'up' },
  decreased: { label: 'Decreased', class: 'bg-orange-50 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400', icon: 'down' },
  unchanged: { label: 'Unchanged', class: 'bg-gray-50 text-gray-600 dark:bg-gray-900/30 dark:text-gray-400', icon: 'flat' },
  new: { label: 'New', class: 'bg-purple-50 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400', icon: 'new' },
}

const CATEGORY_COLORS = {
  Pinnacle: 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400',
  Master: 'bg-teal-50 text-teal-600 dark:bg-teal-900/30 dark:text-teal-400',
  Accelerator: 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
  Starter: 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400',
  Learner: 'bg-orange-50 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400',
  'Zero Level': 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400',
}

function scrollToManpowerDetails() {
  const element = document.getElementById('manpower-details')
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}
</script>

<template>
  <div class="h-full flex flex-col overflow-y-auto">
    <!-- Top breadcrumb bar -->
    <div class="flex items-center gap-2 px-6 py-2.5 bg-[var(--surface)] border-b border-[var(--border)] text-xs text-[var(--text2)] flex-shrink-0">
      <button @click="activeView === 'planning' ? backToProfile() : $emit('back')" class="flex items-center gap-1 hover:text-[var(--text)] transition font-medium">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"></polyline>
        </svg>
        <span>{{ activeView === 'planning' ? 'Branch Profile' : 'Branches' }}</span>
      </button>
      <span class="text-[var(--border)]">/</span>
      <span class="text-sm font-semibold text-[var(--text)]">{{ branch.branch }} ({{ branch.sol_id }})</span>
      <template v-if="activeView === 'planning'">
        <span class="text-[var(--border)]">/</span>
        <span class="text-xs font-bold text-teal-600 dark:text-teal-400">Daily Planning Sheet</span>
      </template>
    </div>

    <!-- Inline Daily Planning Sheet (When branch profile is shown in a popup / switched view) -->
    <div v-if="activeView === 'planning'" class="flex-1 flex flex-col p-5 space-y-4 animate-in fade-in duration-200">
      <div class="flex items-center justify-between p-4 bg-[var(--surface)] border border-[var(--border)] rounded-2xl shadow-sm">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-teal-50 dark:bg-teal-950/60 border border-teal-200 dark:border-teal-800 flex items-center justify-center text-teal-600 dark:text-teal-400 shadow-sm">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h3 class="text-base font-bold text-[var(--text)]">Daily Planning Sheet</h3>
              <span
                class="px-2.5 py-0.5 text-[11px] font-bold rounded-full uppercase tracking-wider"
                :class="isNewChecklist ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300 dark:border-amber-700' : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700'"
              >
                {{ isNewChecklist ? 'New Checklist' : 'Saved Record' }}
              </span>
              <span v-if="checklistDoc.name" class="text-xs text-gray-500 font-mono">
                #{{ checklistDoc.name }}
              </span>
            </div>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              BM Task Planning & Daily Execution Checklist
            </p>
          </div>
        </div>

        <button
          type="button"
          @click="backToProfile"
          class="px-4 py-2 text-xs font-bold rounded-xl text-teal-700 bg-teal-50 dark:bg-teal-950/60 dark:text-teal-300 hover:bg-teal-100 border border-teal-200 dark:border-teal-800 flex items-center gap-1.5 transition cursor-pointer shadow-sm flex-shrink-0"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="19" y1="12" x2="5" y2="12"></line>
            <polyline points="12 19 5 12 12 5"></polyline>
          </svg>
          Back to Branch Profile
        </button>
      </div>

      <!-- Notification Banner -->
      <div
        v-if="planningFeedback.message"
        class="px-4 py-2.5 text-xs font-semibold rounded-xl flex items-center justify-between transition"
        :class="planningFeedback.type === 'success' ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200 border border-emerald-200 dark:border-emerald-800' : 'bg-rose-50 text-rose-800 dark:bg-rose-950 dark:text-rose-200 border border-rose-200 dark:border-rose-800'"
      >
        <div class="flex items-center gap-2">
          <svg v-if="planningFeedback.type === 'success'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
          <span>{{ planningFeedback.message }}</span>
        </div>
        <button @click="planningFeedback.message = ''" class="opacity-60 hover:opacity-100 text-xs font-bold">Dismiss</button>
      </div>

      <!-- Loading or Form Content -->
      <div v-if="isPlanningLoading" class="flex flex-col items-center justify-center py-20 text-gray-400 gap-3">
        <div class="w-8 h-8 border-3 border-teal-500 border-t-transparent rounded-full animate-spin"></div>
        <p class="text-sm font-medium">Loading BM Checklist details...</p>
      </div>

      <div v-else class="space-y-4">
        <!-- Metadata Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-50 dark:bg-gray-800/60 border border-slate-200/80 dark:border-gray-800">
          <div>
            <label class="block text-[11px] font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1">Date</label>
            <input
              type="date"
              v-model="checklistDoc.date"
              class="w-full text-xs font-semibold px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>
          <div>
            <label class="block text-[11px] font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1">BM Employee ID</label>
            <div class="text-xs font-bold text-teal-700 dark:text-teal-400 px-3 py-2 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
              {{ checklistDoc.bm_employee_id || '—' }}
            </div>
          </div>
          <div>
            <label class="block text-[11px] font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1">BM Name</label>
            <div class="text-xs font-semibold text-gray-800 dark:text-gray-200 px-3 py-2 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 truncate" :title="checklistDoc.name1">
              {{ checklistDoc.name1 || '—' }}
            </div>
          </div>
          <div>
            <label class="block text-[11px] font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1">Branch (SOL ID)</label>
            <div class="text-xs font-semibold text-gray-800 dark:text-gray-200 px-3 py-2 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
              {{ branch?.branch || 'Branch' }} ({{ checklistDoc.sol_id || branch?.sol_id }})
            </div>
          </div>
        </div>

        <!-- Progress Section -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-teal-50/50 dark:bg-teal-950/20 border border-teal-100 dark:border-teal-900/50">
          <div class="flex items-center gap-3">
            <div class="text-2xl font-black text-teal-700 dark:text-teal-300">
              {{ completionProgress }}%
            </div>
            <div>
              <div class="text-xs font-bold text-gray-900 dark:text-white">
                Checklist Completion Progress
              </div>
              <div class="text-[11px] text-gray-500 dark:text-gray-400">
                {{ completedTasksCount }} of {{ totalTasksCount }} tasks marked as completed
              </div>
            </div>
          </div>
          <div class="w-full sm:w-48 bg-gray-200 dark:bg-gray-700 h-2.5 rounded-full overflow-hidden">
            <div
              class="h-full bg-teal-600 dark:bg-teal-400 rounded-full transition-all duration-300"
              :style="{ width: `${completionProgress}%` }"
            ></div>
          </div>
        </div>

        <!-- Tasks Table / List -->
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <h4 class="text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300">
                Checklist Tasks
              </h4>
              <span class="px-2 py-0.5 text-[10px] font-extrabold rounded-full bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
                {{ totalTasksCount }}
              </span>
            </div>
            <button
              type="button"
              @click="addTaskRow"
              class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-300 hover:bg-teal-100 dark:hover:bg-teal-900/60 border border-teal-200 dark:border-teal-800 flex items-center gap-1.5 transition cursor-pointer"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
              Add Custom Task
            </button>
          </div>

          <div class="border border-gray-200 dark:border-gray-800 rounded-xl overflow-hidden bg-white dark:bg-gray-900 divide-y divide-gray-100 dark:divide-gray-800">
            <div
              v-for="(t, idx) in checklistDoc.table_lqft"
              :key="idx"
              class="p-3 sm:p-4 flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4 transition"
              :class="t.is_completed ? 'bg-emerald-50/30 dark:bg-emerald-950/10' : 'hover:bg-slate-50/50 dark:hover:bg-gray-800/40'"
            >
              <label class="flex items-center gap-3 cursor-pointer select-none sm:pt-0.5">
                <input
                  type="checkbox"
                  v-model="t.is_completed"
                  class="w-5 h-5 rounded border-gray-300 text-teal-600 focus:ring-teal-500 dark:border-gray-700 dark:bg-gray-800 cursor-pointer"
                />
              </label>

              <div class="flex-1 min-w-0">
                <input
                  v-model="t.task"
                  type="text"
                  placeholder="Task description..."
                  class="w-full text-xs font-semibold bg-transparent border-b border-transparent focus:border-teal-500 focus:bg-white dark:focus:bg-gray-800 px-1 py-1 rounded transition text-gray-800 dark:text-gray-100 focus:outline-none"
                  :class="t.is_completed ? 'line-through text-gray-400 dark:text-gray-500' : ''"
                />
              </div>

              <div class="w-full sm:w-64 flex-shrink-0">
                <input
                  v-model="t.remark"
                  type="text"
                  placeholder="Add note / remark..."
                  class="w-full text-xs px-2.5 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50/60 dark:bg-gray-800/60 text-gray-700 dark:text-gray-200 focus:bg-white dark:focus:bg-gray-900 focus:border-teal-500 focus:outline-none transition"
                />
              </div>

              <button
                type="button"
                @click="removeTaskRow(idx)"
                class="p-1.5 text-gray-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/50 rounded-lg transition self-end sm:self-center"
                title="Remove task"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
              </button>
            </div>

            <div v-if="checklistDoc.table_lqft.length === 0" class="py-8 text-center text-xs text-gray-400">
              No tasks added yet. Click "+ Add Custom Task" above to add your first checklist item.
            </div>
          </div>
        </div>

        <!-- Footer Actions -->
        <div class="p-4 rounded-xl bg-[var(--surface)] border border-[var(--border)] flex items-center justify-between">
          <button
            type="button"
            @click="backToProfile"
            class="px-4 py-2 text-xs font-semibold rounded-xl text-gray-700 dark:text-gray-300 hover:bg-gray-200/70 dark:hover:bg-gray-700 border border-gray-300 dark:border-gray-700 transition cursor-pointer"
          >
            ← Back to Branch Profile
          </button>
          <button
            type="button"
            @click="saveChecklistDoc"
            :disabled="isPlanningSaving || isPlanningLoading"
            class="px-5 py-2 text-xs font-bold rounded-xl bg-teal-600 hover:bg-teal-700 active:scale-95 text-white shadow-md shadow-teal-600/20 flex items-center gap-2 transition cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div v-if="isPlanningSaving" class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>
            <span>{{ isNewChecklist ? 'Create Checklist' : 'Update Checklist' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Main Branch Profile View -->
    <template v-if="activeView === 'profile'">
      <!-- Branch Information Card -->
      <div class="mx-5 my-4 sb-card flex-shrink-0">
      <div class="px-4 py-3 border-b border-[var(--border)] flex items-center justify-between">
        <div class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">Branch Information</div>
        <div class="inline-flex items-stretch rounded-lg overflow-hidden border border-slate-300 dark:border-slate-700 text-xs shadow-sm hover:shadow transition bg-[var(--bg)]">
          <!-- Left side: Every working day date of current week (Mon-Sat) with color variation -->
          <div class="flex items-stretch divide-x divide-slate-200 dark:divide-slate-800">
            <button
              v-for="d in currentWeekWorkingDays"
              :key="d.isoDate"
              type="button"
              @click="handleDailyPlanningClick($event, d.isoDate)"
              class="px-2 py-1 flex flex-col items-center justify-center transition cursor-pointer"
              :class="getDayChipStyle(d).containerClass"
              :title="`${d.fullDisplay} • Status: ${getDayChipStyle(d).statusText}`"
            >
              <span class="text-[9px] uppercase leading-tight tracking-wider" :class="getDayChipStyle(d).dayTextClass">{{ d.dayName }}</span>
              <span class="text-[11px] leading-tight" :class="getDayChipStyle(d).dateTextClass">
                {{ d.dateNum }}
              </span>
            </button>
          </div>
          <!-- Right side: Daily Planning Sheet button -->
          <button
            type="button"
            @click="handleDailyPlanningClick($event)"
            class="px-3.5 py-1.5 font-semibold bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800 transition flex items-center gap-1.5 cursor-pointer border-l border-blue-600/40"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            <span>Daily Planning Sheet</span>
          </button>
        </div>
      </div>
      <div class="px-4 py-4">
        <div class="flex gap-4">
          <!-- Column 1: BM Badge -->
          <div class="flex-shrink-0">
            <span class="inline-flex items-center justify-center w-32 h-32 rounded bg-blue-100 text-blue-600 text-2xl font-bold dark:bg-blue-900/30 dark:text-blue-400">BM</span>
          </div>
          <!-- Column 2: 2 Rows -->
          <div class="flex-1 space-y-3">
            <!-- Row 1: Branch Manager Name -->
            <div>
              <span class="text-sm font-semibold text-[var(--text)]">Branch Manager</span>
              <span class="text-[11px] text-[var(--text3)] ml-2">{{ branchProfile?.bm_name || '—' }}</span>
              <span class="ml-2 inline-flex items-center rounded px-2 py-0.5 text-[10px] font-semibold" :class="employeeStatusClass">{{ employeeStatusLabel }}</span>
            </div>
            <!-- Row 2: 3 Sub-columns -->
            <div class="grid grid-cols-3 gap-4">
              <!-- Sub-column 1: BM Details -->
              <div class="space-y-3">
                <div class="flex gap-2">
                  <span class="text-[11px] font-medium text-[var(--text3)] w-24 shrink-0">BM DOJ</span>
                  <span class="text-[11px] text-[var(--text)]">{{ branchProfile?.bm_doj || '—' }}</span>
                </div>
                <div class="flex gap-2">
                  <span class="text-[11px] font-medium text-[var(--text3)] w-24 shrink-0">BM Vintage</span>
                  <span class="text-[11px] text-[var(--text)]">{{ branchProfile?.bm_vintage || '—' }}</span>
                </div>
                <div class="flex gap-2">
                  <span class="text-[11px] font-medium text-[var(--text3)] w-24 shrink-0">BM Mobile</span>
                  <span class="text-[11px] text-[var(--text)]">{{ branchProfile?.bm_mob_no || '—' }}</span>
                </div>
              </div>
              <!-- Sub-column 2: Branch Details -->
              <div class="space-y-3">
                <div class="flex gap-2">
                  <span class="text-[11px] font-medium text-[var(--text3)] w-24 shrink-0">Branch Opening</span>
                  <span class="text-[11px] text-[var(--text)]">{{ branchProfile?.branch_opening_date || '—' }}</span>
                </div>
                <div class="flex gap-2">
                  <span class="text-[11px] font-medium text-[var(--text3)] w-24 shrink-0">Branch Vintage</span>
                  <span class="text-[11px] text-[var(--text)]">{{ branchProfile?.branch_vintage || '—' }}</span>
                </div>
                <div class="flex gap-2">
                  <span class="text-[11px] font-medium text-[var(--text3)] w-24 shrink-0">Branch Email</span>
                  <span class="text-[11px] text-[var(--text)]">{{ branch.email || branchProfile?.email || '—' }}</span>
                </div>
              </div>
              <!-- Sub-column 3: Reporting Person -->
              <div class="space-y-3">
                <div class="flex gap-2">
                  <span class="text-[11px] font-medium text-[var(--text3)] w-24 shrink-0">Reporting Person</span>
                  <span class="text-[11px] text-[var(--text)]">{{ branchProfile?.ch_name || '—' }}</span>
                </div>
                <div class="flex gap-2">
                  <span class="text-[11px] font-medium text-[var(--text3)] w-24 shrink-0">RP Mobile</span>
                  <span class="text-[11px] text-[var(--text)]">{{ branchProfile?.ch_mob_no || '—' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Three Cards Row -->
    <div class="mx-5 mb-4 grid grid-cols-3 gap-4 flex-shrink-0">
      <!-- Manpower Status Card -->
      <div class="sb-card">
        <div class="px-4 py-3 border-b border-[var(--border)]">
          <div class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">Manpower Status</div>
        </div>
        <div class="px-4 py-4">
          <!-- BDO, BDE, RO Cards in a Row -->
          <div class="grid grid-cols-3 gap-3 mb-4">
            <!-- BDO Card -->
            <div class="rounded border border-[var(--border)] bg-[var(--bg2)] p-3 text-center">
              <div class="text-[10px] font-medium text-[var(--text3)] mb-1">BDO</div>
              <div class="text-lg font-bold text-[var(--text)]">{{ branchProfile?.bdo || '—' }}</div>
            </div>
            <!-- BDE Card -->
            <div class="rounded border border-[var(--border)] bg-[var(--bg2)] p-3 text-center">
              <div class="text-[10px] font-medium text-[var(--text3)] mb-1">BDE</div>
              <div class="text-lg font-bold text-[var(--text)]">{{ branchProfile?.bde || '—' }}</div>
            </div>
            <!-- RO Card -->
            <div class="rounded border border-[var(--border)] bg-[var(--bg2)] p-3 text-center">
              <div class="text-[10px] font-medium text-[var(--text3)] mb-1">RO</div>
              <div class="text-lg font-bold text-[var(--text)]">{{ branchProfile?.ro || '—' }}</div>
            </div>
          </div>
          <!-- Staff Progress Bar -->
          <div>
            <div class="w-full bg-gray-200 rounded-full h-3 dark:bg-gray-700 mb-2">
              <div 
                class="h-3 rounded-full transition-all duration-300"
                :class="(branchProfile?.staff_count || 0) >= (branchProfile?.total_no_of_budgeted_staff || 1) ? 'bg-green-500' : 'bg-amber-500'"
                :style="{ width: Math.min(((branchProfile?.staff_count || 0) / (branchProfile?.total_no_of_budgeted_staff || 1)) * 100, 100) + '%' }"
              ></div>
            </div>
            <div class="flex justify-between items-center mb-2">
              <span class="text-[11px] font-medium text-[var(--text3)]">Budget Staff: {{ branchProfile?.total_no_of_budgeted_staff || '0' }}</span>
              <span class="text-[11px] font-medium text-[var(--text3)]">Staff Count: {{ branchProfile?.staff_count || '0' }}</span>
            </div>
            <div class="text-center">
              <a 
                href="#manpower-details" 
                @click.prevent="scrollToManpowerDetails"
                class="text-[11px] text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 cursor-pointer underline"
              >
                View Detailed Manpower Table
              </a>
            </div>
          </div>
        </div>
      </div>

      <!-- Agent Details Card -->
      <div class="sb-card">
        <div class="px-4 py-3 border-b border-[var(--border)]">
          <div class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">Agent Details</div>
        </div>
        <div class="px-4 py-4">
          <div class="space-y-4">
            <!-- DDS Agents Row -->
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <div class="text-sm font-semibold text-[var(--text)] mb-1">DDS Agents</div>
                <div class="text-[11px] text-[var(--text3)]">
                  Active: {{ branchProfile?.total_active_dds_agent || 0 }} / Total: {{ branchProfile?.total_dds_agent || 0 }}
                </div>
              </div>
              <div class="relative w-16 h-16 flex-shrink-0">
                <svg class="transform -rotate-90" width="64" height="64" viewBox="0 0 64 64">
                  <!-- Background circle -->
                  <circle cx="32" cy="32" r="28" fill="none" stroke="#e5e7eb" stroke-width="6"></circle>
                  <!-- Progress circle -->
                  <circle 
                    cx="32" cy="32" r="28" 
                    fill="none" 
                    stroke="#10b981" 
                    stroke-width="6"
                    stroke-linecap="round"
                    stroke-dasharray="176"
                    :stroke-dashoffset="176 - (176 * ((branchProfile?.total_active_dds_agent || 0) / Math.max(branchProfile?.total_dds_agent || 1, 1)))"
                    class="transition-all duration-300"
                  ></circle>
                </svg>
                <div class="absolute inset-0 flex items-center justify-center">
                  <span class="text-xs font-bold text-[var(--text)]">
                    {{ Math.round(((branchProfile?.total_active_dds_agent || 0) / Math.max(branchProfile?.total_dds_agent || 1, 1)) * 100) }}%
                  </span>
                </div>
              </div>
            </div>

            <!-- SS Agents Row -->
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <div class="text-sm font-semibold text-[var(--text)] mb-1">SS Agents</div>
                <div class="text-[11px] text-[var(--text3)]">
                  Active: {{ branchProfile?.total_active_ss_agent || 0 }} / Total: {{ branchProfile?.total_ss_agent || 0 }}
                </div>
              </div>
              <div class="relative w-16 h-16 flex-shrink-0">
                <svg class="transform -rotate-90" width="64" height="64" viewBox="0 0 64 64">
                  <!-- Background circle -->
                  <circle cx="32" cy="32" r="28" fill="none" stroke="#e5e7eb" stroke-width="6"></circle>
                  <!-- Progress circle -->
                  <circle 
                    cx="32" cy="32" r="28" 
                    fill="none" 
                    stroke="#3b82f6" 
                    stroke-width="6"
                    stroke-linecap="round"
                    stroke-dasharray="176"
                    :stroke-dashoffset="176 - (176 * ((branchProfile?.total_active_ss_agent || 0) / Math.max(branchProfile?.total_ss_agent || 1, 1)))"
                    class="transition-all duration-300"
                  ></circle>
                </svg>
                <div class="absolute inset-0 flex items-center justify-center">
                  <span class="text-xs font-bold text-[var(--text)]">
                    {{ Math.round(((branchProfile?.total_active_ss_agent || 0) / Math.max(branchProfile?.total_ss_agent || 1, 1)) * 100) }}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Category Card -->
      <div class="sb-card">
        <div class="px-4 py-3 border-b border-[var(--border)]">
          <div class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">Category</div>
        </div>
        <div class="px-4 py-4">
          <div class="space-y-2">
            <!-- PINNACLE -->
            <div class="flex items-center justify-between py-1.5 px-2 rounded bg-green-50 dark:bg-green-900/20">
              <span class="text-xs font-semibold text-green-700 dark:text-green-400">PINNACLE</span>
              <span class="text-xs font-medium text-green-600 dark:text-green-500">100%</span>
            </div>
            <!-- MASTER -->
            <div class="flex items-center justify-between py-1.5 px-2 rounded bg-teal-50 dark:bg-teal-900/20">
              <span class="text-xs font-semibold text-teal-700 dark:text-teal-400">MASTER</span>
              <span class="text-xs font-medium text-teal-600 dark:text-teal-500">80-100%</span>
            </div>
            <!-- ACCELERATOR -->
            <div class="flex items-center justify-between py-1.5 px-2 rounded bg-blue-50 dark:bg-blue-900/20">
              <span class="text-xs font-semibold text-blue-700 dark:text-blue-400">ACCELERATOR</span>
              <span class="text-xs font-medium text-blue-600 dark:text-blue-500">65-80%</span>
            </div>
            <!-- STARTER -->
            <div class="flex items-center justify-between py-1.5 px-2 rounded bg-amber-50 dark:bg-amber-900/20">
              <span class="text-xs font-semibold text-amber-700 dark:text-amber-400">STARTER</span>
              <span class="text-xs font-medium text-amber-600 dark:text-amber-500">40-65%</span>
            </div>
            <!-- LEARNER -->
            <div class="flex items-center justify-between py-1.5 px-2 rounded bg-orange-50 dark:bg-orange-900/20">
              <span class="text-xs font-semibold text-orange-700 dark:text-orange-400">LEARNER</span>
              <span class="text-xs font-medium text-orange-600 dark:text-orange-500">20-40%</span>
            </div>
            <!-- ZERO -->
            <div class="flex items-center justify-between py-1.5 px-2 rounded bg-red-50 dark:bg-red-900/20">
              <span class="text-xs font-semibold text-red-700 dark:text-red-400">ZERO</span>
              <span class="text-xs font-medium text-red-600 dark:text-red-500">0-20%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Deposit & Book Position Card -->
    <div class="mx-5 mb-4 sb-card flex-shrink-0">
      <div class="px-4 py-3 border-b border-[var(--border)]">
        <div class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">Deposit & Book Position</div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="px-4 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Account Type</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Book Position</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Composition</th>
            </tr>
          </thead>
          <tbody>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Savings Account (SA)</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.sa_book || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_book ? Math.round((branchProfile?.sa_book || 0) / branchProfile.total_book * 100) : 0 }}%</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Current Account (CA)</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.ca_book || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_book ? Math.round((branchProfile?.ca_book || 0) / branchProfile.total_book * 100) : 0 }}%</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Fixed Deposit (FD)</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.fd_book || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_book ? Math.round((branchProfile?.fd_book || 0) / branchProfile.total_book * 100) : 0 }}%</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Recurring Deposit (RD)</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.rd_book || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_book ? Math.round((branchProfile?.rd_book || 0) / branchProfile.total_book * 100) : 0 }}%</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Daily Deposit Scheme (DDS)</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.dds_book || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_book ? Math.round((branchProfile?.dds_book || 0) / branchProfile.total_book * 100) : 0 }}%</td>
            </tr>
            <tr class="hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">SMBG</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.smbg_book || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_book ? Math.round((branchProfile?.smbg_book || 0) / branchProfile.total_book * 100) : 0 }}%</td>
            </tr>
            <tr class="border-t-2 border-[var(--border)] bg-[var(--bg2)] font-semibold">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Total</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.total_book || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">100%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Account Details Card -->
    <div class="mx-5 mb-4 sb-card flex-shrink-0">
      <div class="px-4 py-3 border-b border-[var(--border)]">
        <div class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">Account Details</div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="px-4 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Category</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Account Count</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Composition</th>
            </tr>
          </thead>
          <tbody>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Savings Account (SA)</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.total_sa_no_of_customers || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_customers_id ? Math.round((branchProfile?.total_sa_no_of_customers || 0) / branchProfile.total_customers_id * 100) : 0 }}%</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Current Account (CA)</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.total_ca_no_of_customers || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_customers_id ? Math.round((branchProfile?.total_ca_no_of_customers || 0) / branchProfile.total_customers_id * 100) : 0 }}%</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Fixed Deposit (FD)</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.total_fd_no_of_customers || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_customers_id ? Math.round((branchProfile?.total_fd_no_of_customers || 0) / branchProfile.total_customers_id * 100) : 0 }}%</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Recurring Deposit (RD)</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.total_rd_no_of_customers || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_customers_id ? Math.round((branchProfile?.total_rd_no_of_customers || 0) / branchProfile.total_customers_id * 100) : 0 }}%</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Daily Deposit Scheme (DDS)</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.total_dds_no_of_customers || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_customers_id ? Math.round((branchProfile?.total_dds_no_of_customers || 0) / branchProfile.total_customers_id * 100) : 0 }}%</td>
            </tr>
            <tr class="hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">SMBG</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.total_smbg_no_of_customers || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ branchProfile?.total_customers_id ? Math.round((branchProfile?.total_smbg_no_of_customers || 0) / branchProfile.total_customers_id * 100) : 0 }}%</td>
            </tr>
            <tr class="border-t-2 border-[var(--border)] bg-[var(--bg2)] font-semibold">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Total</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.total_customers_id || 0) }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">100%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Demand & Collection Performance Card -->
    <div class="mx-5 mb-4 sb-card flex-shrink-0">
      <div class="px-4 py-3 border-b border-[var(--border)]">
        <div class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">Demand & Collection Performance</div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="px-4 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Metric</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Performance</th>
            </tr>
          </thead>
          <tbody>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">DDS Demand</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.dds_demand || 0) }}</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">DDS Collection</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.dds_collection || 0) }}</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">DDS Demand vs Collection</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ branchProfile?.dds_demand_vs_collection || '—' }}</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">SMBG Demand</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.smbg_demand || 0) }}</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">SMBG Collection</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.smbg_collection || 0) }}</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">SMBG Demand vs Collection</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ branchProfile?.smbg_demand_vs_collection || '—' }}</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">RD Demand</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.rd_demand || 0) }}</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">RD Collection</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.rd_collection || 0) }}</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">RD SMBG Collection</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.rd_smbg_collection || 0) }}</td>
            </tr>
            <tr class="hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">RD SMBG Pending</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ formatNumber(branchProfile?.rd_smbg_pending || 0) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Productivity Details Card -->
    <div class="mx-5 mb-4 sb-card flex-shrink-0">
      <div class="px-4 py-3 border-b border-[var(--border)] flex items-center justify-between">
        <div class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">Productivity Details</div>
        <div class="text-[11px] font-medium text-[var(--text3)]">As of: {{ asOfMonth || '—' }}</div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="px-4 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Metric</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Value</th>
            </tr>
          </thead>
          <tbody>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">Total Productivity</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">-</td>
            </tr>
            <tr class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">BDO Productivity</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">-</td>
            </tr>
            <tr class="hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">BDE Productivity</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">-</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Manpower Details Card -->
    <div id="manpower-details" class="mx-5 mb-4 sb-card flex-shrink-0">
      <div class="px-4 py-3 border-b border-[var(--border)]">
        <div class="text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">Manpower Details</div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="px-4 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Employee ID</th>
              <th class="px-4 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Employee Name</th>
              <th class="px-4 py-2 text-center text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Vintage</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Total Leads</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Total Converted</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Conversion Ratio</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Monthly Business</th>
              <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Yearly Business</th>
              <th class="px-4 py-2 text-center text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">PIP Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!branchProfile?.manpower_details || branchProfile.manpower_details.length === 0">
              <td colspan="9" class="px-4 py-3 text-center text-[11px] text-[var(--text3)]">No data available</td>
            </tr>
            <tr v-for="(emp, idx) in branchProfile?.manpower_details || []" :key="idx" class="border-b border-[var(--border)] hover:bg-[var(--bg2)]">
              <td class="px-4 py-3 text-[11px] font-mono text-[var(--text)]">{{ emp.employee_id || '—' }}</td>
              <td class="px-4 py-3 text-[11px] font-medium text-[var(--text)]">{{ emp.employee_name || '—' }}</td>
              <td class="px-4 py-3 text-center text-[11px] text-[var(--text)]">{{ emp.vintage || '—' }}</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ emp.total_leads || '—' }}</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ emp.total_converted || '—' }}</td>
              <td class="px-4 py-3 text-right text-[11px] text-[var(--text)]">{{ emp.conversion_ratio || '—' }}</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ emp.monthly_business || '—' }}</td>
              <td class="px-4 py-3 text-right font-mono text-[11px] text-[var(--text)]">{{ emp.yearly_business || '—' }}</td>
              <td class="px-4 py-3 text-center text-[11px] text-[var(--text)]">{{ emp.pip_status || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Monthly Data Table -->
    <div class="flex-1 overflow-auto">
      <table class="w-full">
        <thead class="sticky top-0 bg-[var(--bg2)]">
          <tr class="border-b border-[var(--border)]">
            <th class="border-r border-[var(--border)] px-4 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
              Month
            </th>
            <th class="border-r border-[var(--border)] px-4 py-2 text-center text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
              Category
            </th>
            <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
              Target
            </th>
            <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
              Achievement
            </th>
            <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
              Ach %
            </th>
            <th class="px-4 py-2 text-center text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
              Status
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="m in months"
            :key="m.key"
            class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
          >
            <td class="border-r border-[var(--border)] px-4 py-3 text-sm font-medium text-[var(--text)]">
              {{ m.display }}
            </td>
            <template v-if="branch.months?.[m.key]">
              <td class="border-r border-[var(--border)] px-4 py-3 text-center">
                <span class="inline-block rounded px-2 py-0.5 text-xs font-medium" :class="CATEGORY_COLORS[branch.months[m.key].category] || ''">
                  {{ branch.months[m.key].category }}
                </span>
              </td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">
                {{ formatNumber(branch.months[m.key].target) }}
              </td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">
                {{ formatNumber(branch.months[m.key].achievement) }}
              </td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm">
                <AchievementBadge :value="branch.months[m.key].percentage" />
              </td>
              <td class="px-4 py-3 text-center">
                <span
                  class="inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium"
                  :class="STATUS_META[branch.months[m.key].status]?.class || ''"
                >
                  <svg v-if="STATUS_META[branch.months[m.key].status]?.icon === 'up'" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="18 15 12 9 6 15"></polyline>
                  </svg>
                  <svg v-else-if="STATUS_META[branch.months[m.key].status]?.icon === 'down'" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="6 9 12 15 18 9"></polyline>
                  </svg>
                  <svg v-else width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                  </svg>
                  {{ STATUS_META[branch.months[m.key].status]?.label || branch.months[m.key].status }}
                </span>
              </td>
            </template>
            <template v-else>
              <td colspan="5" class="px-4 py-3 text-center text-sm text-[var(--text3)]">—</td>
            </template>
          </tr>
        </tbody>
      </table>
    </div>
    </template>

    <!-- Daily Planning Sheet Custom UI Modal (Used in Full-Screen mode) -->
    <div
      v-if="showPlanningModal"
      class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 sm:p-6"
      @click.self="showPlanningModal = false"
    >
      <div class="relative w-full max-w-4xl max-h-[90vh] bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        <!-- Modal Header -->
        <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between bg-slate-50/80 dark:bg-gray-800/80 backdrop-blur-sm flex-shrink-0">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-teal-50 dark:bg-teal-950/60 border border-teal-200 dark:border-teal-800 flex items-center justify-center text-teal-600 dark:text-teal-400 shadow-sm">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h3 class="text-base font-bold text-gray-900 dark:text-white">Daily Planning Sheet</h3>
                <span
                  class="px-2 py-0.5 text-[11px] font-bold rounded-full uppercase tracking-wider"
                  :class="isNewChecklist ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300 dark:border-amber-700' : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700'"
                >
                  {{ isNewChecklist ? 'New Checklist' : 'Saved Record' }}
                </span>
                <span v-if="checklistDoc.name" class="text-xs text-gray-500 font-mono">
                  #{{ checklistDoc.name }}
                </span>
              </div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                BM Task Planning & Daily Execution Checklist
              </p>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <button
              type="button"
              @click="showPlanningModal = false"
              class="w-8 h-8 rounded-lg text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 flex items-center justify-center transition cursor-pointer"
              title="Close"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
        </div>

        <!-- Notification Banner -->
        <div
          v-if="planningFeedback.message"
          class="px-6 py-2.5 text-xs font-semibold flex items-center justify-between transition"
          :class="planningFeedback.type === 'success' ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200 border-b border-emerald-200 dark:border-emerald-800' : 'bg-rose-50 text-rose-800 dark:bg-rose-950 dark:text-rose-200 border-b border-rose-200 dark:border-rose-800'"
        >
          <div class="flex items-center gap-2">
            <svg v-if="planningFeedback.type === 'success'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
            <span>{{ planningFeedback.message }}</span>
          </div>
          <button @click="planningFeedback.message = ''" class="opacity-60 hover:opacity-100 text-xs font-bold">Dismiss</button>
        </div>

        <!-- Modal Body Content -->
        <div class="flex-1 min-h-0 overflow-y-auto p-6 space-y-6">
          <div v-if="isPlanningLoading" class="flex flex-col items-center justify-center py-16 text-gray-400 gap-3">
            <div class="w-8 h-8 border-3 border-teal-500 border-t-transparent rounded-full animate-spin"></div>
            <p class="text-sm font-medium">Loading BM Checklist details...</p>
          </div>

          <template v-else>
            <!-- Top Metadata Grid -->
            <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-50 dark:bg-gray-800/60 border border-slate-200/80 dark:border-gray-800">
              <div>
                <label class="block text-[11px] font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1">Date</label>
                <input
                  type="date"
                  v-model="checklistDoc.date"
                  class="w-full text-xs font-semibold px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>
              <div>
                <label class="block text-[11px] font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1">BM Employee ID</label>
                <div class="text-xs font-bold text-teal-700 dark:text-teal-400 px-3 py-2 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
                  {{ checklistDoc.bm_employee_id || '—' }}
                </div>
              </div>
              <div>
                <label class="block text-[11px] font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1">BM Name</label>
                <div class="text-xs font-semibold text-gray-800 dark:text-gray-200 px-3 py-2 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 truncate" :title="checklistDoc.name1">
                  {{ checklistDoc.name1 || '—' }}
                </div>
              </div>
              <div>
                <label class="block text-[11px] font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1">Branch (SOL ID)</label>
                <div class="text-xs font-semibold text-gray-800 dark:text-gray-200 px-3 py-2 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
                  {{ branch?.branch || 'Branch' }} ({{ checklistDoc.sol_id || branch?.sol_id }})
                </div>
              </div>
            </div>

            <!-- Task Progress Section -->
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-teal-50/50 dark:bg-teal-950/20 border border-teal-100 dark:border-teal-900/50">
              <div class="flex items-center gap-3">
                <div class="text-2xl font-black text-teal-700 dark:text-teal-300">
                  {{ completionProgress }}%
                </div>
                <div>
                  <div class="text-xs font-bold text-gray-900 dark:text-white">
                    Checklist Completion Progress
                  </div>
                  <div class="text-[11px] text-gray-500 dark:text-gray-400">
                    {{ completedTasksCount }} of {{ totalTasksCount }} tasks marked as completed
                  </div>
                </div>
              </div>
              <div class="w-full sm:w-48 bg-gray-200 dark:bg-gray-700 h-2.5 rounded-full overflow-hidden">
                <div
                  class="h-full bg-teal-600 dark:bg-teal-400 rounded-full transition-all duration-300"
                  :style="{ width: `${completionProgress}%` }"
                ></div>
              </div>
            </div>

            <!-- Tasks Table / List -->
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <h4 class="text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300">
                    Checklist Tasks
                  </h4>
                  <span class="px-2 py-0.5 text-[10px] font-extrabold rounded-full bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
                    {{ totalTasksCount }}
                  </span>
                </div>
                <button
                  type="button"
                  @click="addTaskRow"
                  class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-300 hover:bg-teal-100 dark:hover:bg-teal-900/60 border border-teal-200 dark:border-teal-800 flex items-center gap-1.5 transition cursor-pointer"
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                  Add Custom Task
                </button>
              </div>

              <!-- Tasks List Box -->
              <div class="border border-gray-200 dark:border-gray-800 rounded-xl overflow-hidden bg-white dark:bg-gray-900 divide-y divide-gray-100 dark:divide-gray-800">
                <div
                  v-for="(t, idx) in checklistDoc.table_lqft"
                  :key="idx"
                  class="p-3 sm:p-4 flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4 transition"
                  :class="t.is_completed ? 'bg-emerald-50/30 dark:bg-emerald-950/10' : 'hover:bg-slate-50/50 dark:hover:bg-gray-800/40'"
                >
                  <!-- Checkbox -->
                  <label class="flex items-center gap-3 cursor-pointer select-none sm:pt-0.5">
                    <input
                      type="checkbox"
                      v-model="t.is_completed"
                      class="w-5 h-5 rounded border-gray-300 text-teal-600 focus:ring-teal-500 dark:border-gray-700 dark:bg-gray-800 cursor-pointer"
                    />
                  </label>

                  <!-- Task Description -->
                  <div class="flex-1 min-w-0">
                    <input
                      v-model="t.task"
                      type="text"
                      placeholder="Task description..."
                      class="w-full text-xs font-semibold bg-transparent border-b border-transparent focus:border-teal-500 focus:bg-white dark:focus:bg-gray-800 px-1 py-1 rounded transition text-gray-800 dark:text-gray-100 focus:outline-none"
                      :class="t.is_completed ? 'line-through text-gray-400 dark:text-gray-500' : ''"
                    />
                  </div>

                  <!-- Remark Input -->
                  <div class="w-full sm:w-64 flex-shrink-0">
                    <input
                      v-model="t.remark"
                      type="text"
                      placeholder="Add note / remark..."
                      class="w-full text-xs px-2.5 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50/60 dark:bg-gray-800/60 text-gray-700 dark:text-gray-200 focus:bg-white dark:focus:bg-gray-900 focus:border-teal-500 focus:outline-none transition"
                    />
                  </div>

                  <!-- Remove Action -->
                  <button
                    type="button"
                    @click="removeTaskRow(idx)"
                    class="p-1.5 text-gray-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/50 rounded-lg transition self-end sm:self-center"
                    title="Remove task"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                  </button>
                </div>

                <div v-if="checklistDoc.table_lqft.length === 0" class="py-8 text-center text-xs text-gray-400">
                  No tasks added yet. Click "+ Add Custom Task" above to add your first checklist item.
                </div>
              </div>
            </div>
          </template>
        </div>

        <!-- Modal Footer Actions -->
        <div class="px-6 py-4 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between bg-slate-50/80 dark:bg-gray-800/80 backdrop-blur-sm flex-shrink-0">
          <div class="flex items-center gap-2">
            <span class="text-xs text-gray-400">
              {{ isNewChecklist ? 'Create and submit daily planning sheet' : 'Update existing checklist record' }}
            </span>
          </div>

          <div class="flex items-center gap-3">
            <button
              type="button"
              @click="showPlanningModal = false"
              class="px-4 py-2 text-xs font-semibold rounded-xl text-gray-700 dark:text-gray-300 hover:bg-gray-200/70 dark:hover:bg-gray-700 border border-gray-300 dark:border-gray-700 transition cursor-pointer"
            >
              Close
            </button>
            <button
              type="button"
              @click="saveChecklistDoc"
              :disabled="isPlanningSaving || isPlanningLoading"
              class="px-5 py-2 text-xs font-bold rounded-xl bg-teal-600 hover:bg-teal-700 active:scale-95 text-white shadow-md shadow-teal-600/20 flex items-center gap-2 transition cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div v-if="isPlanningSaving" class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>
              <span>{{ isNewChecklist ? 'Create Checklist' : 'Update Checklist' }}</span>
            </button>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>
