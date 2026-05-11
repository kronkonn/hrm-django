import axios from 'axios'
import api from './index'

export const login = (username, password) =>
  axios.post('/api/auth/token/', { username, password })

export const refreshToken = (refresh) =>
  axios.post('/api/auth/token/refresh/', { refresh })

export const getMe = () => api.get('/auth/me/')
export const updateMe = (data) => api.patch('/auth/me/', data)
export const getUsers = () => api.get('/auth/users/')
export const updateUserRole = (id, role) => api.patch(`/auth/users/${id}/`, { role })
export const changeUserPassword = (id, password) => api.post(`/auth/users/${id}/change_password/`, { password })
