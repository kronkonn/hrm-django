<template>
  <div>
    <div class="topbar">
      <div class="topbar-title">Мой профиль</div>
    </div>
    <div class="page-container">
      <div v-if="loading" class="loading"><div class="spinner"></div> Загрузка...</div>

      <template v-else>
        <div class="grid-2">
          <!-- Карточка пользователя -->
          <div class="card">
            <div class="card-header">
              <span class="card-title">Личные данные</span>
              <span v-if="emp" :class="statusBadge(emp.status)" class="badge">{{ statusLabel(emp.status) }}</span>
              <span v-else class="badge badge-gray">{{ roleLabel }}</span>
            </div>
            <div class="card-body">
              <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px">
                <div class="big-avatar">{{ avatarLetters }}</div>
                <div>
                  <div style="font-size:20px;font-weight:700">{{ auth.fullName }}</div>
                  <div style="color:var(--gray-500);margin-top:2px">{{ emp ? emp.position_title : roleLabel }}</div>
                  <div v-if="emp" style="color:var(--gray-400);font-size:12px">{{ emp.department_name }}</div>
                </div>
              </div>

              <div class="info-row"><span>Логин</span><span>{{ auth.username }}</span></div>

              <template v-if="emp">
                <div class="info-row"><span>Email</span><span>{{ emp.email }}</span></div>
                <div class="info-row"><span>Телефон</span><span>{{ emp.phone || '—' }}</span></div>
                <div class="info-row"><span>Дата рождения</span><span>{{ formatDate(emp.birth_date) }}</span></div>
                <div class="info-row"><span>Дата найма</span><span>{{ formatDate(emp.hire_date) }}</span></div>
                <div class="info-row"><span>Руководитель</span><span>{{ emp.manager_name || '—' }}</span></div>
                <div class="info-row"><span>Лет в компании</span><span>{{ emp.years_at_company }}</span></div>
              </template>

              <div class="info-row"><span>Роль в системе</span><span>{{ roleLabel }}</span></div>
            </div>
          </div>

          <!-- Показатели (только если есть employee) -->
          <div v-if="emp" class="card">
            <div class="card-header"><span class="card-title">Мои показатели</span></div>
            <div class="card-body">
              <div class="metric-row">
                <span>Выполнение нормы часов</span>
                <div class="metric-bar-wrap">
                  <div class="metric-bar" :style="{width:Math.min(emp.hours_fulfillment ?? 0, 100)+'%',background:hfColor(emp.hours_fulfillment)}"></div>
                </div>
                <span class="metric-val">{{ emp.hours_fulfillment ?? '—' }}%</span>
              </div>

              <div style="margin-top:16px">
                <div class="info-row"><span>Сверхурочные часы</span><span>{{ emp.overtime_hours }} ч.</span></div>
                <div class="info-row"><span>Обучений в этом году</span><span>{{ emp.training_times_last_year }}</span></div>
              </div>
            </div>
          </div>

          <!-- Карточка смены пароля (когда нет employee, занимает вторую колонку) -->
          <div v-if="!emp" class="card">
            <div class="card-header"><span class="card-title">Безопасность</span></div>
            <div class="card-body">
              <p style="color:var(--gray-500);font-size:13px;margin-bottom:16px">
                Здесь вы можете изменить пароль от своей учётной записи.
              </p>
              <button class="btn btn-secondary" @click="showPasswordModal = true">Изменить пароль</button>
            </div>
          </div>
        </div>

        <!-- Быстрые действия -->
        <div class="card mt-4">
          <div class="card-body" style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
            <!-- EMPLOYEE: ссылка на отпуска -->
            <template v-if="auth.isEmployee">
              <router-link to="/my-leaves" class="btn btn-primary">Мои заявки на отпуск →</router-link>
            </template>

            <!-- ADMIN: ссылка на управление пользователями -->
            <template v-if="auth.isAdmin">
              <router-link to="/admin-panel" class="btn btn-primary">Управление пользователями →</router-link>
            </template>

            <!-- All: смена пароля (если есть employee — она не была выше) -->
            <button v-if="emp" class="btn btn-secondary" @click="showPasswordModal = true">Изменить пароль</button>
          </div>
        </div>
      </template>
    </div>

    <!-- Модальное окно смены пароля -->
    <div v-if="showPasswordModal" class="modal-overlay" @click.self="showPasswordModal = false">
      <div class="modal-box">
        <div class="modal-header">
          <span>Изменить пароль</span>
          <button class="modal-close" @click="showPasswordModal = false">✕</button>
        </div>
        <div class="modal-body">
          <label class="form-label">Новый пароль</label>
          <input v-model="newPassword" type="password" class="form-control" placeholder="Минимум 6 символов" />

          <label class="form-label" style="margin-top:12px">Подтверждение</label>
          <input v-model="confirmPassword" type="password" class="form-control" />

          <p v-if="pwError" style="color:#ef4444;font-size:12px;margin-top:8px">{{ pwError }}</p>
          <p v-if="pwSuccess" style="color:#10b981;font-size:12px;margin-top:8px">Пароль успешно изменён</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showPasswordModal = false">Отмена</button>
          <button class="btn btn-primary" :disabled="pwSaving" @click="changePassword">
            {{ pwSaving ? 'Сохраняем...' : 'Сохранить' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { getMyEmployee } from '@/api/employees'
import { updateMe } from '@/api/auth'

const auth = useAuthStore()
const emp = ref(null)
const loading = ref(false)

const showPasswordModal = ref(false)
const newPassword = ref('')
const confirmPassword = ref('')
const pwError = ref('')
const pwSuccess = ref(false)
const pwSaving = ref(false)

const avatarLetters = computed(() => {
  const name = auth.fullName || auth.username || ''
  const parts = name.trim().split(' ')
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return name.slice(0, 2).toUpperCase()
})

const roleLabel = computed(() => ({
  DIRECTOR: 'Директор',
  HR_MANAGER: 'HR-менеджер',
  EMPLOYEE: 'Сотрудник',
  ADMIN: 'Администратор',
}[auth.role] || auth.role))

function formatDate(d) { return d ? new Date(d).toLocaleDateString('ru-RU') : '—' }
function statusLabel(s) { return { active: 'Активен', inactive: 'Уволен', on_leave: 'В отпуске' }[s] || s }
function statusBadge(s) { return { active: 'badge-green', inactive: 'badge-red', on_leave: 'badge-yellow' }[s] || 'badge-gray' }
function hfColor(v) { return (v ?? 0) >= 90 && (v ?? 0) <= 115 ? '#10b981' : (v ?? 0) >= 70 ? '#f59e0b' : '#ef4444' }

async function changePassword() {
  pwError.value = ''
  pwSuccess.value = false
  if (newPassword.value.length < 6) { pwError.value = 'Пароль должен быть не короче 6 символов'; return }
  if (newPassword.value !== confirmPassword.value) { pwError.value = 'Пароли не совпадают'; return }
  pwSaving.value = true
  try {
    await updateMe({ password: newPassword.value })
    pwSuccess.value = true
    newPassword.value = ''
    confirmPassword.value = ''
    setTimeout(() => { showPasswordModal.value = false; pwSuccess.value = false }, 1500)
  } catch {
    pwError.value = 'Ошибка при смене пароля'
  } finally {
    pwSaving.value = false
  }
}

onMounted(async () => {
  if (!auth.employeeId) return
  loading.value = true
  try {
    const { data } = await getMyEmployee()
    emp.value = data
  } catch {
    emp.value = null
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.big-avatar {
  width: 64px; height: 64px;
  background: var(--primary-light);
  color: var(--primary);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 700; flex-shrink: 0;
}
.info-row { display:flex; justify-content:space-between; padding:7px 0; border-bottom:1px solid var(--gray-100); font-size:13px; }
.info-row span:first-child { color:var(--gray-500); }
.info-row span:last-child { font-weight:500; }
.metric-row { display:flex; align-items:center; gap:10px; margin-bottom:12px; font-size:13px; }
.metric-row > span:first-child { width:150px; flex-shrink:0; color:var(--gray-600); }
.metric-bar-wrap { flex:1; height:8px; background:var(--gray-200); border-radius:4px; overflow:hidden; }
.metric-bar { height:100%; border-radius:4px; transition:width .4s; }
.metric-val { font-weight:600; width:36px; text-align:right; flex-shrink:0; }
.mt-4 { margin-top: 16px; }
</style>
