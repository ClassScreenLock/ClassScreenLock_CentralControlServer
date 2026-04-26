import { ref } from 'vue'

const permissionCache = ref(null)

export const setPermissions = (permissions) => {
  permissionCache.value = permissions
}

export const getPermissions = () => {
  return permissionCache.value
}

export const clearPermissions = () => {
  permissionCache.value = null
}

export const refreshPermissions = async () => {
  try {
    const api = await import('@/api')
    const response = await api.default.get('/permissions')
    setPermissions(response)
    return response
  } catch (error) {
    console.error('Failed to refresh permissions:', error)
    return null
  }
}
