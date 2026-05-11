import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(localStorage.getItem('access_token') || null)
  const refreshToken = ref(localStorage.getItem('refresh_token') || null)
  const username = ref(localStorage.getItem('username') || null)
  const role = ref(localStorage.getItem('role') || null)
  const employeeId = ref(localStorage.getItem('employee_id') ? Number(localStorage.getItem('employee_id')) : null)
  const fullName = ref(localStorage.getItem('full_name') || null)
  const loading = ref(false)
  const error = ref(null)

  const isAuthenticated = computed(() => !!accessToken.value)
  const isDirector = computed(() => role.value === 'DIRECTOR')
  const isHRManager = computed(() => role.value === 'HR_MANAGER')
  const isEmployee = computed(() => role.value === 'EMPLOYEE')
  const isAdmin = computed(() => role.value === 'ADMIN')
  const canAccessAnalytics = computed(() => role.value === 'DIRECTOR' || role.value === 'ADMIN')
  const canAccessHR = computed(() => role.value === 'DIRECTOR' || role.value === 'HR_MANAGER' || role.value === 'ADMIN')

  async function login(user, pass) {
    loading.value = true
    error.value = null
    try {
      const { data } = await axios.post('/api/auth/token/', { username: user, password: pass })
      _applyTokenData(data)
      return true
    } catch (e) {
      error.value = e.response?.data?.detail || 'Неверный логин или пароль'
      return false
    } finally {
      loading.value = false
    }
  }

  function _applyTokenData(data) {
    accessToken.value = data.access
    refreshToken.value = data.refresh
    username.value = data.username
    role.value = data.role
    employeeId.value = data.employee_id ?? null
    fullName.value = data.full_name || data.username

    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    localStorage.setItem('username', data.username)
    localStorage.setItem('role', data.role)
    localStorage.setItem('employee_id', data.employee_id ?? '')
    localStorage.setItem('full_name', data.full_name || data.username)
  }

  function logout() {
    accessToken.value = null
    refreshToken.value = null
    username.value = null
    role.value = null
    employeeId.value = null
    fullName.value = null
    ;['access_token', 'refresh_token', 'username', 'role', 'employee_id', 'full_name'].forEach(k =>
      localStorage.removeItem(k)
    )
  }

  return {
    accessToken, refreshToken, username, role, employeeId, fullName,
    loading, error,
    isAuthenticated, isDirector, isHRManager, isEmployee, isAdmin,
    canAccessAnalytics, canAccessHR,
    login, logout,
  }
})
