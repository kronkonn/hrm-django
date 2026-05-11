<template>
  <div>
    <!-- Topbar -->
    <div class="topbar">
      <div class="topbar-title">Табель рабочего времени</div>
      <div style="display:flex;gap:8px;align-items:center">
        <button class="btn btn-outline btn-sm" @click="generateMonth" :disabled="generating">
          <span v-if="generating" class="spinner" style="width:13px;height:13px"></span>
          {{ generating ? 'Формирование...' : '⚙ Сформировать' }}
        </button>
      </div>
    </div>

    <div class="page-container">
      <!-- Controls -->
      <div class="ts-controls">
        <!-- Переключатель месяца -->
        <div class="month-switcher">
          <button class="btn btn-outline btn-sm btn-icon" @click="changeMonth(-1)">←</button>
          <span class="month-label">{{ monthName }} {{ year }}</span>
          <button class="btn btn-outline btn-sm btn-icon" @click="changeMonth(1)">→</button>
        </div>

        <!-- Фильтр по отделу -->
        <select class="form-control" style="width:180px" v-model="selectedDept" @change="loadData()">
          <option value="">Все отделы</option>
          <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
        </select>

        <!-- Поиск сотрудника -->
        <div class="search-wrap">
          <span class="search-icon">🔍</span>
          <input
            v-model="searchQuery"
            class="form-control search-input"
            placeholder="Поиск по имени..."
            style="width:200px;padding-left:32px"
          />
        </div>

        <!-- Легенда -->
        <div class="ts-legend">
          <div v-for="t in dayTypes" :key="t.key" class="legend-item">
            <div class="legend-dot" :style="{ background: t.bg, border: `2px solid ${t.border}` }"></div>
            <span>{{ t.label }}</span>
          </div>
          <div class="legend-item">
            <div class="legend-dot" style="background:#fff7ed;border:2px solid #f97316;position:relative">
              <div style="position:absolute;top:0;left:0;width:4px;height:100%;background:#f97316;border-radius:2px 0 0 2px"></div>
            </div>
            <span>Переработка</span>
          </div>
        </div>
      </div>

      <!-- Loader -->
      <div v-if="loading" class="loading" style="padding:60px">
        <div class="spinner"></div> Загрузка табеля...
      </div>

      <!-- Нет данных после загрузки и автогенерации -->
      <div v-else-if="!gridRows.length && !searchQuery" class="card">
        <div class="card-body" style="text-align:center;padding:48px">
          <div style="font-size:40px;margin-bottom:12px">📅</div>
          <div style="font-size:16px;font-weight:600;margin-bottom:8px">Табель не сформирован</div>
          <div style="color:#6b7280;margin-bottom:20px">Нажмите «Сформировать» чтобы создать записи за {{ monthName }} {{ year }}</div>
          <button class="btn btn-primary" @click="generateMonth" :disabled="generating">
            ⚙ Сформировать табель
          </button>
        </div>
      </div>

      <!-- Нет результатов поиска -->
      <div v-else-if="!gridRows.length && searchQuery" class="card">
        <div class="card-body" style="text-align:center;padding:40px;color:#6b7280">
          Сотрудник «{{ searchQuery }}» не найден
        </div>
      </div>

      <!-- Сетка -->
      <div v-else class="ts-grid-wrap">
        <div class="ts-grid-container">
          <table class="ts-table">
            <thead>
              <tr class="ts-week-row">
                <th class="ts-name-col" rowspan="2">Сотрудник</th>
                <th
                  v-for="day in daysInMonth"
                  :key="'d' + day"
                  class="ts-day-header"
                  :class="{
                    'ts-weekend-col': isWeekend(day),
                    'ts-today-col': isToday(day),
                  }"
                >
                  <div class="ts-day-num">{{ day }}</div>
                  <div class="ts-day-name">{{ dayShortName(day) }}</div>
                </th>
                <th class="ts-total-col">Часов</th>
                <th class="ts-total-col ts-ot-col">Сверх.</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in gridRows"
                :key="row.employee.id"
                class="ts-row"
                :class="{ 'ts-row-hover': hoveredRow === row.employee.id }"
                @mouseenter="hoveredRow = row.employee.id"
                @mouseleave="hoveredRow = null"
              >
                <!-- Имя сотрудника -->
                <td class="ts-name-cell">
                  <div class="ts-emp-name">{{ row.employee.last_name }}</div>
                  <div class="ts-emp-dept">{{ row.employee.department_name }}</div>
                </td>

                <!-- Ячейки дней -->
                <td
                  v-for="day in daysInMonth"
                  :key="day"
                  class="ts-cell-td"
                  :class="{ 'ts-weekend-col': isWeekend(day), 'ts-today-col': isToday(day) }"
                >
                  <div
                    class="ts-cell"
                    :class="getCellClass(row.days[day])"
                    :title="getCellTooltip(row.employee, day, row.days[day])"
                    @click="openEdit(row.employee, day, row.days[day])"
                  >
                    <div v-if="row.days[day]?.overtime_hours > 0" class="ts-ot-bar"></div>
                    <span class="ts-cell-text">{{ getCellText(row.days[day]) }}</span>
                  </div>
                </td>

                <!-- Итого -->
                <td class="ts-total-cell">
                  <div class="ts-total-val">{{ row.totalHours.toFixed(1) }}</div>
                </td>
                <td class="ts-total-cell ts-ot-col">
                  <div class="ts-ot-val" :class="{ 'ts-ot-nonzero': row.totalOvertime > 0 }">
                    {{ row.totalOvertime > 0 ? '+' + row.totalOvertime.toFixed(1) : '—' }}
                  </div>
                </td>
              </tr>
            </tbody>
            <!-- Итоговая строка -->
            <tfoot>
              <tr class="ts-foot-row">
                <td class="ts-name-cell" style="font-weight:700;font-size:12px">ИТОГО</td>
                <td
                  v-for="day in daysInMonth"
                  :key="'f' + day"
                  class="ts-cell-td ts-foot-cell"
                  :class="{ 'ts-weekend-col': isWeekend(day) }"
                >
                  <span v-if="!isWeekend(day)" style="font-size:10px;color:#6b7280">
                    {{ dayTotalHours(day) }}
                  </span>
                </td>
                <td class="ts-total-cell" style="font-weight:700">{{ grandTotal.toFixed(1) }}</td>
                <td class="ts-total-cell ts-ot-col" style="font-weight:700;color:#f97316">
                  +{{ grandOvertime.toFixed(1) }}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      <!-- ─── Модальное окно редактирования с диапазоном дат ─── -->
      <div v-if="editModal.open" class="modal-overlay" @click.self="editModal.open = false">
        <div class="modal" style="max-width:460px">
          <div class="modal-header">
            <h3>{{ editModal.employeeName }}</h3>
            <button class="btn btn-icon btn-outline" @click="editModal.open = false">✕</button>
          </div>
          <div class="modal-body">

            <!-- Тип дня -->
            <div class="form-group">
              <label class="form-label">Тип дня</label>
              <div class="day-type-grid">
                <button
                  v-for="t in dayTypes"
                  :key="t.key"
                  class="day-type-btn"
                  :class="{ active: editModal.form.day_type === t.key }"
                  :style="editModal.form.day_type === t.key ? { background: t.bg, borderColor: t.border, color: t.color } : {}"
                  @click="selectDayType(t.key)"
                >
                  {{ t.label }}
                </button>
              </div>
            </div>

            <!-- Диапазон дат -->
            <div class="grid-2">
              <div class="form-group">
                <label class="form-label">Дата начала</label>
                <input type="date" v-model="editModal.dateFrom" class="form-control" />
              </div>
              <div class="form-group">
                <label class="form-label">Дата окончания</label>
                <input type="date" v-model="editModal.dateTo" class="form-control" :min="editModal.dateFrom" />
              </div>
            </div>

            <!-- Часы — только для рабочих типов -->
            <template v-if="editModal.form.day_type === 'WORK' || editModal.form.day_type === 'REMOTE'">
              <div class="grid-2">
                <div class="form-group">
                  <label class="form-label">Часов отработано</label>
                  <input
                    v-model.number="editModal.form.hours_worked"
                    type="number" step="0.5" min="0" max="24"
                    class="form-control"
                  />
                </div>
                <div class="form-group">
                  <label class="form-label">Сверхурочных</label>
                  <input
                    v-model.number="editModal.form.overtime_hours"
                    type="number" step="0.5" min="0" max="8"
                    class="form-control"
                  />
                </div>
              </div>
            </template>

            <div class="form-group">
              <label class="form-label">Примечание</label>
              <input v-model="editModal.form.note" class="form-control" placeholder="Необязательно" />
            </div>

            <!-- Индикатор диапазона -->
            <div v-if="rangeLength > 1" class="range-hint">
              Будет заполнено {{ rangeLength }} {{ rangeDaysWord() }} с {{ formatDateHint(editModal.dateFrom) }}
              по {{ formatDateHint(editModal.dateTo) }}
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-outline" @click="editModal.open = false">Отмена</button>
            <button class="btn btn-primary" @click="saveRange" :disabled="editModal.saving || !editModal.dateFrom || !editModal.dateTo">
              <span v-if="editModal.saving" class="spinner" style="width:13px;height:13px"></span>
              {{ rangeLength > 1 ? 'Применить к диапазону' : 'Сохранить' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { getDepartments } from '@/api/employees'
import { getTimesheets, createTimesheet, updateTimesheet, generateMonth as apiGenerate } from '@/api/timesheets'

// ─── Состояние ────────────────────────────────────────────────────────────────
const today        = new Date()
const month        = ref(today.getMonth() + 1)
const year         = ref(today.getFullYear())
const selectedDept = ref('')
const searchQuery  = ref('')
const departments  = ref([])
const loading      = ref(false)
const generating   = ref(false)
const timesheets   = ref([])
const hoveredRow   = ref(null)

// ─── Константы ────────────────────────────────────────────────────────────────
const MONTH_NAMES = [
  'Январь','Февраль','Март','Апрель','Май','Июнь',
  'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь',
]
const DAY_NAMES = ['Вс','Пн','Вт','Ср','Чт','Пт','Сб']

const dayTypes = [
  { key: 'WORK',     label: 'Рабочий',    bg: '#d1fae5', border: '#10b981', color: '#065f46' },
  { key: 'REMOTE',   label: 'Удалённо',   bg: '#dbeafe', border: '#3b82f6', color: '#1e40af' },
  { key: 'VACATION', label: 'Отпуск',     bg: '#fef3c7', border: '#f59e0b', color: '#92400e' },
  { key: 'SICK',     label: 'Больничный', bg: '#fee2e2', border: '#ef4444', color: '#991b1b' },
  { key: 'HOLIDAY',  label: 'Праздник',   bg: '#f3e8ff', border: '#a78bfa', color: '#6b21a8' },
  { key: 'WEEKEND',  label: 'Выходной',   bg: '#f3f4f6', border: '#d1d5db', color: '#9ca3af' },
]

// ─── Вычисляемые ──────────────────────────────────────────────────────────────
const monthName = computed(() => MONTH_NAMES[month.value - 1])

const daysInMonth = computed(() => {
  const d = new Date(year.value, month.value, 0).getDate()
  return Array.from({ length: d }, (_, i) => i + 1)
})

const gridRows = computed(() => {
  if (!timesheets.value.length) return []

  const empMap = {}
  timesheets.value.forEach(t => {
    const eid = t.employee
    if (!empMap[eid]) {
      empMap[eid] = {
        employee: {
          id: eid,
          last_name:       t.employee_name?.split(' ')[0] || '',
          first_name:      t.employee_name?.split(' ')[1] || '',
          full_name:       t.employee_name,
          department_name: t.department_name,
        },
        days:         {},
        totalHours:   0,
        totalOvertime: 0,
      }
    }
    const d = new Date(t.work_date)
    if (d.getFullYear() === year.value && d.getMonth() + 1 === month.value) {
      const dayNum = d.getDate()
      empMap[eid].days[dayNum]     = t
      empMap[eid].totalHours      += t.hours_worked    || 0
      empMap[eid].totalOvertime   += t.overtime_hours  || 0
    }
  })

  let rows = Object.values(empMap).sort((a, b) =>
    (a.employee.last_name || '').localeCompare(b.employee.last_name || '', 'ru')
  )

  // Фильтр по строке поиска
  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    rows = rows.filter(r =>
      (r.employee.full_name || '').toLowerCase().includes(q) ||
      (r.employee.last_name || '').toLowerCase().includes(q)
    )
  }

  return rows
})

const grandTotal    = computed(() => gridRows.value.reduce((s, r) => s + r.totalHours,    0))
const grandOvertime = computed(() => gridRows.value.reduce((s, r) => s + r.totalOvertime, 0))

// Длина выбранного диапазона в днях
const rangeLength = computed(() => {
  if (!editModal.dateFrom || !editModal.dateTo) return 1
  const from = new Date(editModal.dateFrom)
  const to   = new Date(editModal.dateTo)
  if (to < from) return 1
  return Math.round((to - from) / 86400000) + 1
})

function rangeDaysWord() {
  const n = rangeLength.value
  if (n % 10 === 1 && n % 100 !== 11) return 'день'
  if ([2,3,4].includes(n % 10) && ![12,13,14].includes(n % 100)) return 'дня'
  return 'дней'
}

// ─── Хелперы ──────────────────────────────────────────────────────────────────
function isWeekend(day) {
  const wd = new Date(year.value, month.value - 1, day).getDay()
  return wd === 0 || wd === 6
}

function isToday(day) {
  return day === today.getDate() &&
         month.value === today.getMonth() + 1 &&
         year.value  === today.getFullYear()
}

function dayShortName(day) {
  return DAY_NAMES[new Date(year.value, month.value - 1, day).getDay()]
}

function getCellClass(record) {
  if (!record) return 'ts-cell-empty'
  return { WORK: 'ts-work', REMOTE: 'ts-remote', VACATION: 'ts-vacation',
           SICK: 'ts-sick', HOLIDAY: 'ts-holiday', WEEKEND: 'ts-weekend' }[record.day_type] || 'ts-cell-empty'
}

function getCellText(record) {
  if (!record || record.day_type === 'WEEKEND' || record.day_type === 'HOLIDAY') return ''
  if (record.day_type === 'VACATION') return 'О'
  if (record.day_type === 'SICK')     return 'Б'
  if (record.hours_worked > 0)
    return record.hours_worked % 1 === 0
      ? String(record.hours_worked)
      : record.hours_worked.toFixed(1)
  return ''
}

function getCellTooltip(emp, day, record) {
  const dateStr = `${String(day).padStart(2,'0')}.${String(month.value).padStart(2,'0')}.${year.value}`
  if (!record) return `${emp.full_name} — ${dateStr}: нет записи`
  const typeLabel = dayTypes.find(t => t.key === record.day_type)?.label || record.day_type
  let tip = `${emp.full_name} — ${dateStr}\nТип: ${typeLabel}`
  if (record.hours_worked)   tip += `\nЧасов: ${record.hours_worked}`
  if (record.overtime_hours) tip += `\nСверхурочных: ${record.overtime_hours}`
  if (record.note)           tip += `\nПримечание: ${record.note}`
  return tip
}

function dayTotalHours(day) {
  const total = gridRows.value.reduce((s, r) => s + (r.days[day]?.hours_worked || 0), 0)
  return total > 0 ? total.toFixed(0) : ''
}

function formatDateHint(iso) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-')
  return `${d}.${m}.${y}`
}

