<template>
  <div class="permission-manager">
    <div class="page-header">
      <div class="page-title">
        <FluentIcons name="shield" :size="28" class="page-icon" />
        <h2>权限管理</h2>
      </div>
      <div class="permission-actions">
        <button @click="savePermissions" class="btn-primary">
          <FluentIcons name="save" :size="18" />
          <span>保存权限设置</span>
        </button>
        <button @click="resetPermissions" class="btn-secondary">
          <FluentIcons name="refresh" :size="18" />
          <span>重置默认</span>
        </button>
      </div>
    </div>

    <div class="permission-container">
      <div class="permission-card">
        <h3>页面访问权限</h3>
        <p class="card-description">设置各角色可以访问的页面</p>
        
        <div class="permission-table">
          <table>
            <thead>
              <tr>
                <th class="page-col">页面</th>
                <th v-if="showSuperAdminColumn" class="role-col">Super Admin</th>
                <th v-if="showAdminColumn" class="role-col">Admin</th>
                <th v-if="showUserColumn" class="role-col">User</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="page in pages" :key="page.path">
                <td class="page-name">
                  <FluentIcons :name="page.icon" :size="16" class="page-icon" />
                  {{ page.title }}
                </td>
                <td v-if="showSuperAdminColumn">
                  <FluentToggle 
                    :checked="pagePermissions[page.path]?.includes('super_admin')"
                    disabled
                  />
                </td>
                <td v-if="showAdminColumn">
                  <FluentToggle 
                    :checked="pagePermissions[page.path]?.includes('admin')"
                    :disabled="!canEditPermissions"
                    @update:checked="(value) => togglePagePermission(page.path, 'admin', value)"
                  />
                </td>
                <td v-if="showUserColumn">
                  <FluentToggle 
                    :checked="pagePermissions[page.path]?.includes('user')"
                    :disabled="!canEditPermissions"
                    @update:checked="(value) => togglePagePermission(page.path, 'user', value)"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="permission-card">
        <h3>组织管理操作权限</h3>
        <p class="card-description">设置各角色在组织管理中的具体操作权限</p>
        
        <div class="permission-table">
          <table>
            <thead>
              <tr>
                <th class="page-col">操作权限</th>
                <th v-if="showSuperAdminColumn" class="role-col">Super Admin</th>
                <th v-if="showAdminColumn" class="role-col">Admin</th>
                <th v-if="showUserColumn" class="role-col">User</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="perm in orgPermissions" :key="perm.key">
                <td class="perm-name">
                  <FluentIcons :name="perm.icon" :size="16" class="page-icon" />
                  <div class="perm-info">
                    <span class="perm-title">{{ perm.title }}</span>
                    <span class="perm-desc">{{ perm.description }}</span>
                  </div>
                </td>
                <td v-if="showSuperAdminColumn"><FluentToggle checked disabled /></td>
                <td v-if="showAdminColumn">
                  <FluentToggle 
                    :checked="actionPermissions.admin?.org?.[perm.key]"
                    :disabled="!canEditPermissions"
                    @update:checked="(value) => toggleActionPermission('admin', 'org', perm.key, value)"
                  />
                </td>
                <td v-if="showUserColumn">
                  <FluentToggle 
                    :checked="actionPermissions.user?.org?.[perm.key]"
                    :disabled="!canEditPermissions"
                    @update:checked="(value) => toggleActionPermission('user', 'org', perm.key, value)"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="permission-card">
        <h3>设备管理操作权限</h3>
        <p class="card-description">设置各角色在设备管理中的具体操作权限</p>
        
        <div class="permission-table">
          <table>
            <thead>
              <tr>
                <th class="page-col">操作权限</th>
                <th v-if="showSuperAdminColumn" class="role-col">Super Admin</th>
                <th v-if="showAdminColumn" class="role-col">Admin</th>
                <th v-if="showUserColumn" class="role-col">User</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="perm in devicePermissions" :key="perm.key">
                <td class="perm-name">
                  <FluentIcons :name="perm.icon" :size="16" class="page-icon" />
                  <div class="perm-info">
                    <span class="perm-title">{{ perm.title }}</span>
                    <span class="perm-desc">{{ perm.description }}</span>
                  </div>
                </td>
                <td v-if="showSuperAdminColumn"><FluentToggle checked disabled /></td>
                <td v-if="showAdminColumn">
                  <FluentToggle 
                    :checked="actionPermissions.admin?.device?.[perm.key]"
                    :disabled="!canEditPermissions"
                    @update:checked="(value) => toggleActionPermission('admin', 'device', perm.key, value)"
                  />
                </td>
                <td v-if="showUserColumn">
                  <FluentToggle 
                    :checked="actionPermissions.user?.device?.[perm.key]"
                    :disabled="!canEditPermissions"
                    @update:checked="(value) => toggleActionPermission('user', 'device', perm.key, value)"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="permission-card">
        <h3>账户管理操作权限</h3>
        <p class="card-description">设置各角色在账户管理中的具体操作权限</p>
        
        <div class="permission-table">
          <table>
            <thead>
              <tr>
                <th class="page-col">操作权限</th>
                <th v-if="showSuperAdminColumn" class="role-col">Super Admin</th>
                <th v-if="showAdminColumn" class="role-col">Admin</th>
                <th v-if="showUserColumn" class="role-col">User</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="perm in accountPermissions" :key="perm.key">
                <td class="perm-name">
                  <FluentIcons :name="perm.icon" :size="16" class="page-icon" />
                  <div class="perm-info">
                    <span class="perm-title">{{ perm.title }}</span>
                    <span class="perm-desc">{{ perm.description }}</span>
                  </div>
                </td>
                <td v-if="showSuperAdminColumn"><FluentToggle checked disabled /></td>
                <td v-if="showAdminColumn">
                  <FluentToggle 
                    :checked="actionPermissions.admin?.account?.[perm.key]"
                    :disabled="!canEditPermissions"
                    @update:checked="(value) => toggleActionPermission('admin', 'account', perm.key, value)"
                  />
                </td>
                <td v-if="showUserColumn">
                  <FluentToggle 
                    :checked="actionPermissions.user?.account?.[perm.key]"
                    :disabled="!canEditPermissions"
                    @update:checked="(value) => toggleActionPermission('user', 'account', perm.key, value)"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="permission-card">
        <h3>安全中心配置操作权限</h3>
        <p class="card-description">设置各角色在安全中心配置中的具体操作权限</p>
        
        <div class="permission-table">
          <table>
            <thead>
              <tr>
                <th class="page-col">操作权限</th>
                <th v-if="showSuperAdminColumn" class="role-col">Super Admin</th>
                <th v-if="showAdminColumn" class="role-col">Admin</th>
                <th v-if="showUserColumn" class="role-col">User</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="perm in securityPermissions" :key="perm.key">
                <td class="perm-name">
                  <FluentIcons :name="perm.icon" :size="16" class="page-icon" />
                  <div class="perm-info">
                    <span class="perm-title">{{ perm.title }}</span>
                    <span class="perm-desc">{{ perm.description }}</span>
                  </div>
                </td>
                <td v-if="showSuperAdminColumn"><FluentToggle checked disabled /></td>
                <td v-if="showAdminColumn">
                  <FluentToggle 
                    :checked="actionPermissions.admin?.security?.[perm.key]"
                    :disabled="!canEditPermissions"
                    @update:checked="(value) => toggleActionPermission('admin', 'security', perm.key, value)"
                  />
                </td>
                <td v-if="showUserColumn">
                  <FluentToggle 
                    :checked="actionPermissions.user?.security?.[perm.key]"
                    :disabled="!canEditPermissions"
                    @update:checked="(value) => toggleActionPermission('user', 'security', perm.key, value)"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="permission-card">
        <h3>网络拦截配置操作权限</h3>
        <p class="card-description">设置各角色在网络拦截配置中的具体操作权限</p>
        
        <div class="permission-table">
          <table>
            <thead>
              <tr>
                <th class="page-col">操作权限</th>
                <th v-if="showSuperAdminColumn" class="role-col">Super Admin</th>
                <th v-if="showAdminColumn" class="role-col">Admin</th>
                <th v-if="showUserColumn" class="role-col">User</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="perm in networkPermissions" :key="perm.key">
                <td class="perm-name">
                  <FluentIcons :name="perm.icon" :size="16" class="page-icon" />
                  <div class="perm-info">
                    <span class="perm-title">{{ perm.title }}</span>
                    <span class="perm-desc">{{ perm.description }}</span>
                  </div>
                </td>
                <td v-if="showSuperAdminColumn"><FluentToggle checked disabled /></td>
                <td v-if="showAdminColumn">
                  <FluentToggle 
                    :checked="actionPermissions.admin?.network?.[perm.key]"
                    :disabled="!canEditPermissions"
                    @update:checked="(value) => toggleActionPermission('admin', 'network', perm.key, value)"
                  />
                </td>
                <td v-if="showUserColumn">
                  <FluentToggle 
                    :checked="actionPermissions.user?.network?.[perm.key]"
                    :disabled="!canEditPermissions"
                    @update:checked="(value) => toggleActionPermission('user', 'network', perm.key, value)"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div class="permission-card">
        <h3>系统日志操作权限</h3>
        <p class="card-description">设置各角色在系统日志管理中的具体操作权限</p>
        
        <div class="permission-table">
          <table>
            <thead>
              <tr>
                <th class="page-col">操作权限</th>
                <th v-if="showSuperAdminColumn" class="role-col">Super Admin</th>
                <th v-if="showAdminColumn" class="role-col">Admin</th>
                <th v-if="showUserColumn" class="role-col">User</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="perm in systemLogsPermissions" :key="perm.key">
                <td class="perm-name">
                  <FluentIcons :name="perm.icon" :size="16" class="page-icon" />
                  <div class="perm-info">
                    <span class="perm-title">{{ perm.title }}</span>
                    <span class="perm-desc">{{ perm.description }}</span>
                  </div>
                </td>
                <td v-if="showSuperAdminColumn"><FluentToggle checked disabled /></td>
                <td v-if="showAdminColumn">
                  <FluentToggle 
                    :checked="actionPermissions.admin?.systemLogs?.[perm.key]"
                    :disabled="!canEditPermissions"
                    @update:checked="(value) => toggleActionPermission('admin', 'systemLogs', perm.key, value)"
                  />
                </td>
                <td v-if="showUserColumn">
                  <FluentToggle 
                    :checked="actionPermissions.user?.systemLogs?.[perm.key]"
                    :disabled="!canEditPermissions"
                    @update:checked="(value) => toggleActionPermission('user', 'systemLogs', perm.key, value)"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import FluentIcons from '@/components/FluentIcons.vue'
