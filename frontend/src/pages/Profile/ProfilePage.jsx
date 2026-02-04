import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { usersAPI } from '../../services/api'
import toast from 'react-hot-toast'

const ProfilePage = () => {
  const { user, updateUser } = useAuth()
  const [loading, setLoading] = useState(false)
  const [passwordLoading, setPasswordLoading] = useState(false)
  
  const [profileData, setProfileData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    phone: user?.profile?.phone || '',
  })
  
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    new_password_confirm: '',
  })

  const handleProfileChange = (e) => {
    setProfileData({ ...profileData, [e.target.name]: e.target.value })
  }

  const handlePasswordChange = (e) => {
    setPasswordData({ ...passwordData, [e.target.name]: e.target.value })
  }

  const handleProfileSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    
    try {
      const response = await usersAPI.updateProfile(profileData)
      updateUser(response.data.user)
      toast.success('Profile updated successfully')
    } catch (error) {
      toast.error(error.response?.data?.message || 'Failed to update profile')
    }
    
    setLoading(false)
  }

  const handlePasswordSubmit = async (e) => {
    e.preventDefault()
    setPasswordLoading(true)
    
    try {
      await usersAPI.changePassword(passwordData)
      toast.success('Password changed successfully')
      setPasswordData({
        current_password: '',
        new_password: '',
        new_password_confirm: '',
      })
    } catch (error) {
      const message = error.response?.data?.current_password?.[0] ||
                     error.response?.data?.new_password_confirm?.[0] ||
                     error.response?.data?.message ||
                     'Failed to change password'
      toast.error(message)
    }
    
    setPasswordLoading(false)
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Profile Settings</h1>
      
      <div className="space-y-6">
        {/* Profile Information */}
        <div className="card">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Profile Information</h2>
          
          <form onSubmit={handleProfileSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="first_name" className="label">First name</label>
                <input
                  id="first_name"
                  name="first_name"
                  type="text"
                  className="input"
                  value={profileData.first_name}
                  onChange={handleProfileChange}
                />
              </div>
              
              <div>
                <label htmlFor="last_name" className="label">Last name</label>
                <input
                  id="last_name"
                  name="last_name"
                  type="text"
                  className="input"
                  value={profileData.last_name}
                  onChange={handleProfileChange}
                />
              </div>
            </div>
            
            <div>
              <label htmlFor="email" className="label">Email</label>
              <input
                id="email"
                type="email"
                className="input bg-gray-100"
                value={user?.email || ''}
                disabled
              />
              <p className="mt-1 text-xs text-gray-500">Email cannot be changed</p>
            </div>
            
            <div>
              <label htmlFor="phone" className="label">Phone number</label>
              <input
                id="phone"
                name="phone"
                type="tel"
                className="input"
                value={profileData.phone}
                onChange={handleProfileChange}
                placeholder="+1 (555) 000-0000"
              />
            </div>
            
            <div>
              <label className="label">Role</label>
              <div className="px-3 py-2 bg-gray-100 rounded-lg text-gray-700 capitalize">
                {user?.role?.replace('_', ' ')}
              </div>
            </div>
            
            <div className="pt-4">
              <button
                type="submit"
                disabled={loading}
                className="btn-primary"
              >
                {loading ? 'Saving...' : 'Save changes'}
              </button>
            </div>
          </form>
        </div>

        {/* Change Password */}
        <div className="card">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Change Password</h2>
          
          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            <div>
              <label htmlFor="current_password" className="label">Current password</label>
              <input
                id="current_password"
                name="current_password"
                type="password"
                className="input"
                value={passwordData.current_password}
                onChange={handlePasswordChange}
                required
              />
            </div>
            
            <div>
              <label htmlFor="new_password" className="label">New password</label>
              <input
                id="new_password"
                name="new_password"
                type="password"
                className="input"
                value={passwordData.new_password}
                onChange={handlePasswordChange}
                required
              />
              <p className="mt-1 text-xs text-gray-500">At least 8 characters</p>
            </div>
            
            <div>
              <label htmlFor="new_password_confirm" className="label">Confirm new password</label>
              <input
                id="new_password_confirm"
                name="new_password_confirm"
                type="password"
                className="input"
                value={passwordData.new_password_confirm}
                onChange={handlePasswordChange}
                required
              />
            </div>
            
            <div className="pt-4">
              <button
                type="submit"
                disabled={passwordLoading}
                className="btn-primary"
              >
                {passwordLoading ? 'Changing...' : 'Change password'}
              </button>
            </div>
          </form>
        </div>

        {/* Notification Settings */}
        <div className="card">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Notification Settings</h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Email notifications</p>
                <p className="text-sm text-gray-500">Receive email alerts</p>
              </div>
              <input
                type="checkbox"
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                defaultChecked={user?.profile?.notification_settings?.email_enabled}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Maintenance due alerts</p>
                <p className="text-sm text-gray-500">Get notified when maintenance is due</p>
              </div>
              <input
                type="checkbox"
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                defaultChecked={user?.profile?.notification_settings?.maintenance_due}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Critical alerts</p>
                <p className="text-sm text-gray-500">Get notified about critical issues</p>
              </div>
              <input
                type="checkbox"
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                defaultChecked={user?.profile?.notification_settings?.critical_alerts}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ProfilePage
