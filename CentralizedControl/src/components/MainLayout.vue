<template>
  <div class="app-container">
    <nav class="sidebar">
      <div class="sidebar-header">
        <h2>ClassScreenLock</h2>
        <p>集控管理平台</p>
      </div>
      <ul class="nav-menu">
        <li v-for="item in visibleMenuItems" :key="item.path">
          <router-link :to="item.path" class="nav-link" :class="{ active: isActive(item.path) }">
            <FluentIcons :name="item.icon" :size="20" />
            <span>{{ item.title }}</span>
          </router-link>
        </li>
      </ul>
      <div class="sidebar-footer">
        <div class="user-card" v-if="user">
          <div class="user-avatar">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
            </svg>
          </div>
          <div class="user-details">
            <span class="username">{{ user.username }}</span>
            <span class="role-badge" :class="user.role">{{ formatRole(user.role) }}</span>
          </div>
        </div>
        <button @click="handleLogout" class="logout-button">
          <FluentIcons name="logout" :size="18" />
          <span>退出登录</span>
        </button>
      </div>
    </nav>
    <main class="main-content">
      <header class="top-bar">
        <h1>{{ currentTitle }}</h1>
      </header>
      <div class="content">
        <router-view />
      </div>
    </main>
    <Notification ref="notificationRef" />
  </div>
</template>

<script setup>
import { computed, ref, onMounted, provide } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authAPI } from '@/api/auth'
import api from '@/api'
import FluentIcons from './FluentIcons.vue'
import Notification from './Notification.vue'
import { setNotificationHandler } from '@/utils/notification'
import { setPermissions } from '@/stores/permissions'

const route = useRoute()
const router = useRouter()
const user = ref(null)
const notificationRef = ref(null)
const roleRequirements = ref({})

onMounted(() => {
  setNotificationHandler((message, type, title) => {
    if (notificationRef.value) {
      notificationRef.value.showNotification(message, type, title)
    }
  })
})

provide('showNotification', (message, type = 'info') => {
  if (notificationRef.value) {
    notificationRef.value.showNotification(message, type)
  }
})

const allMenuItems = [
  { path: '/dashboard', title: '仪表盘', icon: 'dashboard' },
  { path: '/organizations', title: '组织管理', icon: 'organization' },
  { path: '/devices', title: '设备管理', icon: 'device' },
  { path: '/accounts', title: '账户管理', icon: 'person' },
  { path: '/security-config', title: '安全中心配置', icon: 'security' },
  { path: '/network-intercept', title: '网络拦截配置', icon: 'network' },
  { path: '/permissions', title: '权限管理', icon: 'shield' },
  { path: '/system-logs', title: '系统日志', icon: 'list' },
  { path: '/settings', title: '系统设置', icon: 'settings' }
]

const defaultRoleRequirements = {
  '/dashboard': ['super_admin', 'admin', 'user'],
  '/organizations': ['super_admin', 'admin'],
  '/devices': ['super_admin', 'admin'],
  '/accounts': ['super_admin', 'admin'],
  '/security-config': ['super_admin', 'admin'],
  '/network-intercept': ['super_admin', 'admin'],
  '/settings': ['super_admin', 'admin', 'user'],
  '/permissions': ['super_admin'],
  '/system-logs': ['super_admin', 'admin']
}

const visibleMenuItems = computed(() => {
  if (!user.value) return []
  
  const userRole = user.value.role
  const permissions = roleRequirements.value
  
  return allMenuItems.filter(item => {
    const requiredRoles = permissions[item.path]
    if (!requiredRoles) return false
    return requiredRoles.includes(userRole)
  })
})

const currentTitle = computed(() => route.meta.title || 'Dashboard')

const isActive = (path) => route.path === path

const loadPermissions = async () => {
  try {
    const response = await api.get('/permissions')
    const userRole = user.value?.role
    
    if (response?.[userRole]?.pagePermissions) {
      roleRequirements.value = response[userRole].pagePermissions
      setPermissions({
        admin: {
          pagePermissions: response.admin?.pagePermissions || defaultRoleRequirements,
          actionPermissions: response.admin?.actionPermissions || {}
        },
        user: {
          pagePermissions: response.user?.pagePermissions || defaultRoleRequirements,
          actionPermissions: response.user?.actionPermissions || {}
        }
      })
    } else {
      roleRequirements.value = { ...defaultRoleRequirements }
      setPermissions({
        admin: {
          pagePermissions: defaultRoleRequirements,
          actionPermissions: {}
        },
        user: {
          pagePermissions: defaultRoleRequirements,
          actionPermissions: {}
        }
      })
    }
  } catch (error) {
    console.error('Failed to load permissions:', error)
    roleRequirements.value = { ...defaultRoleRequirements }
    setPermissions({
      admin: {
        pagePermissions: defaultRoleRequirements,
        actionPermissions: {}
      },
      user: {
        pagePermissions: defaultRoleRequirements,
        actionPermissions: {}
      }
    })
  }
}

