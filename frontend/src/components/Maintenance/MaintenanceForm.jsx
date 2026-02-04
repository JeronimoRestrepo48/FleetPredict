import { useState, useEffect } from 'react'
import { maintenanceAPI, vehiclesAPI } from '../../services/api'
import toast from 'react-hot-toast'

const MaintenanceForm = ({ task, vehicleId, onClose, onSuccess }) => {
  const [loading, setLoading] = useState(false)
  const [vehicles, setVehicles] = useState([])
  const [formData, setFormData] = useState({
    title: task?.title || '',
    description: task?.description || '',
    vehicle: task?.vehicle?.id || vehicleId || '',
    maintenance_type: task?.maintenance_type || 'preventive',
    priority: task?.priority || 'medium',
    scheduled_date: task?.scheduled_date || '',
    estimated_duration: task?.estimated_duration || '',
    estimated_cost: task?.estimated_cost || '',
    assignee: task?.assignee?.id || '',
  })

  useEffect(() => {
    fetchVehicles()
  }, [])

  const fetchVehicles = async () => {
    try {
      const response = await vehiclesAPI.getVehicles({ status: 'active' })
      setVehicles(response.data.results || response.data || [])
    } catch (error) {
      console.error('Failed to load vehicles', error)
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData({ ...formData, [name]: value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      const data = {
        ...formData,
        estimated_duration: formData.estimated_duration || null,
        estimated_cost: formData.estimated_cost || null,
        assignee: formData.assignee || null,
      }

      if (task) {
        await maintenanceAPI.updateTask(task.id, data)
        toast.success('Task updated successfully')
      } else {
        await maintenanceAPI.createTask(data)
        toast.success('Task created successfully')
      }
      onSuccess()
    } catch (error) {
      const message = error.response?.data?.message ||
                     Object.values(error.response?.data || {}).flat().join(' ') ||
                     'Failed to save task'
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        {/* Backdrop */}
        <div className="fixed inset-0 bg-black bg-opacity-50" onClick={onClose} />
        
        {/* Modal */}
        <div className="relative bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div className="sticky top-0 bg-white px-6 py-4 border-b flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              {task ? 'Edit Task' : 'Add Maintenance Task'}
            </h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Basic Info */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">Task Information</h3>
              <div className="space-y-4">
                <div>
                  <label className="label">Title *</label>
                  <input
                    type="text"
                    name="title"
                    className="input"
                    value={formData.title}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div>
                  <label className="label">Description</label>
                  <textarea
                    name="description"
                    rows={3}
                    className="input"
                    value={formData.description}
                    onChange={handleChange}
                  />
                </div>
              </div>
            </div>

            {/* Vehicle & Type */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">Vehicle & Type</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label">Vehicle *</label>
                  <select
                    name="vehicle"
                    className="input"
                    value={formData.vehicle}
                    onChange={handleChange}
                    required
                  >
                    <option value="">Select vehicle...</option>
                    {vehicles.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.display_name || `${v.make} ${v.model}`} ({v.license_plate})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label">Maintenance Type *</label>
                  <select
                    name="maintenance_type"
                    className="input"
                    value={formData.maintenance_type}
                    onChange={handleChange}
                    required
                  >
                    <option value="preventive">Preventive</option>
                    <option value="corrective">Corrective</option>
                    <option value="inspection">Inspection</option>
                    <option value="emergency">Emergency</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Schedule */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">Schedule</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="label">Scheduled Date *</label>
                  <input
                    type="date"
                    name="scheduled_date"
                    className="input"
                    value={formData.scheduled_date}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div>
                  <label className="label">Priority</label>
                  <select
                    name="priority"
                    className="input"
                    value={formData.priority}
                    onChange={handleChange}
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
                <div>
                  <label className="label">Est. Duration (min)</label>
                  <input
                    type="number"
                    name="estimated_duration"
                    className="input"
                    min={0}
                    value={formData.estimated_duration}
                    onChange={handleChange}
                  />
                </div>
              </div>
            </div>

            {/* Cost */}
            <div>
              <label className="label">Estimated Cost ($)</label>
              <input
                type="number"
                name="estimated_cost"
                className="input"
                step="0.01"
                min={0}
                value={formData.estimated_cost}
                onChange={handleChange}
              />
            </div>

            {/* Actions */}
            <div className="flex justify-end space-x-3 pt-4 border-t">
              <button
                type="button"
                onClick={onClose}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="btn-primary"
              >
                {loading ? 'Saving...' : task ? 'Update Task' : 'Create Task'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default MaintenanceForm
