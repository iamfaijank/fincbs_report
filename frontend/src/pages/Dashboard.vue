<script setup>
import { ref, inject, computed, watch } from 'vue'
import { useNumberFormat } from '@/composables/useNumberFormat.js'
import { useFilters } from '@/composables/useFilters.js'

const activeView = inject('activeView')
const { formatNumber } = useNumberFormat()
const { zoneFilter, regionFilter, allZonesSelected, allRegionsSelected, isZoneSelected, isRegionSelected } = useFilters()
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

// Expanded zones tracker
const expandedZones = ref(new Set())

// Sample table data grouped by zones
const tableData = ref([
  {
    zone: 'Z-1',
    regions: [
      { region: 'R-1', branches: 42, target: 15678900, ach: 13456780, achPercent: 85.8 },
      { region: 'R-2', branches: 38, target: 14325000, ach: 13234500, achPercent: 92.4 },
      { region: 'R-3', branches: 35, target: 12890000, ach: 10234000, achPercent: 79.4 },
      { region: 'R-4', branches: 28, target: 11234000, ach: 9456000, achPercent: 84.2 },
    ]
  },
  {
    zone: 'Z-2',
    regions: [
      { region: 'R-1', branches: 35, target: 12890000, ach: 9876543, achPercent: 76.6 },
      { region: 'R-2', branches: 41, target: 16750000, ach: 15678900, achPercent: 93.6 },
      { region: 'R-3', branches: 32, target: 13450000, ach: 11234000, achPercent: 83.5 },
      { region: 'R-4', branches: 39, target: 15234000, ach: 13567000, achPercent: 89.1 },
    ]
  },
  {
    zone: 'Z-3',
    regions: [
      { region: 'R-1', branches: 29, target: 9845000, ach: 6734500, achPercent: 68.4 },
      { region: 'R-2', branches: 44, target: 18932000, ach: 16789000, achPercent: 88.7 },
      { region: 'R-3', branches: 31, target: 12567000, ach: 10234000, achPercent: 81.4 },
      { region: 'R-4', branches: 36, target: 14678000, ach: 13123000, achPercent: 89.4 },
    ]
  },
])

// Category table data
const categoryData = ref([
  { category: 'Pinnacle', performanceBand: '>100%', branchCount: 42, movement: '+5', movementDirection: 'up', healthStatus: 'excellent' },
  { category: 'Master', performanceBand: '80–100%', branchCount: 38, movement: '+3', movementDirection: 'up', healthStatus: 'good' },
  { category: 'Accelerator', performanceBand: '60–80%', branchCount: 61, movement: '-2', movementDirection: 'down', healthStatus: 'average' },
  { category: 'Starter', performanceBand: '40–60%', branchCount: 47, movement: '+1', movementDirection: 'up', healthStatus: 'average' },
  { category: 'Learner', performanceBand: '20–40%', branchCount: 28, movement: '-4', movementDirection: 'down', healthStatus: 'poor' },
  { category: 'Zero Level', performanceBand: '0–20%', branchCount: 13, movement: '0', movementDirection: 'neutral', healthStatus: 'critical' },
])

// Product table data - hierarchical: Zone > Region > District/SOL
const productData = ref([
  {
    zone: 'Z-1',
    regions: [
      {
        region: 'R-1',
        sols: [
          { sol: 'DIS-1 / SOL-1001', casa: 15678900, dam: 2345678, dd: 890123, fd: 4567890, rd: 1234567, smbg: 567890, share: 8901234, achievement: 85.8 },
          { sol: 'DIS-1 / SOL-1002', casa: 14325000, dam: 2156789, dd: 789012, fd: 4321098, rd: 1123456, smbg: 456789, share: 8234567, achievement: 92.4 },
        ]
      },
      {
        region: 'R-2',
        sols: [
          { sol: 'DIS-2 / SOL-2001', casa: 12890000, dam: 1987654, dd: 678901, fd: 3987654, rd: 1012345, smbg: 345678, share: 7654321, achievement: 79.4 },
          { sol: 'DIS-2 / SOL-2002', casa: 11234000, dam: 1765432, dd: 567890, fd: 3543210, rd: 901234, smbg: 234567, share: 6543210, achievement: 84.2 },
        ]
      },
    ]
  },
  {
    zone: 'Z-2',
    regions: [
      {
        region: 'R-3',
        sols: [
          { sol: 'DIS-3 / SOL-3001', casa: 12890000, dam: 1654321, dd: 456789, fd: 3210987, rd: 890123, smbg: 123456, share: 5432109, achievement: 76.6 },
          { sol: 'DIS-3 / SOL-3002', casa: 16750000, dam: 2345678, dd: 890123, fd: 4567890, rd: 1345678, smbg: 678901, share: 9012345, achievement: 93.6 },
        ]
      },
    ]
  },
])

// Agent table data - hierarchical: Zone > Region
const agentData = ref([
  {
    zone: 'Z-1',
    regions: [
      { region: 'R-1', ssTarget: 500, ssAchievement: 425, ssShortfall: 75, ssActive: 38, ssInactive: 12, ddTarget: 300, ddAchievement: 270, ddShortfall: 30, ddActive: 28, ddInactive: 5 },
      { region: 'R-2', ssTarget: 450, ssAchievement: 405, ssShortfall: 45, ssActive: 35, ssInactive: 10, ddTarget: 280, ddAchievement: 252, ddShortfall: 28, ddActive: 25, ddInactive: 4 },
      { region: 'R-3', ssTarget: 380, ssAchievement: 304, ssShortfall: 76, ssActive: 30, ssInactive: 8, ddTarget: 220, ddAchievement: 187, ddShortfall: 33, ddActive: 20, ddInactive: 6 },
    ]
  },
  {
    zone: 'Z-2',
    regions: [
      { region: 'R-4', ssTarget: 520, ssAchievement: 494, ssShortfall: 26, ssActive: 42, ssInactive: 8, ddTarget: 310, ddAchievement: 294, ddShortfall: 16, ddActive: 30, ddInactive: 3 },
      { region: 'R-5', ssTarget: 400, ssAchievement: 340, ssShortfall: 60, ssActive: 32, ssInactive: 10, ddTarget: 250, ddAchievement: 212, ddShortfall: 38, ddActive: 22, ddInactive: 7 },
    ]
  },
])

// Branch table data
const branchData = ref([
  { sr: 1, branch: 'ABD-1001', segments: 'SB/CA/ND', category: 'Pinnacle', target: 1567890, julTarget: 522630, ach: 456789, achPercent: 87.4 },
  { sr: 2, branch: 'JHD-1002', segments: 'SB/CA', category: 'Master', target: 1432500, julTarget: 477500, ach: 423456, achPercent: 88.7 },
  { sr: 3, branch: 'PUN-1003', segments: 'SB/CA/FD', category: 'Accelerator', target: 1289000, julTarget: 429667, ach: 345678, achPercent: 80.5 },
  { sr: 4, branch: 'MUM-1004', segments: 'SB/CA/ND/RD', category: 'Pinnacle', target: 1890000, julTarget: 630000, ach: 598765, achPercent: 95.0 },
  { sr: 5, branch: 'DEL-1005', segments: 'SB/CA', category: 'Starter', target: 987650, julTarget: 329217, ach: 234567, achPercent: 71.3 },
  { sr: 6, branch: 'CHN-1006', segments: 'SB/CA/FD/RD', category: 'Master', target: 1654300, julTarget: 551433, ach: 498765, achPercent: 90.6 },
  { sr: 7, branch: 'HYD-1007', segments: 'SB/CA', category: 'Learner', target: 756000, julTarget: 252000, ach: 156789, achPercent: 62.4 },
  { sr: 8, branch: 'KOL-1008', segments: 'SB/CA/ND', category: 'Accelerator', target: 1123400, julTarget: 374467, ach: 298765, achPercent: 79.2 },
])

// Daily Account Opening data - hierarchical: Zone > Region > Branch
const dailyAccountData = ref([
  {
    zone: 'Z-1',
    regions: [
      {
        region: 'R-1',
        branches: [
          { branch: 'ABD-1001', ca: 120, sa: 850, tasc: 35, rd: 420, smbg: 180, dd: 95, fd: 65, totalOpened: 1765 },
          { branch: 'ABD-1002', ca: 95, sa: 720, tasc: 28, rd: 380, smbg: 150, dd: 82, fd: 55, totalOpened: 1510 },
        ]
      },
      {
        region: 'R-2',
        branches: [
          { branch: 'JHD-1001', ca: 110, sa: 780, tasc: 32, rd: 395, smbg: 165, dd: 88, fd: 60, totalOpened: 1630 },
          { branch: 'JHD-1002', ca: 88, sa: 690, tasc: 25, rd: 350, smbg: 140, dd: 75, fd: 48, totalOpened: 1416 },
        ]
      },
    ]
  },
  {
    zone: 'Z-2',
    regions: [
      {
        region: 'R-3',
        branches: [
          { branch: 'PUN-1001', ca: 135, sa: 920, tasc: 40, rd: 450, smbg: 195, dd: 102, fd: 72, totalOpened: 1914 },
          { branch: 'PUN-1002', ca: 105, sa: 810, tasc: 30, rd: 410, smbg: 170, dd: 90, fd: 58, totalOpened: 1673 },
        ]
      },
      {
        region: 'R-4',
        branches: [
          { branch: 'MUM-1001', ca: 150, sa: 980, tasc: 45, rd: 480, smbg: 210, dd: 110, fd: 78, totalOpened: 2053 },
          { branch: 'MUM-1002', ca: 125, sa: 890, tasc: 38, rd: 435, smbg: 185, dd: 98, fd: 68, totalOpened: 1839 },
        ]
      },
    ]
  },
])

