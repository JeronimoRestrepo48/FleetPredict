import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { maintenanceAPI } from '../../services/api'
import { useAuth } from '../../context/AuthContext'
import MaintenanceForm from '../../components/Maintenance/MaintenanceForm'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

const MaintenancePage = () => {
  const { canManageMaintenance } = useAuth()
  const [searchParams] = useSearchParams()
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingTask, setEditingTask] = useState(null)
  const [filters, setFilters] = useState({
    status: searchParams.get('status') || '',
    vehicle: searchParams.get('vehicle') || '',
    priority: '',
    search: '',
  })

  useEffect(() => {
    fetchTasks()
  }, [filters])

  const fetchTasks = async () => {
    try {
      setLoading(true)
      const params = {}
      if (filters.status) params.status = filters.status
      if (filters.vehicle) params.vehicle = filters.vehicle
      if (filters.priority) params.priority = filters.priority
      if (filters.search) params.search = filters.search
      
      const response = await maintenanceAPI.getTasks(params)
      setTasks(response.data.results || response.data)
    } catch (error) {
      toast.error('Failed to load maintenance tasks')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this task?')) return
    
    try {
      await maintenanceAPI.deleteTask(id)
      toast.success('Task deleted successfully')
      fetchTasks()
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to delete task')
    }
  }

  const handleComplete = async (id) => {
    try {
      await maintenanceAPI.completeTask(id, {})
      toast.success('Task marked as completed')
      fetchTasks()
    } catch (error) {
      toast.error('Failed to complete task')
    }
  }

  const handleFormClose = () => {
    setShowForm(false)
    setEditingTask(null)
  }

  const handleFormSuccess = () => {
    handleFormClose()
    fetchTasks()
  }

  const getStatusBadge = (status) => {
    const classes = {
      scheduled: 'badge-primary',
      in_progress: 'badge-warning',
      completed: 'badge-success',
      cancelled: 'badge bg-gray-100 text-gray-600',
      overdue: 'badge-danger',
    }
    return (
      <span className={classes[status] || 'badge'}>
        {status.replace('_', ' ')}
      </span>
    )
  }

  const getPriorityBadge = (priority) => {
    const classes = {
      low: 'text-gray-600',
      medium: 'text-blue-600',
      high: 'text-warning-600',
      critical: 'text-danger-600 font-bold',
    }
    return <span className={classes[priority] || ''}>{priority}</span>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Maintenance</h1>
          <p className="text-gray-600">Manage maintenance tasks</p>
        </div>
        {canManageMaintenance && (
          <button
            onClick={() => setShowForm(true)}
            className="btn-primary mt-4 sm:mt-0"
          >
            <svg className="h-5 w-5 mr-2 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Task
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search tasks..."
              className="input"
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            />
          </div>
          <select
            className="input sm:w-40"
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          >
            <option value="">All Status</option>
            <option value="scheduled">Scheduled</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="overdue">Overdue</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <select
            className="input sm:w-40"
            value={filters.priority}
            onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
          >
            <option value="">All Priority</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>
      </div>

      {/* Tasks Table */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        ) : tasks.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Task</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vehicle</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Priority</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {tasks.map((task) => (
                  <tr key={task.id} className={`hover:bg-gray-50 ${task.is_overdue ? 'bg-red-50' : ''}`}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link 
                        to={`/maintenance/${task.id}`}
                        className="font-medium text-gray-900 hover:text-primary-600"
                      >
                        {task.title}
                      </Link>
                      {task.is_overdue && (
                        <span className="ml-2 text-xs text-danger-600">Overdue!</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link 
                        to={`/vehicles/${task.vehicle}`}
                        className="text-sm text-gray-600 hover:text-primary-600"
                      >
                        {task.vehicle_display} ({task.vehicle_license_plate})
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 capitalize">
                      {task.maintenance_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {format(new Date(task.scheduled_date), 'MMM d, yyyy')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm capitalize">
                      {getPriorityBadge(task.priority)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(task.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                      <Link
                        to={`/maintenance/${task.id}`}
                        className="text-primary-600 hover:text-primary-900 mr-3"
                      >
                        View
                      </Link>
                      {canManageMaintenance && task.status !== 'completed' && task.status !== 'cancelled' && (
                        <>
                          <button
                            onClick={() => handleComplete(task.id)}
                            className="text-success-600 hover:text-success-900 mr-3"
                          >
                            Complete
                          </button>
                          <button
                            onClick={() => {
                              setEditingTask(task)
                              setShowForm(true)
                            }}
                            className="text-gray-600 hover:text-gray-900 mr-3"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDelete(task.id)}
                            className="text-danger-600 hover:text-danger-900"
                          >
                            Delete
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No maintenance tasks</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by creating a maintenance task.</p>
            {canManageMaintenance && (
              <button
                onClick={() => setShowForm(true)}
                className="btn-primary mt-4"
              >
                Add Task
              </button>
            )}
          </div>
        )}
      </div>

      {/* Maintenance Form Modal */}
      {showForm && (
        <MaintenanceForm
          task={editingTask}
          vehicleId={filters.vehicle}
          onClose={handleFormClose}
          onSuccess={handleFormSuccess}
        />
      )}
    </div>
  )
}

export default MaintenancePage
