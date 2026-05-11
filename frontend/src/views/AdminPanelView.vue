<template>
  <div>
    <div class="topbar">
      <div class="topbar-title">Управление пользователями</div>
    </div>

    <div class="page-container">
      <div v-if="loading" class="loading"><div class="spinner"></div> Загрузка...</div>

      <div v-else-if="loadError" class="empty-state">
        <div class="empty-icon">⚠</div>
        <div>{{ loadError }}</div>
        <button class="btn btn-secondary" style="margin-top:12px" @click="loadUsers">Повторить</button>
      </div>

      <div v-else class="card">
        <div class="card-header">
          <span class="card-title">Все пользователи</span>
          <span class="badge badge-gray">{{ users.length }}</span>
        </div>

        <div style="overflow-x:auto">
          <table class="data-table">
            <thead>
              <tr>
                <th style="width:48px">ID</th>
                <th>Логин</th>
                <th>ФИО</th>
                <th>Email</th>
                <th style="width:180px">Роль</th>
                <th style="width:130px">Регистрация</th>
                <th style="width:150px">Действия</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in users" :key="u.id">
                <td class="col-id">#{{ u.id }}</td>
                <td><strong>{{ u.username }}</strong></td>
                <td>{{ u.full_name }}</td>
                <td class="col-muted">{{ u.email || '—' }}</td>
                <td>
                  <div class="role-cell">
                    <select
                      :value="u.role"
                      class="role-select"
                      :class="roleClass(u.role)"
                      :disabled="!!saving[u.id]"
                      @change="onRoleChange(u, $event.target.value)"
                    >
                      <option v-for="opt in roleOptions" :key="opt.value" :value="opt.value">
                        {{ opt.label }}
                      </option>
                    </select>
                    <span v-if="roleSaved[u.id]" class="inline-ok">✓</span>
                    <span v-else-if="roleError[u.id]" class="inline-err">!</span>
                  </div>
                </td>
                <td class="col-muted">{{ formatDate(u.date_joined) }}</td>
                <td>
                  <button class="btn-pw" @click="openPwModal(u)">Сменить пароль</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Password modal -->
    <Teleport to="body">
      <div v-if="pwModal.open" class="modal-backdrop" @click.self="closePwModal">
        <div class="modal-box">
          <div class="modal-header">
            <span>Смена пароля для <strong>{{ pwModal.username }}</strong></span>
            <button class="modal-close-btn" @click="closePwModal">✕</button>
          </div>

          <div class="modal-body">
            <div class="field">
              <label class="field-label">Новый пароль</label>
              <input
                v-model="pwModal.password"
                type="password"
                class="field-input"
                placeholder="Минимум 6 символов"
                autocomplete="new-password"
                @keydown.enter="submitPassword"
              />
            </div>
            <div class="field">
              <label class="field-label">Подтверждение пароля</label>
              <input
                v-model="pwModal.confirm"
                type="password"
                class="field-input"
                placeholder="Повторите пароль"
                autocomplete="new-password"
                @keydown.enter="submitPassword"
              />
            </div>
            <p v-if="pwModal.error" class="field-error">{{ pwModal.error }}</p>
            <p v-if="pwModal.success" class="field-success">Пароль успешно изменён</p>
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" @click="closePwModal">Отмена</button>
            <button class="btn btn-primary" :disabled="pwModal.saving" @click="submitPassword">
              {{ pwModal.saving ? 'Сохраняем...' : 'Сохранить' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getUsers, updateUserRole, changeUserPassword } from '@/api/auth'

const users = ref([])
const loading = ref(false)
const loadError = ref('')

const saving   = reactive({})
const roleSaved = reactive({})
const roleError = reactive({})

const roleOptions = [
  { value: 'DIRECTOR',   label: 'Директор' },
  { value: 'HR_MANAGER', label: 'HR-менеджер' },
  { value: 'EMPLOYEE',   label: 'Сотрудник' },
  { value: 'ADMIN',      label: 'Администратор' },
]

const pwModal = reactive({
  open: false,
  userId: null,
  username: '',
  password: '',
  confirm: '',
  error: '',
  success: false,
  saving: false,
})

function roleClass(role) {
  return { DIRECTOR: 'r-dir', HR_MANAGER: 'r-hr', EMPLOYEE: 'r-emp', ADMIN: 'r-adm' }[role] || ''
}

function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('ru-RU') : '—'
}

async function onRoleChange(user, newRole) {
  if (newRole === user.role) return
  saving[user.id] = true
  roleSaved[user.id] = false
  roleError[user.id] = false
  try {
    await updateUserRole(user.id, newRole)
    user.role = newRole
    roleSaved[user.id] = true
    setTimeout(() => { roleSaved[user.id] = false }, 2000)
  } catch {
    roleError[user.id] = true
    setTimeout(() => { roleError[user.id] = false }, 3000)
  } finally {
    saving[user.id] = false
  }
}

