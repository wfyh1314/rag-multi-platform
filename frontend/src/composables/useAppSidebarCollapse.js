import { ref } from 'vue'

const STORAGE_KEY = 'app_sidebar_collapsed'
const collapsed = ref(localStorage.getItem(STORAGE_KEY) === 'true')

export function useAppSidebarCollapse() {
  function toggle() {
    collapsed.value = !collapsed.value
    localStorage.setItem(STORAGE_KEY, String(collapsed.value))
  }

  return { collapsed, toggle }
}