// CASA NTB & EVR data
const casaNtbData = ref([
  {
    zone: 'Z-1',
    regions: [
      {
        region: 'R-1',
        branches: [
          { branch: 'ABD-1001', ntb: 45, evr: 32, total: 77 },
          { branch: 'ABD-1002', ntb: 38, evr: 28, total: 66 },
        ]
      },
      {
        region: 'R-2',
        branches: [
          { branch: 'JHD-1001', ntb: 42, evr: 35, total: 77 },
          { branch: 'JHD-1002', ntb: 36, evr: 24, total: 60 },
        ]
      },
    ]
  },
  {
    zone: 'Z-2',
    regions: [
      {
        region: 'R-3',
        branches: [
          { branch: 'PUN-1001', ntb: 52, evr: 38, total: 90 },
          { branch: 'PUN-1002', ntb: 41, evr: 30, total: 71 },
        ]
      },
      {
        region: 'R-4',
        branches: [
          { branch: 'MUM-1001', ntb: 58, evr: 42, total: 100 },
          { branch: 'MUM-1002', ntb: 48, evr: 36, total: 84 },
        ]
      },
    ]
  },
])

// CASA Cust Wise AVG Bal data
const casaAvgData = ref([
  { cifId: 'CIF001', acctName: 'Rajesh Kumar', foracid: '1234567890123', acctOpenDate: '2020-03-15', schema: 'SB', solId: 'SOL001', branch: 'ABD-1001', clsFlag: 'N', clsDate: '', cifOpenDate: '2019-01-10', cifStatus: 'Active', tranDateBal: 125000, clrBalAmt: 120000, depositAmt: 350000, totalWeightedBal: 475000, totalDays: 90, avgBalance: 5278, closingMab: 5100, openingMab: 4800, incMab: 300, status: 'Regular', solGlXfer: 'N', rmId: 'RM001', empName: 'Amit Sharma', division: 'Retail', region: 'R-1', circleOffice: 'Circle A' },
  { cifId: 'CIF002', acctName: 'Priya Patel', foracid: '2345678901234', acctOpenDate: '2019-08-22', schema: 'CA', solId: 'SOL001', branch: 'ABD-1001', clsFlag: 'N', clsDate: '', cifOpenDate: '2018-05-14', cifStatus: 'Active', tranDateBal: 850000, clrBalAmt: 820000, depositAmt: 2100000, totalWeightedBal: 2950000, totalDays: 90, avgBalance: 32778, closingMab: 31500, openingMab: 29800, incMab: 1700, status: 'Premium', solGlXfer: 'N', rmId: 'RM002', empName: 'Neha Gupta', division: 'Retail', region: 'R-1', circleOffice: 'Circle A' },
  { cifId: 'CIF003', acctName: 'Arun Singh', foracid: '3456789012345', acctOpenDate: '2021-01-05', schema: 'SB', solId: 'SOL002', branch: 'ABD-1002', clsFlag: 'N', clsDate: '', cifOpenDate: '2020-11-20', cifStatus: 'Active', tranDateBal: 45000, clrBalAmt: 42000, depositAmt: 180000, totalWeightedBal: 225000, totalDays: 90, avgBalance: 2500, closingMab: 2400, openingMab: 2350, incMab: 50, status: 'Regular', solGlXfer: 'N', rmId: 'RM001', empName: 'Amit Sharma', division: 'Retail', region: 'R-1', circleOffice: 'Circle A' },
  { cifId: 'CIF004', acctName: 'Sunita Devi', foracid: '4567890123456', acctOpenDate: '2018-06-12', schema: 'CA', solId: 'SOL003', branch: 'JHD-1001', clsFlag: 'N', clsDate: '', cifOpenDate: '2017-09-01', cifStatus: 'Active', tranDateBal: 1200000, clrBalAmt: 1150000, depositAmt: 3800000, totalWeightedBal: 5000000, totalDays: 90, avgBalance: 55556, closingMab: 54000, openingMab: 52000, incMab: 2000, status: 'Premium', solGlXfer: 'N', rmId: 'RM003', empName: 'Vikram Joshi', division: 'Retail', region: 'R-2', circleOffice: 'Circle B' },
  { cifId: 'CIF005', acctName: 'Mohammad Ali', foracid: '5678901234567', acctOpenDate: '2022-04-18', schema: 'SB', solId: 'SOL003', branch: 'JHD-1001', clsFlag: 'N', clsDate: '', cifOpenDate: '2021-12-05', cifStatus: 'Active', tranDateBal: 78000, clrBalAmt: 75000, depositAmt: 220000, totalWeightedBal: 298000, totalDays: 90, avgBalance: 3311, closingMab: 3200, openingMab: 3100, incMab: 100, status: 'Regular', solGlXfer: 'N', rmId: 'RM004', empName: 'Priya Reddy', division: 'Retail', region: 'R-2', circleOffice: 'Circle B' },
  { cifId: 'CIF006', acctName: 'Deepak Verma', foracid: '6789012345678', acctOpenDate: '2020-09-25', schema: 'SB', solId: 'SOL004', branch: 'JHD-1002', clsFlag: 'Y', clsDate: '2025-12-31', cifOpenDate: '2020-07-15', cifStatus: 'Closed', tranDateBal: 0, clrBalAmt: 0, depositAmt: 50000, totalWeightedBal: 50000, totalDays: 90, avgBalance: 556, closingMab: 0, openingMab: 500, incMab: -500, status: 'Closed', solGlXfer: 'Y', rmId: 'RM003', empName: 'Vikram Joshi', division: 'Retail', region: 'R-2', circleOffice: 'Circle B' },
  { cifId: 'CIF007', acctName: 'Anita Deshmukh', foracid: '7890123456789', acctOpenDate: '2019-11-08', schema: 'CA', solId: 'SOL005', branch: 'PUN-1001', clsFlag: 'N', clsDate: '', cifOpenDate: '2018-03-22', cifStatus: 'Active', tranDateBal: 2500000, clrBalAmt: 2400000, depositAmt: 8500000, totalWeightedBal: 11000000, totalDays: 90, avgBalance: 122222, closingMab: 118000, openingMab: 115000, incMab: 3000, status: 'Premium', solGlXfer: 'N', rmId: 'RM005', empName: 'Sanjay Kulkarni', division: 'Corporate', region: 'R-3', circleOffice: 'Circle C' },
  { cifId: 'CIF008', acctName: 'Rahul Joshi', foracid: '8901234567890', acctOpenDate: '2023-02-14', schema: 'SB', solId: 'SOL005', branch: 'PUN-1001', clsFlag: 'N', clsDate: '', cifOpenDate: '2022-10-01', cifStatus: 'Active', tranDateBal: 32000, clrBalAmt: 30000, depositAmt: 120000, totalWeightedBal: 152000, totalDays: 90, avgBalance: 1689, closingMab: 1600, openingMab: 1550, incMab: 50, status: 'Regular', solGlXfer: 'N', rmId: 'RM005', empName: 'Sanjay Kulkarni', division: 'Retail', region: 'R-3', circleOffice: 'Circle C' },
])

// GL Wise CH Report data - hierarchical: Zone > Region > District > SOL
const glReportData = ref([
  {
    zone: 'Z-1',
    regions: [
      {
        region: 'R-1',
        districts: [
          {
            district: 'DIS-1',
            sols: [
              { sol: 'SOL001', dam: 125, dd: 45, fd: 32, rd: 18, jllRd: 5, smbg: 22, skbg: 8, taskSilver: 15, taskWealth: 6, savSil: 12, cuGold: 9, cuWealth: 4, share: 7, achievement: 308 },
              { sol: 'SOL002', dam: 98, dd: 38, fd: 28, rd: 15, jllRd: 4, smbg: 18, skbg: 6, taskSilver: 12, taskWealth: 5, savSil: 10, cuGold: 7, cuWealth: 3, share: 6, achievement: 250 },
            ]
          }
        ]
      },
      {
        region: 'R-2',
        districts: [
          {
            district: 'DIS-2',
            sols: [
              { sol: 'SOL003', dam: 112, dd: 42, fd: 30, rd: 16, jllRd: 5, smbg: 20, skbg: 7, taskSilver: 14, taskWealth: 5, savSil: 11, cuGold: 8, cuWealth: 4, share: 7, achievement: 281 },
              { sol: 'SOL004', dam: 88, dd: 35, fd: 25, rd: 14, jllRd: 3, smbg: 16, skbg: 5, taskSilver: 10, taskWealth: 4, savSil: 8, cuGold: 6, cuWealth: 3, share: 5, achievement: 222 },
            ]
          }
        ]
      },
    ]
  },
  {
    zone: 'Z-2',
    regions: [
      {
        region: 'R-3',
        districts: [
          {
            district: 'DIS-3',
            sols: [
              { sol: 'SOL005', dam: 140, dd: 52, fd: 38, rd: 22, jllRd: 6, smbg: 28, skbg: 10, taskSilver: 18, taskWealth: 7, savSil: 15, cuGold: 11, cuWealth: 5, share: 8, achievement: 360 },
              { sol: 'SOL006', dam: 105, dd: 40, fd: 30, rd: 17, jllRd: 4, smbg: 21, skbg: 7, taskSilver: 13, taskWealth: 5, savSil: 11, cuGold: 8, cuWealth: 3, share: 6, achievement: 270 },
            ]
          }
        ]
      },
      {
        region: 'R-4',
        districts: [
          {
            district: 'DIS-4',
            sols: [
              { sol: 'SOL007', dam: 132, dd: 48, fd: 35, rd: 20, jllRd: 6, smbg: 25, skbg: 9, taskSilver: 16, taskWealth: 6, savSil: 14, cuGold: 10, cuWealth: 4, share: 8, achievement: 333 },
              { sol: 'SOL008', dam: 95, dd: 36, fd: 26, rd: 14, jllRd: 4, smbg: 17, skbg: 6, taskSilver: 11, taskWealth: 4, savSil: 9, cuGold: 7, cuWealth: 3, share: 5, achievement: 237 },
            ]
          }
        ]
      },
    ]
  },
])

