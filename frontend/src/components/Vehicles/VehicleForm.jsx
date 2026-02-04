import { useState, useEffect } from 'react'
import { vehiclesAPI } from '../../services/api'
import toast from 'react-hot-toast'

const VehicleForm = ({ vehicle, onClose, onSuccess }) => {
  const [loading, setLoading] = useState(false)
  const [vehicleTypes, setVehicleTypes] = useState([])
  const [formData, setFormData] = useState({
    license_plate: vehicle?.license_plate || '',
    vin: vehicle?.vin || '',
    make: vehicle?.make || '',
    model: vehicle?.model || '',
    year: vehicle?.year || new Date().getFullYear(),
    color: vehicle?.color || '',
    vehicle_type: vehicle?.vehicle_type?.id || '',
    status: vehicle?.status || 'active',
    current_mileage: vehicle?.current_mileage || 0,
    fuel_type: vehicle?.fuel_type || '',
    fuel_capacity: vehicle?.fuel_capacity || '',
    notes: vehicle?.notes || '',
  })

  useEffect(() => {
    fetchVehicleTypes()
  }, [])

  const fetchVehicleTypes = async () => {
    try {
      const response = await vehiclesAPI.getVehicleTypes()
      setVehicleTypes(response.data.results || response.data || [])
    } catch (error) {
      console.error('Failed to load vehicle types', error)
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
        vehicle_type: formData.vehicle_type || null,
        fuel_capacity: formData.fuel_capacity || null,
      }

      if (vehicle) {
        // Update - remove immutable fields
        const { license_plate, vin, ...updateData } = data
        await vehiclesAPI.updateVehicle(vehicle.id, updateData)
        toast.success('Vehicle updated successfully')
      } else {
        await vehiclesAPI.createVehicle(data)
        toast.success('Vehicle created successfully')
      }
      onSuccess()
    } catch (error) {
      const message = error.response?.data?.message || 
                     Object.values(error.response?.data || {}).flat().join(' ') ||
                     'Failed to save vehicle'
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
              {vehicle ? 'Edit Vehicle' : 'Add Vehicle'}
            </h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Identification */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">Identification</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label">License Plate *</label>
                  <input
                    type="text"
                    name="license_plate"
                    className="input"
                    value={formData.license_plate}
                    onChange={handleChange}
                    disabled={!!vehicle}
                    required
                  />
                </div>
                <div>
                  <label className="label">VIN *</label>
                  <input
                    type="text"
                    name="vin"
                    className="input font-mono"
                    maxLength={17}
                    value={formData.vin}
                    onChange={handleChange}
                    disabled={!!vehicle}
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">17 characters</p>
                </div>
              </div>
            </div>

            {/* Basic Info */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">Basic Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="label">Make *</label>
                  <input
                    type="text"
                    name="make"
                    className="input"
                    value={formData.make}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div>
                  <label className="label">Model *</label>
                  <input
                    type="text"
                    name="model"
                    className="input"
                    value={formData.model}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div>
                  <label className="label">Year *</label>
                  <input
                    type="number"
                    name="year"
                    className="input"
                    min={1900}
                    max={new Date().getFullYear() + 1}
                    value={formData.year}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div>
                  <label className="label">Color</label>
                  <input
                    type="text"
                    name="color"
                    className="input"
                    value={formData.color}
                    onChange={handleChange}
                  />
                </div>
                <div>
                  <label className="label">Vehicle Type</label>
                  <select
                    name="vehicle_type"
                    className="input"
                    value={formData.vehicle_type}
                    onChange={handleChange}
                  >
                    <option value="">Select type...</option>
                    {vehicleTypes.map((type) => (
                      <option key={type.id} value={type.id}>{type.name}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Operational Data */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">Operational Data</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label">Status</label>
                  <select
                    name="status"
                    className="input"
                    value={formData.status}
                    onChange={handleChange}
                  >
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                    <option value="under_maintenance">Under Maintenance</option>
                    <option value="retired">Retired</option>
                  </select>
                </div>
                <div>
                  <label className="label">Current Mileage (km)</label>
                  <input
                    type="number"
                    name="current_mileage"
                    className="input"
                    min={0}
                    value={formData.current_mileage}
                    onChange={handleChange}
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div>
                  <label className="label">Fuel Type</label>
                  <input
                    type="text"
                    name="fuel_type"
                    className="input"
                    placeholder="e.g., Gasoline, Diesel, Electric"
                    value={formData.fuel_type}
                    onChange={handleChange}
                  />
                </div>
                <div>
                  <label className="label">Fuel Capacity (L)</label>
                  <input
                    type="number"
                    name="fuel_capacity"
                    className="input"
                    step="0.01"
                    min={0}
                    value={formData.fuel_capacity}
                    onChange={handleChange}
                  />
                </div>
              </div>
            </div>

            {/* Notes */}
            <div>
              <label className="label">Notes</label>
              <textarea
                name="notes"
                rows={3}
                className="input"
                value={formData.notes}
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
                {loading ? 'Saving...' : vehicle ? 'Update Vehicle' : 'Add Vehicle'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default VehicleForm
