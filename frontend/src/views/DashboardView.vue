<template>
  <div>
    <div class="topbar">
      <div class="topbar-title">Дашборд</div>
      <button class="btn btn-primary btn-sm" @click="refresh" :disabled="refreshing">
        <span v-if="refreshing" class="spinner" style="width:14px;height:14px"></span>
        {{ refreshing ? 'Обновление...' : '↻ Обновить' }}
      </button>
    </div>
    <div class="page-container">
      <div v-if="loading" class="loading"><div class="spinner"></div> Загрузка...</div>
      <template v-else>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon blue">👥</div>
            <div class="stat-info">
              <div class="stat-value">{{ s.active_employees ?? '—' }}</div>
              <div class="stat-label">Активных сотрудников</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon yellow">🌴</div>
            <div class="stat-info">
              <div class="stat-value">{{ s.pending_leaves ?? '—' }}</div>
              <div class="stat-label">Заявок на отпуск</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon green">📋</div>
            <div class="stat-info">
              <div class="stat-value">{{ s.open_vacancies ?? '—' }}</div>
              <div class="stat-label">Открытых вакансий</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon indigo">🎯</div>
            <div class="stat-info">
              <div class="stat-value">{{ s.total_candidates ?? '—' }}</div>
              <div class="stat-label">Кандидатов</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon red">⚠️</div>
            <div class="stat-info">
              <div class="stat-value">{{ s.high_risk_employees ?? '—' }}</div>
              <div class="stat-label">Высокий риск увольнения</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon purple">🔍</div>
            <div class="stat-info">
              <div class="stat-value">{{ s.active_anomalies ?? '—' }}</div>
              <div class="stat-label">Активных аномалий</div>
            </div>
          </div>
        </div>

        <div class="grid-2">
          <div class="card">
            <div class="card-header"><span class="card-title">Топ рисков увольнения</span></div>
            <div class="card-body" style="padding:0">
              <div v-if="!attritionStore.attrition.length" class="empty-state"><div class="empty-icon">🤖</div>Запустите аналитику</div>
              <table v-else>
                <thead><tr><th>Сотрудник</th><th>Отдел</th><th>Риск</th></tr></thead>
                <tbody>
                  <tr v-for="a in topRisk" :key="a.id">
                    <td>{{ a.employee_name }}</td>
                    <td><span class="text-gray">{{ a.department_name }}</span></td>
                    <td>
                      <div class="flex items-center gap-2">
                        <div class="risk-bar"><div class="risk-fill" :class="a.risk_label" :style="{width: (a.risk_score*100)+'%'}"></div></div>
                        <span :class="riskBadge(a.risk_label)" class="badge">{{ (a.risk_score*100).toFixed(0) }}%</span>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="card">
            <div class="card-header"><span class="card-title">Активные аномалии</span></div>
            <div class="card-body">
              <div v-if="!anomalies.length" class="empty-state"><div class="empty-icon">✅</div>Аномалий не найдено</div>
              <div v-for="a in anomalies" :key="a.id" class="anomaly-item">
                <div class="anomaly-dot" :class="a.severity"></div>
                <div>
                  <div style="font-weight:500;font-size:13px">{{ a.description }}</div>
                  <div class="text-sm text-gray">{{ a.employee_name }} · {{ formatDate(a.detected_at) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Top-3 recommendations -->
        <div class="card mt-4">
          <div class="card-header">
            <span class="card-title">Рекомендации руководителю</span>
            <router-link to="/analytics" class="btn btn-outline btn-sm">Все рекомендации →</router-link>
          </div>
          <div class="card-body">
            <div v-if="!topRecs.length" class="empty-state" style="padding:16px 0">
              <div class="empty-icon">✅</div>
              <div>Запустите аналитику для получения рекомендаций</div>
            </div>
            <div v-for="(rec, i) in topRecs" :key="i" class="rec-row" :class="'rec-' + rec.severity">
              <span class="rec-dot" :class="'dot-' + rec.severity"></span>
              <div class="rec-text">
                <div class="rec-title">{{ rec.title }}</div>
                <div v-if="rec.reason" class="rec-msg">
                  <span class="rec-label">Причина:</span> {{ rec.reason }}
                </div>
                <div v-if="rec.action" class="rec-msg rec-action-text">
                  <span class="rec-label">Действие:</span> {{ rec.action }}
                </div>
                <div v-if="!rec.reason && rec.message" class="rec-msg">{{ rec.message }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="card mt-4">
          <div class="card-header">
            <span class="card-title">Быстрые действия</span>
          </div>
          <div class="card-body" style="display:flex;gap:12px;flex-wrap:wrap">
            <router-link to="/employees" class="btn btn-outline">👥 Список сотрудников</router-link>
            <router-link to="/leaves" class="btn btn-outline">🌴 Заявки на отпуск</router-link>
            <router-link to="/recruiting" class="btn btn-outline">🎯 Вакансии</router-link>
            <router-link to="/analytics" class="btn btn-primary">📊 Аналитический дашборд</router-link>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAnalyticsStore } from '@/stores/analytics'

const attritionStore = useAnalyticsStore()
const loading = ref(false)
const refreshing = ref(false)
const s = computed(() => attritionStore.summary || {})
const topRisk = computed(() => attritionStore.attrition.slice(0, 5))
const anomalies = computed(() => attritionStore.anomalies.filter(a => !a.is_resolved).slice(0, 5))
const topRecs = computed(() => attritionStore.recommendations.slice(0, 3))

function riskBadge(label) {
  return { low: 'badge-green', medium: 'badge-yellow', high: 'badge-red' }[label] || 'badge-gray'
}
function formatDate(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleDateString('ru-RU')
}

async function loadData() {
  loading.value = true
  try {
    await Promise.all([
      attritionStore.fetchSummary(),
      attritionStore.fetchAttrition(),
      attritionStore.fetchAnomalies({ resolved: 'false' }),
      attritionStore.fetchRecommendations(),
    ])
  } finally { loading.value = false }
}

async function refresh() {
  refreshing.value = true
  try { await loadData() } finally { refreshing.value = false }
}

onMounted(loadData)
</script>

<style scoped>
.rec-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  margin-bottom: 8px;
}
.rec-row:last-child { margin-bottom: 0; }
.rec-critical { background: #fef2f2; }
.rec-warning  { background: #fffbeb; }
.rec-info     { background: #eff6ff; }

.rec-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 5px;
}
.dot-critical { background: #ef4444; }
.dot-warning  { background: #f59e0b; }
.dot-info     { background: #3b82f6; }

.rec-text  { flex: 1; min-width: 0; }
.rec-title { font-weight: 600; font-size: 13px; color: #111827; margin-bottom: 3px; }
.rec-msg   { font-size: 12px; color: #4b5563; margin-top: 2px; line-height: 1.5; }
.rec-label { font-weight: 600; color: #374151; }
.rec-action-text { color: #1e40af; }
.rec-critical .rec-action-text { color: #991b1b; }
.rec-warning  .rec-action-text { color: #92400e; }
</style>