onMounted(async () => {
  const userData = localStorage.getItem('user')
  if (userData) {
    user.value = JSON.parse(userData)
    await loadPermissions()
  }
})

const formatRole = (role) => {
  const roleMap = {
    'super_admin': '超级管理员',
    'admin': '管理员',
    'user': '用户'
  }
  return roleMap[role] || role
}

const handleLogout = async () => {
  try {
    await authAPI.logout()
  } catch (err) {
    console.error('登出失败:', err)
  } finally {
    localStorage.removeItem('user')
    router.push('/login')
  }
}
</script>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 280px;
  background: var(--fui-surface);
  border-right: 1px solid var(--fui-border);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.sidebar-header {
  padding: 24px 20px;
  border-bottom: 1px solid var(--fui-border);
}

.sidebar-header h2 {
  font-size: 26px;
  font-weight: 700;
  color: var(--fui-primary);
  margin-bottom: 6px;
  letter-spacing: 0.3px;
  word-break: break-word;
}

.sidebar-header p {
  font-size: 13px;
  color: var(--fui-text-secondary);
  margin: 0;
  font-weight: 500;
}

.nav-menu {
  list-style: none;
  padding: 16px 0;
  flex: 1;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--fui-border);
  background: var(--fui-background);
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  margin-bottom: 10px;
  background: var(--fui-surface);
  border-radius: 12px;
  border: 1px solid var(--fui-border);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #0078d4 0%, #106ebe 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 120, 212, 0.25);
}

.user-avatar svg {
  width: 20px;
  height: 20px;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  flex: 1;
}

.username {
  font-size: 13px;
  font-weight: 600;
  color: var(--fui-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.role-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 6px;
  display: inline-block;
  width: fit-content;
}

.role-badge.super_admin {
  background: linear-gradient(135deg, #0078d4 0%, #106ebe 100%);
  color: white;
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(0, 120, 212, 0.3);
}

.role-badge.admin {
  background: linear-gradient(135deg, #0078d4 0%, #106ebe 100%);
  color: white;
  font-weight: 500;
}

.role-badge.user {
  background: rgba(0, 0, 0, 0.08);
  color: #555;
  font-weight: 500;
}

[data-theme='dark'] .role-badge.user {
  background: rgba(255, 255, 255, 0.12);
  color: #ccc;
}

.logout-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 10px;
  background: transparent;
  border: 1px solid var(--fui-border);
  border-radius: var(--fui-radius);
  color: var(--fui-text);
  font-size: var(--fui-font-size-small);
  cursor: pointer;
  transition: all 0.2s;
}

.logout-button:hover {
  background: var(--error-fill-default);
  border-color: var(--error-stroke-default);
  color: var(--error-foreground-rest);
}

.logout-button :deep(.fluent-icon) {
  margin-right: 8px;
}

.nav-menu li {
  margin: 4px 12px;
}

.nav-link {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  text-decoration: none;
  color: var(--fui-text);
  border-radius: var(--fui-radius);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: var(--fui-font-size-medium);
  opacity: 0.8;
  transform: translateX(-10px);
  animation: navLinkFadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  animation-fill-mode: both;
}

.nav-menu li:nth-child(1) .nav-link { animation-delay: 0.1s; }
.nav-menu li:nth-child(2) .nav-link { animation-delay: 0.2s; }
.nav-menu li:nth-child(3) .nav-link { animation-delay: 0.3s; }
.nav-menu li:nth-child(4) .nav-link { animation-delay: 0.4s; }
.nav-menu li:nth-child(5) .nav-link { animation-delay: 0.5s; }
.nav-menu li:nth-child(6) .nav-link { animation-delay: 0.6s; }
.nav-menu li:nth-child(7) .nav-link { animation-delay: 0.7s; }
.nav-menu li:nth-child(8) .nav-link { animation-delay: 0.8s; }
.nav-menu li:nth-child(9) .nav-link { animation-delay: 0.9s; }

@keyframes navLinkFadeIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 0.8;
    transform: translateX(0);
  }
}

.nav-link:hover {
  background-color: var(--fui-background);
  opacity: 1;
  transform: translateX(4px);
}

.nav-link.active {
  background-color: var(--fui-primary);
  color: white;
}

.nav-link :deep(.fluent-icon) {
  margin-right: 12px;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: var(--fui-background);
  font-size: var(--fui-font-size-base);
}

.top-bar {
  background: var(--fui-surface);
  border-bottom: 1px solid var(--fui-border);
  padding: 20px 32px;
  box-shadow: var(--fui-shadow);
}

.top-bar h1 {
  font-size: 1.5em;
  font-weight: 600;
  margin: 0;
  color: var(--fui-text);
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
  font-size: var(--fui-font-size-base);
}
</style>