function getSolTotals(sol) {
  return { dam: sol.dam, dd: sol.dd, fd: sol.fd, rd: sol.rd, jllRd: sol.jllRd, smbg: sol.smbg, skbg: sol.skbg, taskSilver: sol.taskSilver, taskWealth: sol.taskWealth, savSil: sol.savSil, cuGold: sol.cuGold, cuWealth: sol.cuWealth, share: sol.share, achievement: sol.achievement }
}

function sumField(items, field) { return items.reduce((a, b) => a + b[field], 0) }

function getDistrictTotals(district) {
  const s = district.sols
  return { dam: sumField(s, 'dam'), dd: sumField(s, 'dd'), fd: sumField(s, 'fd'), rd: sumField(s, 'rd'), jllRd: sumField(s, 'jllRd'), smbg: sumField(s, 'smbg'), skbg: sumField(s, 'skbg'), taskSilver: sumField(s, 'taskSilver'), taskWealth: sumField(s, 'taskWealth'), savSil: sumField(s, 'savSil'), cuGold: sumField(s, 'cuGold'), cuWealth: sumField(s, 'cuWealth'), share: sumField(s, 'share'), achievement: sumField(s, 'achievement') }
}

function getRegionGlTotals(region) {
  const t = { dam: 0, dd: 0, fd: 0, rd: 0, jllRd: 0, smbg: 0, skbg: 0, taskSilver: 0, taskWealth: 0, savSil: 0, cuGold: 0, cuWealth: 0, share: 0, achievement: 0 }
  region.districts.forEach(d => { const dt = getDistrictTotals(d); Object.keys(t).forEach(k => t[k] += dt[k]) })
  return t
}

function getZoneGlTotals(zone) {
  const t = { dam: 0, dd: 0, fd: 0, rd: 0, jllRd: 0, smbg: 0, skbg: 0, taskSilver: 0, taskWealth: 0, savSil: 0, cuGold: 0, cuWealth: 0, share: 0, achievement: 0 }
  zone.regions.forEach(r => { const rt = getRegionGlTotals(r); Object.keys(t).forEach(k => t[k] += rt[k]) })
  return t
}

// Filtered data based on sidebar zone/region filters - only applies to active tab
const isFilterApplied = computed(() => !allZonesSelected.value || !allRegionsSelected.value)

const filteredTableData = computed(() => {
  if (!isFilterApplied.value || activeTab.value !== 'zone') return tableData.value
  return tableData.value
    .filter(z => isZoneSelected(z.zone))
    .map(z => ({ ...z, regions: z.regions.filter(r => isRegionSelected(r.region)) }))
    .filter(z => z.regions.length > 0)
})

const filteredCategoryData = computed(() => {
  return categoryData.value
})

const filteredProductData = computed(() => {
  if (!isFilterApplied.value || activeTab.value !== 'product') return productData.value
  return productData.value
    .filter(z => isZoneSelected(z.zone))
    .map(z => ({ ...z, regions: z.regions.filter(r => isRegionSelected(r.region)) }))
    .filter(z => z.regions.length > 0)
})

const filteredAgentData = computed(() => {
  if (!isFilterApplied.value || activeTab.value !== 'agent') return agentData.value
  return agentData.value
    .filter(z => isZoneSelected(z.zone))
    .map(z => ({ ...z, regions: z.regions.filter(r => isRegionSelected(r.region)) }))
    .filter(z => z.regions.length > 0)
})

const filteredBranchData = computed(() => {
  return branchData.value
})

const filteredDailyAccountData = computed(() => {
  if (!isFilterApplied.value || activeTab.value !== 'daily_acct') return dailyAccountData.value
  return dailyAccountData.value
    .filter(z => isZoneSelected(z.zone))
    .map(z => ({ ...z, regions: z.regions.filter(r => isRegionSelected(r.region)) }))
    .filter(z => z.regions.length > 0)
})

const filteredCasaNtbData = computed(() => {
  if (!isFilterApplied.value || activeTab.value !== 'casa_ntb') return casaNtbData.value
  return casaNtbData.value
    .filter(z => isZoneSelected(z.zone))
    .map(z => ({ ...z, regions: z.regions.filter(r => isRegionSelected(r.region)) }))
    .filter(z => z.regions.length > 0)
})

const filteredGlReportData = computed(() => {
  if (!isFilterApplied.value || activeTab.value !== 'gl_report') return glReportData.value
  return glReportData.value
    .filter(z => isZoneSelected(z.zone))
    .map(z => ({ ...z, regions: z.regions.filter(r => isRegionSelected(r.region)) }))
    .filter(z => z.regions.length > 0)
})


function toggleZone(zone) {
  if (expandedZones.value.has(zone)) {
    expandedZones.value.delete(zone)
  } else {
    expandedZones.value.add(zone)
  }
}

function isExpanded(zone) {
  return expandedZones.value.has(zone)
}

function getZoneTotals(zoneData) {
  const totals = zoneData.regions.reduce((acc, region) => {
    acc.branches += region.branches
    acc.target += region.target
    acc.ach += region.ach
    return acc
  }, { branches: 0, target: 0, ach: 0 })
  
  totals.achPercent = ((totals.ach / totals.target) * 100).toFixed(1)
  return totals
}

function getCategoryTotals() {
  const total = categoryData.value.reduce((acc, cat) => {
    acc.branchCount += cat.branchCount
    return acc
  }, { branchCount: 0 })
  return total
}

// Product table helpers
const expandedProductZones = ref(new Set())
const expandedProductRegions = ref(new Set())

function toggleProductZone(zone) {
  if (expandedProductZones.value.has(zone)) {
    expandedProductZones.value.delete(zone)
  } else {
    expandedProductZones.value.add(zone)
  }
}

function isProductZoneExpanded(zone) {
  return expandedProductZones.value.has(zone)
}

function toggleProductRegion(key) {
  if (expandedProductRegions.value.has(key)) {
    expandedProductRegions.value.delete(key)
  } else {
    expandedProductRegions.value.add(key)
  }
}

function isProductRegionExpanded(key) {
  return expandedProductRegions.value.has(key)
}

function getProductZoneTotals(zoneData) {
  const totals = { casa: 0, dam: 0, dd: 0, fd: 0, rd: 0, smbg: 0, share: 0, totalAch: 0, totalTarget: 0 }
  zoneData.regions.forEach(region => {
    region.sols.forEach(sol => {
      totals.casa += sol.casa
      totals.dam += sol.dam
      totals.dd += sol.dd
      totals.fd += sol.fd
      totals.rd += sol.rd
      totals.smbg += sol.smbg
      totals.share += sol.share
      totals.totalAch += sol.casa * sol.achievement / 100
      totals.totalTarget += sol.casa
    })
  })
  totals.achievement = totals.totalTarget > 0 ? ((totals.totalAch / totals.totalTarget) * 100).toFixed(1) : 0
  return totals
}

function getProductRegionTotals(regionData) {
  const totals = { casa: 0, dam: 0, dd: 0, fd: 0, rd: 0, smbg: 0, share: 0, totalAch: 0, totalTarget: 0 }
  regionData.sols.forEach(sol => {
    totals.casa += sol.casa
    totals.dam += sol.dam
    totals.dd += sol.dd
    totals.fd += sol.fd
    totals.rd += sol.rd
    totals.smbg += sol.smbg
    totals.share += sol.share
    totals.totalAch += sol.casa * sol.achievement / 100
    totals.totalTarget += sol.casa
  })
  totals.achievement = totals.totalTarget > 0 ? ((totals.totalAch / totals.totalTarget) * 100).toFixed(1) : 0
  return totals
}

// Agent table helpers
const expandedAgentZones = ref(new Set())
const expandedAgentRegions = ref(new Set())

function toggleAgentZone(zone) {
  if (expandedAgentZones.value.has(zone)) {
    expandedAgentZones.value.delete(zone)
  } else {
    expandedAgentZones.value.add(zone)
  }
}

function isAgentZoneExpanded(zone) {
  return expandedAgentZones.value.has(zone)
}

function toggleAgentRegion(key) {
  if (expandedAgentRegions.value.has(key)) {
    expandedAgentRegions.value.delete(key)
  } else {
    expandedAgentRegions.value.add(key)
  }
}

function isAgentRegionExpanded(key) {
  return expandedAgentRegions.value.has(key)
}

function getAgentZoneTotals(zoneData) {
  const t = { ssTarget: 0, ssAchievement: 0, ssShortfall: 0, ssActive: 0, ssInactive: 0, ddTarget: 0, ddAchievement: 0, ddShortfall: 0, ddActive: 0, ddInactive: 0 }
  zoneData.regions.forEach(r => {
    t.ssTarget += r.ssTarget; t.ssAchievement += r.ssAchievement; t.ssShortfall += r.ssShortfall; t.ssActive += r.ssActive; t.ssInactive += r.ssInactive
    t.ddTarget += r.ddTarget; t.ddAchievement += r.ddAchievement; t.ddShortfall += r.ddShortfall; t.ddActive += r.ddActive; t.ddInactive += r.ddInactive
  })
  t.achPercent = t.ssTarget > 0 ? ((t.ssAchievement / t.ssTarget) * 100).toFixed(1) : 0
  return t
}

function getAgentRegionTotals(regionData) {
  const t = { ssTarget: regionData.ssTarget, ssAchievement: regionData.ssAchievement, ssShortfall: regionData.ssShortfall, ssActive: regionData.ssActive, ssInactive: regionData.ssInactive, ddTarget: regionData.ddTarget, ddAchievement: regionData.ddAchievement, ddShortfall: regionData.ddShortfall, ddActive: regionData.ddActive, ddInactive: regionData.ddInactive }
  t.achPercent = t.ssTarget > 0 ? ((t.ssAchievement / t.ssTarget) * 100).toFixed(1) : 0
  return t
}

// Daily Account Opening helpers
const expandedDailyZones = ref(new Set())
const expandedDailyRegions = ref(new Set())