import FluentToggle from '@/components/FluentToggle.vue'
import { notify } from '@/utils/notification'
import api from '@/api'
import { setPermissions } from '@/stores/permissions'

const showNotification = inject('showNotification')

const currentUserRole = computed(() => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    try {
      const userData = JSON.parse(userStr)
      return userData.role || 'user'
    } catch {
      return 'user'
    }
  }
  return 'user'
})

const showSuperAdminColumn = computed(() => currentUserRole.value === 'super_admin')
const showAdminColumn = computed(() => currentUserRole.value === 'super_admin' || currentUserRole.value === 'admin')
const showUserColumn = computed(() => true)
const canEditPermissions = computed(() => currentUserRole.value === 'super_admin')

const pages = [
  { path: '/dashboard', title: '仪表盘', icon: 'dashboard' },
  { path: '/organizations', title: '组织管理', icon: 'organization' },
  { path: '/devices', title: '设备管理', icon: 'device' },
  { path: '/accounts', title: '账户管理', icon: 'person' },
  { path: '/security-config', title: '安全中心配置', icon: 'security' },
  { path: '/network-intercept', title: '网络拦截配置', icon: 'network' },
  { path: '/system-logs', title: '系统日志', icon: 'list' },
  { path: '/settings', title: '系统设置', icon: 'settings' },
  { path: '/permissions', title: '权限管理', icon: 'shield' }
]

