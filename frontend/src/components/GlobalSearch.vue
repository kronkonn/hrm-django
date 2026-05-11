<template>
  <div class="gs-wrap" ref="wrapRef">
    <!-- Input -->
    <div class="gs-input-row">
      <span class="gs-icon">
        <svg width="14" height="14" viewBox="0 0 20 20" fill="none">
          <circle cx="9" cy="9" r="6.5" stroke="currentColor" stroke-width="1.8"/>
          <path d="M14 14l3.5 3.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
        </svg>
      </span>
      <input
        ref="inputRef"
        v-model="query"
        class="gs-input"
        type="text"
        placeholder="Поиск по системе..."
        autocomplete="off"
        @input="onInput"
        @keydown.escape="close"
        @keydown.down.prevent="moveFocus(1)"
        @keydown.up.prevent="moveFocus(-1)"
        @keydown.enter.prevent="selectFocused"
        @focus="onFocus"
      />
      <button v-if="query" class="gs-clear" @mousedown.prevent @click="clearQuery">✕</button>
      <span v-if="loading" class="gs-spinner"></span>
    </div>

    <!-- Dropdown -->
    <div v-if="open" class="gs-dropdown">
      <!-- Empty / too short -->
      <div v-if="query.length < 2" class="gs-hint">Введите минимум 2 символа</div>

      <template v-else-if="!loading">
        <div v-if="isEmpty" class="gs-empty">Ничего не найдено по «{{ query }}»</div>

        <template v-else>
          <!-- Employees -->
          <div v-if="results.employees.length" class="gs-section">
            <div class="gs-section-title">Сотрудники</div>
            <div
              v-for="(item, i) in results.employees"
              :key="'e' + item.id"
              class="gs-item"
              :class="{ focused: focusedIdx === globalIdx('employees', i) }"
              @mousedown.prevent
              @click="navigate('employee', item)"
            >
              <span class="gs-item-icon gs-icon-emp">👤</span>
              <div class="gs-item-body">
                <div class="gs-item-main">{{ item.full_name }}</div>
                <div class="gs-item-sub">{{ item.position }}<span v-if="item.position && item.department"> · </span>{{ item.department }}</div>
              </div>
              <span class="gs-item-arrow">→</span>
            </div>
          </div>

          <!-- Vacancies -->
          <div v-if="results.vacancies.length" class="gs-section">
            <div class="gs-section-title">Вакансии</div>
            <div
              v-for="(item, i) in results.vacancies"
              :key="'v' + item.id"
              class="gs-item"
              :class="{ focused: focusedIdx === globalIdx('vacancies', i) }"
              @mousedown.prevent
              @click="navigate('vacancy', item)"
            >
              <span class="gs-item-icon gs-icon-vac">🎯</span>
              <div class="gs-item-body">
                <div class="gs-item-main">{{ item.title }}</div>
                <div class="gs-item-sub">{{ item.department }} · <span :class="vacStatusClass(item.status)">{{ item.status_display }}</span></div>
              </div>
              <span class="gs-item-arrow">→</span>
            </div>
          </div>

          <!-- Candidates -->
          <div v-if="results.candidates.length" class="gs-section">
            <div class="gs-section-title">Кандидаты</div>
            <div
              v-for="(item, i) in results.candidates"
              :key="'c' + item.id"
              class="gs-item"
              :class="{ focused: focusedIdx === globalIdx('candidates', i) }"
              @mousedown.prevent
              @click="navigate('candidate', item)"
            >
              <span class="gs-item-icon gs-icon-cand">📋</span>
              <div class="gs-item-body">
                <div class="gs-item-main">{{ item.full_name }}</div>
                <div class="gs-item-sub">{{ item.vacancy_title }} · {{ item.stage_display }}</div>
              </div>
              <span class="gs-item-arrow">→</span>
            </div>
          </div>
        </template>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { globalSearch } from '@/api/search'

const router  = useRouter()
const wrapRef = ref(null)
const inputRef = ref(null)

const query    = ref('')
const open     = ref(false)
const loading  = ref(false)
const results  = ref({ employees: [], vacancies: [], candidates: [] })
const focusedIdx = ref(-1)

let debounceTimer = null

// ── Helpers ────────────────────────────────────────────────────────────────

const isEmpty = computed(() =>
  !results.value.employees.length &&
  !results.value.vacancies.length &&
  !results.value.candidates.length
)

const flatItems = computed(() => [
  ...results.value.employees.map(e => ({ type: 'employee', item: e })),
  ...results.value.vacancies.map(v => ({ type: 'vacancy',  item: v })),
  ...results.value.candidates.map(c => ({ type: 'candidate', item: c })),
])

function globalIdx(section, localIdx) {
  const offsets = {
    employees: 0,
    vacancies:  results.value.employees.length,
    candidates: results.value.employees.length + results.value.vacancies.length,
  }
  return offsets[section] + localIdx
}

function vacStatusClass(status) {
  return { open: 'vac-open', closed: 'vac-closed', on_hold: 'vac-hold' }[status] || ''
}

// ── Events ──────────────────────────────────────────────────────────────────

function onInput() {
  focusedIdx.value = -1
  clearTimeout(debounceTimer)
  if (query.value.length < 2) {
    results.value = { employees: [], vacancies: [], candidates: [] }
    open.value = query.value.length > 0
    return
  }
  open.value = true
  loading.value = true
  debounceTimer = setTimeout(fetchResults, 280)
}