function toggleDailyZone(zone) {
  if (expandedDailyZones.value.has(zone)) {
    expandedDailyZones.value.delete(zone)
  } else {
    expandedDailyZones.value.add(zone)
  }
}

function isDailyZoneExpanded(zone) {
  return expandedDailyZones.value.has(zone)
}

function toggleDailyRegion(key) {
  if (expandedDailyRegions.value.has(key)) {
    expandedDailyRegions.value.delete(key)
  } else {
    expandedDailyRegions.value.add(key)
  }
}

function isDailyRegionExpanded(key) {
  return expandedDailyRegions.value.has(key)
}

function sumBranches(branches, field) {
  return branches.reduce((a, b) => a + b[field], 0)
}

function getDailyRegionTotals(regionData) {
  const b = regionData.branches
  const ca = sumBranches(b, 'ca'), sa = sumBranches(b, 'sa'), tasc = sumBranches(b, 'tasc')
  const rd = sumBranches(b, 'rd'), smbg = sumBranches(b, 'smbg'), dd = sumBranches(b, 'dd'), fd = sumBranches(b, 'fd')
  return { ca, sa, tasc, rd, smbg, dd, fd, branches: b.length, caSaTasc: ca + sa + tasc, rdSmbgDdFd: rd + smbg + dd + fd, totalOpened: sumBranches(b, 'totalOpened') }
}

function getDailyZoneTotals(zoneData) {
  const t = { ca: 0, sa: 0, tasc: 0, rd: 0, smbg: 0, dd: 0, fd: 0, branches: 0, totalOpened: 0 }
  zoneData.regions.forEach(r => {
    const rt = getDailyRegionTotals(r)
    t.ca += rt.ca; t.sa += rt.sa; t.tasc += rt.tasc; t.rd += rt.rd; t.smbg += rt.smbg; t.dd += rt.dd; t.fd += rt.fd
    t.branches += rt.branches; t.totalOpened += rt.totalOpened
  })
  t.caSaTasc = t.ca + t.sa + t.tasc
  t.rdSmbgDdFd = t.rd + t.smbg + t.dd + t.fd
  return t
}

// CASA NTB & EVR helpers
const expandedCasaNtbZones = ref(new Set())
const expandedCasaNtbRegions = ref(new Set())

function toggleCasaNtbZone(zone) {
  if (expandedCasaNtbZones.value.has(zone)) {
    expandedCasaNtbZones.value.delete(zone)
  } else {
    expandedCasaNtbZones.value.add(zone)
  }
}

function isCasaNtbZoneExpanded(zone) {
  return expandedCasaNtbZones.value.has(zone)
}

function toggleCasaNtbRegion(key) {
  if (expandedCasaNtbRegions.value.has(key)) {
    expandedCasaNtbRegions.value.delete(key)
  } else {
    expandedCasaNtbRegions.value.add(key)
  }
}

function isCasaNtbRegionExpanded(key) {
  return expandedCasaNtbRegions.value.has(key)
}

function getCasaNtbRegionTotals(regionData) {
  const b = regionData.branches
  const ntb = b.reduce((a, b) => a + b.ntb, 0)
  const evr = b.reduce((a, b) => a + b.evr, 0)
  return { ntb, evr, branches: b.length, total: ntb + evr }
}

function getCasaNtbZoneTotals(zoneData) {
  const t = { ntb: 0, evr: 0, branches: 0, total: 0 }
  zoneData.regions.forEach(r => {
    const rt = getCasaNtbRegionTotals(r)
    t.ntb += rt.ntb; t.evr += rt.evr; t.branches += rt.branches; t.total += rt.total
  })
  return t
}

// GL Wise CH Report expand/collapse
const expandedGlZones = ref(new Set())
const expandedGlRegions = ref(new Set())
const expandedGlDistricts = ref(new Set())

function toggleGlZone(zone) {
  if (expandedGlZones.value.has(zone)) { expandedGlZones.value.delete(zone) } else { expandedGlZones.value.add(zone) }
}
function isGlZoneExpanded(zone) { return expandedGlZones.value.has(zone) }

function toggleGlRegion(key) {
  if (expandedGlRegions.value.has(key)) { expandedGlRegions.value.delete(key) } else { expandedGlRegions.value.add(key) }
}
function isGlRegionExpanded(key) { return expandedGlRegions.value.has(key) }

function toggleGlDistrict(key) {
  if (expandedGlDistricts.value.has(key)) { expandedGlDistricts.value.delete(key) } else { expandedGlDistricts.value.add(key) }
}
function isGlDistrictExpanded(key) { return expandedGlDistricts.value.has(key) }
</script>

