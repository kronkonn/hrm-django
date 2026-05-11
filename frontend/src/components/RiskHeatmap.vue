<template>
  <div>
    <div v-if="!data.length" class="empty-state" style="padding:32px">
      <div class="empty-icon">📊</div>Нет данных
    </div>
    <template v-else>
      <!-- Heatmap -->
      <div class="heatmap-scroll">
        <table class="heatmap-table">
          <thead>
            <tr>
              <th class="th-emp">Сотрудник</th>
              <th class="th-score">Риск</th>
              <th v-for="col in COLUMNS" :key="col.key" class="th-feat" :title="col.label">
                {{ col.short }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rows" :key="row.id">
              <td class="td-emp">
                <div class="emp-name">{{ row.employee_name }}</div>
                <div class="emp-dept">{{ row.department_name }}</div>
              </td>
              <td class="td-score">
                <span class="badge" :class="badge(row.risk_label)">
                  {{ (row.risk_score * 100).toFixed(0) }}%
                </span>
              </td>
              <td
                v-for="col in COLUMNS"
                :key="col.key"
                class="td-heat"
                :style="cellStyle(row.shap[col.key])"
                :title="cellTooltip(row, col)"
              >
                {{ shapText(row.shap[col.key]) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Legend -->
      <div class="heatmap-legend">
        <div class="legend-grad"></div>
        <div class="legend-labels">
          <span>Снижает риск</span>
          <span>Нейтральный</span>
          <span>Повышает риск</span>
        </div>
      </div>

      <!-- Detail table -->
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Сотрудник</th>
              <th>Отдел</th>
              <th>Риск-балл</th>
              <th>Уровень</th>
              <th>Топ-факторы (SHAP)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in data" :key="'t' + a.id">
              <td style="font-weight:500">{{ a.employee_name }}</td>
              <td class="text-gray text-sm">{{ a.department_name }}</td>
              <td>
                <div style="display:flex;align-items:center;gap:8px">
                  <div class="risk-bar"><div class="risk-fill" :class="a.risk_label" :style="{width:(a.risk_score*100)+'%'}"></div></div>
                  <span style="font-weight:600;font-size:13px">{{ (a.risk_score*100).toFixed(1) }}%</span>
                </div>
              </td>
              <td><span :class="badge(a.risk_label)" class="badge">{{ labelRu(a.risk_label) }}</span></td>
              <td>
                <div v-for="f in topFactors(a)" :key="f.feature" style="font-size:11px;display:flex;align-items:baseline;gap:3px;margin-bottom:3px">
                  <span :style="f.direction==='up'?'color:#ef4444;font-weight:700;flex-shrink:0':'color:#10b981;font-weight:700;flex-shrink:0'">
                    {{ f.direction==='up' ? '↑' : '↓' }}
                  </span>
                  <span style="color:#111827;font-weight:500">{{ f.label || f.feature }}</span>
                  <span v-if="f.raw_value" style="color:#6b7280">: {{ f.raw_value }}</span>
                  <span :style="f.direction==='up'?'color:#ef4444':'color:#10b981'">
                    ({{ Math.round(Math.abs(f.shap_value) * 100) }}%)
                  </span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ data: { type: Array, default: () => [] } })

const COLUMNS = [
  { key: 'hours_fulfillment',     short: 'Норм.ч.',   label: 'Выполнение нормы часов (%)' },
  { key: 'overtime_hours',        short: 'Перераб.',  label: 'Сверхурочные часы' },
  { key: 'salary',                short: 'Зарплата',  label: 'Уровень зарплаты' },
  { key: 'years_at_company',      short: 'Стаж',      label: 'Лет в компании' },
  { key: 'num_companies_worked',  short: 'Раб.мест',  label: 'Количество работодателей' },
  { key: 'awards_last_year',      short: 'Награды',   label: 'Наград за год' },
  { key: 'days_since_last_award', short: 'Без нагр.', label: 'Дней без награждения' },
  { key: 'sick_days',             short: 'Больн.',    label: 'Больничных дней за год' },
  { key: 'bonus_share',           short: 'Бонус',     label: 'Доля бонуса' },
  { key: 'has_bonus_program',     short: 'Бон.пр.',   label: 'Бонусная программа' },
  { key: 'distance_from_home',    short: 'Дист.',     label: 'Расстояние до офиса' },
  { key: 'vacation_days_used',    short: 'Отпуск',    label: 'Дней отпуска за год' },
  { key: 'trainings_last_year',   short: 'Обуч.',     label: 'Обучений за год' },
]

const rows = computed(() =>
  [...props.data]
    .sort((a, b) => b.risk_score - a.risk_score)
    .map(row => {
      const shap = {}
      const shapRaw = {}
      for (const f of (row.top_factors || [])) {
        shap[f.feature]    = f.shap_value
        shapRaw[f.feature] = f.raw_value
      }
      return { ...row, shap, shapRaw }
    })
)

function badge(l) { return { low: 'badge-green', medium: 'badge-yellow', high: 'badge-red' }[l] || 'badge-gray' }
function labelRu(l) { return { low: 'Низкий', medium: 'Средний', high: 'Высокий' }[l] || l }
function topFactors(a) { return (a.top_factors || []).filter(f => Math.abs(f.shap_value) > 0.003).slice(0, 3) }

// Normalize SHAP relative to 0.25 so even values of 0.02-0.05 give visible color
const SHAP_MAX = 0.25

function cellStyle(val) {
  if (val === undefined || val === null) return { background: '#f3f4f6', color: '#9ca3af' }
  const v = Math.max(-SHAP_MAX, Math.min(SHAP_MAX, val))
  const t = Math.abs(v) / SHAP_MAX   // 0..1
  if (t < 0.005) return { background: '#f9fafb', color: '#9ca3af' }
  if (v > 0) {
    // white → pink → red
    const g = Math.round(255 - t * 215)
    const b = Math.round(255 - t * 215)
    return {
      background: `rgb(255,${g},${b})`,
      color: t > 0.55 ? '#fff' : '#7f1d1d',
    }
  } else {
    // white → mint → green
    const r = Math.round(255 - t * 225)
    const b = Math.round(255 - t * 145)
    return {
      background: `rgb(${r},210,${b})`,
      color: t > 0.55 ? '#fff' : '#064e3b',
    }
  }
}

function cellTooltip(row, col) {
  const val = row.shap[col.key]
  if (val === undefined || val === null) return col.label
  const raw = row.shapRaw?.[col.key]
  const pct = Math.round(Math.abs(val) * 100)
  const dir = val > 0 ? 'увеличивает риск увольнения' : 'снижает риск увольнения'
  const rawStr = raw ? `: ${raw}` : ''
  return `${col.label}${rawStr} — ${dir} на ${pct}%`
}

function shapText(val) {
  if (val === undefined || val === null) return ''
  if (Math.abs(val) < 0.005) return ''
  return val > 0 ? '↑' : '↓'
}
</script>

<style scoped>
.heatmap-scroll {
  overflow-x: auto;
  padding: 16px 20px 0;
}

.heatmap-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  white-space: nowrap;
}

