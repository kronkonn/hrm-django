import axios from 'axios'

const publicApi = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  headers: { 'Content-Type': 'application/json' },
})

export const getPublicVacancy = (token) => publicApi.get(`/public/vacancy/${token}/`)

export const applyToVacancy = (token, formData) =>
  publicApi.post(`/public/vacancy/${token}/apply/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