// ─── Редактирование ячейки / диапазона ────────────────────────────────────────
const editModal = reactive({
  open: false,
  saving: false,
  employeeId: null,
  employeeName: '',
  dateFrom: '',
  dateTo: '',
  form: { day_type: 'WORK', hours_worked: 8, overtime_hours: 0, note: '' },
})

function toIso(y, m, d) {
  return `${y}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}`
}

function openEdit(emp, day, record) {
  const iso = toIso(year.value, month.value, day)
  editModal.open         = true
  editModal.saving       = false
  editModal.employeeId   = emp.id
  editModal.employeeName = emp.full_name || `${emp.last_name} ${emp.first_name}`
  editModal.dateFrom     = iso
  editModal.dateTo       = iso

  if (record) {
    editModal.form = {
      day_type:       record.day_type,
      hours_worked:   record.hours_worked,
      overtime_hours: record.overtime_hours,
      note:           record.note || '',
    }
  } else {
    const weekend = isWeekend(day)
    editModal.form = {
      day_type:       weekend ? 'WEEKEND' : 'WORK',
      hours_worked:   weekend ? 0 : 8,
      overtime_hours: 0,
      note:           '',
    }
  }
}

function selectDayType(key) {
  editModal.form.day_type = key
  if (['WEEKEND', 'HOLIDAY', 'SICK', 'VACATION'].includes(key)) {
    editModal.form.hours_worked   = 0
    editModal.form.overtime_hours = 0
  } else if (editModal.form.hours_worked === 0) {
    editModal.form.hours_worked = 8
  }
}