<template>
  <div>
    <!-- Summary Cards - Only in Drishti mode -->
    <div v-if="activeView === 'drishti'" class="mb-4 grid grid-cols-4 gap-3">
      <div class="sb-card">
        <div class="flex items-center justify-between w-full">
          <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
            Total Branches
          </div>
          <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">229</div>
        </div>
        <div class="text-[10px] text-[var(--text3)] flex items-center gap-1">
          <span class="rounded bg-green-50 px-1 py-0.5 text-[9px] font-medium text-green-600 dark:bg-green-900/30 dark:text-green-400">
            +3.2%
          </span>
          <span>vs last month</span>
        </div>
      </div>
      <div class="sb-card">
        <div class="flex items-center justify-between w-full">
          <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
            Target (MTD)
          </div>
          <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">
            <span class="text-xs text-[var(--text3)]">₹</span>163<span class="text-xs text-[var(--text3)]">Cr</span>
          </div>
        </div>
        <div class="text-[10px] text-[var(--text3)] flex items-center gap-1">
          <span class="rounded bg-amber-50 px-1 py-0.5 text-[9px] font-medium text-amber-600 dark:bg-amber-900/30 dark:text-amber-400">
            Monthly
          </span>
          <span>target set</span>
        </div>
      </div>
      <div class="sb-card">
        <div class="flex items-center justify-between w-full">
          <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
            Achievement
          </div>
          <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">
            <span class="text-xs text-[var(--text3)]">₹</span>91.4<span class="text-xs text-[var(--text3)]">Cr</span>
          </div>
        </div>
        <div class="text-[10px] text-[var(--text3)] flex items-center gap-1">
          <span class="rounded bg-red-50 px-1 py-0.5 text-[9px] font-medium text-red-600 dark:bg-red-900/30 dark:text-red-400">
            57.9%
          </span>
          <span>achieved</span>
        </div>
      </div>
      <div class="sb-card">
        <div class="flex items-center justify-between w-full">
          <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">
            Active Zones
          </div>
          <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">6</div>
        </div>
        <div class="text-[10px] text-[var(--text3)] flex items-center gap-1">
          <span class="rounded bg-green-50 px-1 py-0.5 text-[9px] font-medium text-green-600 dark:bg-green-900/30 dark:text-green-400">
            All live
          </span>
          <span>operational</span>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="mb-4 flex items-center gap-0.5 border-b border-[var(--border)]">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="flex items-center gap-1.5 border-b-2 px-4 py-2.5 text-[13px] font-medium transition"
        :class="
          activeTab === tab.id
            ? 'border-green-500 text-green-600'
            : 'border-transparent text-[var(--text3)] hover:text-[var(--text)]'
        "
        @click="activeTab = tab.id"
      >
        <span class="size-1.5 rounded-full" :style="{ backgroundColor: tab.color }" />
        {{ tab.label }}
      </button>
      <div class="flex-1" />
    </div>

    <!-- Table - Only in Drishti mode -->
    <div v-if="activeView === 'drishti' && activeTab === 'zone'" class="sb-card card-table">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-[var(--border)]">
              <th rowspan="2" class="border-r border-[var(--border)] bg-[var(--bg2)] px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Zone/Region
              </th>
              <th rowspan="2" class="border-r border-[var(--border)] bg-[var(--bg2)] px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Branches
              </th>
              <th colspan="3" class="border-b border-[var(--border)] bg-[var(--bg1)] px-5 py-2 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Jul-2026<br/>
                <span class="text-[10px] font-normal">SR % | 14 Working Days Left</span>
              </th>
            </tr>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="border-r border-[var(--border)] px-5 py-2 text-right text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Target
              </th>
              <th class="border-r border-[var(--border)] px-5 py-2 text-right text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Ach
              </th>
              <th class="px-5 py-2 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Ach %
              </th>
            </tr>
          </thead>
          <tbody>
            <template v-for="zoneData in filteredTableData" :key="zoneData.zone">
              <!-- Zone Row (Collapsed shows totals) -->
              <tr
                class="cursor-pointer border-b border-[var(--border)] bg-[var(--bg1)] font-semibold transition hover:bg-[var(--bg2)]"
                @click="toggleZone(zoneData.zone)"
              >
                <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text)]">
                  <div class="flex items-center gap-2">
                    <svg
                      width="14"
                      height="14"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      class="transition-transform"
                      :class="isExpanded(zoneData.zone) ? 'rotate-90' : ''"
                    >
                      <polyline points="9 18 15 12 9 6"></polyline>
                    </svg>
                    {{ zoneData.zone }}
                  </div>
                </td>
                <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text)]">
                  {{ getZoneTotals(zoneData).branches }}
                </td>
                <td class="border-r border-[var(--border)] px-5 py-3 text-right font-mono text-sm text-[var(--text)]">
                  {{ formatNumber(getZoneTotals(zoneData).target) }}
                </td>
                <td class="border-r border-[var(--border)] px-5 py-3 text-right font-mono text-sm text-[var(--text)]">
                  {{ formatNumber(getZoneTotals(zoneData).ach) }}
                </td>
                <td class="px-5 py-3 text-center font-mono text-sm text-[var(--text)]">
                  <span
                    class="inline-block rounded px-2 py-0.5 text-xs font-medium"
                    :class="
                      getZoneTotals(zoneData).achPercent >= 90
                        ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                        : getZoneTotals(zoneData).achPercent >= 75
                        ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400'
                        : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'
                    "
                  >
                    {{ getZoneTotals(zoneData).achPercent }}%
                  </span>
                </td>
              </tr>

              <!-- Region Rows (Expanded) -->
              <template v-if="isExpanded(zoneData.zone)">
                <tr
                  v-for="region in zoneData.regions"
                  :key="`${zoneData.zone}-${region.region}`"
                  class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
                >
                  <td class="border-r border-[var(--border)] px-5 py-3 pl-12 text-sm text-[var(--text3)]">
                    {{ region.region }}
                  </td>
                  <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text)]">
                    {{ region.branches }}
                  </td>
                  <td class="border-r border-[var(--border)] px-5 py-3 text-right font-mono text-sm text-[var(--text)]">
                    {{ formatNumber(region.target) }}
                  </td>
                  <td class="border-r border-[var(--border)] px-5 py-3 text-right font-mono text-sm text-[var(--text)]">
                    {{ formatNumber(region.ach) }}
                  </td>
                  <td class="px-5 py-3 text-center font-mono text-sm text-[var(--text)]">
                    <span
                      class="inline-block rounded px-2 py-0.5 text-xs font-medium"
                      :class="
                        region.achPercent >= 90
                          ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                          : region.achPercent >= 75
                          ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400'
                          : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'
                      "
                    >
                      {{ region.achPercent }}%
                    </span>
                  </td>
                </tr>
              </template>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Category Wise Table - Only in Drishti mode -->
    <div v-if="activeView === 'drishti' && activeTab === 'category'" class="sb-card card-table">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="border-r border-[var(--border)] px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Category
              </th>
              <th class="border-r border-[var(--border)] px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Performance Band
              </th>
              <th class="border-r border-[var(--border)] px-5 py-3 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Branch Count
              </th>
              <th class="border-r border-[var(--border)] px-5 py-3 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Movement (vs Prev. Day)
              </th>
              <th class="px-5 py-3 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Health Status
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, index) in filteredCategoryData"
              :key="index"
              class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
            >
              <td class="border-r border-[var(--border)] px-5 py-3 text-sm font-semibold text-[var(--text)]">
                {{ row.category }}
              </td>
              <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text)]">
                <span class="rounded bg-[var(--bg2)] px-2 py-1 font-mono text-xs">{{ row.performanceBand }}</span>
              </td>
              <td class="border-r border-[var(--border)] px-5 py-3 text-center font-mono text-sm text-[var(--text)]">
                {{ row.branchCount }}
              </td>
              <td class="border-r border-[var(--border)] px-5 py-3 text-center text-sm">
                <span
                  class="inline-flex items-center gap-1 rounded px-2 py-0.5 font-mono text-xs font-medium"
                  :class="
                    row.movementDirection === 'up'
                      ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                      : row.movementDirection === 'down'
                      ? 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'
                      : 'bg-gray-50 text-gray-600 dark:bg-gray-900/30 dark:text-gray-400'
                  "
                >
                  <svg
                    v-if="row.movementDirection === 'up'"
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <polyline points="18 15 12 9 6 15"></polyline>
                  </svg>
                  <svg
                    v-else-if="row.movementDirection === 'down'"
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <polyline points="6 9 12 15 18 9"></polyline>
                  </svg>
                  <svg
                    v-else
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                  </svg>
                  {{ row.movement }}
                </span>
              </td>
              <td class="px-5 py-3 text-center">
                <span
                  class="inline-block rounded-full px-3 py-1 text-xs font-medium"
                  :class="
                    row.healthStatus === 'excellent'
                      ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                      : row.healthStatus === 'good'
                      ? 'bg-teal-50 text-teal-600 dark:bg-teal-900/30 dark:text-teal-400'
                      : row.healthStatus === 'average'
                      ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400'
                      : row.healthStatus === 'poor'
                      ? 'bg-orange-50 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400'
                      : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'
                  "
                >
                  {{ row.healthStatus.charAt(0).toUpperCase() + row.healthStatus.slice(1) }}
                </span>
              </td>
            </tr>
            <!-- Total Row -->
            <tr class="border-t-2 border-[var(--border)] bg-[var(--bg2)] font-semibold">
              <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text)]">
                Total
              </td>
              <td class="border-r border-[var(--border)] px-5 py-3 text-sm text-[var(--text3)]">
                —
              </td>
              <td class="border-r border-[var(--border)] px-5 py-3 text-center font-mono text-sm text-[var(--text)]">
                {{ getCategoryTotals().branchCount }}
              </td>
              <td class="border-r border-[var(--border)] px-5 py-3 text-center text-sm text-[var(--text3)]">
                —
              </td>
              <td class="px-5 py-3 text-center text-sm text-[var(--text3)]">
                —
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Product Wise Table - Only in Drishti mode -->
    <div v-if="activeView === 'drishti' && activeTab === 'product'" class="sb-card card-table">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th rowspan="2" class="border-r border-[var(--border)] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Z/R/DIS/SOL
              </th>
              <th colspan="7" class="border-b border-r border-[var(--border)] px-4 py-2 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                Product Values
              </th>
              <th rowspan="2" class="border-r border-[var(--border)] px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                SHARE
              </th>
              <th rowspan="2" class="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                ACHIEVEMENT
              </th>
            </tr>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">CASA</th>
              <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">DAM</th>
              <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">DD</th>
              <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">FD</th>
              <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">RD</th>
              <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">SMBG</th>
              <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Total</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="zoneData in filteredProductData" :key="zoneData.zone">
              <!-- Zone Row -->
              <tr
                class="cursor-pointer border-b border-[var(--border)] bg-[var(--bg1)] font-semibold transition hover:bg-[var(--bg2)]"
                @click="toggleProductZone(zoneData.zone)"
              >
                <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">
                  <div class="flex items-center gap-2">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="transition-transform" :class="isProductZoneExpanded(zoneData.zone) ? 'rotate-90' : ''">
                      <polyline points="9 18 15 12 9 6"></polyline>
                    </svg>
                    {{ zoneData.zone }}
                  </div>
                </td>
                <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductZoneTotals(zoneData).casa) }}</td>
                <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductZoneTotals(zoneData).dam) }}</td>
                <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductZoneTotals(zoneData).dd) }}</td>
                <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductZoneTotals(zoneData).fd) }}</td>
                <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductZoneTotals(zoneData).rd) }}</td>
                <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductZoneTotals(zoneData).smbg) }}</td>
                <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductZoneTotals(zoneData).casa + getProductZoneTotals(zoneData).dam + getProductZoneTotals(zoneData).dd + getProductZoneTotals(zoneData).fd + getProductZoneTotals(zoneData).rd + getProductZoneTotals(zoneData).smbg) }}</td>
                <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductZoneTotals(zoneData).share) }}</td>
                <td class="px-4 py-3 text-center font-mono text-sm">
                  <span class="inline-block rounded px-2 py-0.5 text-xs font-medium" :class="getProductZoneTotals(zoneData).achievement >= 90 ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400' : getProductZoneTotals(zoneData).achievement >= 75 ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400' : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'">
                    {{ getProductZoneTotals(zoneData).achievement }}%
                  </span>
                </td>
              </tr>

              <!-- Region Rows -->
              <template v-if="isProductZoneExpanded(zoneData.zone)">
                <template v-for="regionData in zoneData.regions" :key="`${zoneData.zone}-${regionData.region}`">
                  <tr
                    class="cursor-pointer border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
                    @click="toggleProductRegion(`${zoneData.zone}-${regionData.region}`)"
                  >
                    <td class="border-r border-[var(--border)] px-4 py-3 pl-12 text-sm text-[var(--text2)]">
                      <div class="flex items-center gap-2">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="transition-transform" :class="isProductRegionExpanded(`${zoneData.zone}-${regionData.region}`) ? 'rotate-90' : ''">
                          <polyline points="9 18 15 12 9 6"></polyline>
                        </svg>
                        {{ regionData.region }}
                      </div>
                    </td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductRegionTotals(regionData).casa) }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductRegionTotals(regionData).dam) }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductRegionTotals(regionData).dd) }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductRegionTotals(regionData).fd) }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductRegionTotals(regionData).rd) }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductRegionTotals(regionData).smbg) }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductRegionTotals(regionData).casa + getProductRegionTotals(regionData).dam + getProductRegionTotals(regionData).dd + getProductRegionTotals(regionData).fd + getProductRegionTotals(regionData).rd + getProductRegionTotals(regionData).smbg) }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getProductRegionTotals(regionData).share) }}</td>
                    <td class="px-4 py-3 text-center font-mono text-sm">
                      <span class="inline-block rounded px-2 py-0.5 text-xs font-medium" :class="getProductRegionTotals(regionData).achievement >= 90 ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400' : getProductRegionTotals(regionData).achievement >= 75 ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400' : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'">
                        {{ getProductRegionTotals(regionData).achievement }}%
                      </span>
                    </td>
                  </tr>

                  <!-- SOL Rows -->
                  <template v-if="isProductRegionExpanded(`${zoneData.zone}-${regionData.region}`)">
                    <tr
                      v-for="(sol, solIdx) in regionData.sols"
                      :key="solIdx"
                      class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
                    >
                      <td class="border-r border-[var(--border)] px-4 py-3 pl-20 text-sm text-[var(--text3)]">
                        {{ sol.sol }}
                      </td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(sol.casa) }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(sol.dam) }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(sol.dd) }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(sol.fd) }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(sol.rd) }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(sol.smbg) }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(sol.casa + sol.dam + sol.dd + sol.fd + sol.rd + sol.smbg) }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(sol.share) }}</td>
                      <td class="px-4 py-3 text-center font-mono text-sm">
                        <span class="inline-block rounded px-2 py-0.5 text-xs font-medium" :class="sol.achievement >= 90 ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400' : sol.achievement >= 75 ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400' : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'">
                          {{ sol.achievement }}%
                        </span>
                      </td>
                    </tr>
                  </template>
                </template>
              </template>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Agent Wise Table - Only in Drishti mode -->
    <div v-if="activeView === 'drishti' && activeTab === 'agent'" class="sb-card card-table">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th rowspan="2" class="border-r border-[var(--border)] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                ZONE/REGION
              </th>
              <th colspan="5" class="border-b border-r border-[var(--border)] px-4 py-2 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                SS
              </th>
              <th colspan="5" class="border-b border-r border-[var(--border)] px-4 py-2 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                DD
              </th>
              <th rowspan="2" class="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                ACH %
              </th>
            </tr>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="border-r border-[var(--border)] px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Target</th>
              <th class="border-r border-[var(--border)] px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Ach</th>
              <th class="border-r border-[var(--border)] px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Shortfall</th>
              <th class="border-r border-[var(--border)] px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Active</th>
              <th class="border-r border-[var(--border)] px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Inactive</th>
              <th class="border-r border-[var(--border)] px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Target</th>
              <th class="border-r border-[var(--border)] px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Ach</th>
              <th class="border-r border-[var(--border)] px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Shortfall</th>
              <th class="border-r border-[var(--border)] px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Active</th>
              <th class="border-r border-[var(--border)] px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Inactive</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="zoneData in filteredAgentData" :key="zoneData.zone">
              <!-- Zone Row -->
              <tr
                class="cursor-pointer border-b border-[var(--border)] bg-[var(--bg1)] font-semibold transition hover:bg-[var(--bg2)]"
                @click="toggleAgentZone(zoneData.zone)"
              >
                <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">
                  <div class="flex items-center gap-2">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="transition-transform" :class="isAgentZoneExpanded(zoneData.zone) ? 'rotate-90' : ''">
                      <polyline points="9 18 15 12 9 6"></polyline>
                    </svg>
                    {{ zoneData.zone }}
                  </div>
                </td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getAgentZoneTotals(zoneData).ssTarget) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getAgentZoneTotals(zoneData).ssAchievement) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getAgentZoneTotals(zoneData).ssShortfall) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getAgentZoneTotals(zoneData).ssActive) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getAgentZoneTotals(zoneData).ssInactive) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getAgentZoneTotals(zoneData).ddTarget) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getAgentZoneTotals(zoneData).ddAchievement) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getAgentZoneTotals(zoneData).ddShortfall) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getAgentZoneTotals(zoneData).ddActive) }}</td>
                <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(getAgentZoneTotals(zoneData).ddInactive) }}</td>
                <td class="px-4 py-3 text-center font-mono text-sm">
                  <span class="inline-block rounded px-2 py-0.5 text-xs font-medium" :class="getAgentZoneTotals(zoneData).achPercent >= 90 ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400' : getAgentZoneTotals(zoneData).achPercent >= 75 ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400' : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'">
                    {{ getAgentZoneTotals(zoneData).achPercent }}%
                  </span>
                </td>
              </tr>

              <!-- Region Rows -->
              <template v-if="isAgentZoneExpanded(zoneData.zone)">
                <tr
                  v-for="regionData in zoneData.regions"
                  :key="`${zoneData.zone}-${regionData.region}`"
                  class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
                >
                  <td class="border-r border-[var(--border)] px-4 py-3 pl-12 text-sm text-[var(--text2)]">
                    {{ regionData.region }}
                  </td>
                  <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ssTarget) }}</td>
                  <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ssAchievement) }}</td>
                  <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ssShortfall) }}</td>
                  <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ssActive) }}</td>
                  <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ssInactive) }}</td>
                  <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ddTarget) }}</td>
                  <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ddAchievement) }}</td>
                  <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ddShortfall) }}</td>
                  <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ddActive) }}</td>
                  <td class="border-r border-[var(--border)] px-3 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(regionData.ddInactive) }}</td>
                  <td class="px-4 py-3 text-center font-mono text-sm">
                    <span class="inline-block rounded px-2 py-0.5 text-xs font-medium" :class="getAgentRegionTotals(regionData).achPercent >= 90 ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400' : getAgentRegionTotals(regionData).achPercent >= 75 ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400' : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'">
                      {{ getAgentRegionTotals(regionData).achPercent }}%
                    </span>
                  </td>
                </tr>
              </template>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Branch Wise Table - Only in Drishti mode -->
    <div v-if="activeView === 'drishti' && activeTab === 'branch'" class="sb-card card-table">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th rowspan="2" class="border-r border-[var(--border)] px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                SR. NO.
              </th>
              <th rowspan="2" class="border-r border-[var(--border)] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                BRANCH
              </th>
              <th rowspan="2" class="border-r border-[var(--border)] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                SEGMENTS
              </th>
              <th colspan="4" class="border-b border-r border-[var(--border)] px-4 py-2 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">
                JUL-2026<br/>
                <span class="text-[10px] font-normal">10 WORKING DAYS LEFT</span>
              </th>
            </tr>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="border-r border-[var(--border)] px-4 py-2 text-center text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">CATEGORY</th>
              <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">TARGET</th>
              <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">ACH</th>
              <th class="border-r border-[var(--border)] px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">ACH %</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in filteredBranchData"
              :key="row.sr"
              class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
            >
              <td class="border-r border-[var(--border)] px-4 py-3 text-center font-mono text-sm text-[var(--text3)]">
                {{ row.sr }}
              </td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-sm font-semibold text-[var(--text)]">
                {{ row.branch }}
              </td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text2)]">
                {{ row.segments }}
              </td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-center">
                <span class="inline-block rounded px-2 py-0.5 text-xs font-medium"
                  :class="
                    row.category === 'Pinnacle' ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                    : row.category === 'Master' ? 'bg-teal-50 text-teal-600 dark:bg-teal-900/30 dark:text-teal-400'
                    : row.category === 'Accelerator' ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400'
                    : row.category === 'Starter' ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400'
                    : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'
                  "
                >
                  {{ row.category }}
                </span>
              </td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">
                {{ formatNumber(row.target) }}
              </td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">
                {{ formatNumber(row.ach) }}
              </td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm">
                <span class="inline-block rounded px-2 py-0.5 text-xs font-medium"
                  :class="
                    row.achPercent >= 90 ? 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                    : row.achPercent >= 75 ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400'
                    : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'
                  "
                >
                  {{ row.achPercent }}%
                </span>
              </td>
            </tr>
            <!-- Total Row -->
            <tr class="border-t-2 border-[var(--border)] bg-[var(--bg2)] font-semibold">
              <td class="border-r border-[var(--border)] px-4 py-3 text-center text-sm text-[var(--text3)]"></td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">Total</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text3)]">—</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-center text-sm text-[var(--text3)]">—</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(branchData.reduce((a, r) => a + r.target, 0)) }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ formatNumber(branchData.reduce((a, r) => a + r.ach, 0)) }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ (branchData.reduce((a, r) => a + r.ach, 0) / branchData.reduce((a, r) => a + r.target, 0) * 100).toFixed(1) }}%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- MIS Reports Tabs Content -->
    <template v-if="activeView === 'mis'">
      <!-- RD & SMBG Pending -->
      <div v-if="activeTab === 'rd_smbg'">
        <!-- Summary Cards -->
        <div class="mb-4 grid grid-cols-5 gap-3">
          <div class="sb-card">
            <div class="flex items-center justify-between w-full">
              <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Total Accounts</div>
              <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">4,27,943</div>
            </div>
          </div>
          <div class="sb-card">
            <div class="flex items-center justify-between w-full">
              <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Total Collection</div>
              <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">₹233.95 Cr</div>
            </div>
          </div>
          <div class="sb-card">
            <div class="flex items-center justify-between w-full">
              <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Pending Accounts</div>
              <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">2,43,415</div>
            </div>
          </div>
          <div class="sb-card">
            <div class="flex items-center justify-between w-full">
              <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Pending Instalments</div>
              <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">13,75,432</div>
            </div>
          </div>
          <div class="sb-card">
            <div class="flex items-center justify-between w-full">
              <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Pending Amount</div>
              <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">₹401.21 Cr</div>
            </div>
          </div>
        </div>

        <!-- Table -->
        <div class="sb-card card-table">
          <div class="overflow-x-auto">
            <table class="w-full">
              <thead>
                <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
                  <th class="border-r border-[var(--border)] px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">SR</th>
                  <th class="border-r border-[var(--border)] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">ZONE/REGION/BRANCH</th>
                  <th class="border-r border-[var(--border)] px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">BRANCHES</th>
                  <th class="border-r border-[var(--border)] px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">TOTAL ACCOUNTS</th>
                  <th class="border-r border-[var(--border)] px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">TOTAL COLLECTION</th>
                  <th class="border-r border-[var(--border)] px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">PENDING ACCOUNTS</th>
                  <th class="border-r border-[var(--border)] px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">PENDING INSTALMENTS</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-[var(--text3)]">PENDING AMOUNT</th>
                </tr>
              </thead>
              <tbody>
                <tr class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]">
                  <td class="border-r border-[var(--border)] px-4 py-3 text-center font-mono text-sm text-[var(--text3)]">1</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-sm font-semibold text-[var(--text)]">Z-1 / R-1 / ABD-1001</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">42</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">52,340</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">₹28.45 Cr</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">28,920</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">1,65,230</td>
                  <td class="px-4 py-3 text-right font-mono text-sm text-[var(--text)]">₹48.76 Cr</td>
                </tr>
                <tr class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]">
                  <td class="border-r border-[var(--border)] px-4 py-3 text-center font-mono text-sm text-[var(--text3)]">2</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-sm font-semibold text-[var(--text)]">Z-1 / R-2 / JHD-1002</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">38</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">48,120</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">₹25.67 Cr</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">24,560</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">1,42,890</td>
                  <td class="px-4 py-3 text-right font-mono text-sm text-[var(--text)]">₹42.34 Cr</td>
                </tr>
                <tr class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]">
                  <td class="border-r border-[var(--border)] px-4 py-3 text-center font-mono text-sm text-[var(--text3)]">3</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-sm font-semibold text-[var(--text)]">Z-2 / R-3 / PUN-1003</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">35</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">45,670</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">₹22.34 Cr</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">22,180</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">1,28,450</td>
                  <td class="px-4 py-3 text-right font-mono text-sm text-[var(--text)]">₹38.92 Cr</td>
                </tr>
                <tr class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]">
                  <td class="border-r border-[var(--border)] px-4 py-3 text-center font-mono text-sm text-[var(--text3)]">4</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-sm font-semibold text-[var(--text)]">Z-2 / R-4 / MUM-1004</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">45</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">58,900</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">₹32.12 Cr</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">31,200</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">1,78,900</td>
                  <td class="px-4 py-3 text-right font-mono text-sm text-[var(--text)]">₹52.45 Cr</td>
                </tr>
                <tr class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]">
                  <td class="border-r border-[var(--border)] px-4 py-3 text-center font-mono text-sm text-[var(--text3)]">5</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-sm font-semibold text-[var(--text)]">Z-3 / R-5 / DEL-1005</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">32</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">42,340</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">₹20.78 Cr</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">19,870</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">1,12,340</td>
                  <td class="px-4 py-3 text-right font-mono text-sm text-[var(--text)]">₹35.67 Cr</td>
                </tr>
                <tr class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]">
                  <td class="border-r border-[var(--border)] px-4 py-3 text-center font-mono text-sm text-[var(--text3)]">6</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-sm font-semibold text-[var(--text)]">Z-3 / R-6 / CHN-1006</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">40</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">50,230</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">₹26.89 Cr</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">26,450</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">1,52,670</td>
                  <td class="px-4 py-3 text-right font-mono text-sm text-[var(--text)]">₹45.23 Cr</td>
                </tr>
                <!-- Total Row -->
                <tr class="border-t-2 border-[var(--border)] bg-[var(--bg2)] font-semibold">
                  <td class="border-r border-[var(--border)] px-4 py-3 text-center text-sm text-[var(--text3)]"></td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">Total</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">232</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">2,97,600</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">₹156.25 Cr</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">1,53,180</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">8,80,480</td>
                  <td class="px-4 py-3 text-right font-mono text-sm text-[var(--text)]">₹263.37 Cr</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Daily Account Opening -->
      <div v-if="activeTab === 'daily_acct'">
        <!-- Summary Cards -->
        <div class="mb-4 grid grid-cols-4 gap-3">
          <div class="sb-card flex items-start justify-between">
            <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">SA ACCOUNTS</div>
            <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">2,942</div>
          </div>
          <div class="sb-card flex items-start justify-between">
            <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">CA ACCOUNTS</div>
            <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">5</div>
          </div>
          <div class="sb-card flex items-start justify-between">
            <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">TASC ACCOUNTS</div>
            <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">10,443</div>
          </div>
          <div class="sb-card flex items-start justify-between">
            <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">RD ACCOUNTS</div>
            <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">6,442</div>
          </div>
        </div>
        <div class="mb-4 grid grid-cols-4 gap-3">
          <div class="sb-card flex items-start justify-between">
            <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">SMBG ACCOUNTS</div>
            <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">5,389</div>
          </div>
          <div class="sb-card flex items-start justify-between">
            <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">DD ACCOUNTS</div>
            <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">3,122</div>
          </div>
          <div class="sb-card flex items-start justify-between">
            <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">FD ACCOUNTS</div>
            <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">8</div>
          </div>
          <div class="sb-card flex items-start justify-between">
            <div class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">TOTAL OPENED</div>
            <div class="font-mono text-lg font-semibold text-[var(--text)] leading-tight">28,351</div>
          </div>
        </div>

        <!-- Table -->
        <div class="sb-card card-table overflow-x-auto">
          <table class="w-full border-collapse text-sm">
            <thead>
              <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
                <th class="border-r border-[var(--border)] px-4 py-2.5 text-center text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)] w-12">SR</th>
                <th class="border-r border-[var(--border)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">ZONE / REGION / BRANCH</th>
                <th class="border-r border-[var(--border)] px-4 py-2.5 text-center text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">BRANCHES</th>
                <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">CA</th>
                <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">SA</th>
                <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">TASC</th>
                <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">RD</th>
                <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">SMBG</th>
                <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">DD</th>
                <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">FD</th>
                <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">CA+SA+TASC</th>
                <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">RD+SMBG+DD+FD</th>
                <th class="px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">TOTAL</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="(zone, zi) in filteredDailyAccountData" :key="zone.zone">
                <!-- Zone row -->
                <tr class="cursor-pointer border-b border-[var(--border)] bg-[var(--bg2)] transition hover:bg-[var(--bg)]"
                    @click="toggleDailyZone(zone.zone)">
                  <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm font-semibold text-[var(--text3)]">{{ zi + 1 }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-2.5 text-sm font-semibold text-[var(--text)]">
                    <span class="mr-2 text-[var(--text3)]">{{ isDailyZoneExpanded(zone.zone) ? '▼' : '▶' }}</span>
                    {{ zone.zone }}
                  </td>
                  <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm font-semibold text-[var(--text)]">{{ getDailyZoneTotals(zone).branches }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getDailyZoneTotals(zone).ca.toLocaleString() }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getDailyZoneTotals(zone).sa.toLocaleString() }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getDailyZoneTotals(zone).tasc.toLocaleString() }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getDailyZoneTotals(zone).rd.toLocaleString() }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getDailyZoneTotals(zone).smbg.toLocaleString() }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getDailyZoneTotals(zone).dd.toLocaleString() }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getDailyZoneTotals(zone).fd.toLocaleString() }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getDailyZoneTotals(zone).caSaTasc.toLocaleString() }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getDailyZoneTotals(zone).rdSmbgDdFd.toLocaleString() }}</td>
                  <td class="px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getDailyZoneTotals(zone).totalOpened.toLocaleString() }}</td>
                </tr>

                <!-- Region rows -->
                <template v-if="isDailyZoneExpanded(zone.zone)">
                  <template v-for="(region, ri) in zone.regions" :key="region.region">
                    <tr class="cursor-pointer border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
                        @click="toggleDailyRegion(zone.zone + '-' + region.region)">
                      <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm text-[var(--text3)]">{{ zi + 1 }}.{{ ri + 1 }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-2.5 pl-8 text-sm font-medium text-[var(--text)]">
                        <span class="mr-2 text-[var(--text3)]">{{ isDailyRegionExpanded(zone.zone + '-' + region.region) ? '▼' : '▶' }}</span>
                        {{ region.region }}
                      </td>
                      <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm text-[var(--text)]">{{ getDailyRegionTotals(region).branches }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getDailyRegionTotals(region).ca.toLocaleString() }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getDailyRegionTotals(region).sa.toLocaleString() }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getDailyRegionTotals(region).tasc.toLocaleString() }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getDailyRegionTotals(region).rd.toLocaleString() }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getDailyRegionTotals(region).smbg.toLocaleString() }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getDailyRegionTotals(region).dd.toLocaleString() }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getDailyRegionTotals(region).fd.toLocaleString() }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getDailyRegionTotals(region).caSaTasc.toLocaleString() }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getDailyRegionTotals(region).rdSmbgDdFd.toLocaleString() }}</td>
                      <td class="px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getDailyRegionTotals(region).totalOpened.toLocaleString() }}</td>
                    </tr>

                    <!-- Branch rows -->
                    <template v-if="isDailyRegionExpanded(zone.zone + '-' + region.region)">
                      <tr v-for="(branch, bi) in region.branches" :key="branch.branch"
                          class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]">
                        <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-xs text-[var(--text3)]">{{ zi + 1 }}.{{ ri + 1 }}.{{ bi + 1 }}</td>
                        <td class="border-r border-[var(--border)] px-4 py-2.5 pl-16 text-sm text-[var(--text)]">{{ branch.branch }}</td>
                        <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm text-[var(--text)]">1</td>
                        <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.ca.toLocaleString() }}</td>
                        <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.sa.toLocaleString() }}</td>
                        <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.tasc.toLocaleString() }}</td>
                        <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.rd.toLocaleString() }}</td>
                        <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.smbg.toLocaleString() }}</td>
                        <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.dd.toLocaleString() }}</td>
                        <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.fd.toLocaleString() }}</td>
                        <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ (branch.ca + branch.sa + branch.tasc).toLocaleString() }}</td>
                        <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ (branch.rd + branch.smbg + branch.dd + branch.fd).toLocaleString() }}</td>
                        <td class="px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.totalOpened.toLocaleString() }}</td>
                      </tr>
                    </template>
                  </template>
                </template>
              </template>
            </tbody>
          </table>
        </div>
      </div>

      <!-- CASA NTB & EVR -->
      <div v-if="activeTab === 'casa_ntb'">
        <div class="sb-card card-table overflow-x-auto">
          <table class="w-full border-collapse text-sm">
            <thead>
              <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
                <th class="border-r border-[var(--border)] px-4 py-2.5 text-center text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)] w-12">SR</th>
                <th class="border-r border-[var(--border)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">ZONE / REGION / BRANCH</th>
                <th class="border-r border-[var(--border)] px-4 py-2.5 text-center text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">BRANCHES</th>
                <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">NTB</th>
                <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">EVR</th>
                <th class="px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">TOTAL</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="(zone, zi) in filteredCasaNtbData" :key="zone.zone">
                <!-- Zone row -->
                <tr class="cursor-pointer border-b border-[var(--border)] bg-[var(--bg2)] transition hover:bg-[var(--bg)]"
                    @click="toggleCasaNtbZone(zone.zone)">
                  <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm font-semibold text-[var(--text3)]">{{ zi + 1 }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-2.5 text-sm font-semibold text-[var(--text)]">
                    <span class="mr-2 text-[var(--text3)]">{{ isCasaNtbZoneExpanded(zone.zone) ? '▼' : '▶' }}</span>
                    {{ zone.zone }}
                  </td>
                  <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm font-semibold text-[var(--text)]">{{ getCasaNtbZoneTotals(zone).branches }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getCasaNtbZoneTotals(zone).ntb }}</td>
                  <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getCasaNtbZoneTotals(zone).evr }}</td>
                  <td class="px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getCasaNtbZoneTotals(zone).total }}</td>
                </tr>

                <!-- Region rows -->
                <template v-if="isCasaNtbZoneExpanded(zone.zone)">
                  <template v-for="(region, ri) in zone.regions" :key="region.region">
                    <tr class="cursor-pointer border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
                        @click="toggleCasaNtbRegion(zone.zone + '-' + region.region)">
                      <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm text-[var(--text3)]">{{ zi + 1 }}.{{ ri + 1 }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-2.5 pl-8 text-sm font-medium text-[var(--text)]">
                        <span class="mr-2 text-[var(--text3)]">{{ isCasaNtbRegionExpanded(zone.zone + '-' + region.region) ? '▼' : '▶' }}</span>
                        {{ region.region }}
                      </td>
                      <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm text-[var(--text)]">{{ getCasaNtbRegionTotals(region).branches }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getCasaNtbRegionTotals(region).ntb }}</td>
                      <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getCasaNtbRegionTotals(region).evr }}</td>
                      <td class="px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getCasaNtbRegionTotals(region).total }}</td>
                    </tr>

                    <!-- Branch rows -->
                    <template v-if="isCasaNtbRegionExpanded(zone.zone + '-' + region.region)">
                      <tr v-for="(branch, bi) in region.branches" :key="branch.branch"
                          class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]">
                        <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-xs text-[var(--text3)]">{{ zi + 1 }}.{{ ri + 1 }}.{{ bi + 1 }}</td>
                        <td class="border-r border-[var(--border)] px-4 py-2.5 pl-16 text-sm text-[var(--text)]">{{ branch.branch }}</td>
                        <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm text-[var(--text)]">1</td>
                        <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.ntb }}</td>
                        <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.evr }}</td>
                        <td class="px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ branch.total }}</td>
                      </tr>
                    </template>
                  </template>
                </template>
              </template>
            </tbody>
          </table>
        </div>
      </div>

      <!-- CASA Cust Wise AVG Bal -->
      <div v-if="activeTab === 'casa_avg'" class="sb-card card-table overflow-x-auto">
        <table class="w-full border-collapse text-sm whitespace-nowrap">
          <thead class="sticky top-0 z-10">
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="sticky left-0 z-20 border-r border-[var(--border)] bg-[var(--bg2)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">CIF ID</th>
              <th class="sticky left-[100px] z-20 border-r border-[var(--border)] bg-[var(--bg2)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Acct Name</th>
              <th class="sticky left-[220px] z-20 border-r border-[var(--border)] bg-[var(--bg2)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Foracid</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Acct Open Date</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Schema</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">SOL ID</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Branch</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Cls Flag</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Cls Date</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">CIF Open Date</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">CIF Status</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Tran Date Bal</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">CLR Bal Amt</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Deposit Amt</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Total Weighted Bal</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Total Days</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Avg Balance</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Closing MAB</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Opening MAB</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Inc MAB</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Status</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">SOL/GL Xfer</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">RM ID</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Emp Name</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Division</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Region</th>
              <th class="px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Circle Office</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in casaAvgData" :key="i"
                class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]">
              <td class="sticky left-0 z-10 border-r border-[var(--border)] bg-[var(--bg)] px-4 py-3 font-mono text-sm text-[var(--text)]">{{ row.cifId }}</td>
              <td class="sticky left-[100px] z-10 border-r border-[var(--border)] bg-[var(--bg)] px-4 py-3 text-sm text-[var(--text)]">{{ row.acctName }}</td>
              <td class="sticky left-[220px] z-10 border-r border-[var(--border)] bg-[var(--bg)] px-4 py-3 font-mono text-sm text-[var(--text)]">{{ row.foracid }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 font-mono text-sm text-[var(--text3)]">{{ row.acctOpenDate }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">{{ row.schema }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 font-mono text-sm text-[var(--text)]">{{ row.solId }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">{{ row.branch }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">{{ row.clsFlag }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 font-mono text-sm text-[var(--text3)]">{{ row.clsDate || '—' }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 font-mono text-sm text-[var(--text3)]">{{ row.cifOpenDate }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">{{ row.cifStatus }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ row.tranDateBal.toLocaleString() }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ row.clrBalAmt.toLocaleString() }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ row.depositAmt.toLocaleString() }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ row.totalWeightedBal.toLocaleString() }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ row.totalDays }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ row.avgBalance.toLocaleString() }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ row.closingMab.toLocaleString() }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ row.openingMab.toLocaleString() }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ row.incMab.toLocaleString() }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">{{ row.status }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">{{ row.solGlXfer }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 font-mono text-sm text-[var(--text)]">{{ row.rmId }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">{{ row.empName }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">{{ row.division }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-sm text-[var(--text)]">{{ row.region }}</td>
              <td class="px-4 py-3 text-sm text-[var(--text)]">{{ row.circleOffice }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- GL. Wise CH Report -->
      <div v-if="activeTab === 'gl_report'" class="sb-card card-table overflow-x-auto">
        <table class="w-full border-collapse text-sm">
          <thead>
            <tr class="border-b border-[var(--border)] bg-[var(--bg2)]">
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-center text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)] w-12">SR</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">Z / R / DIS / SOL</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">DAM</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">DD</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">FD</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">RD</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">JLL RD</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">SMBG</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">SKBG</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">TASK SILVER</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">TASK WEALTH</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">SAV SIL</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">CU GOLD</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">CU WEALTH</th>
              <th class="border-r border-[var(--border)] px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">SHARE</th>
              <th class="px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--text3)]">ACHIEVEMENT</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(zone, zi) in filteredGlReportData" :key="zone.zone">
              <!-- Zone row -->
              <tr class="cursor-pointer border-b border-[var(--border)] bg-[var(--bg2)] transition hover:bg-[var(--bg)]"
                  @click="toggleGlZone(zone.zone)">
                <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm font-semibold text-[var(--text3)]">{{ zi + 1 }}</td>
                <td class="border-r border-[var(--border)] px-4 py-2.5 text-sm font-semibold text-[var(--text)]">
                  <span class="mr-2 text-[var(--text3)]">{{ isGlZoneExpanded(zone.zone) ? '▼' : '▶' }}</span>
                  {{ zone.zone }}
                </td>
                <td v-for="col in ['dam','dd','fd','rd','jllRd','smbg','skbg','taskSilver','taskWealth','savSil','cuGold','cuWealth','share','achievement']"
                    :key="col" class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--text)]">{{ getZoneGlTotals(zone)[col] }}</td>
              </tr>

              <!-- Region rows -->
              <template v-if="isGlZoneExpanded(zone.zone)">
                <template v-for="(region, ri) in zone.regions" :key="region.region">
                  <tr class="cursor-pointer border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
                      @click="toggleGlRegion(zone.zone + '-' + region.region)">
                    <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm text-[var(--text3)]">{{ zi + 1 }}.{{ ri + 1 }}</td>
                    <td class="border-r border-[var(--border)] px-4 py-2.5 pl-8 text-sm font-medium text-[var(--text)]">
                      <span class="mr-2 text-[var(--text3)]">{{ isGlRegionExpanded(zone.zone + '-' + region.region) ? '▼' : '▶' }}</span>
                      {{ region.region }}
                    </td>
                    <td v-for="col in ['dam','dd','fd','rd','jllRd','smbg','skbg','taskSilver','taskWealth','savSil','cuGold','cuWealth','share','achievement']"
                        :key="col" class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getRegionGlTotals(region)[col] }}</td>
                  </tr>

                  <!-- District rows -->
                  <template v-if="isGlRegionExpanded(zone.zone + '-' + region.region)">
                    <template v-for="(district, di) in region.districts" :key="district.district">
                      <tr class="cursor-pointer border-b border-[var(--border)] transition hover:bg-[var(--bg2)]"
                          @click="toggleGlDistrict(zone.zone + '-' + region.region + '-' + district.district)">
                        <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-sm text-[var(--text3)]">{{ zi + 1 }}.{{ ri + 1 }}.{{ di + 1 }}</td>
                        <td class="border-r border-[var(--border)] px-4 py-2.5 pl-16 text-sm font-medium text-[var(--text)]">
                          <span class="mr-2 text-[var(--text3)]">{{ isGlDistrictExpanded(zone.zone + '-' + region.region + '-' + district.district) ? '▼' : '▶' }}</span>
                          {{ district.district }}
                        </td>
                        <td v-for="col in ['dam','dd','fd','rd','jllRd','smbg','skbg','taskSilver','taskWealth','savSil','cuGold','cuWealth','share','achievement']"
                            :key="col" class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ getDistrictTotals(district)[col] }}</td>
                      </tr>

                      <!-- SOL rows -->
                      <template v-if="isGlDistrictExpanded(zone.zone + '-' + region.region + '-' + district.district)">
                        <tr v-for="(sol, si) in district.sols" :key="sol.sol"
                            class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]">
                          <td class="border-r border-[var(--border)] px-4 py-2.5 text-center font-mono text-xs text-[var(--text3)]">{{ zi + 1 }}.{{ ri + 1 }}.{{ di + 1 }}.{{ si + 1 }}</td>
                          <td class="border-r border-[var(--border)] px-4 py-2.5 pl-24 text-sm text-[var(--text)]">{{ sol.sol }}</td>
                          <td v-for="col in ['dam','dd','fd','rd','jllRd','smbg','skbg','taskSilver','taskWealth','savSil','cuGold','cuWealth','share','achievement']"
                              :key="col" class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ sol[col] }}</td>
                        </tr>
                      </template>
                    </template>
                  </template>
                </template>
              </template>
            </template>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>
