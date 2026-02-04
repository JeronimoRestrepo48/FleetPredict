import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { dashboardAPI } from '../../services/api'
import { useAuth } from '../../context/AuthContext'
import { format } from 'date-fns'

const DashboardPage = () => {
  const { user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      const response = await dashboardAPI.getSummary()
      setData(response.data)
    } catch (err) {
      setError('Failed to load dashboard data')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-danger-500">{error}</p>
        <button onClick={fetchDashboardData} className="mt-4 btn-primary">
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {user?.first_name}!
        </h1>
        <p className="text-gray-600">Here's an overview of your fleet.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total Vehicles"
          value={data?.summary?.total_vehicles || 0}
          icon={<TruckIcon />}
          color="blue"
        />
        <StatsCard
          title="Fleet Availability"
          value={`${data?.summary?.fleet_availability || 0}%`}
          icon={<CheckIcon />}
          color="green"
        />
        <StatsCard
          title="Overdue Tasks"
          value={data?.summary?.overdue_tasks || 0}
          icon={<AlertIcon />}
          color={data?.summary?.overdue_tasks > 0 ? 'red' : 'gray'}
        />
        <StatsCard
          title="Monthly Costs"
          value={`$${(data?.costs?.monthly_total || 0).toLocaleString()}`}
          icon={<CurrencyIcon />}
          color="purple"
        />
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Vehicles by Status */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Vehicles by Status</h2>
            <Link to="/vehicles" className="text-sm text-primary-600 hover:text-primary-700">
              View all
            </Link>
          </div>
          <div className="space-y-3">
            <StatusBar 
              label="Active" 
              count={data?.vehicles?.by_status?.active || 0}
              total={data?.vehicles?.total || 1}
              color="bg-success-500"
            />
            <StatusBar 
              label="Under Maintenance" 
              count={data?.vehicles?.by_status?.under_maintenance || 0}
              total={data?.vehicles?.total || 1}
              color="bg-warning-500"
            />
            <StatusBar 
              label="Inactive" 
              count={data?.vehicles?.by_status?.inactive || 0}
              total={data?.vehicles?.total || 1}
              color="bg-gray-400"
            />
            <StatusBar 
              label="Retired" 
              count={data?.vehicles?.by_status?.retired || 0}
              total={data?.vehicles?.total || 1}
              color="bg-danger-500"
            />
          </div>
        </div>

        {/* Maintenance by Status */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Maintenance Tasks</h2>
            <Link to="/maintenance" className="text-sm text-primary-600 hover:text-primary-700">
              View all
            </Link>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <TaskStatusCard 
              label="Scheduled" 
              count={data?.maintenance?.by_status?.scheduled || 0}
              color="text-primary-600 bg-primary-50"
            />
            <TaskStatusCard 
              label="In Progress" 
              count={data?.maintenance?.by_status?.in_progress || 0}
              color="text-warning-600 bg-warning-50"
            />
            <TaskStatusCard 
              label="Completed" 
              count={data?.maintenance?.by_status?.completed || 0}
              color="text-success-600 bg-success-50"
            />
            <TaskStatusCard 
              label="Overdue" 
              count={data?.maintenance?.by_status?.overdue || 0}
              color="text-danger-600 bg-danger-50"
            />
          </div>
        </div>
      </div>

      {/* Upcoming Maintenance */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Upcoming Maintenance (Next 7 Days)
          </h2>
          <Link to="/maintenance" className="text-sm text-primary-600 hover:text-primary-700">
            View all
          </Link>
        </div>
        
        {data?.maintenance?.upcoming?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Task</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vehicle</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Priority</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {data.maintenance.upcoming.map((task) => (
                  <tr key={task.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <Link 
                        to={`/maintenance/${task.id}`}
                        className="text-sm font-medium text-gray-900 hover:text-primary-600"
                      >
                        {task.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <Link 
                        to={`/vehicles/${task.vehicle_id}`}
                        className="text-sm text-gray-600 hover:text-primary-600"
                      >
                        {task.vehicle} ({task.license_plate})
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {format(new Date(task.scheduled_date), 'MMM d, yyyy')}
                    </td>
                    <td className="px-4 py-3">
                      <PriorityBadge priority={task.priority} />
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={task.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">
            No upcoming maintenance tasks in the next 7 days.
          </p>
        )}
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recently Completed</h2>
        
        {data?.recent_activity?.completed_tasks?.length > 0 ? (
          <div className="space-y-3">
            {data.recent_activity.completed_tasks.map((task) => (
              <div key={task.id} className="flex items-center justify-between py-2 border-b last:border-0">
                <div>
                  <Link 
                    to={`/maintenance/${task.id}`}
                    className="font-medium text-gray-900 hover:text-primary-600"
                  >
                    {task.title}
                  </Link>
                  <p className="text-sm text-gray-500">{task.vehicle}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-600">
                    {format(new Date(task.completion_date), 'MMM d, yyyy')}
                  </p>
                  {task.actual_cost && (
                    <p className="text-sm text-gray-500">${task.actual_cost.toLocaleString()}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">
            No recently completed tasks.
          </p>
        )}
      </div>
    </div>
  )
}

// Components
const StatsCard = ({ title, value, icon, color }) => {
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    red: 'bg-red-500',
    purple: 'bg-purple-500',
    gray: 'bg-gray-500',
  }

  return (
    <div className="card flex items-center">
      <div className={`p-3 rounded-lg ${colorClasses[color]} text-white mr-4`}>
        {icon}
      </div>
      <div>
        <p className="text-sm text-gray-500">{title}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
      </div>
    </div>
  )
}

const StatusBar = ({ label, count, total, color }) => {
  const percentage = total > 0 ? (count / total) * 100 : 0
  
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600">{label}</span>
        <span className="font-medium">{count}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className={`${color} h-2 rounded-full transition-all`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

const TaskStatusCard = ({ label, count, color }) => (
  <div className={`p-4 rounded-lg ${color}`}>
    <p className="text-2xl font-bold">{count}</p>
    <p className="text-sm">{label}</p>
  </div>
)

const PriorityBadge = ({ priority }) => {
  const classes = {
    low: 'badge bg-gray-100 text-gray-600',
    medium: 'badge bg-blue-100 text-blue-600',
    high: 'badge bg-warning-50 text-warning-600',
    critical: 'badge bg-danger-50 text-danger-600',
  }
  
  return (
    <span className={classes[priority] || classes.medium}>
      {priority}
    </span>
  )
}

const StatusBadge = ({ status }) => {
  const classes = {
    scheduled: 'badge-primary',
    in_progress: 'badge-warning',
    completed: 'badge-success',
    overdue: 'badge-danger',
    cancelled: 'badge bg-gray-100 text-gray-600',
  }
  
  return (
    <span className={classes[status] || 'badge'}>
      {status.replace('_', ' ')}
    </span>
  )
}

// Icons
const TruckIcon = () => (
  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0" />
  </svg>
)

const CheckIcon = () => (
  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
)

const AlertIcon = () => (
  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
  </svg>
)

const CurrencyIcon = () => (
  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
)

export default DashboardPage
