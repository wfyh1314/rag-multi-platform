<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from '@/components/AppSidebar.vue'
import { useAppSidebarCollapse } from '@/composables/useAppSidebarCollapse'

const route = useRoute()
const { collapsed: appSidebarCollapsed } = useAppSidebarCollapse()

const showNav = computed(() => !route.meta.public)
const isWorkspace = computed(() => route.meta.menu === 'workspace')
</script>

<template>
  <div class="app-shell" :class="{ 'app-shell--with-sidebar': showNav }">
    <div
      v-if="showNav"
      class="app-sidebar-wrap"
      :class="{ 'app-sidebar-wrap--collapsed': appSidebarCollapsed && isWorkspace }"
    >
      <AppSidebar v-show="!(appSidebarCollapsed && isWorkspace)" />
    </div>
    <main class="app-main" :class="{ 'app-main--full': !showNav }">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.app-main--full {
  min-height: 100vh;
}
</style>
