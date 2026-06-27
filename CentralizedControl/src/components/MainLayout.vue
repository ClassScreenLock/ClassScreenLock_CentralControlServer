<template>
  <div class="app-container" :class="{ 'sidebar-open': sidebarOpen }">
    <!-- 移动端遮罩 -->
    <div class="sidebar-overlay" v-if="sidebarOpen" @click="closeSidebar"></div>

    <nav class="sidebar" :class="{ 'sidebar--open': sidebarOpen }">
      <div class="sidebar-header">
        <h2>ClassScreenLock</h2>
        <p>集控管理平台</p>
      </div>
      <ul class="nav-menu">
        <li v-for="item in visibleMenuItems" :key="item.path">
          <router-link :to="item.path" class="nav-link" :class="{ active: isActive(item.path) }" @click="closeSidebar">
            <FluentIcons :name="item.icon" :size="20" />
            <span>{{ item.title }}</span>
          </router-link>
        </li>
      </ul>
    </nav>
    <main class="main-content">
      <header class="top-bar">
        <button class="hamburger-btn" @click="toggleSidebar" :title="sidebarOpen ? '关闭菜单' : '打开菜单'">
          <span class="hamburger-line"></span>
          <span class="hamburger-line"></span>
          <span class="hamburger-line"></span>
        </button>
        <h1>{{ currentTitle }}</h1>
        <div class="top-bar-spacer"></div>
        <div class="top-bar-right" v-if="user">
          <!-- 用户菜单触发器 -->
          <button class="user-trigger" @click.stop="toggleUserMenu" :class="{ 'is-open': userMenuOpen }">
            <div class="user-avatar">
              <img v-if="userAvatarUrl" :src="userAvatarUrl" class="user-avatar-img" alt="" />
              <svg v-else viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
              </svg>
            </div>
            <span class="user-trigger-name">{{ displayName }}</span>
            <svg class="user-trigger-chevron" viewBox="0 0 16 16" fill="currentColor" width="12" height="12">
              <path d="M4.646 5.646a.5.5 0 0 1 .708 0L8 8.293l2.646-2.647a.5.5 0 0 1 .708.708l-3 3a.5.5 0 0 1-.708 0l-3-3a.5.5 0 0 1 0-.708z"/>
            </svg>
          </button>

          <!-- 下拉菜单 -->
          <Transition name="user-menu">
            <div v-if="userMenuOpen" class="user-menu-dropdown" @click.stop>
              <div class="user-menu-header">
                <div class="user-menu-avatar">
                  <img v-if="userAvatarUrl" :src="userAvatarUrl" class="user-menu-avatar-img" alt="" />
                  <svg v-else viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                  </svg>
                </div>
                <div class="user-menu-info">
                  <span class="user-menu-name">{{ displayName }}</span>
                  <span class="user-menu-role" :class="user.role">{{ formatRole(user.role) }}</span>
                </div>
              </div>
              <div class="user-menu-divider"></div>
              <button class="user-menu-item" @click="goProfile">
                <FluentIcons name="person" :size="16" />
                <span>个人资料</span>
              </button>
              <button class="user-menu-item" @click="handleLogout">
                <FluentIcons name="logout" :size="16" />
                <span>退出登录</span>
              </button>
            </div>
          </Transition>
        </div>
      </header>
      <div class="content">
        <router-view />
      </div>
    </main>
    <Notification ref="notificationRef" />
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onBeforeUnmount, provide } from 'vue'
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
const sidebarOpen = ref(false)
const userMenuOpen = ref(false)

const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value
}

const closeSidebar = () => {
  sidebarOpen.value = false
}

const toggleUserMenu = () => {
  userMenuOpen.value = !userMenuOpen.value
}

const closeUserMenu = () => {
  userMenuOpen.value = false
}

// 点击外部关闭用户菜单
const onDocumentClick = (e) => {
  if (userMenuOpen.value) {
    userMenuOpen.value = false
  }
}

// 监听路由变化关闭侧边栏 + 刷新用户信息
router.afterEach(() => {
  sidebarOpen.value = false
  const userData = localStorage.getItem('user')
  if (userData) {
    user.value = JSON.parse(userData)
  }
})

