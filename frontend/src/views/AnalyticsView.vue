<template>
  <div>
    <div class="topbar">
      <div class="topbar-title">Аналитика персонала</div>
      <div style="display:flex;gap:8px;align-items:center">
        <button class="btn btn-outline btn-sm" @click="exportFile('xlsx')" :disabled="exporting" title="Экспорт в Excel">
          <span v-if="exporting === 'xlsx'" class="spinner" style="width:12px;height:12px"></span>
          <span v-else>📊</span> Excel
        </button>
        <button class="btn btn-outline btn-sm" @click="exportFile('pdf')" :disabled="exporting" title="Экспорт в PDF">
          <span v-if="exporting === 'pdf'" class="spinner" style="width:12px;height:12px"></span>
          <span v-else>📄</span> PDF
        </button>
        <button class="btn btn-primary btn-sm" @click="runAnalytics" :disabled="store.running">
          <span v-if="store.running" class="spinner" style="width:14px;height:14px"></span>
          {{ store.running ? 'Вычисление ML...' : '▶ Запустить анализ' }}
        </button>
      </div>
    </div>
    <div class="page-container">

      <!-- Run prompt -->
      <div v-if="!hasData && !store.running && !store.loading" class="card" style="margin-bottom:24px">
        <div class="card-body" style="text-align:center;padding:40px">
          <div style="font-size:40px;margin-bottom:12px">🤖</div>
          <div style="font-size:16px;font-weight:600;margin-bottom:8px">Данные аналитики не найдены</div>
          <div style="color:#6b7280;margin-bottom:20px">Нажмите "Запустить анализ" чтобы вычислить ML-модели</div>
          <button class="btn btn-primary" @click="runAnalytics">▶ Запустить анализ</button>
        </div>
      </div>

      <div v-if="store.running" class="card" style="margin-bottom:24px">
        <div class="card-body" style="text-align:center;padding:32px">
          <div class="spinner" style="width:32px;height:32px;margin:0 auto 12px"></div>
          <div>Выполняется XGBoost, K-Means, Isolation Forest, SARIMA...</div>
        </div>
      </div>

      <template v-if="hasData">
        <!-- Tabs -->
        <div class="tabs">
          <button class="tab-btn" :class="{active: tab==='attrition'}" @click="tab='attrition'">Риск увольнения</button>
          <button class="tab-btn" :class="{active: tab==='clusters'}" @click="tab='clusters'">Кластеры</button>
          <button class="tab-btn" :class="{active: tab==='anomalies'}" @click="tab='anomalies'">Аномалии</button>
          <button class="tab-btn" :class="{active: tab==='forecast'}" @click="tab='forecast'">Прогнозы SARIMA</button>
          <button class="tab-btn" :class="{active: tab==='recommendations'}" @click="tab='recommendations'">
            Рекомендации
            <span v-if="criticalCount" class="rec-badge">{{ criticalCount }}</span>
          </button>
        </div>

        <!-- Attrition Heatmap -->
        <div v-show="tab === 'attrition'">
          <div class="grid-3" style="margin-bottom:16px">
            <div class="stat-card">
              <div class="stat-icon red">🔴</div>
              <div class="stat-info">
                <div class="stat-value">{{ riskCounts.high }}</div>
                <div class="stat-label">Высокий риск</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon yellow">🟡</div>
              <div class="stat-info">
                <div class="stat-value">{{ riskCounts.medium }}</div>
                <div class="stat-label">Средний риск</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon green">🟢</div>
              <div class="stat-info">
                <div class="stat-value">{{ riskCounts.low }}</div>
                <div class="stat-label">Низкий риск</div>
              </div>
            </div>
          </div>

          <div class="card">
            <div class="card-header">
              <span class="card-title">Тепловая карта риска увольнения (XGBoost)</span>
              <select class="form-control" style="width:160px" v-model="riskFilter" @change="applyRiskFilter">
                <option value="">Все</option>
                <option value="high">Высокий</option>
                <option value="medium">Средний</option>
                <option value="low">Низкий</option>
              </select>
            </div>
            <div class="card-body" style="padding:0">
              <RiskHeatmap :data="filteredAttrition" />
            </div>
          </div>
        </div>

        <!-- Clusters -->
        <div v-show="tab === 'clusters'">
          <!-- Sub-tabs -->
          <div class="sub-tabs" style="margin-bottom:12px">
            <button class="sub-tab-btn" :class="{active: clusterSubTab==='departments'}" @click="clusterSubTab='departments'">
              Отделы
            </button>
            <button class="sub-tab-btn" :class="{active: clusterSubTab==='tsne'}" @click="clusterSubTab='tsne'">
              t-SNE
            </button>
          </div>

          <!-- Departments bubble chart -->
          <div v-show="clusterSubTab === 'departments'" class="card">
            <div class="card-body">
              <DepartmentBubbleChart :data="store.departmentClusters" />
            </div>
          </div>

          <!-- t-SNE scatter -->
          <div v-show="clusterSubTab === 'tsne'" class="card">
            <div class="card-header">
              <span class="card-title">Кластеризация сотрудников (K-Means + t-SNE)</span>
            </div>
            <div class="card-body">
              <ClusterChart :data="store.clusters" />
            </div>
          </div>
        </div>

        <!-- Anomalies -->
        <div v-show="tab === 'anomalies'">
          <div class="card">
            <div class="card-header">
              <span class="card-title">Лента аномалий (Isolation Forest)</span>
              <label style="display:flex;align-items:center;gap:6px;font-size:13px;cursor:pointer">
                <input type="checkbox" v-model="showResolved" @change="loadAnomalies" />
                Показать решённые
              </label>
            </div>
            <div class="card-body">
              <div v-if="!store.anomalies.length" class="empty-state">
                <div class="empty-icon">✅</div>
                <div>Аномалий не обнаружено</div>
              </div>
              <div v-for="a in store.anomalies" :key="a.id" class="anomaly-item">
                <div class="anomaly-dot" :class="a.severity"></div>
                <div style="flex:1">
                  <div style="display:flex;align-items:center;justify-content:space-between">
                    <div style="font-weight:500;font-size:13px">{{ a.description }}</div>
                    <span :class="severityBadge(a.severity)" class="badge">{{ a.severity }}</span>
                  </div>
                  <div class="text-sm text-gray" style="margin-top:2px">
                    {{ a.employee_name || 'Системная' }} · {{ metricLabel(a.metric) }} · score: {{ a.anomaly_score?.toFixed(3) }}
                    · {{ formatDt(a.detected_at) }}
                  </div>
                </div>
                <button v-if="!a.is_resolved" class="btn btn-outline btn-sm" @click="resolveAnomaly(a.id)">
                  Решено
                </button>
                <span v-else class="badge badge-green">Решено</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Forecasts -->
        <div v-if="tab === 'forecast'">
          <div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap">
            <button v-for="m in metrics" :key="m.value" class="btn" :class="selectedMetric===m.value?'btn-primary':'btn-outline'" @click="selectedMetric=m.value">
              {{ m.label }}
            </button>
          </div>
          <div class="card">
            <div class="card-header"><span class="card-title">Прогноз SARIMA: {{ currentMetricLabel }}</span></div>
            <div class="card-body">
              <ForecastChart :data="store.forecasts" :metric="selectedMetric" />
            </div>
          </div>
        </div>

        <!-- Recommendations -->
        <div v-show="tab === 'recommendations'">
          <div class="card">
            <div class="card-header">
              <span class="card-title">Рекомендации руководителю</span>
              <span class="text-gray text-sm">На основе XGBoost, Isolation Forest, K-Means и обучения</span>
            </div>
            <div class="card-body">
              <div v-if="!store.recommendations.length" class="empty-state">
                <div class="empty-icon">✅</div>
                <div>Рекомендаций нет — запустите анализ</div>
              </div>
              <div v-for="(rec, i) in store.recommendations" :key="i" class="rec-card" :class="'rec-' + rec.severity">
                <div class="rec-icon">{{ recIcon(rec) }}</div>
                <div class="rec-body">
                  <div class="rec-header-row">
                    <div class="rec-title">{{ rec.title }}</div>
                    <span class="badge" :class="recBadge(rec.severity)">{{ recSeverityRu(rec.severity) }}</span>
                  </div>
                  <div v-if="rec.reason" class="rec-section">
                    <span class="rec-label">Причина:</span> {{ rec.reason }}
                  </div>
                  <div v-if="rec.action" class="rec-section rec-action">
                    <span class="rec-label">Действие:</span> {{ rec.action }}
                  </div>
                  <!-- fallback for legacy message field -->
                  <div v-if="!rec.reason && rec.message" class="rec-msg">{{ rec.message }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useAnalyticsStore } from '@/stores/analytics'
