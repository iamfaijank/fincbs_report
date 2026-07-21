import { ref } from 'vue'

const numberFormat = ref('words')

function formatWords(num) {
  if (num === 0) return '0'
  
  const absNum = Math.abs(num)
  const sign = num < 0 ? '-' : ''
  
  if (absNum >= 10000000) {
    const cr = absNum / 10000000
    return sign + cr.toFixed(2) + ' Cr'
  }
  if (absNum >= 100000) {
    const l = absNum / 100000
    return sign + l.toFixed(2) + ' L'
  }
  if (absNum >= 1000) {
    const k = absNum / 1000
    return sign + k.toFixed(2) + ' K'
  }
  return sign + absNum.toString()
}

function formatNumeric(num) {
  return num.toLocaleString('en-IN')
}

function formatNumber(num, format) {
  if (format === 'words') {
    return formatWords(num)
  }
  return formatNumeric(num)
}

export function useNumberFormat() {
  return {
    numberFormat,
    formatNumber: (num) => formatNumber(num, numberFormat.value),
  }
}