async function saveRange() {
  if (!editModal.dateFrom || !editModal.dateTo) return
  editModal.saving = true
  try {
    const from = new Date(editModal.dateFrom)
    const to   = new Date(editModal.dateTo)
    if (to < from) return

    const cur = new Date(from)
    while (cur <= to) {
      const d        = cur.getDate()
      const m        = cur.getMonth() + 1
      const y        = cur.getFullYear()
      const workDate = toIso(y, m, d)

      const existing = timesheets.value.find(
        t => t.employee === editModal.employeeId && t.work_date === workDate
      )
      const payload = {
        employee:       editModal.employeeId,
        work_date:      workDate,
        day_type:       editModal.form.day_type,
        hours_worked:   editModal.form.hours_worked,
        overtime_hours: editModal.form.overtime_hours,
        note:           editModal.form.note,
      }

      if (existing) {
        const { data } = await updateTimesheet(existing.id, payload)
        _patchRecord(data)
      } else {
        const { data } = await createTimesheet(payload)
        _patchRecord(data)
      }
      cur.setDate(cur.getDate() + 1)
    }
    editModal.open = false
  } finally {
    editModal.saving = false
  }
}

function _patchRecord(data) {
  const idx = timesheets.value.findIndex(t => t.id === data.id)
  if (idx !== -1) timesheets.value[idx] = data
  else            timesheets.value.push(data)
}

