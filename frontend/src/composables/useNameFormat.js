export function useNameFormat() {
  function formatZone(name) {
    if (!name) return ''
    // ZONE-1 -> Z1, ZONE-12 -> Z12, Zone-1 -> Z1
    const match = name.match(/^(?:ZONE|Zone)\s*-?\s*(\d+)$/i)
    if (match) return 'Z' + match[1]
    return name
  }

  function formatRegion(name) {
    if (!name) return ''
    // REGION-1 -> R1, REGION-12 -> R12, Region-1 -> R1
    const match = name.match(/^(?:REGION|Region)\s*-?\s*(\d+)$/i)
    if (match) return 'R' + match[1]
    return name
  }

  return { formatZone, formatRegion }
}