import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { maintenanceAPI } from '../../services/api'
import { useAuth } from '../../context/AuthContext'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

const MaintenanceDetailPage = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { canManageMaintenance } = useAuth()
  const [task, setTask] = useState(null)
  const [loading, setLoading] = useState(true)
  const [completeModalOpen, setCompleteModalOpen] = useState(false)
  const [completeData, setCompleteData] = useState({
    completion_notes: '',
    actual_cost: '',
    mileage_at_maintenance: '',
  })
  const [newComment, setNewComment] = useState('')

  useEffect(() => {
    fetchTask()
  }, [id])

  const fetchTask = async () => {
    try {
      setLoading(true)
      const response = await maintenanceAPI.getTask(id)
      setTask(response.data.task || response.data)
    } catch (error) {
      toast.error('Failed to load task')
      navigate('/maintenance')
    } finally {
      setLoading(false)
    }
  }

  const handleComplete = async () => {
    try {
      const data = {
        completion_notes: completeData.completion_notes,
        actual_cost: completeData.actual_cost ? parseFloat(completeData.actual_cost) : null,
        mileage_at_maintenance: completeData.mileage_at_maintenance ? parseInt(completeData.mileage_at_maintenance) : null,
      }
      await maintenanceAPI.completeTask(id, data)
      toast.success('Task completed successfully')
      setCompleteModalOpen(false)
      fetchTask()
    } catch (error) {
      toast.error('Failed to complete task')
    }
  }

  const handleAddComment = async (e) => {
    e.preventDefault()
    if (!newComment.trim()) return

    try {
      await maintenanceAPI.addComment(id, { content: newComment })
      toast.success('Comment added')
      setNewComment('')
      fetchTask()
    } catch (error) {
      toast.error('Failed to add comment')
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      await maintenanceAPI.uploadDocument(id, formData)
      toast.success('Document uploaded')
      fetchTask()
    } catch (error) {
      toast.error('Failed to upload document')
    }
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
      low: 'badge bg-gray-100 text-gray-600',
      medium: 'badge bg-blue-100 text-blue-600',
      high: 'badge bg-warning-50 text-warning-600',
      critical: 'badge bg-danger-50 text-danger-600',
    }
    return <span className={classes[priority] || 'badge'}>{priority}</span>
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!task) return null

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <Link to="/maintenance" className="text-gray-500 hover:text-gray-700">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </Link>
            <h1 className="text-2xl font-bold text-gray-900">{task.title}</h1>
          </div>
          <p className="text-gray-600 mt-1">
            <Link to={`/vehicles/${task.vehicle?.id}`} className="hover:text-primary-600">
              {task.vehicle?.display_name || `${task.vehicle?.make} ${task.vehicle?.model}`}
            </Link>
            {' '} ({task.vehicle?.license_plate})
          </p>
        </div>
        <div className="flex items-center space-x-3 mt-4 sm:mt-0">
          {getStatusBadge(task.status)}
          {getPriorityBadge(task.priority)}
          {canManageMaintenance && task.status !== 'completed' && task.status !== 'cancelled' && (
            <button
              onClick={() => setCompleteModalOpen(true)}
              className="btn-success"
            >
              Mark Complete
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Task Details */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Task Details</h2>
            
            {task.description && (
              <div className="mb-4">
                <h3 className="text-sm font-medium text-gray-500 mb-1">Description</h3>
                <p className="text-gray-900 whitespace-pre-wrap">{task.description}</p>
              </div>
            )}

            <dl className="grid grid-cols-2 gap-4">
              <div>
                <dt className="text-sm text-gray-500">Type</dt>
                <dd className="text-gray-900 font-medium capitalize">{task.maintenance_type}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Scheduled Date</dt>
                <dd className="text-gray-900 font-medium">
                  {format(new Date(task.scheduled_date), 'MMM d, yyyy')}
                </dd>
              </div>
              {task.estimated_duration && (
                <div>
                  <dt className="text-sm text-gray-500">Estimated Duration</dt>
                  <dd className="text-gray-900 font-medium">{task.estimated_duration} minutes</dd>
                </div>
              )}
              {task.assignee && (
                <div>
                  <dt className="text-sm text-gray-500">Assigned To</dt>
                  <dd className="text-gray-900 font-medium">{task.assignee.full_name}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Completion Details (if completed) */}
          {task.status === 'completed' && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Completion Details</h2>
              <dl className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm text-gray-500">Completion Date</dt>
                  <dd className="text-gray-900 font-medium">
                    {task.completion_date && format(new Date(task.completion_date), 'MMM d, yyyy')}
                  </dd>
                </div>
                {task.actual_cost && (
                  <div>
                    <dt className="text-sm text-gray-500">Actual Cost</dt>
                    <dd className="text-gray-900 font-medium">${task.actual_cost.toLocaleString()}</dd>
                  </div>
                )}
                {task.mileage_at_maintenance && (
                  <div>
                    <dt className="text-sm text-gray-500">Mileage at Maintenance</dt>
                    <dd className="text-gray-900 font-medium">{task.mileage_at_maintenance.toLocaleString()} km</dd>
                  </div>
                )}
              </dl>
              {task.completion_notes && (
                <div className="mt-4">
                  <dt className="text-sm text-gray-500 mb-1">Notes</dt>
                  <dd className="text-gray-900 whitespace-pre-wrap">{task.completion_notes}</dd>
                </div>
              )}
            </div>
          )}

          {/* Documents */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Documents</h2>
              {canManageMaintenance && (
                <label className="btn-secondary cursor-pointer">
                  <svg className="h-4 w-4 mr-2 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                  Upload
                  <input type="file" className="hidden" onChange={handleFileUpload} />
                </label>
              )}
            </div>
            
            {task.documents?.length > 0 ? (
              <ul className="divide-y divide-gray-200">
                {task.documents.map((doc) => (
                  <li key={doc.id} className="py-3 flex items-center justify-between">
                    <div className="flex items-center">
                      <svg className="h-5 w-5 text-gray-400 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                      </svg>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{doc.filename}</p>
                        <p className="text-xs text-gray-500">
                          {doc.file_type?.toUpperCase()} • {(doc.file_size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                    </div>
                    <a
                      href={doc.file}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-600 hover:text-primary-900 text-sm"
                    >
                      Download
                    </a>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 text-center py-4">No documents attached.</p>
            )}
          </div>

          {/* Comments */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Comments</h2>
            
            {task.comments?.length > 0 ? (
              <div className="space-y-4 mb-4">
                {task.comments.map((comment) => (
                  <div key={comment.id} className="flex space-x-3">
                    <div className="h-8 w-8 rounded-full bg-gray-200 flex items-center justify-center">
                      <span className="text-xs font-medium text-gray-600">
                        {comment.user?.first_name?.[0]}{comment.user?.last_name?.[0]}
                      </span>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium text-gray-900">
                          {comment.user?.full_name}
                        </span>
                        <span className="text-xs text-gray-500">
                          {format(new Date(comment.created_at), 'MMM d, h:mm a')}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 mt-1">{comment.content}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4 mb-4">No comments yet.</p>
            )}

            <form onSubmit={handleAddComment} className="flex space-x-3">
              <input
                type="text"
                className="input flex-1"
                placeholder="Add a comment..."
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
              />
              <button type="submit" className="btn-primary">Post</button>
            </form>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Cost Summary */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Cost Summary</h2>
            <dl className="space-y-3">
              {task.estimated_cost && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Estimated</dt>
                  <dd className="font-medium">${task.estimated_cost.toLocaleString()}</dd>
                </div>
              )}
              {task.actual_cost && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Actual</dt>
                  <dd className="font-medium text-success-600">${task.actual_cost.toLocaleString()}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Metadata */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Information</h2>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Created</dt>
                <dd>{format(new Date(task.created_at), 'MMM d, yyyy')}</dd>
              </div>
              {task.created_by && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Created by</dt>
                  <dd>{task.created_by.full_name}</dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-gray-500">Last updated</dt>
                <dd>{format(new Date(task.updated_at), 'MMM d, h:mm a')}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>

      {/* Complete Modal */}
      {completeModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-screen items-center justify-center p-4">
            <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setCompleteModalOpen(false)} />
            <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Complete Task</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="label">Actual Cost ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    className="input"
                    value={completeData.actual_cost}
                    onChange={(e) => setCompleteData({ ...completeData, actual_cost: e.target.value })}
                  />
                </div>
                <div>
                  <label className="label">Mileage at Maintenance (km)</label>
                  <input
                    type="number"
                    className="input"
                    value={completeData.mileage_at_maintenance}
                    onChange={(e) => setCompleteData({ ...completeData, mileage_at_maintenance: e.target.value })}
                  />
                </div>
                <div>
                  <label className="label">Completion Notes</label>
                  <textarea
                    rows={3}
                    className="input"
                    value={completeData.completion_notes}
                    onChange={(e) => setCompleteData({ ...completeData, completion_notes: e.target.value })}
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button onClick={() => setCompleteModalOpen(false)} className="btn-secondary">
                  Cancel
                </button>
                <button onClick={handleComplete} className="btn-success">
                  Complete Task
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default MaintenanceDetailPage
