import { ref } from 'vue'

export function useExpandableSet() {
  const expanded = ref(new Set())

  function toggle(key) {
    if (expanded.value.has(key)) {
      expanded.value.delete(key)
    } else {
      expanded.value.add(key)
    }
  }

  function isExpanded(key) {
    return expanded.value.has(key)
  }

  return { expanded, toggle, isExpanded }
}
