<template>
  <div>
    <div v-if="!filteredData.length" class="empty-state">
      <div class="empty-icon">📈</div>Нет данных прогноза
    </div>
    <div v-else class="chart-container" style="height:320px;position:relative">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import {
  Chart, LineController, LineElement, PointElement, CategoryScale, LinearScale, Filler, Tooltip, Legend,
} from 'chart.js'
Chart.register(LineController, LineElement, PointElement, CategoryScale, LinearScale, Filler, Tooltip, Legend)

const props = defineProps({
  data:   { type: Array,  default: () => [] },
  metric: { type: String, default: '' },
})

const chartCanvas = ref(null)
let chart = null

// Фильтруем по метрике если в data смешаны несколько метрик
const filteredData = computed(() => {
  if (!props.metric) return props.data
  const withMetric = props.data.filter(d => d.metric === props.metric)
  return withMetric.length > 0 ? withMetric : props.data
})

function formatPeriod(p) {
  if (!p) return ''
  const d = new Date(p)
  return d.toLocaleDateString('ru-RU', { month: 'short', year: 'numeric' })
}

function buildChart() {
  if (!chartCanvas.value || !filteredData.value.length) return
  if (chart) { chart.destroy(); chart = null }

  const sorted  = [...filteredData.value].sort((a, b) => a.period.localeCompare(b.period))
  const labels   = sorted.map(d => formatPeriod(d.period))
  const forecast = sorted.map(d => d.forecast_value)
  const lower    = sorted.map(d => d.lower_bound ?? null)
  const upper    = sorted.map(d => d.upper_bound ?? null)

  chart = new Chart(chartCanvas.value, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Прогноз',
          data: forecast,
          borderColor: '#4f46e5',
          backgroundColor: 'rgba(79,70,229,.1)',
          borderWidth: 2.5,
          tension: 0.3,
          fill: false,
          pointRadius: 5,
        },
        {
          label: '_lower',
          data: lower,
          borderColor: 'transparent',
          borderWidth: 0,
          tension: 0.3,
          fill: false,
          pointRadius: 0,
        },
        {
          label: '95% дов. интервал',
          data: upper,
          borderColor: 'rgba(156,163,175,.5)',
          borderDash: [3, 3],
          borderWidth: 1,
          tension: 0.3,
          fill: '-1',
          backgroundColor: 'rgba(156,163,175,.22)',
          pointRadius: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { intersect: false, mode: 'index' },
      plugins: {
        legend: {
          position: 'top',
          labels: { filter: item => !item.text.startsWith('_') },
        },
        tooltip: {
          filter: item => !item.dataset.label.startsWith('_'),
          callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.raw?.toFixed(1) ?? '—'}` },
        },
      },
      scales: {
        x: { grid: { color: '#f3f4f6' } },
        y: { grid: { color: '#f3f4f6' }, beginAtZero: false },
      },
    },
  })
}

watch(() => [props.data, props.metric], () => nextTick(buildChart), { deep: true })
onMounted(() => nextTick(buildChart))
onUnmounted(() => { if (chart) chart.destroy() })
</script>
