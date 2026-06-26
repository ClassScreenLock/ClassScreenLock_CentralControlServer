<template>
  <router-view />
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import wsService from '@/utils/websocket'
import { useRoute } from 'vue-router'

const route = useRoute()

onMounted(() => {
  // 加载暗黑模式设置
  const savedTheme = localStorage.getItem('theme') || 'light'
  document.documentElement.setAttribute('data-theme', savedTheme)
  
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