.heatmap-table thead tr {
  background: #f9fafb;
}

.th-emp {
  text-align: left;
  padding: 8px 12px;
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: .4px;
  min-width: 140px;
  border-bottom: 2px solid #e5e7eb;
}
.th-score {
  text-align: center;
  padding: 8px 10px;
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: .4px;
  min-width: 54px;
  border-bottom: 2px solid #e5e7eb;
}
.th-feat {
  text-align: center;
  padding: 8px 4px;
  font-size: 10px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: .3px;
  min-width: 62px;
  max-width: 72px;
  border-bottom: 2px solid #e5e7eb;
  cursor: default;
}

.td-emp {
  padding: 6px 12px;
  border-bottom: 1px solid #f3f4f6;
}
.emp-name { font-weight: 500; color: #111827; font-size: 12px; }
.emp-dept { color: #9ca3af; font-size: 11px; }

.td-score {
  text-align: center;
  padding: 6px 8px;
  border-bottom: 1px solid #f3f4f6;
}

.td-heat {
  text-align: center;
  padding: 6px 4px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 13px;
  font-weight: 700;
  cursor: default;
  transition: opacity .1s;
  min-width: 62px;
}
.td-heat:hover { opacity: .75; }

/* Legend */
.heatmap-legend {
  padding: 12px 20px 16px;
}
.legend-grad {
  height: 10px;
  border-radius: 5px;
  background: linear-gradient(to right, #10b981, #f9fafb, #ef4444);
  margin-bottom: 4px;
}
.legend-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #6b7280;
}

/* Detail table */
.table-wrap {
  overflow-x: auto;
  padding: 0 20px 20px;
}
.table-wrap table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.table-wrap th {
  text-align: left;
  padding: 10px 14px;
  border-bottom: 2px solid #e5e7eb;
  color: #6b7280;
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .5px;
}
.table-wrap td {
  padding: 10px 14px;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: middle;
}
.table-wrap tr:last-child td { border-bottom: none; }

.risk-bar { width: 80px; height: 6px; background: #f3f4f6; border-radius: 3px; overflow: hidden; }
.risk-fill { height: 100%; border-radius: 3px; }
.risk-fill.high   { background: #ef4444; }
.risk-fill.medium { background: #f59e0b; }
.risk-fill.low    { background: #10b981; }
</style>
