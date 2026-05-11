<template>
  <div>
    <div class="topbar">
      <div class="topbar-title">Заявки на отпуск</div>
      <button class="btn btn-primary btn-sm" @click="showModal = true">+ Новая заявка</button>
    </div>
    <div class="page-container">
      <div class="page-header" style="margin-bottom:16px">
        <div class="tabs" style="border:none;margin:0">
          <button v-for="tab in tabs" :key="tab.value" class="tab-btn" :class="{active: activeTab === tab.value}" @click="activeTab = tab.value; loadLeaves()">
            {{ tab.label }}
          </button>
        </div>
      </div>

      <div class="card">
        <div v-if="loading" class="loading"><div class="spinner"></div></div>
        <div v-else class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Сотрудник</th>
                <th>Тип</th>
                <th>Период</th>
                <th>Дней</th>
                <th>Статус</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!leaves.length">
                <td colspan="6" style="text-align:center;padding:32px;color:#9ca3af">Заявок нет</td>
              </tr>
              <tr v-for="leave in leaves" :key="leave.id">
                <td style="font-weight:500">{{ leave.employee_name }}</td>
                <td>{{ leave.leave_type_display }}</td>
                <td class="text-sm">{{ formatDate(leave.start_date) }} — {{ formatDate(leave.end_date) }}</td>
                <td>{{ leave.days_count }}</td>
                <td><span :class="statusBadge(leave.status)" class="badge">{{ leave.status_display }}</span></td>
                <td>
                  <div style="display:flex;gap:6px;align-items:center">
                    <template v-if="leave.status === 'pending'">
                      <button class="btn btn-success btn-sm" @click="approve(leave.id)">✓</button>
                      <button class="btn btn-danger btn-sm" @click="reject(leave.id)">✕</button>
                    </template>
                    <button
                      v-if="leave.leave_type === 'sick' && authStore.canAccessHR"
                      class="btn btn-outline btn-sm"
                      title="Данные больничного листа"
                      @click="openSickModal(leave)"
                    >🏥</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- New leave modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>Новая заявка на отпуск</h3>
          <button class="btn btn-icon btn-outline" @click="showModal = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">Сотрудник *</label>
            <select v-model="form.employee" class="form-control" required>
              <option value="">— Выберите —</option>
              <option v-for="e in employees" :key="e.id" :value="e.id">{{ e.full_name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Тип отпуска</label>
            <select v-model="form.leave_type" class="form-control">
              <option value="annual">Ежегодный</option>
              <option value="sick">Больничный</option>
              <option value="unpaid">Без сохранения зарплаты</option>
              <option value="study">Учебный</option>
            </select>
          </div>
          <div class="grid-2">
            <div class="form-group">
              <label class="form-label">Начало *</label>
              <input v-model="form.start_date" type="date" class="form-control" required />
            </div>
            <div class="form-group">
              <label class="form-label">Конец *</label>
              <input v-model="form.end_date" type="date" class="form-control" required />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Причина</label>
            <textarea v-model="form.reason" class="form-control" rows="2"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="showModal = false">Отмена</button>
          <button class="btn btn-primary" @click="saveLeave" :disabled="saving">
            {{ saving ? 'Сохранение...' : 'Создать' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Sick leave details modal -->
    <div v-if="showSickModal" class="modal-overlay" @click.self="showSickModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>Данные больничного листа</h3>
          <button class="btn btn-icon btn-outline" @click="showSickModal = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="text-sm" style="color:#6b7280;margin-bottom:12px">
            {{ sickLeave?.employee_name }} · {{ formatDate(sickLeave?.start_date) }} — {{ formatDate(sickLeave?.end_date) }}
          </div>
          <div class="form-group">
            <label class="form-label">Номер ЭЛН (12 цифр)</label>
            <input v-model="sickForm.sick_leave_number" type="text" maxlength="12" class="form-control" placeholder="123456789012" />
          </div>
          <div class="grid-2">
            <div class="form-group">
              <label class="form-label">Дата открытия</label>
              <input v-model="sickForm.issue_date" type="date" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Дата закрытия</label>
              <input v-model="sickForm.close_date" type="date" class="form-control" />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Медицинское учреждение</label>
            <input v-model="sickForm.medical_institution" type="text" class="form-control" placeholder="ГБУЗ Городская поликлиника №1" />
          </div>
          <div class="form-group">
            <label class="form-label">Код диагноза (МКБ-10)</label>
            <input v-model="sickForm.diagnosis_code" type="text" maxlength="20" class="form-control" placeholder="J06.9" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="showSickModal = false">Отмена</button>
          <button class="btn btn-primary" @click="saveSickDetails" :disabled="savingSick">
            {{ savingSick ? 'Сохранение...' : 'Сохранить' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as leavesApi from '@/api/leaves'
import { getEmployees } from '@/api/employees'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const leaves = ref([])
const employees = ref([])
const loading = ref(false)
const showModal = ref(false)
const saving = ref(false)
const activeTab = ref('pending')
const form = ref({ employee: '', leave_type: 'annual', start_date: '', end_date: '', reason: '' })

const showSickModal = ref(false)
const savingSick = ref(false)
const sickLeave = ref(null)
const sickForm = ref({ sick_leave_number: '', issue_date: '', close_date: '', medical_institution: '', diagnosis_code: '' })

const tabs = [
  { value: 'pending', label: 'На рассмотрении' },
  { value: 'approved', label: 'Одобренные' },
  { value: 'rejected', label: 'Отклонённые' },
  { value: '', label: 'Все' },
]

function formatDate(d) { return d ? new Date(d).toLocaleDateString('ru-RU') : '—' }
function statusBadge(s) { return { pending: 'badge-yellow', approved: 'badge-green', rejected: 'badge-red', cancelled: 'badge-gray' }[s] || 'badge-gray' }

async function loadLeaves() {
  loading.value = true
  try {
    const { data } = await leavesApi.getLeaves(activeTab.value ? { status: activeTab.value } : {})
    leaves.value = data.results ?? data
  } finally { loading.value = false }
}

async function approve(id) {
  await leavesApi.approveLeave(id)
  await loadLeaves()
}

async function reject(id) {
  await leavesApi.rejectLeave(id)
  await loadLeaves()
}

async function saveLeave() {
  saving.value = true
  try {
    await leavesApi.createLeave(form.value)
    showModal.value = false
    form.value = { employee: '', leave_type: 'annual', start_date: '', end_date: '', reason: '' }
    await loadLeaves()
  } finally { saving.value = false }
}

function openSickModal(leave) {
  sickLeave.value = leave
  const d = leave.sick_details || {}
  sickForm.value = {
    sick_leave_number: d.sick_leave_number || '',
    issue_date: d.issue_date || '',
    close_date: d.close_date || '',
    medical_institution: d.medical_institution || '',
    diagnosis_code: d.diagnosis_code || '',
  }
  showSickModal.value = true
}

async function saveSickDetails() {
  savingSick.value = true
  try {
    await leavesApi.updateSickDetails(sickLeave.value.id, sickForm.value)
    showSickModal.value = false
    await loadLeaves()
  } finally { savingSick.value = false }
}

onMounted(async () => {
  await loadLeaves()
  const { data } = await getEmployees({ status: 'active', page_size: 100 })
  employees.value = data.results ?? data
})
</script>
