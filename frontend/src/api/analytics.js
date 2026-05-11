import api from './index'

export const getDashboardSummary = () => api.get('/analytics/dashboard/')
export const runAnalytics = () => api.post('/analytics/run/')

export const getAttrition = (params) => api.get('/analytics/attrition/', { params })
export const getClusters = (params) => api.get('/analytics/clusters/', { params })
export const getAnomalies = (params) => api.get('/analytics/anomalies/', { params })
export const getForecasts = (params) => api.get('/analytics/forecasts/', { params })
export const resolveAnomaly = (id) => api.patch(`/analytics/anomalies/${id}/`, { is_resolved: true })
export const getRecommendations = () => api.get('/analytics/recommendations/')
export const getDepartmentClusters = () => api.get('/analytics/department-clusters/')
