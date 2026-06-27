import api from './index'

export const organizationAPI = {
  getAll: () => api.get('/organizations'),
  getAllWithDeviceCounts: () => api.get('/organizations/with-device-counts'),
  getById: (id) => api.get(`/organizations/${id}`),
  create: (data) => api.post('/organizations', data),
  update: (id, data) => api.put(`/organizations/${id}`, data),
  delete: (id) => api.delete(`/organizations/${id}`),
  getDevices: (id) => api.get(`/organizations/${id}/devices`),
  getSecurityConfig: (id) => api.get(`/organizations/${id}/security-config`),
  updateSecurityConfig: (id, config) => api.put(`/organizations/${id}/security-config`, config),
  getNetworkConfig: (id) => api.get(`/organizations/${id}/network-config`),
  updateNetworkConfig: (id, config) => api.put(`/organizations/${id}/network-config`, config),
  exportConfig: (id) => api.get(`/organizations/${id}/export-config`),
  getScheduleConfig: (id) => api.get(`/organizations/${id}/schedule-config`),
  updateScheduleConfig: (id, config) => api.put(`/organizations/${id}/schedule-config`, config)
}

export const deviceAPI = {
  getAll: () => api.get('/devices'),
  getById: (id) => api.get(`/devices/${id}`),
  updateStatus: (id, status) => api.patch(`/devices/${id}/status`, { status }),
  delete: (id) => api.delete(`/devices/${id}`),
  getSoftware: (id, params = {}) => api.get(`/devices/${id}/software`, { params }),
  refreshSoftware: (id) => api.post(`/devices/${id}/software/refresh`),
  getScheduleConfig: (id) => api.get(`/devices/${id}/schedule-config`),
  updateScheduleConfig: (id, config) => api.put(`/devices/${id}/schedule-config`, config),
  deleteScheduleConfig: (id) => api.delete(`/devices/${id}/schedule-config`)
}