// ─── Загрузка данных ──────────────────────────────────────────────────────────
async function loadData(autoGenerate = false) {
  loading.value = true
  try {
    const params = { month: month.value, year: year.value }
    if (selectedDept.value) params.department = selectedDept.value
    const { data } = await getTimesheets(params)
    timesheets.value = data.results ?? data

    // Авто-генерация стандартного графика если нет записей
    if (autoGenerate && !timesheets.value.length) {
      loading.value = false
      await generateMonth()
    }
  } finally {
    loading.value = false
  }
}

async function generateMonth() {
  generating.value = true
  try {
    await apiGenerate(month.value, year.value)
    await loadData()
  } finally {
    generating.value = false
  }
}

function changeMonth(delta) {
  let m = month.value + delta
  let y = year.value
  if (m > 12) { m = 1;  y++ }
  if (m < 1)  { m = 12; y-- }
  month.value = m
  year.value  = y
  loadData(true)
}

onMounted(async () => {
  const [, deptRes] = await Promise.all([
    loadData(true),
    getDepartments(),
  ])
  departments.value = deptRes.data.results ?? deptRes.data
})
</script>

<style scoped>
/* Controls */
.ts-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}
.month-switcher {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fff;
  border: 1px solid var(--gray-300);
  border-radius: 8px;
  padding: 6px 12px;
}
.month-label {
  font-size: 15px;
  font-weight: 700;
  min-width: 140px;
  text-align: center;
  color: var(--gray-800);
}