const defaultPagePermissions = {
  '/dashboard': ['super_admin', 'admin', 'user'],
  '/organizations': ['super_admin', 'admin'],
  '/devices': ['super_admin', 'admin'],
  '/accounts': ['super_admin', 'admin'],
  '/security-config': ['super_admin', 'admin'],
  '/network-intercept': ['super_admin', 'admin'],
  '/system-logs': ['super_admin', 'admin'],
  '/settings': ['super_admin', 'admin', 'user'],
  '/permissions': ['super_admin']
}

const orgPermissions = [
  { key: 'edit', title: '编辑组织', description: '是否可以修改组织的基本信息', icon: 'edit' },
  { key: 'delete', title: '删除组织', description: '是否可以删除已有组织', icon: 'delete' },
  { key: 'create', title: '创建组织', description: '是否可以创建新的组织', icon: 'add' }
]

const devicePermissions = [
  { key: 'viewDetail', title: '查看设备详情', description: '是否可以查看设备的详细信息', icon: 'view' },
  { key: 'delete', title: '删除设备', description: '是否可以删除已注册的设备', icon: 'delete' }
]

const accountPermissions = [
  { key: 'create', title: '添加账户', description: '是否可以创建新的用户账户', icon: 'add' },
  { key: 'changeRole', title: '修改账户等级', description: '是否可以更改账户的角色权限级别', icon: 'shield' },
  { key: 'delete', title: '删除账户', description: '是否可以删除已有账户', icon: 'delete' }
]

