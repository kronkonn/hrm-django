import api from './index'

export const getEmployees = (params) => api.get('/employees/list/', { params })
export const getEmployee = (id) => api.get(`/employees/list/${id}/`)
export const createEmployee = (data) => api.post('/employees/list/', data)
export const updateEmployee = (id, data) => api.patch(`/employees/list/${id}/`, data)
export const deleteEmployee = (id) => api.delete(`/employees/list/${id}/`)

export const getDepartments = (params) => api.get('/employees/departments/', { params })
export const getPositions = (params) => api.get('/employees/positions/', { params })

export const getEmployeeStats = () => api.get('/employees/list/stats/')
export const getMyEmployee = () => api.get('/employees/list/me/')