/* Search */
.search-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.search-icon {
  position: absolute;
  left: 9px;
  font-size: 13px;
  pointer-events: none;
  z-index: 1;
}
.search-input { padding-left: 30px !important; }

.ts-legend {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-left: auto;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--gray-600);
}
.legend-dot {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
}

/* Grid wrapper */
.ts-grid-wrap { overflow-x: auto; }
.ts-grid-container { min-width: 100%; display: inline-block; }

/* Table */
.ts-table {
  border-collapse: separate;
  border-spacing: 0;
  font-size: 12px;
  white-space: nowrap;
}

/* Header */
.ts-day-header {
  padding: 4px 2px;
  text-align: center;
  background: var(--gray-50);
  border-bottom: 2px solid var(--gray-200);
  border-right: 1px solid var(--gray-100);
  min-width: 38px;
  max-width: 38px;
  position: sticky;
  top: 0;
  z-index: 5;
  vertical-align: bottom;
}
.ts-day-num {
  font-weight: 700;
  font-size: 13px;
  color: var(--gray-700);
  line-height: 1.2;
}
.ts-day-name {
  font-size: 10px;
  color: var(--gray-400);
  font-weight: 500;
}
.ts-name-col {
  position: sticky;
  left: 0;
  z-index: 10;
  background: var(--gray-50);
  border-bottom: 2px solid var(--gray-200);
  border-right: 2px solid var(--gray-200);
  padding: 8px 12px;
  min-width: 160px;
  max-width: 180px;
  text-align: left;
  font-size: 12px;
  color: var(--gray-600);
  font-weight: 600;
}
.ts-total-col {
  min-width: 56px;
  text-align: center;
  padding: 4px 8px;
  background: var(--gray-50);
  border-bottom: 2px solid var(--gray-200);
  border-left: 2px solid var(--gray-200);
  font-size: 11px;
  color: var(--gray-600);
  font-weight: 600;
  position: sticky;
  top: 0;
  z-index: 5;
}
.ts-ot-col { color: #f97316 !important; }

/* Row highlight — светло-голубой при наведении */
.ts-row-hover .ts-name-cell,
.ts-row-hover .ts-cell-td,
.ts-row-hover .ts-total-cell {
  background: #eff6ff !important;
}
/* Sticky name cell must also update */
.ts-row-hover .ts-name-cell {
  background: #eff6ff !important;
}

.ts-name-cell {
  position: sticky;
  left: 0;
  z-index: 4;
  background: #fff;
  border-right: 2px solid var(--gray-200);
  border-bottom: 1px solid var(--gray-100);
  padding: 6px 12px;
  min-width: 160px;
  max-width: 180px;
  transition: background .1s;
}
.ts-emp-name { font-weight: 600; font-size: 13px; color: var(--gray-800); }
.ts-emp-dept { font-size: 10px; color: var(--gray-400); margin-top: 1px; }

.ts-cell-td {
  padding: 2px 2px;
  border-bottom: 1px solid var(--gray-100);
  border-right: 1px solid var(--gray-100);
  vertical-align: middle;
  transition: background .1s;
}

/* Day-type coloring on column */
.ts-weekend-col { background: #f9fafb !important; }
.ts-today-col .ts-day-num { color: var(--primary) !important; }
.ts-today-col > .ts-day-num::after {
  content: '';
  display: block;
  width: 4px;
  height: 4px;
  background: var(--primary);
  border-radius: 50%;
  margin: 2px auto 0;
}

/* Cell */
.ts-cell {
  height: 30px;
  width: 34px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: filter .15s;
  position: relative;
  overflow: hidden;
  margin: 0 auto;
}
.ts-cell:hover { filter: brightness(.90); }

.ts-cell-empty { background: transparent; cursor: pointer; }
.ts-cell-empty:hover { background: var(--gray-100); }
.ts-work     { background: #d1fae5; }
.ts-remote   { background: #dbeafe; }
.ts-vacation { background: #fef3c7; }
.ts-sick     { background: #fee2e2; }
.ts-holiday  { background: #f3e8ff; }
.ts-weekend  { background: #f3f4f6; cursor: default; }

/* Overtime bar */
.ts-ot-bar {
  position: absolute;
  top: 0; left: 0;
  width: 4px;
  height: 100%;
  background: #f97316;
  border-radius: 3px 0 0 3px;
}

/* Cell text */
.ts-cell-text {
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
  color: rgba(0,0,0,.55);
  position: relative;
}

/* Total column cells */
.ts-total-cell {
  border-left: 2px solid var(--gray-200);
  border-bottom: 1px solid var(--gray-100);
  text-align: center;
  padding: 0 6px;
  min-width: 56px;
  transition: background .1s;
}
.ts-total-val { font-weight: 700; font-size: 13px; color: var(--gray-700); }
.ts-ot-val { font-size: 12px; color: var(--gray-400); }
.ts-ot-nonzero { color: #f97316 !important; font-weight: 600; }

/* Footer */
.ts-foot-row { background: var(--gray-50); }
.ts-foot-cell { text-align: center; padding: 4px 2px; border-bottom: none; }
.ts-week-row th { top: 0; }

/* Edit modal day-type grid */
.day-type-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
}
.day-type-btn {
  padding: 8px 4px;
  border: 2px solid var(--gray-300);
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  color: var(--gray-700);
  transition: all .15s;
  text-align: center;
}
.day-type-btn:hover { border-color: var(--gray-400); background: var(--gray-50); }
.day-type-btn.active { border-width: 2px; }

/* Range hint */
.range-hint {
  margin-top: 4px;
  padding: 8px 12px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  font-size: 12px;
  color: #1d4ed8;
}
</style>
