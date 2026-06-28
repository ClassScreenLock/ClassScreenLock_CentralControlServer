<template>
  <router-view />
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import wsService from '@/utils/websocket'
import { useRoute } from 'vue-router'
import { refreshPermissions } from '@/stores/permissions'

const route = useRoute()

onMounted(async () => {
  // 加载暗黑模式设置
  const savedTheme = localStorage.getItem('theme') || 'light'
  document.documentElement.setAttribute('data-theme', savedTheme)
  
  // 仅在已登录时加载权限，避免未登录时产生 401 错误
  const user = localStorage.getItem('user')
  if (user) {
    const userData = JSON.parse(user)
    if (userData.token) {
      await refreshPermissions()
    }
  }
  
  // 初始化 WebSocket 连接
  wsService.connect()
})

onUnmounted(() => {
  // 断开 WebSocket 连接
  wsService.disconnect()
})
</script>

<style>
</style>
