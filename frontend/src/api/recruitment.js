import api from './index'

export const getVacancies = (params) => api.get('/recruitment/vacancies/', { params })
export const getVacancy = (id) => api.get(`/recruitment/vacancies/${id}/`)
export const createVacancy = (data) => api.post('/recruitment/vacancies/', data)
export const updateVacancy = (id, data) => api.patch(`/recruitment/vacancies/${id}/`, data)
export const deleteVacancy = (id) => api.delete(`/recruitment/vacancies/${id}/`)

export const getCandidates = (params) => api.get('/recruitment/candidates/', { params })
export const getCandidate = (id) => api.get(`/recruitment/candidates/${id}/`)
export const createCandidate = (data) => api.post('/recruitment/candidates/', data)
export const updateCandidate = (id, data) => api.patch(`/recruitment/candidates/${id}/`, data)
export const advanceCandidate = (id) => api.post(`/recruitment/candidates/${id}/advance_stage/`)
export const rejectCandidate  = (id) => api.post(`/recruitment/candidates/${id}/reject/`)

export const analyzeCandidate = (id) => api.post(`/recruitment/candidates/${id}/analyze/`)
export const analyzeVacancyAll = (vacancyId) => api.post(`/recruitment/vacancies/${vacancyId}/analyze_all/`)

// Vacancy questionnaire management
export const getVacancyQuestions = (vacancyId) => api.get(`/recruitment/vacancies/${vacancyId}/questions/`)
export const createVacancyQuestion = (vacancyId, data) => api.post(`/recruitment/vacancies/${vacancyId}/questions/`, data)
export const deleteVacancyQuestion = (vacancyId, questionId) => api.delete(`/recruitment/vacancies/${vacancyId}/questions/${questionId}/`)

// Publication toggle
export const publishVacancy = (vacancyId, data) => api.patch(`/recruitment/vacancies/${vacancyId}/publish/`, data)

// Resume file URL with JWT token in query param (needed for direct browser navigation)
export const getResumeUrl = (candidateId) => {
  const base = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
  const token = localStorage.getItem('access_token') || ''
  return `${base}/recruitment/candidates/${candidateId}/resume/?token=${token}`
}
