<script setup>
import AppNav from '@/components/AppNav.vue'
</script>

<template>
  <div class="app-shell">
    <AppNav />
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>
