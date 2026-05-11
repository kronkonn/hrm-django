<template>
  <div>
    <div v-if="!data.length" class="empty-state">
      <div class="empty-icon">🔵</div>Нет данных по отделам
    </div>
    <template v-else>
      <div class="chart-header">
        <div class="chart-title">Анализ отделов по риску увольнения и выполнению нормы</div>
        <div class="chart-subtitle">Размер круга = количество сотрудников в отделе</div>
      </div>

      <div class="chart-container" style="height:400px;position:relative">
        <canvas ref="chartCanvas"></canvas>
      </div>

      <!-- Department table -->
      <div style="margin-top:20px;overflow-x:auto">
        <table class="dept-table">
          <thead>
            <tr>
              <th>Отдел</th>
              <th class="num">Сотрудников</th>
              <th class="num">Средний риск</th>
              <th class="num">Норма часов</th>
              <th>Кластер</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="dept in sortedData" :key="dept.department_name" :class="rowClass(dept.avg_risk_score)">
              <td style="font-weight:500">{{ dept.department_name }}</td>
              <td class="num">{{ dept.employee_count }}</td>
              <td class="num">
                <span class="risk-pill" :class="riskPillClass(dept.avg_risk_score)">
                  {{ dept.avg_risk_score }}%
                </span>
              </td>
              <td class="num">{{ dept.avg_hours_fulfillment }}%</td>
              <td>
                <span class="cluster-dot" :style="{ background: clusterColor(dept.dominant_cluster_id) }"></span>
                {{ dept.dominant_cluster }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted, onUnmounted, nextTick } from 'vue'
import {
  Chart, BubbleController, PointElement, LinearScale, Tooltip, Legend,
} from 'chart.js'
Chart.register(BubbleController, PointElement, LinearScale, Tooltip, Legend)

const props = defineProps({ data: { type: Array, default: () => [] } })
const chartCanvas = ref(null)
let chart = null

const CLUSTER_COLORS = {
  0: 'rgba(99,102,241,0.75)',
  1: 'rgba(239,68,68,0.75)',
  2: 'rgba(16,185,129,0.75)',
  3: 'rgba(245,158,11,0.75)',
}
const CLUSTER_BORDER = {
  0: 'rgb(99,102,241)',
  1: 'rgb(239,68,68)',
  2: 'rgb(16,185,129)',
  3: 'rgb(245,158,11)',
}
const CLUSTER_NAMES = {
  0: 'Высокая эффективность',
  1: 'Группа риска',
  2: 'Стабильные',
  3: 'Новички',
}

function clusterColor(cid) { return CLUSTER_BORDER[cid] ?? '#6b7280' }

const sortedData = computed(() => [...props.data].sort((a, b) => b.avg_risk_score - a.avg_risk_score))

function rowClass(risk) {
  if (risk >= 65) return 'row-red'
  if (risk >= 30) return 'row-yellow'
  return 'row-green'
}

function riskPillClass(risk) {
  if (risk >= 65) return 'pill-red'
  if (risk >= 30) return 'pill-yellow'
  return 'pill-green'
}

function buildDatasets() {
  const maxCount = Math.max(...props.data.map(d => d.employee_count), 1)
  const groups = {}
  props.data.forEach(dept => {
    const cid = dept.dominant_cluster_id ?? 0
    if (!groups[cid]) {
      groups[cid] = {
        label: CLUSTER_NAMES[cid] || `Кластер ${cid}`,
        data: [],
        backgroundColor: CLUSTER_COLORS[cid] || 'rgba(107,114,128,0.75)',
        borderColor: CLUSTER_BORDER[cid] || '#6b7280',
        borderWidth: 1.5,
      }
    }
    groups[cid].data.push({
      x: dept.avg_risk_score,
      y: dept.avg_hours_fulfillment,
      r: Math.max(8, 8 + (dept.employee_count / maxCount) * 20),
      dept,
    })
  })
  return Object.values(groups)
}

function buildChart() {
  if (!chartCanvas.value || !props.data.length) return
  if (chart) { chart.destroy(); chart = null }
  chart = new Chart(chartCanvas.value, {
    type: 'bubble',
    data: { datasets: buildDatasets() },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top' },
        tooltip: {
          callbacks: {
            label: ctx => {
              const d = ctx.raw.dept
              return [
                `Отдел: ${d.department_name}`,
                `Сотрудников: ${d.employee_count}`,
                `Средний риск: ${d.avg_risk_score}%`,
                `Норма часов: ${d.avg_hours_fulfillment}%`,
                `Преобладающий кластер: ${d.dominant_cluster}`,
              ]
            },
          },
        },
      },
      scales: {
        x: {
          title: { display: true, text: 'Средний риск увольнения (%)' },
          min: 0,
          max: 100,
          grid: { color: '#f3f4f6' },
          ticks: { callback: v => v + '%' },
        },
        y: {
          title: { display: true, text: 'Среднее выполнение нормы часов (%)' },
          grid: { color: '#f3f4f6' },
          ticks: { callback: v => v + '%' },
        },
      },
    },
  })
}

watch(() => props.data, () => nextTick(buildChart), { deep: true })
onMounted(() => nextTick(buildChart))
onUnmounted(() => { if (chart) chart.destroy() })
</script>

<style scoped>
.chart-header { margin-bottom: 14px; }
.chart-title { font-size: 14px; font-weight: 600; color: var(--gray-800); }
.chart-subtitle { font-size: 12px; color: var(--gray-400); margin-top: 2px; }

.dept-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.dept-table th {
  text-align: left;
  padding: 8px 12px;
  font-size: 11px;
  font-weight: 600;
  color: var(--gray-500);
  text-transform: uppercase;
  letter-spacing: .4px;
  border-bottom: 2px solid var(--gray-200);
  background: var(--gray-50);
}
.dept-table th.num, .dept-table td.num { text-align: right; }
.dept-table td {
  padding: 9px 12px;
  border-bottom: 1px solid var(--gray-100);
  vertical-align: middle;
}
.dept-table tbody tr:last-child td { border-bottom: none; }

.row-red    { background: #fff5f5; }
.row-yellow { background: #fffbeb; }
.row-green  { background: #f0fdf4; }

.risk-pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 12px;
}
.pill-red    { background: #fee2e2; color: #b91c1c; }
.pill-yellow { background: #fef3c7; color: #92400e; }
.pill-green  { background: #dcfce7; color: #15803d; }

.cluster-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
}
</style>
