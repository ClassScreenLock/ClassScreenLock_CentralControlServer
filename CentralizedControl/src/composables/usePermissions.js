import { computed } from 'vue'
import { getPermissions } from '@/stores/permissions'

const defaultActionPermissions = {
  admin: {
    org: { edit: true, delete: true, create: true },
    device: { viewDetail: true, delete: true },
    account: { create: true, changeRole: true, delete: true },
    security: { manageAccounts: true, jsonEdit: true, enableTwoFactor: true, changeLoginMode: true, modifyPermissions: true },
    network: { enableGlobal: true, manageDomains: true },
    systemLogs: { view: true, search: true, deleteSingle: true, batchDelete: true, clearAll: true },
    permissionMgmt: { modifyLowerOrSame: true }
  },
  user: {
    org: { edit: false, delete: false, create: false },
    device: { viewDetail: true, delete: false },
    account: { create: false, changeRole: false, delete: false },
    security: { manageAccounts: false, jsonEdit: false, enableTwoFactor: false, changeLoginMode: false, modifyPermissions: false },
    network: { enableGlobal: false, manageDomains: false },
    systemLogs: { view: false, search: false, deleteSingle: false, batchDelete: false, clearAll: false },
    permissionMgmt: { modifyLowerOrSame: false }
  }
}

export function usePermissions() {
  const getCurrentUserRole = () => {
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
  }

  const permissions = computed(() => getPermissions())

  const hasActionPermission = (category, action) => {
    const role = getCurrentUserRole()
    
    if (role === 'super_admin') {
      return true
    }

    const currentPermissions = permissions.value
    if (!currentPermissions || !currentPermissions[role]) {
      const defaultPerms = defaultActionPermissions[role]
      return defaultPerms?.[category]?.[action] ?? false
    }

    const actionPermissions = currentPermissions[role].actionPermissions
    if (!actionPermissions) {
      const defaultPerms = defaultActionPermissions[role]
      return defaultPerms?.[category]?.[action] ?? false
    }

    if (!actionPermissions[category]) {
      const defaultPerms = defaultActionPermissions[role]
      return defaultPerms?.[category]?.[action] ?? false
    }

    return actionPermissions[category][action] ?? false
  }

  return {
    hasActionPermission
  }
}
