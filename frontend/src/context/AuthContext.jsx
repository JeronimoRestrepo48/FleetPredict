import { createContext, useContext, useState, useEffect } from 'react'
import { authAPI, usersAPI } from '../services/api'
import toast from 'react-hot-toast'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Check for existing session on mount
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token')
      const savedUser = localStorage.getItem('user')
      
      if (token && savedUser) {
        try {
          // Verify token by fetching profile
          const response = await usersAPI.getProfile()
          setUser(response.data)
          localStorage.setItem('user', JSON.stringify(response.data))
        } catch (error) {
          // Token invalid, clear storage
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user')
        }
      }
      setLoading(false)
    }

    initAuth()
  }, [])

  const login = async (email, password) => {
    try {
      const response = await authAPI.login({ email, password })
      const { user: userData, tokens } = response.data
      
      localStorage.setItem('access_token', tokens.access)
      localStorage.setItem('refresh_token', tokens.refresh)
      localStorage.setItem('user', JSON.stringify(userData))
      
      setUser(userData)
      toast.success('Login successful!')
      return { success: true }
    } catch (error) {
      const message = error.response?.data?.detail || 
                     error.response?.data?.message ||
                     'Login failed. Please check your credentials.'
      toast.error(message)
      return { success: false, error: message }
    }
  }

  const register = async (data) => {
    try {
      const response = await authAPI.register(data)
      const { user: userData, tokens } = response.data
      
      localStorage.setItem('access_token', tokens.access)
      localStorage.setItem('refresh_token', tokens.refresh)
      localStorage.setItem('user', JSON.stringify(userData))
      
      setUser(userData)
      toast.success('Registration successful!')
      return { success: true }
    } catch (error) {
      const errors = error.response?.data || {}
      const message = Object.values(errors).flat().join(' ') || 'Registration failed.'
      toast.error(message)
      return { success: false, error: message, errors }
    }
  }

  const logout = async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        await authAPI.logout(refreshToken)
      }
    } catch (error) {
      // Ignore logout errors
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      setUser(null)
      toast.success('Logged out successfully')
    }
  }

  const updateUser = (userData) => {
    setUser(userData)
    localStorage.setItem('user', JSON.stringify(userData))
  }

  // Permission helpers
  const isAdmin = user?.role === 'administrator'
  const isFleetManager = user?.role === 'fleet_manager'
  const isMechanic = user?.role === 'mechanic'
  const isDriver = user?.role === 'driver'
  
  const canManageVehicles = isAdmin || isFleetManager
  const canManageMaintenance = isAdmin || isFleetManager || isMechanic
  const canViewReports = isAdmin || isFleetManager

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    updateUser,
    isAdmin,
    isFleetManager,
    isMechanic,
    isDriver,
    canManageVehicles,
    canManageMaintenance,
    canViewReports,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