import RiskHeatmap from '@/components/RiskHeatmap.vue'
import ClusterChart from '@/components/ClusterChart.vue'
import ForecastChart from '@/components/ForecastChart.vue'
import DepartmentBubbleChart from '@/components/DepartmentBubbleChart.vue'

const store = useAnalyticsStore()
const exporting = ref(null) // 'xlsx' | 'pdf' | null
const tab = ref('attrition')
const clusterSubTab = ref('departments')
const riskFilter = ref('')
const showResolved = ref(false)
const selectedMetric = ref('headcount')

const metrics = [
  { value: 'headcount', label: 'Численность' },
  { value: 'turnover', label: 'Текучесть %' },
  { value: 'avg_salary', label: 'Средняя зарплата' },
  { value: 'sick_days', label: 'Больничные дни' },
  { value: 'overtime', label: 'Сверхурочные' },
]

const hasData = computed(() =>
  store.attrition.length > 0 ||
  store.clusters.length > 0 ||
  store.anomalies.length > 0 ||
  store.recommendations.length > 0 ||
  store.forecasts.length > 0
)
const criticalCount = computed(() => store.recommendations.filter(r => r.severity === 'critical').length)
const currentMetricLabel = computed(() => metrics.find(m => m.value === selectedMetric.value)?.label || '')

const riskCounts = computed(() => ({
  high: store.attrition.filter(a => a.risk_label === 'high').length,
  medium: store.attrition.filter(a => a.risk_label === 'medium').length,
  low: store.attrition.filter(a => a.risk_label === 'low').length,
}))

