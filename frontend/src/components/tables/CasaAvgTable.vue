<script setup>
import { ref } from 'vue'

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
</script>

<template>
  <div class="sb-card card-table overflow-x-auto">
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
</template>
