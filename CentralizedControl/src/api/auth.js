import api from './index'

export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  logout: () => api.post('/auth/logout'),
  getCurrentUser: () => api.get('/auth/me'),
  changePassword: (data) => api.put('/auth/password', data),
  updateProfile: (data) => api.put('/auth/profile', data),
  uploadAvatar: (imageBase64) => api.post('/auth/avatar', { image: imageBase64 })
}