const filteredAttrition = computed(() => {
  if (!riskFilter.value) return store.attrition
  return store.attrition.filter(a => a.risk_label === riskFilter.value)
})

const METRIC_NAMES = {
  salary:            'Зарплата',
  overtime_hours:    'Переработки',
  hours_fulfillment: 'Выполнение нормы часов (%)',
  years_at_company:  'Стаж',
}
function metricLabel(m) { return METRIC_NAMES[m] || m }
function applyRiskFilter() {}
function severityBadge(s) { return { high: 'badge-red', medium: 'badge-yellow', low: 'badge-green' }[s] || 'badge-gray' }
function formatDt(dt) { return dt ? new Date(dt).toLocaleDateString('ru-RU') : '' }
function recIcon(rec) {
  if (rec.type === 'attrition') return rec.severity === 'critical' ? '🔴' : '🟡'
  if (rec.type === 'anomaly') return '🔍'
  if (rec.type === 'cluster') return '👥'
  if (rec.type === 'training') return rec.severity === 'warning' ? '🟡' : '📚'
  return '💡'
}
function recBadge(s) { return { critical: 'badge-red', warning: 'badge-yellow', info: 'badge-blue' }[s] || 'badge-gray' }
function recSeverityRu(s) { return { critical: 'Критично', warning: 'Внимание', info: 'Инфо' }[s] || s }

async function runAnalytics() {
  await store.runAll()
}

async function exportFile(fmt) {
  exporting.value = fmt
  const ext   = fmt === 'pdf' ? 'pdf' : 'xlsx'
  const today = new Date().toISOString().slice(0, 10)
  const token = localStorage.getItem('access_token') || ''

  try {
    const res = await fetch(`/api/analytics/export/?export_format=${fmt}`, {
      headers: { Authorization: `Bearer ${token}` },
    })

    if (!res.ok) {
      let detail = `HTTP ${res.status}`
      try {
        const text = await res.text()
        const json = JSON.parse(text)
        detail = json.detail || json.error || text || detail
      } catch {}
      throw new Error(detail)
    }

    const blob = await res.blob()
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `hr_analytics_${today}.${ext}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (err) {
    alert(`Ошибка экспорта: ${err.message}`)
  } finally {
    exporting.value = null
  }
}

async function loadAnomalies() {
  await store.fetchAnomalies(showResolved.value ? {} : { resolved: 'false' })
}

async function loadForecast() {
  await store.fetchForecasts(selectedMetric.value)
}

async function resolveAnomaly(id) {
  await store.resolveAnomaly(id)
}

onMounted(async () => {
  await Promise.all([
    store.fetchAttrition(),
    store.fetchClusters(),
    store.fetchDepartmentClusters(),
    store.fetchAnomalies({ resolved: 'false' }),
    store.fetchForecasts(),        // без метрики — грузим все 15 записей сразу
    store.fetchRecommendations(),
  ])
  // Если ML ещё не запускался, но прогнозы в БД есть — показываем их
  if (store.forecasts.length > 0 && store.attrition.length === 0) {
    tab.value = 'forecast'
  }
})
</script>

<style scoped>
.rec-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: #ef4444;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  margin-left: 6px;
  line-height: 1;
}

.rec-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 8px;
  margin-bottom: 10px;
  border-left: 4px solid transparent;
}
.rec-card:last-child { margin-bottom: 0; }

.rec-critical { background: #fef2f2; border-left-color: #ef4444; }
.rec-warning  { background: #fffbeb; border-left-color: #f59e0b; }
.rec-info     { background: #eff6ff; border-left-color: #3b82f6; }

.rec-icon { font-size: 22px; flex-shrink: 0; margin-top: 2px; }

.rec-body { flex: 1; min-width: 0; }

.rec-header-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.rec-title { font-weight: 600; font-size: 13px; color: #111827; flex: 1; line-height: 1.4; }

.rec-section {
  font-size: 12px;
  color: #4b5563;
  line-height: 1.5;
  margin-bottom: 4px;
}
.rec-section:last-child { margin-bottom: 0; }

.rec-label {
  font-weight: 600;
  color: #374151;
}

.rec-action { color: #1e40af; }
.rec-critical .rec-action { color: #991b1b; }
.rec-warning  .rec-action { color: #92400e; }

.rec-msg { font-size: 12px; color: #6b7280; line-height: 1.4; }

.badge-blue { background: #dbeafe; color: #1d4ed8; }

.sub-tabs {
  display: flex;
  gap: 4px;
  background: var(--gray-100);
  border-radius: 8px;
  padding: 3px;
  width: fit-content;
}
.sub-tab-btn {
  padding: 5px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  color: var(--gray-500);
  background: transparent;
  cursor: pointer;
  transition: all .15s;
}
.sub-tab-btn.active {
  background: #fff;
  color: var(--gray-800);
  box-shadow: 0 1px 3px rgba(0,0,0,.1);
  font-weight: 600;
}
.sub-tab-btn:not(.active):hover { color: var(--gray-700); }
</style>
