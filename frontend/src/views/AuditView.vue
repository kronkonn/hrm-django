<template>
  <div>
    <div class="topbar">
      <div class="topbar-title">Журнал аудита</div>
      <span class="badge badge-gray">{{ total }} записей</span>
    </div>

    <div class="page-container">
      <!-- Filters -->
      <div class="card" style="margin-bottom:16px">
        <div class="card-body" style="padding:14px 20px">
          <div class="filters-row">
            <div class="filter-group">
              <label>Действие</label>
              <select v-model="filters.action" class="filter-select" @change="load(1)">
                <option value="">Все</option>
                <option v-for="a in ACTIONS" :key="a.value" :value="a.value">{{ a.label }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label>Пользователь</label>
              <select v-model="filters.user" class="filter-select" @change="load(1)">
                <option value="">Все</option>
                <option v-for="u in users" :key="u.id" :value="u.id">{{ u.username }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label>С даты</label>
              <input v-model="filters.date_from" type="date" class="filter-select" @change="load(1)" />
            </div>
            <div class="filter-group">
              <label>По дату</label>
              <input v-model="filters.date_to" type="date" class="filter-select" @change="load(1)" />
            </div>
            <div class="filter-group" style="flex:2">
              <label>Поиск</label>
              <input v-model="filters.search" type="text" placeholder="пользователь, объект, детали..."
                class="filter-select" @input="onSearchInput" />
            </div>
            <button class="btn btn-outline btn-sm" style="align-self:flex-end" @click="resetFilters">Сбросить</button>
          </div>
        </div>
      </div>

      <!-- Table -->
      <div class="card">
        <div v-if="loading" class="loading"><div class="spinner"></div></div>
        <div v-else-if="!logs.length" class="empty-state" style="padding:32px">
          <div class="empty-icon">📋</div>Записей не найдено
        </div>
        <div v-else style="overflow-x:auto">
          <table class="data-table audit-table">
            <thead>
              <tr>
                <th style="width:155px">Дата/время</th>
                <th style="width:120px">Пользователь</th>
                <th style="width:100px">Действие</th>
                <th>Объект</th>
                <th style="width:130px">IP-адрес</th>
                <th style="width:200px">Детали</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in logs" :key="log.id" class="audit-row" @click="openModal(log)">
                <td class="col-muted" style="white-space:nowrap">{{ formatTs(log.timestamp) }}</td>
                <td>
                  <span class="username-pill">{{ log.username || '—' }}</span>
                </td>
                <td>
                  <span class="badge" :class="actionBadge(log.action)">{{ actionLabel(log.action) }}</span>
                </td>
                <td>
                  <span v-if="log.model_name" style="font-weight:500">{{ log.model_name }}</span>
                  <span v-if="log.object_id" class="col-muted"> #{{ log.object_id }}</span>
                  <div v-if="log.object_repr" class="col-muted" style="font-size:11px">{{ log.object_repr }}</div>
                </td>
                <td class="col-muted" style="font-family:monospace;font-size:12px">{{ log.ip_address || '—' }}</td>
                <td class="col-muted" style="font-size:12px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
                    :title="log.details">{{ log.details }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="pagination-row">
          <button class="btn btn-outline btn-sm" :disabled="page === 1" @click="load(page - 1)">← Назад</button>
          <span class="page-info">{{ page }} / {{ totalPages }}</span>
          <button class="btn btn-outline btn-sm" :disabled="page === totalPages" @click="load(page + 1)">Вперёд →</button>
        </div>
      </div>
    </div>

    <!-- Detail Modal -->
    <div v-if="modal" class="modal-overlay" @click.self="modal = null">
      <div class="modal-box" style="max-width:600px">
        <div class="modal-header">
          <span class="modal-title">Запись аудита #{{ modal.id }}</span>
          <span class="badge" :class="actionBadge(modal.action)">{{ actionLabel(modal.action) }}</span>
          <button class="modal-close" @click="modal = null">✕</button>
        </div>
        <div class="modal-body">
          <div class="detail-grid">
            <div class="detail-row"><span>Время</span><span>{{ formatTs(modal.timestamp) }}</span></div>
            <div class="detail-row"><span>Пользователь</span><span>{{ modal.username || '—' }}</span></div>
            <div class="detail-row"><span>IP-адрес</span><span style="font-family:monospace">{{ modal.ip_address || '—' }}</span></div>
            <div class="detail-row"><span>Модель</span><span>{{ modal.model_name || '—' }}</span></div>
            <div class="detail-row"><span>ID объекта</span><span>{{ modal.object_id || '—' }}</span></div>
            <div v-if="modal.object_repr" class="detail-row">
              <span>Представление</span><span>{{ modal.object_repr }}</span>
            </div>
            <div v-if="modal.details" class="detail-row">
              <span>Детали</span><span>{{ modal.details }}</span>
            </div>
          </div>

          <div v-if="modal.changes" style="margin-top:16px">
            <div style="font-size:12px;font-weight:600;color:var(--gray-500);text-transform:uppercase;
                        letter-spacing:.5px;margin-bottom:8px">Изменения</div>
            <pre class="changes-pre">{{ JSON.stringify(modal.changes, null, 2) }}</pre>
          </div>
          <div v-else style="margin-top:12px;color:var(--gray-400);font-size:13px">Нет данных об изменениях</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/api/index'

const ACTIONS = [
  { value: 'CREATE', label: 'Создание' },
  { value: 'UPDATE', label: 'Изменение' },
  { value: 'DELETE', label: 'Удаление' },
  { value: 'LOGIN',  label: 'Вход' },
  { value: 'LOGOUT', label: 'Выход' },
  { value: 'VIEW',   label: 'Просмотр' },
]

const ACTION_BADGE = {
  CREATE: 'badge-green',
  UPDATE: 'badge-blue',
  DELETE: 'badge-red',
  LOGIN:  'badge-gray',
  LOGOUT: 'badge-gray',
  VIEW:   'badge-yellow',
}

const ACTION_LABEL = {
  CREATE: 'Создание',
  UPDATE: 'Изменение',
  DELETE: 'Удаление',
  LOGIN:  'Вход',
  LOGOUT: 'Выход',
  VIEW:   'Просмотр',
}

const logs      = ref([])
const users     = ref([])
const loading   = ref(false)
const total     = ref(0)
const page      = ref(1)
const pageSize  = 50
const totalPages = ref(1)
const modal     = ref(null)

const filters = reactive({ action: '', user: '', date_from: '', date_to: '', search: '' })

let searchTimer = null
function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => load(1), 400)
}

function actionBadge(a) { return ACTION_BADGE[a] || 'badge-gray' }
function actionLabel(a)  { return ACTION_LABEL[a] || a }

function formatTs(ts) {
  if (!ts) return '—'
  const d = new Date(ts)
  return d.toLocaleDateString('ru-RU') + ' ' + d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

async function load(p = 1) {
  loading.value = true
  page.value = p
  try {
    const params = { page: p, page_size: pageSize }
    if (filters.action)    params.action    = filters.action
    if (filters.user)      params.user      = filters.user
    if (filters.date_from) params.date_from = filters.date_from
    if (filters.date_to)   params.date_to   = filters.date_to
    if (filters.search)    params.search    = filters.search

    const { data } = await api.get('/audit/logs/', { params })
    logs.value  = data.results ?? data
    total.value = data.count ?? logs.value.length
    totalPages.value = Math.ceil(total.value / pageSize) || 1
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadUsers() {
  try {
    const { data } = await api.get('/auth/users/')
    users.value = data
  } catch {}
}

function resetFilters() {
  Object.assign(filters, { action: '', user: '', date_from: '', date_to: '', search: '' })
  load(1)
}

function openModal(log) { modal.value = log }

onMounted(() => { load(1); loadUsers() })
</script>

<style scoped>
.filters-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: flex-end;
}
.filter-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 120px;
}
.filter-group label {
  font-size: 11px;
  font-weight: 600;
  color: var(--gray-500);
  text-transform: uppercase;
  letter-spacing: .4px;
}
.filter-select {
  padding: 6px 10px;
  border: 1px solid var(--gray-200);
  border-radius: 6px;
  font-size: 13px;
  background: #fff;
  color: var(--gray-800);
  height: 34px;
}
.filter-select:focus { outline: none; border-color: var(--primary); }

.audit-table tbody tr { cursor: pointer; }
.audit-row:hover { background: var(--gray-50); }

.username-pill {
  display: inline-block;
  padding: 2px 8px;
  background: var(--gray-100);
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
}

.badge-blue { background: #dbeafe; color: #1d4ed8; }

.pagination-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  border-top: 1px solid var(--gray-100);
  justify-content: flex-end;
}
.page-info { font-size: 13px; color: var(--gray-500); }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.45);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.modal-box {
  background: #fff;
  border-radius: 12px;
  width: 100%;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0,0,0,.25);
}
.modal-header {
  display: flex; align-items: center; gap: 10px;
  padding: 18px 20px 14px;
  border-bottom: 1px solid var(--gray-100);
}
.modal-title { font-size: 16px; font-weight: 700; flex: 1; }
.modal-close {
  background: none; border: none; font-size: 18px;
  color: var(--gray-400); cursor: pointer; padding: 0 4px;
}
.modal-close:hover { color: var(--gray-700); }
.modal-body { padding: 16px 20px 20px; }

.detail-grid { display: flex; flex-direction: column; gap: 0; }
.detail-row {
  display: flex; justify-content: space-between; align-items: baseline;
  padding: 7px 0;
  border-bottom: 1px solid var(--gray-100);
  font-size: 13px;
}
.detail-row span:first-child { color: var(--gray-500); min-width: 120px; }
.detail-row span:last-child  { font-weight: 500; text-align: right; word-break: break-all; }

.changes-pre {
  background: var(--gray-50);
  border: 1px solid var(--gray-200);
  border-radius: 8px;
  padding: 12px;
  font-size: 12px;
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
  margin: 0;
}
</style>
