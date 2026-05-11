import api from './index'

export const getTimesheets = (params) =>
  api.get('/timesheets/', { params: { ...params, page_size: 1000 } })

export const createTimesheet = (data) => api.post('/timesheets/', data)

export const updateTimesheet = (id, data) => api.patch(`/timesheets/${id}/`, data)

export const generateMonth = (month, year) =>
  api.post('/timesheets/generate/', { month, year })

export const getTimesheetSummary = (params) =>
  api.get('/timesheets/summary/', { params })
