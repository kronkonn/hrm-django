<template>
  <div>
    <div class="topbar">
      <router-link to="/employees" class="btn btn-outline btn-sm">← Назад</router-link>
      <div class="topbar-title">{{ emp?.full_name || 'Сотрудник' }}</div>
    </div>
    <div class="page-container">
      <div v-if="empStore.loading" class="loading"><div class="spinner"></div></div>
      <template v-else-if="emp">
        <div class="grid-2">
          <div class="card">
            <div class="card-header">
              <span class="card-title">Основная информация</span>
              <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
                <span :class="statusBadge(emp.status)" class="badge">{{ statusLabel(emp.status) }}</span>
                <span v-if="emp.current_leave" class="badge badge-blue">
                  В отпуске: {{ fmtRange(emp.current_leave) }}
                </span>
                <span v-else-if="emp.upcoming_leave" class="badge badge-yellow">
                  Отпуск с {{ fmtShortD(emp.upcoming_leave.start_date) }} по {{ fmtShortD(emp.upcoming_leave.end_date) }}
                </span>
                <button class="btn btn-outline btn-sm" @click="openEditModal">Редактировать</button>
              </div>
            </div>
            <div class="card-body">
              <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px">
                <div style="width:64px;height:64px;border-radius:50%;background:var(--primary-light);color:var(--primary);display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:700;flex-shrink:0">
                  {{ initials }}
                </div>
                <div>
                  <div style="font-size:18px;font-weight:700">{{ emp.full_name }}</div>
                  <div class="text-gray">{{ emp.position_title }}</div>
                </div>
              </div>
              <div class="info-row"><span>Email</span><span>{{ emp.email }}</span></div>
              <div class="info-row"><span>Телефон</span><span>{{ emp.phone || '—' }}</span></div>
              <div class="info-row"><span>Отдел</span><span>{{ emp.department_name }}</span></div>
              <div class="info-row"><span>Должность</span><span>{{ emp.position_title }}</span></div>
              <div class="info-row"><span>Руководитель</span><span>{{ emp.manager_name || '—' }}</span></div>
              <div class="info-row"><span>Дата найма</span><span>{{ formatDate(emp.hire_date) }}</span></div>
              <div class="info-row"><span>Оклад</span><span>{{ formatSalary(emp.salary) }}</span></div>
              <div class="info-row"><span>Пол</span><span>{{ emp.gender === 'M' ? 'Мужской' : 'Женский' }}</span></div>
              <div class="info-row"><span>Дата рождения</span><span>{{ formatDate(emp.birth_date) }}</span></div>
            </div>
          </div>

          <div class="card">
            <div class="card-header"><span class="card-title">Показатели для ML</span></div>
            <div class="card-body">
              <div class="metric-row">
                <span>Выполнение нормы часов</span>
                <div class="metric-bar-wrap">
                  <div class="metric-bar" :style="{width: Math.min(emp.hours_fulfillment ?? 0, 100)+'%', background: hfColor(emp.hours_fulfillment)}"></div>
                </div>
                <span style="font-weight:600">{{ emp.hours_fulfillment ?? '—' }}%</span>
              </div>
              <div class="info-row"><span>Сверхурочные ч.</span><span>{{ emp.overtime_hours }}</span></div>
              <div class="info-row"><span>Расстояние до офиса</span><span>{{ emp.distance_from_home }} км</span></div>
              <div class="info-row"><span>Кол-во работодателей</span><span>{{ emp.num_companies_worked }}</span></div>
              <div class="info-row"><span>Лет в компании</span><span>{{ emp.years_at_company }}</span></div>
              <div class="info-row"><span>Обучений в году</span><span>{{ emp.training_times_last_year }}</span></div>

              <div v-if="prediction" style="margin-top:16px;padding:12px;background:var(--gray-50);border-radius:8px">
                <div style="font-weight:600;font-size:13px;margin-bottom:8px">Прогноз увольнения</div>
                <div class="flex items-center gap-2 mb-4">
                  <div class="risk-bar" style="width:120px"><div class="risk-fill" :class="prediction.risk_label" :style="{width: (prediction.risk_score*100)+'%'}"></div></div>
                  <span :class="riskBadge(prediction.risk_label)" class="badge">{{ (prediction.risk_score*100).toFixed(0) }}%</span>
                </div>
                <div v-if="prediction.top_factors?.length" style="font-size:12px">
                  <div style="margin-bottom:6px;font-weight:600;color:#374151">Ключевые факторы:</div>
                  <div
                    v-for="f in prediction.top_factors.slice(0,3)"
                    :key="f.feature"
                    style="display:flex;align-items:baseline;gap:4px;margin-bottom:5px;line-height:1.4"
                  >
                    <span :style="f.direction === 'up' ? 'color:#ef4444;font-weight:700;flex-shrink:0' : 'color:#10b981;font-weight:700;flex-shrink:0'">
                      {{ f.direction === 'up' ? '↑' : '↓' }}
                    </span>
                    <span style="color:#111827">
                      <span style="font-weight:500">{{ f.label || f.feature }}</span>
                      <span v-if="f.raw_value" style="color:#374151">: {{ f.raw_value }}</span>
                      <span v-if="featureHint(f.feature)" style="color:#9ca3af;font-size:11px"> ({{ featureHint(f.feature) }})</span>
                      <span :style="f.direction === 'up' ? 'color:#ef4444' : 'color:#10b981'">
                        — {{ f.direction === 'up' ? 'повышает риск' : 'снижает риск' }}
                      </span>
                      <span style="color:#9ca3af"> ({{ Math.round(Math.abs(f.shap_value) * 100) }}%)</span>
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Leave history -->
        <div class="card" style="margin-top:16px">
          <div class="card-header"><span class="card-title">История отпусков и больничных</span></div>
          <div class="card-body" style="padding:0">
            <div v-if="leavesLoading" class="loading" style="padding:24px"><div class="spinner"></div></div>
            <div v-else-if="!leaves.length" style="padding:24px;text-align:center;color:#9ca3af">Нет записей</div>
            <table v-else style="width:100%">
              <thead>
                <tr>
                  <th style="padding:10px 16px;font-size:12px;font-weight:600;color:#6b7280;text-align:left">Тип</th>
                  <th style="padding:10px 16px;font-size:12px;font-weight:600;color:#6b7280;text-align:left">Период</th>
                  <th style="padding:10px 16px;font-size:12px;font-weight:600;color:#6b7280;text-align:left">Дней</th>
                  <th style="padding:10px 16px;font-size:12px;font-weight:600;color:#6b7280;text-align:left">Статус</th>
                  <th style="padding:10px 16px;font-size:12px;font-weight:600;color:#6b7280;text-align:left">ЭЛН</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="leave in leaves" :key="leave.id" style="border-top:1px solid var(--gray-100)">
                  <td style="padding:8px 16px;font-size:13px">{{ leave.leave_type_display }}</td>
                  <td style="padding:8px 16px;font-size:13px">{{ formatDate(leave.start_date) }} — {{ formatDate(leave.end_date) }}</td>
                  <td style="padding:8px 16px;font-size:13px">{{ leave.days_count }}</td>
                  <td style="padding:8px 16px"><span :class="leaveBadge(leave.status)" class="badge">{{ leave.status_display }}</span></td>
                  <td style="padding:8px 16px;font-size:13px;font-family:monospace">
                    <span v-if="leave.leave_type === 'sick' && leave.sick_details?.sick_leave_number">
                      {{ leave.sick_details.sick_leave_number }}
                    </span>
                    <span v-else-if="leave.leave_type === 'sick'" style="color:#9ca3af">—</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </div>

    <!-- Edit modal -->
    <Teleport to="body">
      <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
        <div class="modal modal-md">
          <div class="modal-header">
            <h3>Редактировать сотрудника</h3>
            <button class="btn btn-icon btn-outline" @click="showEditModal = false">✕</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label class="form-label">Отдел <span class="req">*</span></label>
              <select v-model="editForm.department" class="form-control" :class="{ 'input-error': editErrors.department }">
                <option value="">— Выберите отдел —</option>
                <option v-for="d in empStore.departments" :key="d.id" :value="d.id">{{ d.name }}</option>
              </select>
              <div v-if="editErrors.department" class="field-error">{{ editErrors.department }}</div>
            </div>
            <div class="form-group">
              <label class="form-label">Должность <span class="req">*</span></label>
              <select v-model="editForm.position" class="form-control" :class="{ 'input-error': editErrors.position }">
                <option value="">— Выберите должность —</option>
                <option v-for="p in empStore.positions" :key="p.id" :value="p.id">{{ p.title }}</option>
              </select>
              <div v-if="editErrors.position" class="field-error">{{ editErrors.position }}</div>
            </div>
            <div class="form-group">
              <label class="form-label">Оклад, ₽ <span class="req">*</span></label>
              <input
                v-model.number="editForm.salary"
                type="number"
                min="0"
                step="1000"
                class="form-control"
                :class="{ 'input-error': editErrors.salary }"
                placeholder="0"
              />
              <div v-if="editErrors.salary" class="field-error">{{ editErrors.salary }}</div>
            </div>
            <div class="form-group">
              <label class="form-label">Статус <span class="req">*</span></label>
              <select v-model="editForm.status" class="form-control" :class="{ 'input-error': editErrors.status }">
                <option value="">— Выберите статус —</option>
                <option value="active">Активен</option>
                <option value="inactive">Уволен</option>
                <option value="on_leave">В отпуске</option>
              </select>
              <div v-if="editErrors.status" class="field-error">{{ editErrors.status }}</div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-outline" @click="showEditModal = false">Отмена</button>
            <button class="btn btn-primary" :disabled="saving" @click="saveEdit">
              <span v-if="saving" class="spinner" style="width:14px;height:14px"></span>
              {{ saving ? 'Сохранение...' : 'Сохранить' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Toast -->
    <Teleport to="body">
      <div v-if="toast.show" class="toast-notify" :class="'toast-' + toast.type">{{ toast.message }}</div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useEmployeesStore } from '@/stores/employees'
import { useAnalyticsStore } from '@/stores/analytics'
import api from '@/api/index'
import { getLeaves } from '@/api/leaves'

const route = useRoute()
const empStore = useEmployeesStore()
const analyticsStore = useAnalyticsStore()
const prediction = ref(null)
const leaves = ref([])
const leavesLoading = ref(false)

const showEditModal = ref(false)
const saving = ref(false)
const editForm = ref({ department: '', position: '', salary: 0, status: '' })
const editErrors = ref({})
const toast = ref({ show: false, type: 'success', message: '' })
let _toastTimer = null

function openEditModal() {
  const e = emp.value
  editForm.value = {
    department: e.department ?? '',
    position:   e.position  ?? '',
    salary:     Number(e.salary) || 0,
    status:     e.status    ?? '',
  }
  editErrors.value = {}
  showEditModal.value = true
}

function validateEdit() {
  const errs = {}
  if (!editForm.value.department) errs.department = 'Выберите отдел'
  if (!editForm.value.position)   errs.position   = 'Выберите должность'
  if (!editForm.value.salary || editForm.value.salary <= 0) errs.salary = 'Укажите оклад больше 0'
  if (!editForm.value.status)     errs.status     = 'Выберите статус'
  editErrors.value = errs
  return Object.keys(errs).length === 0
}

function showToast(message, type = 'success') {
  if (_toastTimer) clearTimeout(_toastTimer)
  toast.value = { show: true, type, message }
  _toastTimer = setTimeout(() => { toast.value.show = false }, 3500)
}

async function saveEdit() {
  if (!validateEdit()) return
  saving.value = true
  try {
    await empStore.update(Number(route.params.id), editForm.value)
    showEditModal.value = false
    showToast('Данные сотрудника обновлены')
  } catch {
    showToast('Ошибка при сохранении', 'error')
  } finally {
    saving.value = false
  }
}

const emp = computed(() => empStore.current)
const initials = computed(() => {
  if (!emp.value) return ''
  return ((emp.value.last_name?.[0] || '') + (emp.value.first_name?.[0] || '')).toUpperCase()
})

function formatDate(d) { return d ? new Date(d).toLocaleDateString('ru-RU') : '—' }
function formatSalary(v) { return v ? Number(v).toLocaleString('ru-RU') + ' ₽' : '—' }
function statusLabel(s) { return { active: 'Активен', inactive: 'Уволен', on_leave: 'Отпуск' }[s] || s }
function statusBadge(s) { return { active: 'badge-green', inactive: 'badge-red', on_leave: 'badge-yellow' }[s] || 'badge-gray' }
function fmtShortD(iso) {
  if (!iso) return ''
  const [, m, day] = iso.split('-')
  return `${day}.${m}`
}
function fmtRange(leave) {
  return `${fmtShortD(leave.start_date)} — ${fmtShortD(leave.end_date)}`
}
function riskBadge(l) { return { low: 'badge-green', medium: 'badge-yellow', high: 'badge-red' }[l] || 'badge-gray' }
function leaveBadge(s) { return { pending: 'badge-yellow', approved: 'badge-green', rejected: 'badge-red', cancelled: 'badge-gray' }[s] || 'badge-gray' }
function hfColor(v) { return (v ?? 0) >= 90 && (v ?? 0) <= 115 ? '#10b981' : (v ?? 0) >= 70 ? '#f59e0b' : '#ef4444' }

const FEATURE_HINTS = {
  overtime_hours:       'норма 0–8ч',
  hours_fulfillment:    'норма 80–115%',
  num_companies_worked: 'чем больше — тем выше риск',
  days_since_last_award: 'чем дольше — тем выше риск',
  salary:               'ниже среднего по отделу',
  sick_days:            'норма до 5 дней/год',
}
function featureHint(feature) { return FEATURE_HINTS[feature] || '' }

onMounted(async () => {
  const empId = route.params.id
  await Promise.all([
    empStore.fetchOne(empId),
    empStore.fetchDepartments(),
    empStore.fetchPositions(),
  ])
  try {
    const { data } = await api.get(`/analytics/attrition/`, { params: {} })
    const list = data.results ?? data
    prediction.value = list.find(a => a.employee === Number(empId)) || null
  } catch {}
  leavesLoading.value = true
  try {
    const { data } = await getLeaves({ employee: empId, page_size: 50 })
    leaves.value = data.results ?? data
  } catch {} finally {
    leavesLoading.value = false
  }
})
</script>

<style scoped>
.info-row { display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid var(--gray-100); font-size:13px; }
.info-row span:first-child { color:var(--gray-500); }
.info-row span:last-child { font-weight:500; }
.metric-row { display:flex; align-items:center; gap:10px; margin-bottom:10px; font-size:13px; }
.metric-row > span:first-child { width:140px; flex-shrink:0; color:var(--gray-600); }
.metric-bar-wrap { flex:1; height:8px; background:var(--gray-200); border-radius:4px; overflow:hidden; }
.metric-bar { height:100%; border-radius:4px; transition:width .4s; }

.modal-md { max-width: 480px; width: 100%; }
.req { color: #ef4444; }
.input-error { border-color: #ef4444 !important; }
.field-error { font-size: 12px; color: #ef4444; margin-top: 4px; }

.toast-notify {
  position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%);
  padding: 12px 24px; border-radius: 10px;
  font-size: 14px; font-weight: 500;
  box-shadow: 0 8px 24px rgba(0,0,0,.2);
  z-index: 9999; white-space: nowrap;
  animation: toast-in .2s ease;
}
.toast-success { background: #064e3b; color: #d1fae5; }
.toast-error   { background: #7f1d1d; color: #fee2e2; }
@keyframes toast-in {
  from { opacity: 0; transform: translateX(-50%) translateY(10px); }
  to   { opacity: 1; transform: translateX(-50%) translateY(0); }
}
</style>
