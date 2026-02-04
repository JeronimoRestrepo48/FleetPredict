import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { vehiclesAPI } from '../../services/api'
import { useAuth } from '../../context/AuthContext'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

const VehicleDetailPage = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { canManageVehicles } = useAuth()
  const [vehicle, setVehicle] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('details')

  useEffect(() => {
    fetchVehicle()
    fetchHistory()
  }, [id])

  const fetchVehicle = async () => {
    try {
      setLoading(true)
      const response = await vehiclesAPI.getVehicle(id)
      setVehicle(response.data.vehicle || response.data)
    } catch (error) {
      toast.error('Failed to load vehicle')
      navigate('/vehicles')
    } finally {
      setLoading(false)
    }
  }

  const fetchHistory = async () => {
    try {
      const response = await vehiclesAPI.getVehicleHistory(id)
      setHistory(response.data.history || [])
    } catch (error) {
      console.error('Failed to load history', error)
    }
  }

  const getStatusBadge = (status) => {
    const classes = {
      active: 'badge-success',
      inactive: 'badge bg-gray-100 text-gray-600',
      under_maintenance: 'badge-warning',
      retired: 'badge-danger',
    }
    return (
      <span className={classes[status] || 'badge'}>
        {status.replace('_', ' ')}
      </span>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!vehicle) {
    return null
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <Link to="/vehicles" className="text-gray-500 hover:text-gray-700">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </Link>
            <h1 className="text-2xl font-bold text-gray-900">
              {vehicle.display_name || `${vehicle.year} ${vehicle.make} ${vehicle.model}`}
            </h1>
          </div>
          <p className="text-gray-600 mt-1">{vehicle.license_plate} • {vehicle.vin}</p>
        </div>
        <div className="flex items-center space-x-3 mt-4 sm:mt-0">
          {getStatusBadge(vehicle.status)}
          {canManageVehicles && (
            <Link to={`/maintenance?vehicle=${id}`} className="btn-primary">
              Schedule Maintenance
            </Link>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('details')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'details'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Details
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'history'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Maintenance History
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'details' ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Vehicle Info */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Vehicle Information</h2>
            <dl className="space-y-4">
              <div className="flex justify-between">
                <dt className="text-gray-500">Make</dt>
                <dd className="text-gray-900 font-medium">{vehicle.make}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Model</dt>
                <dd className="text-gray-900 font-medium">{vehicle.model}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Year</dt>
                <dd className="text-gray-900 font-medium">{vehicle.year}</dd>
              </div>
              {vehicle.color && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Color</dt>
                  <dd className="text-gray-900 font-medium">{vehicle.color}</dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-gray-500">VIN</dt>
                <dd className="text-gray-900 font-medium font-mono text-sm">{vehicle.vin}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">License Plate</dt>
                <dd className="text-gray-900 font-medium">{vehicle.license_plate}</dd>
              </div>
              {vehicle.vehicle_type && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Type</dt>
                  <dd className="text-gray-900 font-medium">{vehicle.vehicle_type.name}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Operational Info */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Operational Data</h2>
            <dl className="space-y-4">
              <div className="flex justify-between">
                <dt className="text-gray-500">Status</dt>
                <dd>{getStatusBadge(vehicle.status)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Current Mileage</dt>
                <dd className="text-gray-900 font-medium">{vehicle.current_mileage?.toLocaleString()} km</dd>
              </div>
              {vehicle.fuel_type && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Fuel Type</dt>
                  <dd className="text-gray-900 font-medium">{vehicle.fuel_type}</dd>
                </div>
              )}
              {vehicle.fuel_capacity && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Fuel Capacity</dt>
                  <dd className="text-gray-900 font-medium">{vehicle.fuel_capacity} L</dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-gray-500">Maintenance Tasks</dt>
                <dd className="text-gray-900 font-medium">{vehicle.maintenance_count}</dd>
              </div>
              {vehicle.last_maintenance && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Last Maintenance</dt>
                  <dd className="text-gray-900 font-medium">
                    {format(new Date(vehicle.last_maintenance), 'MMM d, yyyy')}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Assignment Info */}
          {vehicle.assigned_driver && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Assignment</h2>
              <div className="flex items-center">
                <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center">
                  <span className="text-primary-600 font-medium">
                    {vehicle.assigned_driver.first_name?.[0]}{vehicle.assigned_driver.last_name?.[0]}
                  </span>
                </div>
                <div className="ml-3">
                  <p className="text-gray-900 font-medium">
                    {vehicle.assigned_driver.full_name}
                  </p>
                  <p className="text-sm text-gray-500">{vehicle.assigned_driver.email}</p>
                </div>
              </div>
            </div>
          )}

          {/* Notes */}
          {vehicle.notes && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Notes</h2>
              <p className="text-gray-600 whitespace-pre-wrap">{vehicle.notes}</p>
            </div>
          )}
        </div>
      ) : (
        /* Maintenance History Tab */
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Maintenance History</h2>
          
          {history.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Task</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cost</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Mileage</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {history.map((task) => (
                    <tr key={task.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <Link 
                          to={`/maintenance/${task.id}`}
                          className="font-medium text-gray-900 hover:text-primary-600"
                        >
                          {task.title}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 capitalize">
                        {task.maintenance_type}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {task.completion_date && format(new Date(task.completion_date), 'MMM d, yyyy')}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {task.actual_cost ? `$${task.actual_cost.toLocaleString()}` : '-'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {task.mileage_at_maintenance?.toLocaleString() || '-'} km
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">
              No maintenance history for this vehicle.
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export default VehicleDetailPage