onMounted(() => {
  setNotificationHandler((message, type, title) => {
    if (notificationRef.value) {
      notificationRef.value.showNotification(message, type, title)
    }
  })
  document.addEventListener('click', onDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
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
  { path: '/screen-monitor', title: '集控端屏幕监控', icon: 'desktop' },
  { path: '/schedule-control', title: '课表控制', icon: 'calendar' },
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
  '/screen-monitor': ['super_admin', 'admin', 'user'],
  '/schedule-control': ['super_admin', 'admin'],
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

const userAvatarUrl = computed(() => user.value?.avatarUrl || '')
const displayName = computed(() => user.value?.nickname || user.value?.username || '用户')

const goProfile = () => {
  userMenuOpen.value = false
  router.push('/profile')
}

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
  userMenuOpen.value = false
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

/* ===== 侧边栏遮罩 (移动端) ===== */
.sidebar-overlay {
  display: none;
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 99;
}

.sidebar {
  width: 280px;
  background: var(--fui-surface);
  border-right: 1px solid var(--fui-border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  z-index: 100;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  /* 整体不滚动，只让菜单区域滚动 */
  overflow: hidden;
}

.sidebar-header {
  padding: 24px 20px;
  border-bottom: 1px solid var(--fui-border);
  flex-shrink: 0;
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
  overflow-y: auto;
  min-height: 0;
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

/* ===== 主内容区 ===== */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: var(--fui-background);
  font-size: var(--fui-font-size-base);
  min-width: 0;
}

/* ===== 顶栏 ===== */
.top-bar {
  background: var(--fui-surface);
  border-bottom: 1px solid var(--fui-border);
  padding: 12px 24px;
  box-shadow: var(--fui-shadow);
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.top-bar h1 {
  font-size: 1.25em;
  font-weight: 600;
  margin: 0;
  color: var(--fui-text);
  white-space: nowrap;
}

.top-bar-spacer {
  flex: 1;
}

/* ===== 右上角用户菜单 ===== */
.top-bar-right {
  position: relative;
  flex-shrink: 0;
}

/* 触发器按钮 */
.user-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px 4px 4px;
  background: var(--fui-background);
  border: 1px solid var(--fui-border);
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}

.user-trigger:hover {
  background: var(--fui-surface);
  border-color: var(--fui-primary);
}

.user-trigger.is-open {
  border-color: var(--fui-primary);
  background: rgba(0, 120, 212, 0.08);
}

.user-trigger .user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, #0078d4 0%, #106ebe 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.user-trigger .user-avatar svg {
  width: 18px;
  height: 18px;
}

.user-avatar-img {
  width: 100%;
  height: 100%;
  border-radius: inherit;
  object-fit: cover;
}

.user-menu-avatar .user-menu-avatar-img {
  width: 100%;
  height: 100%;
  border-radius: inherit;
  object-fit: cover;
}

.user-trigger-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--fui-text);
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-trigger-chevron {
  color: var(--fui-text-secondary);
  transition: transform 0.25s ease;
}

.user-trigger.is-open .user-trigger-chevron {
  transform: rotate(180deg);
  color: var(--fui-primary);
}

/* 下拉菜单 */
.user-menu-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 220px;
  background: var(--fui-surface);
  border: 1px solid var(--fui-border);
  border-radius: 12px;
  box-shadow:
    0 12px 40px rgba(0, 0, 0, 0.18),
    0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 200;
  overflow: hidden;
  padding: 8px;
}

/* 菜单头 - 用户信息 */
.user-menu-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 10px 6px;
}

.user-menu-avatar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #0078d4 0%, #106ebe 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 120, 212, 0.3);
}

.user-menu-avatar svg {
  width: 22px;
  height: 22px;
}

.user-menu-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.user-menu-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--fui-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-menu-role {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  width: fit-content;
  font-weight: 500;
}

.user-menu-role.super_admin {
  background: rgba(0, 120, 212, 0.15);
  color: #0078d4;
}

.user-menu-role.admin {
  background: rgba(0, 120, 212, 0.1);
  color: #0078d4;
}

.user-menu-role.user {
  background: rgba(0, 0, 0, 0.06);
  color: #555;
}

[data-theme='dark'] .user-menu-role.user {
  background: rgba(255, 255, 255, 0.1);
  color: #bbb;
}

.user-menu-divider {
  height: 1px;
  background: var(--fui-border);
  margin: 6px 4px;
}

/* 菜单项 */
.user-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: var(--fui-text);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
}

.user-menu-item:hover {
  background: rgba(232, 17, 35, 0.08);
  color: #e81123;
}

/* 过渡动画 */
.user-menu-enter-active {
  transition: opacity 0.2s ease, transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.user-menu-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.user-menu-enter-from {
  opacity: 0;
  transform: translateY(-8px) scale(0.95);
}
.user-menu-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.97);
}

/* ===== 汉堡菜单按钮 ===== */
.hamburger-btn {
  display: none;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 5px;
  width: 36px;
  height: 36px;
  padding: 6px;
  background: transparent;
  border: 1px solid var(--fui-border);
  border-radius: 6px;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.2s;
}

.hamburger-btn:hover {
  background: var(--fui-background);
}

.hamburger-line {
  display: block;
  width: 20px;
  height: 2px;
  background: var(--fui-text);
  border-radius: 2px;
  transition: transform 0.3s, opacity 0.3s;
}

.sidebar-open .hamburger-line:nth-child(1) {
  transform: translateY(7px) rotate(45deg);
}

.sidebar-open .hamburger-line:nth-child(2) {
  opacity: 0;
}

.sidebar-open .hamburger-line:nth-child(3) {
  transform: translateY(-7px) rotate(-45deg);
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  font-size: var(--fui-font-size-base);
}

/* ===== 响应式 - 移动端 (<= 768px) ===== */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 0; left: 0; bottom: 0;
    transform: translateX(-100%);
    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.3);
  }

  .sidebar--open {
    transform: translateX(0);
  }

  .sidebar-overlay {
    display: block;
  }

  .hamburger-btn {
    display: flex;
  }

  .top-bar {
    padding: 10px 14px;
    gap: 8px;
  }

  .top-bar h1 {
    font-size: 1em;
  }

  .top-bar-right {
    position: static;
  }

  .user-trigger-name {
    display: none;
  }

  .user-menu-dropdown {
    position: fixed;
    top: auto;
    bottom: 0;
    left: 0;
    right: 0;
    min-width: 100%;
    border-radius: 16px 16px 0 0;
    box-shadow: 0 -8px 32px rgba(0, 0, 0, 0.2);
  }

  .content {
    padding: 12px;
  }
}

/* ===== 响应式 - 平板 (769px - 1024px) ===== */
@media (min-width: 769px) and (max-width: 1024px) {
  .sidebar {
    width: 240px;
  }

  .sidebar-header {
    padding: 20px 16px;
  }

  .sidebar-header h2 {
    font-size: 22px;
  }

  .top-bar {
    padding: 12px 18px;
  }

  .content {
    padding: 16px 20px;
  }
}
</style>
