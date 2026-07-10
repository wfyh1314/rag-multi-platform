<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppNav from '@/components/AppNav.vue'

const route = useRoute()
const showNav = computed(() => !route.meta.public)
</script>

<template>
  <div class="app-shell">
    <AppNav v-if="showNav" />
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
