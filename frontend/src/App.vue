<script setup>
import AppSidebar from '@/components/AppSidebar.vue'
</script>

<template>
  <div style="display:flex;height:100vh;overflow:hidden;">
    <AppSidebar />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>
