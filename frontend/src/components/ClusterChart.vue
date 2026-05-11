<template>
  <div>
    <div v-if="!data.length" class="empty-state">
      <div class="empty-icon">🔵</div>Нет данных кластеризации
    </div>
    <template v-else>
      <div class="chart-container" style="height:420px;position:relative">
        <canvas ref="chartCanvas"></canvas>
      </div>
      <div style="margin-top:16px;display:flex;gap:16px;flex-wrap:wrap">
        <div v-for="(label, cid) in clusterLabels" :key="cid" style="display:flex;align-items:center;gap:6px;font-size:13px">
          <div :style="{width:'12px',height:'12px',borderRadius:'50%',background:clusterColors[cid]}"></div>
          {{ label }} ({{ clusterCount(cid) }})
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { Chart, ScatterController, PointElement, LinearScale, Tooltip, Legend } from 'chart.js'
Chart.register(ScatterController, PointElement, LinearScale, Tooltip, Legend)

const props = defineProps({ data: { type: Array, default: () => [] } })
const chartCanvas = ref(null)
let chart = null

const clusterColors = ['#6366f1', '#ef4444', '#10b981', '#f59e0b', '#3b82f6', '#8b5cf6']
const clusterLabels = { 0: 'Высокая эффективность', 1: 'Группа риска', 2: 'Стабильные', 3: 'Новички' }

function clusterCount(cid) { return props.data.filter(d => d.cluster_id === Number(cid)).length }

function groupByCluster() {
  const groups = {}
  props.data.forEach(d => {
    const k = d.cluster_id
    if (!groups[k]) groups[k] = { label: clusterLabels[k] || `Кластер ${k}`, data: [], pointBackgroundColor: [], pointBorderColor: [] }
    groups[k].data.push({ x: d.x_tsne, y: d.y_tsne, name: d.employee_name })
    groups[k].pointBackgroundColor.push(clusterColors[k % clusterColors.length])
    groups[k].pointBorderColor.push(clusterColors[k % clusterColors.length])
  })
  return Object.values(groups).map((g, i) => ({
    ...g,
    pointRadius: 7,
    pointHoverRadius: 10,
  }))
}

function buildChart() {
  if (!chartCanvas.value || !props.data.length) return
  if (chart) { chart.destroy(); chart = null }
  chart = new Chart(chartCanvas.value, {
    type: 'scatter',
    data: { datasets: groupByCluster() },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top' },
        tooltip: {
          callbacks: {
            label: ctx => {
              const pt = ctx.dataset.data[ctx.dataIndex]
              return `${pt.name || ''} (${ctx.parsed.x.toFixed(1)}, ${ctx.parsed.y.toFixed(1)})`
            },
          },
        },
      },
      scales: {
        x: { title: { display: true, text: 't-SNE 1' }, grid: { color: '#f3f4f6' } },
        y: { title: { display: true, text: 't-SNE 2' }, grid: { color: '#f3f4f6' } },
      },
    },
  })
}

watch(() => props.data, () => nextTick(buildChart), { deep: true })
onMounted(() => nextTick(buildChart))
onUnmounted(() => { if (chart) chart.destroy() })
</script>
