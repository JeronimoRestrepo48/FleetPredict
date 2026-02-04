import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // If 401 and we haven't already tried to refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          const response = await axios.post(`${API_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          })

          const { access } = response.data
          localStorage.setItem('access_token', access)

          // Retry the original request
          originalRequest.headers.Authorization = `Bearer ${access}`
          return api(originalRequest)
        }
      } catch (refreshError) {
        // Refresh failed, logout user
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

export default api

// ============== Auth API ==============
export const authAPI = {
  login: (data) => api.post('/auth/login/', data),
  register: (data) => api.post('/auth/register/', data),
  logout: (refresh) => api.post('/auth/logout/', { refresh }),
  refreshToken: (refresh) => api.post('/auth/token/refresh/', { refresh }),
}

// ============== Users API ==============
export const usersAPI = {
  getProfile: () => api.get('/users/profile/'),
  updateProfile: (data) => api.put('/users/profile/', data),
  changePassword: (data) => api.post('/users/profile/change-password/', data),
  getUsers: (params) => api.get('/users/', { params }),
  getUser: (id) => api.get(`/users/${id}/`),
  updateUser: (id, data) => api.patch(`/users/${id}/`, data),
}

// ============== Vehicles API ==============
export const vehiclesAPI = {
  getVehicles: (params) => api.get('/vehicles/', { params }),
  getVehicle: (id) => api.get(`/vehicles/${id}/`),
  createVehicle: (data) => api.post('/vehicles/', data),
  updateVehicle: (id, data) => api.patch(`/vehicles/${id}/`, data),
  deleteVehicle: (id) => api.delete(`/vehicles/${id}/`),
  getVehicleHistory: (id) => api.get(`/vehicles/${id}/history/`),
  
  // Vehicle Types
  getVehicleTypes: () => api.get('/vehicles/types/'),
  createVehicleType: (data) => api.post('/vehicles/types/', data),
  updateVehicleType: (id, data) => api.patch(`/vehicles/types/${id}/`, data),
  deleteVehicleType: (id) => api.delete(`/vehicles/types/${id}/`),
}

// ============== Maintenance API ==============
export const maintenanceAPI = {
  getTasks: (params) => api.get('/maintenance/', { params }),
  getTask: (id) => api.get(`/maintenance/${id}/`),
  createTask: (data) => api.post('/maintenance/', data),
  updateTask: (id, data) => api.patch(`/maintenance/${id}/`, data),
  deleteTask: (id) => api.delete(`/maintenance/${id}/`),
  completeTask: (id, data) => api.post(`/maintenance/${id}/complete/`, data),
  changeStatus: (id, data) => api.post(`/maintenance/${id}/status/`, data),
  
  // Documents
  uploadDocument: (taskId, formData) => api.post(`/maintenance/${taskId}/documents/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  deleteDocument: (id) => api.delete(`/maintenance/documents/${id}/`),
  
  // Comments
  getComments: (taskId) => api.get(`/maintenance/${taskId}/comments/`),
  addComment: (taskId, data) => api.post(`/maintenance/${taskId}/comments/`, data),
}

// ============== Dashboard API ==============
export const dashboardAPI = {
  getSummary: () => api.get('/dashboard/summary/'),
  getStats: () => api.get('/dashboard/stats/'),
}
