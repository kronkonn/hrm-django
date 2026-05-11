<template>
  <div>
    <div class="topbar">
      <div class="topbar-title">Обучение персонала</div>
      <button v-if="auth.canAccessHR" class="btn btn-primary btn-sm" @click="openNewCourseModal">
        + Новый курс
      </button>
    </div>

    <div class="page-container">
      <div v-if="store.loading" class="loading"><div class="spinner"></div></div>

      <template v-else>

        <!-- ═══ HR / DIRECTOR / ADMIN ═══ -->
        <template v-if="auth.canAccessHR">
          <div class="tabs" style="margin-bottom:20px">
            <button class="tab-btn" :class="{active: tab==='courses'}"     @click="tab='courses'">Курсы</button>
            <button class="tab-btn" :class="{active: tab==='assignments'}" @click="tab='assignments'">Назначения</button>
            <button class="tab-btn" :class="{active: tab==='certificates'}" @click="tab='certificates'">Сертификаты</button>
          </div>

          <!-- ── Courses ── -->
          <div v-show="tab==='courses'">
            <div class="card">
              <div v-if="!store.courses.length" class="empty-state" style="padding:40px">
                <div class="empty-icon">📚</div>
                <div>Курсов пока нет</div>
              </div>
              <div v-else class="table-wrap">
                <table class="train-table">
                  <thead>
                    <tr>
                      <th>Название</th>
                      <th>Категория</th>
                      <th>Длительность</th>
                      <th>Дедлайн</th>
                      <th>Назначений</th>
                      <th>Завершили</th>
                      <th>Статус</th>
                      <th>Действия</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="c in store.courses" :key="c.id">
                      <td>
                        <div style="font-weight:500">{{ c.title }}</div>
                        <div class="text-sm text-gray">{{ c.description?.slice(0, 60) }}{{ c.description?.length > 60 ? '…' : '' }}</div>
                      </td>
                      <td><span :class="categoryBadge(c.category)" class="badge">{{ c.category_display }}</span></td>
                      <td>{{ c.duration_hours }} ч.</td>
                      <td>{{ c.deadline ? fmtDate(c.deadline) : '—' }}</td>
                      <td style="text-align:center">{{ c.assignments_count }}</td>
                      <td style="text-align:center">{{ c.completed_count }}</td>
                      <td><span :class="c.status==='active'?'badge-green':'badge-gray'" class="badge">{{ c.status_display }}</span></td>
                      <td style="white-space:nowrap">
                        <button class="btn btn-outline btn-sm" @click="openAssignModal(c)">Назначить</button>
                        <button class="btn btn-outline btn-sm" style="margin-left:4px" @click="openEditModal(c)">Изменить</button>
                        <button v-if="c.status==='active'" class="btn btn-outline btn-sm" style="margin-left:4px" @click="archiveCourse(c)">Архив</button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- ── Assignments ── -->
          <div v-show="tab==='assignments'">
            <div class="card">
              <div class="card-header">
                <span class="card-title">Все назначения</span>
                <div style="display:flex;gap:8px">
                  <select v-model="statusFilter" class="form-control" style="width:140px">
                    <option value="">Все статусы</option>
                    <option value="assigned">Назначен</option>
                    <option value="in_progress">В процессе</option>
                    <option value="completed">Завершён</option>
                    <option value="overdue">Просрочен</option>
                  </select>
                  <select v-model="deptFilter" class="form-control" style="width:160px">
                    <option value="">Все отделы</option>
                    <option v-for="d in uniqueDepts" :key="d" :value="d">{{ d }}</option>
                  </select>
                </div>
              </div>
              <div class="table-wrap">
                <table class="train-table">
                  <thead>
                    <tr>
                      <th>Сотрудник</th>
                      <th>Курс</th>
                      <th style="min-width:160px">Прогресс</th>
                      <th>Статус</th>
                      <th>Дедлайн</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="a in filteredAssignments" :key="a.id">
                      <td>
                        <div style="font-weight:500">{{ a.employee_name }}</div>
                        <div class="text-sm text-gray">{{ a.department_name }}</div>
                      </td>
                      <td>{{ a.course_title }}</td>
                      <td>
                        <div style="display:flex;align-items:center;gap:8px">
                          <div class="prog-bar"><div class="prog-fill" :style="{width:a.progress+'%'}"></div></div>
                          <span style="font-size:12px;font-weight:600;width:30px">{{ a.progress }}%</span>
                        </div>
                      </td>
                      <td><span :class="statusBadge(a.status)" class="badge">{{ a.status_display }}</span></td>
                      <td>{{ a.course_deadline ? fmtDate(a.course_deadline) : '—' }}</td>
                    </tr>
                    <tr v-if="!filteredAssignments.length">
                      <td colspan="5" style="text-align:center;color:var(--gray-400);padding:24px">Нет назначений</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- ── Certificates ── -->
          <div v-show="tab==='certificates'">
            <div class="card">
              <div v-if="!store.certificates.length" class="empty-state" style="padding:40px">
                <div class="empty-icon">🏆</div>
                <div>Сертификатов пока нет</div>
              </div>
              <div v-else class="table-wrap">
                <table class="train-table">
                  <thead>
                    <tr>
                      <th>Сотрудник</th>
                      <th>Отдел</th>
                      <th>Курс</th>
                      <th>Номер сертификата</th>
                      <th>Дата выдачи</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="c in store.certificates" :key="c.id">
                      <td style="font-weight:500">{{ c.employee_name }}</td>
                      <td class="text-gray text-sm">{{ c.department_name }}</td>
                      <td>{{ c.course_title }}</td>
                      <td><code style="font-size:12px;background:var(--gray-100);padding:2px 6px;border-radius:4px">{{ c.certificate_number }}</code></td>
                      <td>{{ fmtDate(c.issued_at) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </template>

        <!-- ═══ EMPLOYEE ═══ -->
        <template v-else-if="auth.isEmployee">
          <div class="tabs" style="margin-bottom:20px">
            <button class="tab-btn" :class="{active: tab==='my-courses'}"  @click="tab='my-courses'">Мои курсы</button>
            <button class="tab-btn" :class="{active: tab==='my-certs'}"    @click="tab='my-certs'">Мои сертификаты</button>
          </div>

          <!-- ── My Courses ── -->
          <div v-show="tab==='my-courses'">
            <div v-if="!store.assignments.length" class="empty-state" style="padding:48px">
              <div class="empty-icon">📚</div>
              <div>Вам пока не назначено курсов</div>
            </div>
            <div v-else class="grid-3">
              <div v-for="a in store.assignments" :key="a.id" class="card">
                <div class="card-header" style="padding-bottom:8px">
                  <span class="card-title" style="font-size:13px;line-height:1.4">{{ a.course_title }}</span>
                  <span :class="statusBadge(a.status)" class="badge" style="flex-shrink:0">{{ a.status_display }}</span>
                </div>
                <div class="card-body" style="padding-top:8px">
                  <div class="text-sm text-gray" style="margin-bottom:10px">
                    <span :class="categoryBadge(a.course_category)" class="badge" style="margin-right:6px">{{ categoryLabel(a.course_category) }}</span>
                    {{ a.course_duration }} ч.
                  </div>
                  <div style="margin-bottom:10px">
                    <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px">
                      <span style="color:var(--gray-500)">Прогресс</span>
                      <span style="font-weight:700">{{ a.progress }}%</span>
                    </div>
                    <div class="prog-bar"><div class="prog-fill" :style="{width:a.progress+'%'}"></div></div>
                  </div>
                  <div v-if="a.course_deadline" class="text-sm text-gray" style="margin-bottom:12px">
                    Дедлайн: {{ fmtDate(a.course_deadline) }}
                  </div>
                  <router-link
                    v-if="a.status !== 'completed'"
                    :to="`/training/course/${a.id}`"
                    class="btn btn-primary btn-sm"
                    style="width:100%;text-align:center;display:block"
                  >{{ a.progress === 0 ? '▶ Начать курс' : '▶ Продолжить курс' }}</router-link>
                  <router-link
                    v-else
                    :to="`/training/course/${a.id}`"
                    class="btn btn-outline btn-sm"
                    style="width:100%;text-align:center;display:block;color:#10b981;border-color:#10b981"
                  >✓ Завершён — просмотр</router-link>
                </div>
              </div>
            </div>
          </div>

          <!-- ── My Certificates ── -->
          <div v-show="tab==='my-certs'">
            <div v-if="!store.certificates.length" class="empty-state" style="padding:48px">
              <div class="empty-icon">🏆</div>
              <div>Сертификатов пока нет — завершите курс на 100%</div>
            </div>
            <div v-else class="grid-3">
              <div v-for="c in store.certificates" :key="c.id" class="card cert-card">
                <div class="cert-icon">🏆</div>
                <div style="font-weight:700;font-size:14px;margin-bottom:4px">{{ c.course_title }}</div>
                <code class="cert-num">{{ c.certificate_number }}</code>
                <div class="text-sm text-gray" style="margin-top:6px">Выдан: {{ fmtDate(c.issued_at) }}</div>
              </div>
            </div>
          </div>
        </template>

      </template>
    </div>

    <!-- ═══ New / Edit Course Modal ═══ -->
    <div v-if="showCourseModal" class="modal-overlay" @click.self="showCourseModal=false">
      <div class="modal-box" style="width:500px">
        <div class="modal-header">
          <span>{{ editingCourse ? 'Редактировать курс' : 'Новый курс' }}</span>
          <button class="modal-close" @click="showCourseModal=false">✕</button>
        </div>
        <div class="modal-body">
          <label class="form-label">Название *</label>
          <input v-model="courseForm.title" class="form-control" placeholder="Название курса" />

          <label class="form-label" style="margin-top:12px">Описание</label>
          <textarea v-model="courseForm.description" class="form-control" rows="3" placeholder="Краткое описание курса..."></textarea>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px">
            <div>
              <label class="form-label">Категория</label>
              <select v-model="courseForm.category" class="form-control">
                <option value="mandatory">Обязательный</option>
                <option value="development">Развивающий</option>
                <option value="technical">Технический</option>
              </select>
            </div>
            <div>
              <label class="form-label">Длительность (часов)</label>
              <input v-model.number="courseForm.duration_hours" type="number" min="1" class="form-control" />
            </div>
          </div>

          <label class="form-label" style="margin-top:12px">Дедлайн</label>
          <input v-model="courseForm.deadline" type="date" class="form-control" />
          <p v-if="formError" style="color:#ef4444;font-size:12px;margin-top:8px">{{ formError }}</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showCourseModal=false">Отмена</button>
          <button class="btn btn-primary" :disabled="store.saving" @click="saveCourse">
            {{ store.saving ? 'Сохранение...' : 'Сохранить' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ═══ Assign Modal ═══ -->
    <div v-if="showAssignModal" class="modal-overlay" @click.self="showAssignModal=false">
      <div class="modal-box" style="width:460px">
        <div class="modal-header">
          <span>Назначить: {{ assigningCourse?.title }}</span>
          <button class="modal-close" @click="showAssignModal=false">✕</button>
        </div>
        <div class="modal-body">
          <div v-if="loadingEmps" style="text-align:center;padding:16px"><div class="spinner"></div></div>
          <div v-else style="max-height:340px;overflow-y:auto">
            <label
              v-for="emp in allEmployees" :key="emp.id"
              class="emp-row"
              style="display:flex;align-items:center;gap:10px;padding:8px 4px;cursor:pointer;border-radius:6px"
            >
              <input type="checkbox" :value="emp.id" v-model="selectedEmpIds" style="width:16px;height:16px;cursor:pointer" />
              <div>
                <div style="font-weight:500;font-size:13px">{{ emp.full_name }}</div>
                <div class="text-sm text-gray">{{ emp.department_name }}</div>
              </div>
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <span class="text-sm text-gray">Выбрано: {{ selectedEmpIds.length }}</span>
          <button class="btn btn-secondary" @click="showAssignModal=false">Отмена</button>
          <button class="btn btn-primary" :disabled="!selectedEmpIds.length || store.saving" @click="doAssign">
            {{ store.saving ? 'Назначение...' : `Назначить (${selectedEmpIds.length})` }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore }     from '@/stores/auth'
import { useTrainingStore } from '@/stores/training'
import api from '@/api/index'

const auth  = useAuthStore()
const store = useTrainingStore()

const tab          = ref(auth.canAccessHR ? 'courses' : 'my-courses')
const statusFilter = ref('')
const deptFilter   = ref('')

// Modals state
const showCourseModal = ref(false)
const showAssignModal = ref(false)

const editingCourse  = ref(null)
const courseForm     = ref({ title: '', description: '', category: 'mandatory', duration_hours: 8, deadline: '' })
const formError      = ref('')

const assigningCourse = ref(null)
const allEmployees    = ref([])
const selectedEmpIds  = ref([])
const loadingEmps     = ref(false)

// ── Computed ──────────────────────────────────────────────────────────────
const uniqueDepts = computed(() => {
  const names = [...new Set(store.assignments.map(a => a.department_name).filter(Boolean))]
  return names.sort()
})

const filteredAssignments = computed(() => {
  let list = store.assignments
  if (statusFilter.value) list = list.filter(a => a.status === statusFilter.value)
  if (deptFilter.value)   list = list.filter(a => a.department_name === deptFilter.value)
  return list
})

// ── Helpers ───────────────────────────────────────────────────────────────
function fmtDate(d) { return d ? new Date(d).toLocaleDateString('ru-RU') : '—' }

function categoryBadge(c) {
  return { mandatory: 'badge-red', development: 'badge-green', technical: 'badge-yellow' }[c] || 'badge-gray'
}
function categoryLabel(c) {
  return { mandatory: 'Обязательный', development: 'Развивающий', technical: 'Технический' }[c] || c
}
function statusBadge(s) {
  return { assigned: 'badge-gray', in_progress: 'badge-yellow', completed: 'badge-green', overdue: 'badge-red' }[s] || 'badge-gray'
}

// ── Course CRUD ───────────────────────────────────────────────────────────
function openNewCourseModal() {
  editingCourse.value = null
  formError.value     = ''
  courseForm.value    = { title: '', description: '', category: 'mandatory', duration_hours: 8, deadline: '' }
  showCourseModal.value = true
}

function openEditModal(course) {
  editingCourse.value = course
  formError.value     = ''
  courseForm.value    = {
    title:          course.title,
    description:    course.description || '',
    category:       course.category,
    duration_hours: course.duration_hours,
    deadline:       course.deadline || '',
  }
  showCourseModal.value = true
}

async function saveCourse() {
  formError.value = ''
  if (!courseForm.value.title.trim()) {
    formError.value = 'Укажите название курса'
    return
  }
  const payload = { ...courseForm.value }
  if (!payload.deadline) delete payload.deadline
  if (editingCourse.value) {
    await store.updateCourse(editingCourse.value.id, payload)
  } else {
    await store.createCourse(payload)
  }
  showCourseModal.value = false
}

async function archiveCourse(course) {
  await store.updateCourse(course.id, { status: 'archived' })
}

// ── Assign ────────────────────────────────────────────────────────────────
async function openAssignModal(course) {
  assigningCourse.value = course
  selectedEmpIds.value  = []
  showAssignModal.value = true
  if (!allEmployees.value.length) {
    loadingEmps.value = true
    try {
      const { data } = await api.get('/employees/list/', { params: { page_size: 500 } })
      allEmployees.value = (data.results ?? data).filter(e => e.status === 'active')
    } finally {
      loadingEmps.value = false
    }
  }
}

async function doAssign() {
  await store.assignCourse(assigningCourse.value.id, selectedEmpIds.value)
  showAssignModal.value = false
  await store.fetchCourses()
}

// ── Mount ─────────────────────────────────────────────────────────────────
onMounted(async () => {
  if (auth.canAccessHR) {
    await Promise.all([
      store.fetchCourses(),
      store.fetchAssignments(),
      store.fetchCertificates(),
    ])
  } else {
    await Promise.all([
      store.fetchAssignments(),
      store.fetchCertificates(),
    ])
  }
})
</script>

<style scoped>
/* ── Table ── */
.table-wrap { overflow-x: auto; }
.train-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.train-table th {
  text-align: left;
  padding: 10px 16px;
  border-bottom: 2px solid var(--gray-200);
  color: var(--gray-500);
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .5px;
  white-space: nowrap;
  background: #f9fafb;
}
.train-table td {
  padding: 10px 16px;
  border-bottom: 1px solid var(--gray-100);
  vertical-align: middle;
}
.train-table tr:last-child td { border-bottom: none; }
.train-table tr:hover td { background: var(--gray-50); }

/* ── Progress bar ── */
.prog-bar  { flex:1; height:8px; background:var(--gray-200); border-radius:4px; overflow:hidden; }
.prog-fill { height:100%; background:var(--primary); border-radius:4px; transition:width .3s; }

/* ── Employee row in assign modal ── */
.emp-row:hover { background: var(--gray-50); }

/* ── Certificate card ── */
.cert-card {
  text-align: center;
  padding: 0;
}
.cert-card .card-body { padding: 28px 20px; }
.cert-icon { font-size: 36px; margin-bottom: 10px; }
.cert-num {
  display: inline-block;
  font-size: 11px;
  background: var(--gray-100);
  padding: 2px 8px;
  border-radius: 4px;
  color: var(--gray-500);
}
</style>
