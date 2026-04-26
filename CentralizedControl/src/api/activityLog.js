import api from './index'

export const activityLogAPI = {
  getAll: (params = {}) => api.get('/activity-logs', { params }),
  getRecent: (limit = 50) => api.get('/activity-logs', { params: { limit } }),
  getByCategory: (category, limit = 50) => api.get('/activity-logs', { params: { category, limit } }),
  getMyLogs: (limit = 50) => api.get('/activity-logs/my', { params: { limit } }),
  delete: (logId) => api.delete(`/activity-logs/${logId}`),
  batchDelete: (logIds) => api.delete('/activity-logs/batch', { data: { ids: logIds } }),
  clearAll: () => api.delete('/activity-logs/clear')
}
