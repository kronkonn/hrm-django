import api from './index'

export const getLeaves = (params) => api.get('/leaves/', { params })
export const getLeave = (id) => api.get(`/leaves/${id}/`)
export const createLeave = (data) => api.post('/leaves/', data)
export const updateLeave = (id, data) => api.patch(`/leaves/${id}/`, data)
export const approveLeave = (id) => api.post(`/leaves/${id}/approve/`)
export const rejectLeave = (id) => api.post(`/leaves/${id}/reject/`)
export const updateSickDetails = (id, data) => api.patch(`/leaves/${id}/sick_details/`, data)
