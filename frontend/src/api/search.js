import api from './index'

export const globalSearch = (q) => api.get('/search/', { params: { q } })
