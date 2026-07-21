import { ref } from 'vue'

const collapsed = ref(false)

export function useSidebar() {
  const toggleSidebar = () => {
    console.log('toggleSidebar called, current state:', collapsed.value)
    collapsed.value = !collapsed.value
    console.log('toggleSidebar new state:', collapsed.value)
  }

  return {
    collapsed,
    toggleSidebar
  }
}
