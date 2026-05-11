<template>
  <div>
    <div class="topbar">
      <div class="topbar-title">Мои заявки на отпуск</div>
      <button class="btn btn-primary btn-sm" @click="showModal = true">+ Новая заявка</button>
    </div>
    <div class="page-container">

      <!-- Статистика -->
      <div class="stats-grid" style="grid-template-columns:repeat(3,1fr);margin-bottom:20px">
        <div class="stat-card">
          <div class="stat-icon yellow">🌴</div>
          <div class="stat-info">
            <div class="stat-value">{{ counts.pending }}</div>
            <div class="stat-label">На рассмотрении</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon green">✅</div>
          <div class="stat-info">
            <div class="stat-value">{{ counts.approved }}</div>
            <div class="stat-label">Одобрено</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon red">✕</div>
          <div class="stat-info">
            <div class="stat-value">{{ counts.rejected }}</div>
            <div class="stat-label">Отклонено</div>
          </div>
        </div>
      </div>

      <div class="card">
        <div v-if="loading" class="loading"><div class="spinner"></div></div>
        <div v-else>
          <div v-if="!leaves.length" class="empty-state">
            <div class="empty-icon">🌴</div>
            <div>Заявок пока нет</div>
            <button class="btn btn-primary" style="margin-top:12px" @click="showModal = true">Создать заявку</button>
          </div>
          <div v-else class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Тип</th>
                  <th>Период</th>
                  <th>Дней</th>
                  <th>Статус</th>
                  <th>Дата подачи</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="leave in leaves" :key="leave.id">
                  <td>{{ leave.leave_type_display }}</td>
                  <td class="text-sm">{{ formatDate(leave.start_date) }} — {{ formatDate(leave.end_date) }}</td>
                  <td>{{ leave.days_count }}</td>
                  <td>
                    <span :class="statusBadge(leave.status)" class="badge">{{ leave.status_display }}</span>
                  </td>
                  <td class="text-sm text-gray">{{ formatDate(leave.created_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Модалка создания -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>Новая заявка на отпуск</h3>
          <button class="btn btn-icon btn-outline" @click="showModal = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">Тип отпуска</label>
            <select v-model="form.leave_type" class="form-control">
              <option value="annual">Ежегодный оплачиваемый</option>
              <option value="sick">Больничный</option>
              <option value="unpaid">Без сохранения зарплаты</option>
              <option value="study">Учебный</option>
            </select>
          </div>
          <div class="grid-2">
            <div class="form-group">
              <label class="form-label">Дата начала *</label>
              <input v-model="form.start_date" type="date" class="form-control" required />
            </div>
            <div class="form-group">
              <label class="form-label">Дата окончания *</label>
              <input v-model="form.end_date" type="date" class="form-control" required />
            </div>
          </div>
          <div v-if="form.start_date && form.end_date" class="form-group">
            <div style="font-size:13px;color:var(--gray-600);background:var(--gray-50);padding:8px 12px;border-radius:6px">
              Продолжительность: <strong>{{ calcDays }} дн.</strong>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Причина (необязательно)</label>
            <textarea v-model="form.reason" class="form-control" rows="2" placeholder="Комментарий к заявке..."></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="showModal = false">Отмена</button>
          <button class="btn btn-primary" @click="submitLeave" :disabled="saving || !form.start_date || !form.end_date">
            {{ saving ? 'Отправка...' : 'Подать заявку' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getLeaves, createLeave } from '@/api/leaves'

const leaves = ref([])
const loading = ref(false)
const showModal = ref(false)
const saving = ref(false)
const form = ref({ leave_type: 'annual', start_date: '', end_date: '', reason: '' })

const counts = computed(() => ({
  pending: leaves.value.filter(l => l.status === 'pending').length,
  approved: leaves.value.filter(l => l.status === 'approved').length,
  rejected: leaves.value.filter(l => l.status === 'rejected').length,
}))

const calcDays = computed(() => {
  if (!form.value.start_date || !form.value.end_date) return 0
  const ms = new Date(form.value.end_date) - new Date(form.value.start_date)
  return Math.max(1, Math.floor(ms / 86400000) + 1)
})

function formatDate(d) { return d ? new Date(d).toLocaleDateString('ru-RU') : '—' }
function statusBadge(s) { return { pending: 'badge-yellow', approved: 'badge-green', rejected: 'badge-red', cancelled: 'badge-gray' }[s] || 'badge-gray' }

async function loadLeaves() {
  loading.value = true
  try {
    const { data } = await getLeaves()
    leaves.value = data.results ?? data
  } finally {
    loading.value = false
  }
}

async function submitLeave() {
  saving.value = true
  try {
    await createLeave({
      leave_type: form.value.leave_type,
      start_date: form.value.start_date,
      end_date: form.value.end_date,
      reason: form.value.reason,
    })
    showModal.value = false
    form.value = { leave_type: 'annual', start_date: '', end_date: '', reason: '' }
    await loadLeaves()
  } finally {
    saving.value = false
  }
}

onMounted(loadLeaves)
</script>
