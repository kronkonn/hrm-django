import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/analytics'

export const useAnalyticsStore = defineStore('analytics', () => {
  const summary = ref(null)
  const attrition = ref([])
  const clusters = ref([])
  const departmentClusters = ref([])
  const anomalies = ref([])
  const forecasts = ref([])
  const recommendations = ref([])
  const loading = ref(false)
  const running = ref(false)

  async function fetchSummary() {
    const { data } = await api.getDashboardSummary()
    summary.value = data
  }

  async function fetchAttrition(params = {}) {
    loading.value = true
    try {
      const { data } = await api.getAttrition(params)
      attrition.value = data.results ?? data
    } finally { loading.value = false }
  }

  async function fetchClusters() {
    const { data } = await api.getClusters()
    clusters.value = data.results ?? data
  }

  async function fetchDepartmentClusters() {
    const { data } = await api.getDepartmentClusters()
    departmentClusters.value = data
  }

  async function fetchAnomalies(params = {}) {
    const { data } = await api.getAnomalies(params)
    anomalies.value = data.results ?? data
  }

  async function fetchForecasts(metric) {
    const params = metric ? { metric } : {}
    const { data } = await api.getForecasts(params)
    forecasts.value = data.results ?? data
  }

  async function runAll() {
    running.value = true
    try {
      const { data } = await api.runAnalytics()
      await Promise.all([fetchAttrition(), fetchClusters(), fetchDepartmentClusters(), fetchAnomalies(), fetchForecasts(), fetchRecommendations()])
      return data
    } finally { running.value = false }
  }

  async function fetchRecommendations() {
    const { data } = await api.getRecommendations()
    recommendations.value = data
  }

  async function resolveAnomaly(id) {
    await api.resolveAnomaly(id)
    const idx = anomalies.value.findIndex(a => a.id === id)
    if (idx !== -1) anomalies.value[idx].is_resolved = true
  }

  return { summary, attrition, clusters, departmentClusters, anomalies, forecasts, recommendations, loading, running, fetchSummary, fetchAttrition, fetchClusters, fetchDepartmentClusters, fetchAnomalies, fetchForecasts, fetchRecommendations, runAll, resolveAnomaly }
})