function onFocus() {
  if (query.value.length >= 1) open.value = true
}

async function fetchResults() {
  try {
    const { data } = await globalSearch(query.value)
    results.value = data
  } catch {
    results.value = { employees: [], vacancies: [], candidates: [] }
  } finally {
    loading.value = false
  }
}

function close() {
  open.value = false
  focusedIdx.value = -1
}

function clearQuery() {
  query.value = ''
  results.value = { employees: [], vacancies: [], candidates: [] }
  open.value = false
  inputRef.value?.focus()
}

function moveFocus(dir) {
  if (!open.value || !flatItems.value.length) return
  const max = flatItems.value.length - 1
  focusedIdx.value = Math.max(0, Math.min(max, focusedIdx.value + dir))
}

function selectFocused() {
  if (focusedIdx.value < 0 || focusedIdx.value >= flatItems.value.length) return
  const { type, item } = flatItems.value[focusedIdx.value]
  navigate(type, item)
}

function navigate(type, item) {
  close()
  query.value = ''
  if (type === 'employee') {
    router.push(`/employees/${item.id}`)
  } else {
    // vacancies and candidates both live in /recruiting
    router.push('/recruiting')
  }
}

// ── Click outside ────────────────────────────────────────────────────────

function onDocClick(e) {
  if (wrapRef.value && !wrapRef.value.contains(e.target)) close()
}
onMounted(() => document.addEventListener('mousedown', onDocClick))
onUnmounted(() => {
  document.removeEventListener('mousedown', onDocClick)
  clearTimeout(debounceTimer)
})
</script>

<style scoped>
.gs-wrap {
  position: relative;
  flex: 1;
  max-width: 480px;
}

/* ── Input row ─────────────────────────────────────────────────────── */
.gs-input-row {
  display: flex;
  align-items: center;
  background: var(--gray-100, #f3f4f6);
  border: 1.5px solid transparent;
  border-radius: 8px;
  padding: 0 10px;
  gap: 6px;
  transition: border-color .15s, background .15s;
}
.gs-input-row:focus-within {
  background: #fff;
  border-color: var(--primary, #4f46e5);
  box-shadow: 0 0 0 3px rgba(79,70,229,.1);
}

.gs-icon { color: var(--gray-400, #9ca3af); display: flex; align-items: center; flex-shrink: 0; }

.gs-input {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-size: 13px;
  color: var(--gray-800, #1f2937);
  padding: 8px 0;
  min-width: 0;
}
.gs-input::placeholder { color: var(--gray-400, #9ca3af); }

.gs-clear {
  background: none;
  border: none;
  color: var(--gray-400);
  cursor: pointer;
  font-size: 11px;
  padding: 2px 4px;
  border-radius: 4px;
  flex-shrink: 0;
  line-height: 1;
}
.gs-clear:hover { background: var(--gray-200); color: var(--gray-600); }

.gs-spinner {
  width: 14px; height: 14px;
  border: 2px solid var(--gray-200);
  border-top-color: var(--primary, #4f46e5);
  border-radius: 50%;
  animation: gs-spin .6s linear infinite;
  flex-shrink: 0;
}
@keyframes gs-spin { to { transform: rotate(360deg); } }

/* ── Dropdown ──────────────────────────────────────────────────────── */
.gs-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid var(--gray-200, #e5e7eb);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,.12), 0 2px 8px rgba(0,0,0,.06);
  z-index: 200;
  max-height: 420px;
  overflow-y: auto;
}

.gs-hint, .gs-empty {
  padding: 14px 16px;
  font-size: 13px;
  color: var(--gray-400, #9ca3af);
  text-align: center;
}

/* ── Sections ──────────────────────────────────────────────────────── */
.gs-section { padding: 6px 0; }
.gs-section + .gs-section { border-top: 1px solid var(--gray-100, #f3f4f6); }

.gs-section-title {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .6px;
  color: var(--gray-400, #9ca3af);
  padding: 6px 14px 4px;
}

/* ── Items ─────────────────────────────────────────────────────────── */
.gs-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  cursor: pointer;
  transition: background .1s;
}
.gs-item:hover, .gs-item.focused {
  background: var(--gray-50, #f9fafb);
}

.gs-item-icon {
  font-size: 14px;
  width: 26px; height: 26px;
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.gs-icon-emp  { background: #eff6ff; }
.gs-icon-vac  { background: #fef3c7; }
.gs-icon-cand { background: #f0fdf4; }

.gs-item-body { flex: 1; min-width: 0; }
.gs-item-main {
  font-size: 13px;
  font-weight: 500;
  color: var(--gray-800, #1f2937);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.gs-item-sub {
  font-size: 11px;
  color: var(--gray-400, #9ca3af);
  margin-top: 1px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gs-item-arrow {
  font-size: 12px;
  color: var(--gray-300);
  flex-shrink: 0;
  opacity: 0;
  transition: opacity .1s;
}
.gs-item:hover .gs-item-arrow, .gs-item.focused .gs-item-arrow { opacity: 1; }

/* vacancy status inline */
.vac-open   { color: #059669; }
.vac-hold   { color: #d97706; }
.vac-closed { color: #6b7280; }
</style>
