import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/employees'

export const useEmployeesStore = defineStore('employees', () => {
  const list = ref([])
  const current = ref(null)
  const departments = ref([])
  const positions = ref([])
  const loading = ref(false)
  const total = ref(0)
  const page = ref(1)

  async function fetchList(params = {}) {
    loading.value = true
    try {
      const { data } = await api.getEmployees({ page: page.value, ...params })
      list.value = data.results ?? data
      total.value = data.count ?? list.value.length
    } finally { loading.value = false }
  }

  async function fetchOne(id) {
    loading.value = true
    try {
      const { data } = await api.getEmployee(id)
      current.value = data
    } finally { loading.value = false }
  }

  async function fetchDepartments() {
    const { data } = await api.getDepartments()
    departments.value = data.results ?? data
  }

  async function fetchPositions() {
    const { data } = await api.getPositions()
    positions.value = data.results ?? data
  }

  async function create(payload) {
    const { data } = await api.createEmployee(payload)
    list.value.unshift(data)
    return data
  }

  async function update(id, payload) {
    const { data } = await api.updateEmployee(id, payload)
    const idx = list.value.findIndex(e => e.id === id)
    if (idx !== -1) list.value[idx] = data
    if (current.value?.id === id) current.value = data
    return data
  }

  async function remove(id) {
    await api.deleteEmployee(id)
    list.value = list.value.filter(e => e.id !== id)
  }

  return { list, current, departments, positions, loading, total, page, fetchList, fetchOne, fetchDepartments, fetchPositions, create, update, remove }
})
