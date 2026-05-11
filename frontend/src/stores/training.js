import { ref } from 'vue'
import { defineStore } from 'pinia'
import api from '@/api/index'

export const useTrainingStore = defineStore('training', () => {
  const courses      = ref([])
  const assignments  = ref([])
  const certificates = ref([])
  const loading      = ref(false)
  const saving       = ref(false)

  async function fetchCourses(params = {}) {
    loading.value = true
    try {
      const { data } = await api.get('/training/courses/', { params })
      courses.value = data.results ?? data
    } finally { loading.value = false }
  }

  async function createCourse(payload) {
    saving.value = true
    try {
      const { data } = await api.post('/training/courses/', payload)
      courses.value.unshift(data)
      return data
    } finally { saving.value = false }
  }

  async function updateCourse(id, payload) {
    saving.value = true
    try {
      const { data } = await api.patch(`/training/courses/${id}/`, payload)
      const idx = courses.value.findIndex(c => c.id === id)
      if (idx !== -1) courses.value[idx] = data
      return data
    } finally { saving.value = false }
  }

  async function assignCourse(courseId, employeeIds) {
    saving.value = true
    try {
      const { data } = await api.post(`/training/courses/${courseId}/assign/`, { employee_ids: employeeIds })
      return data
    } finally { saving.value = false }
  }

  async function fetchAssignments(params = {}) {
    loading.value = true
    try {
      const { data } = await api.get('/training/assignments/', { params })
      assignments.value = data.results ?? data
    } finally { loading.value = false }
  }

  async function updateProgress(id, progress) {
    saving.value = true
    try {
      const { data } = await api.patch(`/training/assignments/${id}/progress/`, { progress })
      const idx = assignments.value.findIndex(a => a.id === id)
      if (idx !== -1) assignments.value[idx] = data
      return data
    } finally { saving.value = false }
  }

  async function fetchCertificates(params = {}) {
    loading.value = true
    try {
      const { data } = await api.get('/training/certificates/', { params })
      certificates.value = data.results ?? data
    } finally { loading.value = false }
  }

  async function fetchAssignment(id) {
    const { data } = await api.get(`/training/assignments/${id}/`)
    return data
  }

  async function completeLesson(assignmentId, lessonId) {
    saving.value = true
    try {
      const { data } = await api.patch(
        `/training/assignments/${assignmentId}/complete-lesson/`,
        { lesson_id: lessonId },
      )
      const idx = assignments.value.findIndex(a => a.id === assignmentId)
      if (idx !== -1) assignments.value[idx] = data
      return data
    } finally { saving.value = false }
  }

  return {
    courses, assignments, certificates, loading, saving,
    fetchCourses, createCourse, updateCourse, assignCourse,
    fetchAssignments, updateProgress, fetchCertificates,
    fetchAssignment, completeLesson,
  }
})