const securityPermissions = [
  { key: 'manageAccounts', title: '管理安全账户', description: '是否可以添加或删除安全中心的管理账户', icon: 'person' },
  { key: 'jsonEdit', title: 'JSON编辑', description: '是否可以使用JSON编辑器直接修改配置', icon: 'code' },
  { key: 'enableTwoFactor', title: '启用双重验证', description: '是否可以开启或关闭双重身份验证功能', icon: 'security' },
  { key: 'changeLoginMode', title: '修改登录验证模式', description: '是否可以更改系统的登录验证方式', icon: 'lock' },
  { key: 'modifyPermissions', title: '修改软件权限', description: '是否可以修改客户端软件的功能权限设置', icon: 'shield' }
]

const networkPermissions = [
  { key: 'enableGlobal', title: '启用全局拦截', description: '是否可以开启或关闭全局网络拦截功能', icon: 'network' },
  { key: 'manageDomains', title: '管理域名规则', description: '是否可以添加或删除网络拦截的域名规则', icon: 'globe' }
]

const systemLogsPermissions = [
  { key: 'view', title: '查看日志', description: '是否可以查看系统日志记录', icon: 'view' },
  { key: 'search', title: '搜索日志', description: '是否可以使用搜索功能查找日志', icon: 'search' },
  { key: 'deleteSingle', title: '删除单条日志', description: '是否可以删除单条日志记录', icon: 'delete' },
  { key: 'batchDelete', title: '批量删除日志', description: '是否可以批量删除多条日志记录', icon: 'delete' },
  { key: 'clearAll', title: '清空所有日志', description: '是否可以清空所有系统日志记录', icon: 'delete' }
]

const defaultActionPermissions = {
  admin: {
    org: { edit: true, delete: true, create: true },
    device: { viewDetail: true, delete: true },
    account: { create: true, changeRole: true, delete: true },
    security: { manageAccounts: true, jsonEdit: true, enableTwoFactor: true, changeLoginMode: true, modifyPermissions: true },
    network: { enableGlobal: true, manageDomains: true },
    systemLogs: { view: true, search: true, deleteSingle: true, batchDelete: true, clearAll: true }
  },
  user: {
    org: { edit: false, delete: false, create: false },
    device: { viewDetail: true, delete: false },
    account: { create: false, changeRole: false, delete: false },
    security: { manageAccounts: false, jsonEdit: false, enableTwoFactor: false, changeLoginMode: false, modifyPermissions: false },
    network: { enableGlobal: false, manageDomains: false },
    systemLogs: { view: false, search: false, deleteSingle: false, batchDelete: false, clearAll: false }
  }
}

const allPermissions = ref({})
const pagePermissions = ref({ ...defaultPagePermissions })
const actionPermissions = ref({
  admin: JSON.parse(JSON.stringify(defaultActionPermissions.admin)),
  user: JSON.parse(JSON.stringify(defaultActionPermissions.user))
})

const loadPermissions = async () => {
  try {
    const response = await api.get('/permissions')
    allPermissions.value = response
    applyPermissions()
  } catch (error) {
    console.error('Failed to load permissions:', error)
    allPermissions.value = {}
    applyPermissions()
  }
}

const applyPermissions = () => {
  const adminData = allPermissions.value?.['admin']
  const userData = allPermissions.value?.['user']
  
  if (adminData?.pagePermissions) {
    pagePermissions.value = JSON.parse(JSON.stringify(adminData.pagePermissions))
  } else if (userData?.pagePermissions) {
    pagePermissions.value = JSON.parse(JSON.stringify(userData.pagePermissions))
  } else {
    pagePermissions.value = JSON.parse(JSON.stringify(defaultPagePermissions))
  }
  
  if (adminData?.actionPermissions) {
    actionPermissions.value.admin = JSON.parse(JSON.stringify(adminData.actionPermissions))
  } else {
    actionPermissions.value.admin = JSON.parse(JSON.stringify(defaultActionPermissions.admin))
  }
  
  if (userData?.actionPermissions) {
    actionPermissions.value.user = JSON.parse(JSON.stringify(userData.actionPermissions))
  } else {
    actionPermissions.value.user = JSON.parse(JSON.stringify(defaultActionPermissions.user))
  }
  
  setPermissions({
    admin: {
      pagePermissions: pagePermissions.value,
      actionPermissions: actionPermissions.value.admin
    },
    user: {
      pagePermissions: pagePermissions.value,
      actionPermissions: actionPermissions.value.user
    }
  })
}