function openPwModal(user) {
  pwModal.open = true
  pwModal.userId = user.id
  pwModal.username = user.username
  pwModal.password = ''
  pwModal.confirm = ''
  pwModal.error = ''
  pwModal.success = false
  pwModal.saving = false
}

function closePwModal() {
  pwModal.open = false
}

async function submitPassword() {
  pwModal.error = ''
  pwModal.success = false
  if (pwModal.password.length < 6) {
    pwModal.error = 'Пароль должен быть не короче 6 символов'
    return
  }
  if (pwModal.password !== pwModal.confirm) {
    pwModal.error = 'Пароли не совпадают'
    return
  }
  pwModal.saving = true
  try {
    await changeUserPassword(pwModal.userId, pwModal.password)
    pwModal.success = true
    setTimeout(closePwModal, 1200)
  } catch (e) {
    pwModal.error = e.response?.data?.detail || 'Ошибка при смене пароля'
  } finally {
    pwModal.saving = false
  }
}

async function loadUsers() {
  loading.value = true
  loadError.value = ''
  try {
    const { data } = await getUsers()
    users.value = data
  } catch (e) {
    loadError.value = e.response?.data?.detail || 'Не удалось загрузить список пользователей'
  } finally {
    loading.value = false
  }
}

onMounted(loadUsers)
</script>

<style scoped>
/* ── Table ─────────────────────────────────────────── */
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.data-table th {
  text-align: left;
  padding: 10px 14px;
  border-bottom: 2px solid var(--gray-200);
  color: var(--gray-500);
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .5px;
  white-space: nowrap;
}
.data-table td {
  padding: 11px 14px;
  border-bottom: 1px solid var(--gray-100);
  vertical-align: middle;
}
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: var(--gray-50); }
.col-id   { color: var(--gray-400); font-size: 12px; }
.col-muted { color: var(--gray-500); }

/* ── Role select ────────────────────────────────────── */
.role-cell { display: flex; align-items: center; gap: 6px; }

.role-select {
  border: none;
  border-radius: 12px;
  padding: 4px 12px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: .4px;
  outline: none;
  appearance: none;
  -webkit-appearance: none;
  transition: opacity .15s;
}
.role-select:disabled { opacity: .55; cursor: default; }

.r-dir { background: rgba(99,102,241,.15); color: #4f46e5; }
.r-hr  { background: rgba(16,185,129,.15); color: #059669; }
.r-emp { background: rgba(245,158,11,.15); color: #b45309; }
.r-adm { background: rgba(239,68,68,.15);  color: #b91c1c; }

.inline-ok  { color: #10b981; font-size: 13px; font-weight: 700; }
.inline-err { color: #ef4444; font-size: 13px; font-weight: 700; }

/* ── Password button ────────────────────────────────── */
.btn-pw {
  background: none;
  border: 1px solid var(--gray-300);
  border-radius: 6px;
  padding: 5px 12px;
  font-size: 12px;
  color: var(--gray-600);
  cursor: pointer;
  white-space: nowrap;
  transition: background .15s, color .15s;
}
.btn-pw:hover {
  background: var(--primary-light);
  color: var(--primary);
  border-color: var(--primary);
}

/* ── Modal backdrop ─────────────────────────────────── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, .45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-box {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, .25);
  width: 420px;
  max-width: calc(100vw - 32px);
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 24px 16px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 15px;
  color: #111;
}

.modal-close-btn {
  background: none;
  border: none;
  font-size: 16px;
  color: #999;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  line-height: 1;
}
.modal-close-btn:hover { background: #f5f5f5; color: #333; }

.modal-body {
  padding: 20px 24px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 24px 20px;
  border-top: 1px solid #f0f0f0;
}

/* ── Form fields inside modal ───────────────────────── */
.field { margin-bottom: 16px; }
.field:last-of-type { margin-bottom: 0; }

.field-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #555;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: .4px;
}

.field-input {
  width: 100%;
  box-sizing: border-box;
  padding: 9px 12px;
  border: 1.5px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  color: #111;
  background: #fafafa;
  outline: none;
  transition: border-color .15s, box-shadow .15s;
}
.field-input:focus {
  border-color: var(--primary, #6366f1);
  box-shadow: 0 0 0 3px rgba(99,102,241,.12);
  background: #fff;
}

.field-error   { color: #dc2626; font-size: 12px; margin-top: 10px; }
.field-success { color: #059669; font-size: 12px; margin-top: 10px; font-weight: 600; }
</style>
