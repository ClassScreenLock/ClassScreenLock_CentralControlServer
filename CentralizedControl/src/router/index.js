import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../components/MainLayout.vue'
import { getPermissions } from '@/stores/permissions'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/dashboard',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '仪表盘' }
      },
      {
        path: '/organizations',
        name: 'Organizations',
        component: () => import('../views/Organizations.vue'),
        meta: { title: '组织管理' }
      },
      {
        path: '/devices',
        name: 'Devices',
        component: () => import('../views/Devices.vue'),
        meta: { title: '设备管理' }
      },
      {
        path: '/accounts',
        name: 'Accounts',
        component: () => import('../views/Accounts.vue'),
        meta: { title: '账户管理' }
      },
      {
        path: '/security-config',
        name: 'SecurityConfig',
        component: () => import('../views/SecurityConfig.vue'),
        meta: { title: '安全中心配置' }
      },
      {
        path: '/network-intercept',
        name: 'NetworkIntercept',
        component: () => import('../views/NetworkIntercept.vue'),
        meta: { title: '网络拦截配置' }
      },
      {
        path: '/settings',
        name: 'Settings',
        component: () => import('../views/Settings.vue'),
        meta: { title: '系统设置' }
      },
      {
        path: '/permissions',
        name: 'Permissions',
        component: () => import('../views/Permissions.vue'),
        meta: { title: '权限管理' }
      },
      {
        path: '/system-logs',
        name: 'SystemLogs',
        component: () => import('../views/SystemLogs.vue'),
        meta: { title: '系统日志' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from) => {
  const user = localStorage.getItem('user')
  const isLoggedIn = user !== null
  
  // 检查 token 是否过期
  const tokenExpiresAt = localStorage.getItem('tokenExpiresAt')
  let isTokenExpired = false
  
  if (tokenExpiresAt) {
    try {
      const expiryTime = new Date(tokenExpiresAt)
      if (new Date() > expiryTime) {
        isTokenExpired = true
        // Token 过期，清除登录信息
        localStorage.removeItem('user')
        localStorage.removeItem('tokenExpiresAt')
      }
    } catch (error) {
      console.error('Failed to parse token expiry time:', error)
      isTokenExpired = true
    }
  }
  
  // 如果访问登录页
  if (to.path === '/login') {
    // 如果已登录且 token 未过期，跳转到仪表盘
    if (isLoggedIn && !isTokenExpired) {
      return '/dashboard'
    }
    return true
  }
  
  // 访问其他页面需要登录
  if (!isLoggedIn || isTokenExpired) {
    return '/login'
  }
  
  // 权限检查
  const userData = JSON.parse(user)
  const userRole = userData.role
  
  // 从缓存加载权限设置
  const permissions = getPermissions()
  
  // 默认权限配置
  const defaultPagePermissions = {
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
  
  // 获取当前用户的页面权限配置
  let pagePermissions = JSON.parse(JSON.stringify(defaultPagePermissions))
  
  if (permissions && permissions[userRole] && permissions[userRole].pagePermissions) {
    pagePermissions = JSON.parse(JSON.stringify(permissions[userRole].pagePermissions))
  } else if (permissions && permissions[userRole]) {
    pagePermissions = JSON.parse(JSON.stringify(permissions[userRole]))
  }
  
  // 确保仪表盘始终对当前用户角色可访问（防止无限重定向循环）
  if (!pagePermissions['/dashboard']) {
    pagePermissions['/dashboard'] = []
  }
  if (!pagePermissions['/dashboard'].includes(userRole)) {
    pagePermissions['/dashboard'].push(userRole)
  }
  
  // 检查当前页面是否需要权限
  const requiredRoles = pagePermissions[to.path]
  if (requiredRoles && !requiredRoles.includes(userRole)) {
    // 显示权限不足提示
    import('@/utils/notification').then(({ notify }) => {
      notify.error('权限不足，无法访问该页面')
    })
    return '/dashboard'
  }
  
  return true
})

export default router