const savePermissions = async () => {
  try {
    if (!canEditPermissions.value) {
      notify.error('您没有权限修改任何角色的权限配置')
      return
    }
    
    await api.put('/permissions/admin', {
      pagePermissions: pagePermissions.value,
      actionPermissions: actionPermissions.value.admin
    })
    
    await api.put('/permissions/user', {
      pagePermissions: pagePermissions.value,
      actionPermissions: actionPermissions.value.user
    })
    
    setPermissions({
      admin: {
        pagePermissions: pagePermissions.value,
        actionPermissions: actionPermissions.value.admin
      },
      user: {
        pagePermissions: pagePermissions.value,
        actionPermissions: actionPermissions.value.user
      }
    })
    
    if (showNotification) {
      showNotification('权限设置已保存', 'success')
    } else {
      notify.success('权限设置已保存')
    }
  } catch (error) {
    console.error('Failed to save permissions:', error)
    const errorMessage = error.response?.data?.error || '保存权限设置失败'
    if (showNotification) {
      showNotification(errorMessage, 'error')
    } else {
      notify.error(errorMessage)
    }
  }
}

const resetPermissions = async () => {
  pagePermissions.value = { ...defaultPagePermissions }
  actionPermissions.value = {
    admin: JSON.parse(JSON.stringify(defaultActionPermissions.admin)),
    user: JSON.parse(JSON.stringify(defaultActionPermissions.user))
  }
  if (showNotification) {
    showNotification('已重置默认权限设置', 'info')
  } else {
    notify.info('已重置默认权限设置')
  }
}

const togglePagePermission = (path, role, value) => {
  if (!pagePermissions.value[path]) {
    pagePermissions.value[path] = []
  }
  
  const index = pagePermissions.value[path].indexOf(role)
  if (value && index === -1) {
    pagePermissions.value[path].push(role)
  } else if (!value && index > -1) {
    pagePermissions.value[path].splice(index, 1)
  }
}

const toggleActionPermission = (role, category, key, value) => {
  if (!actionPermissions.value[role]) {
    actionPermissions.value[role] = {}
  }
  if (!actionPermissions.value[role][category]) {
    actionPermissions.value[role][category] = {}
  }
  actionPermissions.value[role][category][key] = value
}

onMounted(() => {
  loadPermissions()
})
</script>

<style scoped>
.permission-manager {
  padding: 24px;
  background: rgba(255, 255, 255, 0.05);
  min-height: 100vh;
  font-size: var(--fui-font-size-base);
}

.page-header {
  margin-bottom: 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 16px 24px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-radius: 8px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-icon {
  color: var(--fui-text);
  opacity: 0.9;
}

.page-title h2 {
  margin: 0;
  font-size: 1.25em;
  font-weight: 600;
  color: var(--fui-text);
  letter-spacing: -0.3px;
}

.permission-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.permission-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  padding: 24px;
  animation: containerFadeIn 0.4s ease-out 0.1s both;
}

@keyframes containerFadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.permission-card h3 {
  margin: 0 0 8px 0;
  font-size: 1.125em;
  font-weight: 600;
  color: var(--fui-text);
}

.card-description {
  margin: 0 0 20px 0;
  font-size: 0.875em;
  color: var(--fui-text-secondary);
  opacity: 0.8;
}

.permission-table {
  overflow-x: auto;
}

table {
  width: 100%;
  border-spacing: 0;
  border: 1.5px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  overflow: hidden;
}

th, td {
  padding: 12px 16px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
}

.page-col {
  min-width: 250px;
  text-align: left !important;
}

.role-col {
  min-width: 120px;
}

.perm-name {
  display: flex;
  align-items: center;
  gap: 12px;
  text-align: left;
}

.perm-name .page-icon {
  opacity: 0.7;
  flex-shrink: 0;
}

.perm-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.perm-title {
  font-weight: 500;
  color: var(--fui-text);
  word-break: break-word;
}

.perm-desc {
  font-size: 0.8em;
  color: var(--fui-text-secondary);
  opacity: 0.7;
  word-break: break-word;
  line-height: 1.4;
}

th {
  background: rgba(255, 255, 255, 0.1);
  color: var(--fui-text);
  font-weight: 600;
  font-size: 0.75em;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

td {
  color: var(--fui-text);
  font-size: 0.875em;
}

th:last-child, td:last-child {
  border-right: none;
}

tr:last-child td {
  border-bottom: none;
}

.page-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.page-name .page-icon {
  opacity: 0.7;
  flex-shrink: 0;
}

.permission-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}

.btn-primary, .btn-secondary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875em;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-primary {
  background: var(--fui-primary);
  color: white;
}

.btn-primary:hover {
  background: var(--fui-primary-hover);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: var(--fui-text);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.15);
}
</style>
