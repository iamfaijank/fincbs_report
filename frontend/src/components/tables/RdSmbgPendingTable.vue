<script setup>
import SummaryCardGroup from '@/components/cards/SummaryCardGroup.vue'

const summaryCards = [
  { label: 'Total Accounts', value: '4,27,943' },
  { label: 'Total Collection', value: '₹233.95 Cr' },
  { label: 'Pending Accounts', value: '2,43,415' },
  { label: 'Pending Instalments', value: '13,75,432' },
  { label: 'Pending Amount', value: '₹401.21 Cr' },
]

const tableData = [
  { sr: 1, zone: 'Z-1 / R-1 / ABD-1001', branches: 42, totalAccounts: '52,340', totalCollection: '₹28.45 Cr', pendingAccounts: '28,920', pendingInstalments: '1,65,230', pendingAmount: '₹48.76 Cr' },
  { sr: 2, zone: 'Z-1 / R-2 / JHD-1002', branches: 38, totalAccounts: '48,120', totalCollection: '₹25.67 Cr', pendingAccounts: '24,560', pendingInstalments: '1,42,890', pendingAmount: '₹42.34 Cr' },
  { sr: 3, zone: 'Z-2 / R-3 / PUN-1003', branches: 35, totalAccounts: '45,670', totalCollection: '₹22.34 Cr', pendingAccounts: '22,180', pendingInstalments: '1,28,450', pendingAmount: '₹38.92 Cr' },
  { sr: 4, zone: 'Z-2 / R-4 / MUM-1004', branches: 45, totalAccounts: '58,900', totalCollection: '₹32.12 Cr', pendingAccounts: '31,200', pendingInstalments: '1,78,900', pendingAmount: '₹52.45 Cr' },
  { sr: 5, zone: 'Z-3 / R-5 / DEL-1005', branches: 32, totalAccounts: '42,340', totalCollection: '₹20.78 Cr', pendingAccounts: '19,870', pendingInstalments: '1,12,340', pendingAmount: '₹35.67 Cr' },
  { sr: 6, zone: 'Z-3 / R-6 / CHN-1006', branches: 40, totalAccounts: '50,230', totalCollection: '₹26.89 Cr', pendingAccounts: '26,450', pendingInstalments: '1,52,670', pendingAmount: '₹45.23 Cr' },
]
</script>

<template>
  <div>
    <SummaryCardGroup :cards="summaryCards" :cols="5" />

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
            <tr v-for="row in tableData" :key="row.sr" class="border-b border-[var(--border)] transition hover:bg-[var(--bg2)]">
              <td class="border-r border-[var(--border)] px-4 py-3 text-center font-mono text-sm text-[var(--text3)]">{{ row.sr }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-sm font-semibold text-[var(--text)]">{{ row.zone }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ row.branches }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ row.totalAccounts }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ row.totalCollection }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ row.pendingAccounts }}</td>
              <td class="border-r border-[var(--border)] px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ row.pendingInstalments }}</td>
              <td class="px-4 py-3 text-right font-mono text-sm text-[var(--text)]">{{ row.pendingAmount }}</td>
            </tr>
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
</template>
