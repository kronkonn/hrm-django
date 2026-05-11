import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/recruitment'

export const useRecruitmentStore = defineStore('recruitment', () => {
  const vacancies  = ref([])
  const candidates = ref([])
  const loading    = ref(false)
  const analyzing  = ref(false)

  async function fetchVacancies(params = {}) {
    loading.value = true
    try {
      const { data } = await api.getVacancies(params)
      vacancies.value = data.results ?? data
    } finally { loading.value = false }
  }

  async function fetchCandidates(params = {}) {
    loading.value = true
    try {
      const { data } = await api.getCandidates(params)
      candidates.value = data.results ?? data
    } finally { loading.value = false }
  }

  async function createVacancy(payload) {
    const { data } = await api.createVacancy(payload)
    vacancies.value.unshift(data)
    return data
  }

  async function updateVacancy(id, payload) {
    const { data } = await api.updateVacancy(id, payload)
    const idx = vacancies.value.findIndex(v => v.id === id)
    if (idx !== -1) vacancies.value[idx] = data
    return data
  }

  async function deleteVacancy(id) {
    await api.deleteVacancy(id)
    vacancies.value = vacancies.value.filter(v => v.id !== id)
  }

  async function createCandidate(payload) {
    const { data } = await api.createCandidate(payload)
    candidates.value.unshift(data)
    return data
  }

  async function advanceCandidate(id) {
    const { data } = await api.advanceCandidate(id)
    _patchCandidate(data)
    return data
  }

  async function rejectCandidate(id) {
    const { data } = await api.rejectCandidate(id)
    _patchCandidate(data)
    return data
  }

  async function analyzeCandidate(id) {
    const { data } = await api.analyzeCandidate(id)
    _patchCandidate(data)
    return data
  }

  async function analyzeVacancyAll(vacancyId) {
    analyzing.value = true
    try {
      const { data } = await api.analyzeVacancyAll(vacancyId)
      for (const c of data.candidates) _patchCandidate(c)
      return data
    } finally { analyzing.value = false }
  }

  function _patchCandidate(updated) {
    const idx = candidates.value.findIndex(c => c.id === updated.id)
    if (idx !== -1) candidates.value[idx] = updated
  }

  return {
    vacancies, candidates, loading, analyzing,
    fetchVacancies, fetchCandidates,
    createVacancy, updateVacancy, deleteVacancy,
    createCandidate, advanceCandidate, rejectCandidate,
    analyzeCandidate, analyzeVacancyAll,
  }
})
