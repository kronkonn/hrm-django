<template>
  <div>
    <div class="topbar">
      <div class="topbar-title">Сотрудники</div>
      <button class="btn btn-primary btn-sm" @click="showModal = true">+ Добавить</button>
    </div>
    <div class="page-container">
      <div class="page-header">
        <div class="search-bar">
          <span class="icon">🔍</span>
          <input v-model="search" placeholder="Поиск по имени или email..." @input="onSearch" />
        </div>
        <select class="form-control" style="width:180px" v-model="filterDept" @change="onSearch">
          <option value="">Все отделы</option>
          <option v-for="d in empStore.departments" :key="d.id" :value="d.id">{{ d.name }}</option>
        </select>
        <select class="form-control" style="width:150px" v-model="filterStatus" @change="onSearch">
          <option value="">Все статусы</option>
          <option value="active">Активные</option>
          <option value="inactive">Уволен</option>
          <option value="on_leave">В отпуске</option>
        </select>
      </div>

      <div class="card">
        <div v-if="empStore.loading" class="loading"><div class="spinner"></div> Загрузка...</div>
        <div v-else>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Сотрудник</th>
                  <th>Отдел</th>
                  <th>Должность</th>
                  <th>Оклад</th>
                  <th>Дата найма</th>
                  <th>Статус</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!empStore.list.length">
                  <td colspan="7" style="text-align:center;padding:32px;color:#9ca3af">Сотрудники не найдены</td>
                </tr>
                <tr v-for="emp in empStore.list" :key="emp.id">
                  <td>
                    <div style="display:flex;align-items:center;gap:10px">
                      <div class="avatar-sm">{{ initials(emp) }}</div>
                      <div>
                        <div style="font-weight:500">{{ emp.full_name }}</div>
                        <div class="text-sm text-gray">{{ emp.email }}</div>
                      </div>
                    </div>
                  </td>
                  <td>{{ emp.department_name || '—' }}</td>
                  <td>{{ emp.position_title || '—' }}</td>
                  <td>{{ formatSalary(emp.salary) }}</td>
                  <td>{{ formatDate(emp.hire_date) }}</td>
                  <td>
                    <div style="display:flex;flex-direction:column;gap:4px;align-items:flex-start">
                      <span :class="statusBadge(emp.status)" class="badge">{{ statusLabel(emp.status) }}</span>
                      <span v-if="emp.current_leave" class="badge badge-blue" style="font-size:11px">
                        В отпуске по {{ fmtShort(emp.current_leave.end_date) }}
                      </span>
                      <span v-else-if="emp.upcoming_leave" class="badge badge-yellow" style="font-size:11px">
                        Отпуск с {{ fmtShort(emp.upcoming_leave.start_date) }}
                      </span>
                    </div>
                  </td>
                  <td>
                    <router-link :to="`/employees/${emp.id}`" class="btn btn-outline btn-sm">Открыть</router-link>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="empStore.total > 20" class="pagination">
            <button @click="changePage(empStore.page - 1)" :disabled="empStore.page <= 1">←</button>
            <span style="font-size:12px;color:#6b7280">{{ empStore.page }} / {{ Math.ceil(empStore.total/20) }}</span>
            <button @click="changePage(empStore.page + 1)" :disabled="empStore.page >= Math.ceil(empStore.total/20)">→</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Employee Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>Новый сотрудник</h3>
          <button class="btn btn-icon btn-outline" @click="showModal = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="grid-2">
            <div class="form-group">
              <label class="form-label">Фамилия *</label>
              <input v-model="form.last_name" class="form-control" required />
            </div>
            <div class="form-group">
              <label class="form-label">Имя *</label>
              <input v-model="form.first_name" class="form-control" required />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Email *</label>
            <input v-model="form.email" type="email" class="form-control" required />
          </div>
          <div class="grid-2">
            <div class="form-group">
              <label class="form-label">Отдел</label>
              <select v-model="form.department" class="form-control">
                <option value="">—</option>
                <option v-for="d in empStore.departments" :key="d.id" :value="d.id">{{ d.name }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Должность</label>
              <select v-model="form.position" class="form-control">
                <option value="">—</option>
                <option v-for="p in empStore.positions" :key="p.id" :value="p.id">{{ p.title }}</option>
              </select>
            </div>
          </div>
          <div class="grid-2">
            <div class="form-group">
              <label class="form-label">Оклад</label>
              <input v-model.number="form.salary" type="number" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Дата найма *</label>
              <input v-model="form.hire_date" type="date" class="form-control" required />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="showModal = false">Отмена</button>
          <button class="btn btn-primary" @click="saveEmployee" :disabled="saving">
            {{ saving ? 'Сохранение...' : 'Создать' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useEmployeesStore } from '@/stores/employees'

const empStore = useEmployeesStore()
const search = ref('')
const filterDept = ref('')
const filterStatus = ref('active')
const showModal = ref(false)
const saving = ref(false)
const form = ref({ last_name: '', first_name: '', email: '', department: '', position: '', salary: 0, hire_date: '' })

let searchTimer = null
function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    empStore.page = 1
    empStore.fetchList({ search: search.value, department: filterDept.value, status: filterStatus.value })
  }, 350)
}

function changePage(p) {
  empStore.page = p
  empStore.fetchList({ search: search.value, department: filterDept.value, status: filterStatus.value })
}

function initials(emp) {
  return ((emp.last_name?.[0] || '') + (emp.first_name?.[0] || '')).toUpperCase()
}
function formatSalary(v) { return v ? Number(v).toLocaleString('ru-RU') + ' ₽' : '—' }
function formatDate(d) { return d ? new Date(d).toLocaleDateString('ru-RU') : '—' }
function fmtShort(iso) {
  if (!iso) return ''
  const [, m, day] = iso.split('-')
  return `${day}.${m}`
}
function statusLabel(s) { return { active: 'Активен', inactive: 'Уволен', on_leave: 'Отпуск' }[s] || s }
function statusBadge(s) { return { active: 'badge-green', inactive: 'badge-red', on_leave: 'badge-yellow' }[s] || 'badge-gray' }

async function saveEmployee() {
  saving.value = true
  try {
    await empStore.create(form.value)
    showModal.value = false
    form.value = { last_name: '', first_name: '', email: '', department: '', position: '', salary: 0, hire_date: '' }
  } finally { saving.value = false }
}

onMounted(async () => {
  await Promise.all([
    empStore.fetchList({ status: filterStatus.value }),
    empStore.fetchDepartments(),
    empStore.fetchPositions(),
  ])
})
</script>

<style scoped>
.avatar-sm {
  width: 34px; height: 34px;
  background: var(--primary-light);
  color: var(--primary);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 12px; flex-shrink: 0;
}
</style>
