<template>
  <div>
    <div class="topbar">
      <div class="topbar-title">
        <button class="btn-back" @click="$router.back()">← Назад</button>
        <span v-if="vacancy">{{ vacancy.title }}</span>
        <span v-else>Вакансия</span>
      </div>
    </div>

    <div class="page-container" v-if="vacancy">
      <div class="tabs">
        <button class="tab-btn" :class="{active: tab==='info'}"     @click="tab='info'">О вакансии</button>
        <button class="tab-btn" :class="{active: tab==='kanban'}"   @click="tab='kanban'">Кандидаты</button>
        <button class="tab-btn" :class="{active: tab==='publish'}"  @click="tab='publish'">Публикация</button>
      </div>

      <!-- ── О вакансии ──────────────────────────────────────────── -->
      <div v-if="tab==='info'" class="info-tab">
        <div class="info-header">
          <div>
            <div class="info-title">{{ vacancy.title }}</div>
            <div class="info-meta">
              <span class="chip">{{ vacancy.department_name }}</span>
              <span class="chip" v-if="vacancy.employment_type">{{ employmentLabel(vacancy.employment_type) }}</span>
              <span class="chip" v-if="vacancy.experience_years">Опыт от {{ vacancy.experience_years }} лет</span>
              <span :class="statusBadge(vacancy.status)" class="badge">{{ vacancy.status_display }}</span>
            </div>
          </div>
          <div class="salary-block" v-if="vacancy.salary_from || vacancy.salary_to">
            <span class="salary-val">
              {{ vacancy.salary_from ? vacancy.salary_from.toLocaleString('ru-RU') : '' }}
              {{ vacancy.salary_from && vacancy.salary_to ? ' — ' : '' }}
              {{ vacancy.salary_to ? vacancy.salary_to.toLocaleString('ru-RU') : '' }} ₽
            </span>
          </div>
        </div>

        <div v-if="vacancy.required_skills && vacancy.required_skills.length" class="info-section">
          <div class="info-section-title">Требуемые навыки</div>
          <div class="skills-list">
            <span v-for="sk in vacancy.required_skills" :key="sk" class="skill-tag">{{ sk }}</span>
          </div>
        </div>

        <div v-if="vacancy.description" class="info-section">
          <div class="info-section-title">Описание</div>
          <div class="info-text">{{ vacancy.description }}</div>
        </div>

        <div v-if="vacancy.responsibilities" class="info-section">
          <div class="info-section-title">Обязанности</div>
          <div class="info-text">{{ vacancy.responsibilities }}</div>
        </div>

        <div v-if="vacancy.requirements" class="info-section">
          <div class="info-section-title">Требования</div>
          <div class="info-text">{{ vacancy.requirements }}</div>
        </div>

        <div v-if="vacancy.conditions" class="info-section">
          <div class="info-section-title">Условия</div>
          <div class="info-text">{{ vacancy.conditions }}</div>
        </div>
      </div>

      <!-- ── Кандидаты (канбан) ──────────────────────────────────── -->
      <div v-if="tab==='kanban'">
        <div class="kanban-toolbar">
          <button class="btn btn-outline btn-sm" @click="showAddCandidate = true">+ Кандидат</button>
          <button class="btn btn-ai btn-sm" :disabled="analyzing" @click="runAnalyzeAll">
            <span v-if="analyzing" class="spinner-xs"></span>
            <span v-else>✦</span>
            {{ analyzing ? 'Анализируем...' : 'AI Анализ всех' }}
          </button>
        </div>
        <div class="kanban">
          <div v-for="stage in stages" :key="stage.value" class="kanban-col">
            <div class="kanban-col-title">
              {{ stage.label }}
              <span class="col-count">{{ candidatesByStage(stage.value).length }}</span>
            </div>
            <div v-if="!candidatesByStage(stage.value).length" class="kanban-empty">Нет кандидатов</div>
            <div v-for="c in candidatesByStage(stage.value)" :key="c.id"
                 class="kanban-card" @click="openDetail(c)">
              <div class="card-top">
                <span class="cand-name">{{ c.full_name }}</span>
                <span class="source-icon" :title="c.source === 'public' ? 'Публичная форма' : 'Добавлен HR'">
                  {{ c.source === 'public' ? '🔗' : '➕' }}
                </span>
                <span v-if="c.ai_score != null" :class="aiBadgeClass(c.ai_score)" class="ai-badge">
                  ✦ {{ aiPercent(c.ai_score) }}
                </span>
              </div>
              <div v-if="c.extracted_skills && c.extracted_skills.length" class="card-skills">
                <span v-for="sk in c.extracted_skills.slice(0,3)" :key="sk" class="skill-tag-sm">{{ sk }}</span>
              </div>
              <div class="card-footer">
                <span class="rating-stars">{{ '★'.repeat(c.rating) }}{{ '☆'.repeat(5 - c.rating) }}</span>
                <span v-if="c.ml_hiring_probability != null" class="prob-badge">
                  {{ mlPercent(c.ml_hiring_probability) }} найм
                </span>
              </div>
              <button v-if="stage.value !== 'hired' && stage.value !== 'rejected'"
                      class="btn btn-outline btn-xs" style="margin-top:8px;width:100%"
                      @click.stop="advance(c.id)">→ Следующий этап</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Публикация ──────────────────────────────────────────── -->
      <div v-if="tab==='publish'" class="publish-tab">
        <div class="card publish-card">
          <div class="publish-row">
            <div>
              <div class="publish-label">Открыта для откликов</div>
              <div class="publish-hint">Публичная ссылка будет доступна без авторизации</div>
            </div>
            <label class="toggle">
              <input type="checkbox" v-model="publishForm.is_public" @change="savePublish">
              <span class="toggle-slider"></span>
            </label>
          </div>

          <div class="publish-row" v-if="publishForm.is_public">
            <div class="form-group" style="flex:1">
              <label class="form-label">Дедлайн заявок</label>
              <input type="date" class="form-control" v-model="publishForm.application_deadline"
                     @change="savePublish">
            </div>
          </div>

          <div v-if="vacancy.is_public" class="publish-link-block">
            <div class="publish-label" style="margin-bottom:8px">Публичная ссылка</div>
            <div class="link-row">
              <input type="text" class="form-control link-input" :value="publicUrl" readonly>
              <button class="btn btn-outline btn-sm" @click="copyLink">
                {{ copied ? '✓ Скопировано' : 'Копировать' }}
              </button>
            </div>
            <div class="qr-block" style="margin-top:16px">
              <img :src="qrUrl" alt="QR код" class="qr-img">
            </div>
          </div>
        </div>

        <!-- Опросник -->
        <div class="card" style="margin-top:20px">
          <div class="section-header">
            <div class="section-title">Вопросы для кандидатов</div>
            <button class="btn btn-outline btn-sm" @click="showQuestionForm = !showQuestionForm">
              {{ showQuestionForm ? 'Отмена' : '+ Добавить вопрос' }}
            </button>
          </div>

          <div v-if="showQuestionForm" class="question-form">
            <div class="form-group">
              <label class="form-label">Текст вопроса *</label>
              <input type="text" class="form-control" v-model="newQuestion.question_text" placeholder="Введите вопрос...">
            </div>
            <div class="form-row">
              <div class="form-group" style="flex:1">
                <label class="form-label">Тип</label>
                <select class="form-control" v-model="newQuestion.question_type">
                  <option value="text">Текст</option>
                  <option value="single">Один вариант</option>
                  <option value="multiple">Несколько вариантов</option>
                </select>
              </div>
              <div class="form-group" style="display:flex;align-items:center;gap:8px;padding-top:24px">
                <input type="checkbox" id="qRequired" v-model="newQuestion.is_required">
                <label for="qRequired" class="form-label" style="margin:0">Обязательный</label>
              </div>
            </div>
            <div v-if="newQuestion.question_type !== 'text'" class="form-group">
              <label class="form-label">Варианты ответа (по одному, Enter)</label>
              <div class="tag-input-wrap">
                <span v-for="(opt, i) in newQuestion.options" :key="i" class="skill-tag">
                  {{ opt }} <span class="tag-remove" @click="newQuestion.options.splice(i,1)">×</span>
                </span>
                <input
                  v-model="optionInput"
                  class="tag-inner-input"
                  placeholder="Вариант..."
                  @keydown.enter.prevent="addOption"
                  @keydown.tab.prevent="addOption"
                >
              </div>
            </div>
            <button class="btn btn-primary btn-sm" @click="addQuestion" :disabled="!newQuestion.question_text.trim()">
              Сохранить вопрос
            </button>
          </div>

          <div v-if="!questions.length" class="empty-hint">Вопросов нет</div>
          <div v-for="(q, idx) in questions" :key="q.id" class="question-item">
            <div class="q-num">{{ idx + 1 }}</div>
            <div class="q-body">
              <div class="q-text">{{ q.question_text }}</div>
              <div class="q-meta">
                <span class="chip-sm">{{ questionTypeLabel(q.question_type) }}</span>
                <span v-if="q.is_required" class="chip-sm chip-required">Обязательный</span>
                <span v-if="q.options && q.options.length" class="q-opts">
                  Варианты: {{ q.options.join(', ') }}
                </span>
              </div>
            </div>
            <button class="btn-icon-del" @click="removeQuestion(q.id)" title="Удалить">✕</button>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="loading" class="page-container">
      <div class="card" style="padding:48px;text-align:center"><div class="spinner" style="margin:0 auto"></div></div>
    </div>

    <!-- Candidate detail modal -->
    <div v-if="selectedCandidate" class="modal-overlay" @click.self="selectedCandidate=null">
      <div class="modal modal-wide">
        <button class="modal-close" @click="selectedCandidate=null">×</button>
        <h3 class="modal-title">{{ selectedCandidate.full_name }}</h3>
        <div class="detail-meta">
          <span class="badge badge-blue">{{ selectedCandidate.stage_display }}</span>
          <span class="rating-stars">{{ '★'.repeat(selectedCandidate.rating) }}{{ '☆'.repeat(5-selectedCandidate.rating) }}</span>
          <span class="source-icon-lg" :title="selectedCandidate.source === 'public' ? 'Публичная форма' : 'Добавлен HR'">
            {{ selectedCandidate.source === 'public' ? '🔗 Публичная форма' : '➕ Добавлен HR' }}
          </span>
        </div>
        <div v-if="selectedCandidate.ai_score != null" :class="aiBadgeClass(selectedCandidate.ai_score)" class="ai-score-block">
          ✦ AI-оценка: {{ aiPercent(selectedCandidate.ai_score) }} &nbsp;|&nbsp; Найм: {{ mlPercent(selectedCandidate.ml_hiring_probability) }}
        </div>
        <div v-if="selectedCandidate.ai_comment" class="ai-comment">{{ selectedCandidate.ai_comment }}</div>
        <div class="detail-section">
          <div class="detail-section-title-row">
            <span class="detail-section-title">Резюме</span>
            <a
              v-if="selectedCandidate.resume"
              :href="resumeFileUrl(selectedCandidate.id)"
              target="_blank"
              rel="noopener"
              class="btn-resume-open"
            >📎 Открыть резюме</a>
            <span v-else class="btn-resume-disabled" title="Файл не прикреплён">📎 Открыть резюме</span>
          </div>
          <pre v-if="selectedCandidate.resume_text" class="resume-pre">{{ selectedCandidate.resume_text }}</pre>
          <div v-else class="resume-empty">Текст не добавлен</div>
        </div>
        <div v-if="selectedCandidate.cover_letter" class="detail-section">
          <div class="detail-section-title">Сопроводительное письмо</div>
          <div class="detail-text">{{ selectedCandidate.cover_letter }}</div>
        </div>
        <div v-if="candidateAnswers.length" class="detail-section">
          <div class="detail-section-title">Ответы на вопросы</div>
          <div v-for="ans in candidateAnswers" :key="ans.id" class="answer-item">
            <div class="answer-q">{{ ans.question_text }}</div>
            <div class="answer-a">{{ ans.answer_text || '—' }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add candidate modal -->
    <div v-if="showAddCandidate" class="modal-overlay" @click.self="showAddCandidate=false">
      <div class="modal">
        <button class="modal-close" @click="showAddCandidate=false">×</button>
        <h3 class="modal-title">Добавить кандидата</h3>
        <div class="form-row">
          <div class="form-group" style="flex:1">
            <label class="form-label">Имя *</label>
            <input type="text" class="form-control" v-model="candForm.first_name">
          </div>
          <div class="form-group" style="flex:1">
            <label class="form-label">Фамилия *</label>
            <input type="text" class="form-control" v-model="candForm.last_name">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group" style="flex:1">
            <label class="form-label">Email *</label>
            <input type="email" class="form-control" v-model="candForm.email">
          </div>
          <div class="form-group" style="flex:1">
            <label class="form-label">Телефон</label>
            <input type="text" class="form-control" v-model="candForm.phone">
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Резюме (текст)</label>
          <textarea class="form-control" rows="6" v-model="candForm.resume_text" placeholder="Вставьте текст резюме..."></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">Сопроводительное письмо</label>
          <textarea class="form-control" rows="3" v-model="candForm.cover_letter"></textarea>
        </div>
        <div class="form-row">
          <div class="form-group" style="flex:1">
            <label class="form-label">Рейтинг (0–5)</label>
            <input type="number" class="form-control" v-model.number="candForm.rating" min="0" max="5">
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="showAddCandidate=false">Отмена</button>
          <button class="btn btn-primary" @click="saveCandidate" :disabled="savingCandidate">
            {{ savingCandidate ? 'Сохранение...' : 'Сохранить' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import * as recruitApi from '@/api/recruitment'
import { getResumeUrl } from '@/api/recruitment'

const route = useRoute()
const vacancyId = route.params.id

const vacancy = ref(null)
const loading = ref(true)
const tab = ref('info')
const candidates = ref([])
const analyzing = ref(false)
const questions = ref([])
const selectedCandidate = ref(null)
const candidateAnswers = ref([])
const showAddCandidate = ref(false)
const savingCandidate = ref(false)
const showQuestionForm = ref(false)
const copied = ref(false)
const publishForm = ref({ is_public: false, application_deadline: '' })
const newQuestion = ref({ question_text: '', question_type: 'text', options: [], is_required: false })
const optionInput = ref('')

const stages = [
  { value: 'new', label: 'Новые' },
  { value: 'screening', label: 'Скрининг' },
  { value: 'interview', label: 'Интервью' },
  { value: 'offer', label: 'Оффер' },
  { value: 'hired', label: 'Принят' },
  { value: 'rejected', label: 'Отклонён' },
]

const candForm = ref({
  first_name: '', last_name: '', email: '', phone: '',
  resume_text: '', cover_letter: '', rating: 0,
})

const publicUrl = computed(() => {
  if (!vacancy.value) return ''
  return `${window.location.origin}/apply/${vacancy.value.public_token}`
})

const qrUrl = computed(() =>
  publicUrl.value
    ? `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(publicUrl.value)}`
    : ''
)

function resumeFileUrl(id) { return getResumeUrl(id) }

function employmentLabel(type) {
  const m = { full_time: 'Полная занятость', part_time: 'Частичная', remote: 'Удалённо', hybrid: 'Гибрид', contract: 'Контракт', internship: 'Стажировка' }
  return m[type] || type
}

function statusBadge(status) {
  return { open: 'badge-green', closed: 'badge-gray', on_hold: 'badge-yellow' }[status] || 'badge-gray'
}

function questionTypeLabel(t) {
  return { text: 'Текст', single: 'Один вариант', multiple: 'Несколько вариантов' }[t] || t
}

function candidatesByStage(stage) {
  return candidates.value.filter(c => c.stage === stage)
}

function aiBadgeClass(score) {
  const s = parseFloat(score)
  if (s >= 0.7) return 'ai-badge-high'
  if (s >= 0.4) return 'ai-badge-mid'
  return 'ai-badge-low'
}

function aiPercent(score) { return score != null ? Math.round(parseFloat(score) * 100) + '%' : '' }
function mlPercent(prob) { return prob != null ? Math.round(parseFloat(prob) * 100) + '%' : '' }

async function loadVacancy() {
  try {
    const res = await recruitApi.getVacancy(vacancyId)
    vacancy.value = res.data
    publishForm.value.is_public = res.data.is_public
    publishForm.value.application_deadline = res.data.application_deadline || ''
  } finally {
    loading.value = false
  }
}

async function loadCandidates() {
  const res = await recruitApi.getCandidates({ vacancy: vacancyId })
  candidates.value = res.data.results || res.data
}

async function loadQuestions() {
  const res = await recruitApi.getVacancyQuestions(vacancyId)
  questions.value = res.data
}

async function advance(id) {
  const res = await recruitApi.advanceCandidate(id)
  const idx = candidates.value.findIndex(c => c.id === id)
  if (idx !== -1) candidates.value[idx] = res.data
}

async function runAnalyzeAll() {
  analyzing.value = true
  try {
    const res = await recruitApi.analyzeVacancyAll(vacancyId)
    candidates.value = res.data.candidates
  } finally {
    analyzing.value = false
  }
}

async function openDetail(c) {
  selectedCandidate.value = c
  candidateAnswers.value = []
  try {
    const res = await recruitApi.getCandidate(c.id)
    selectedCandidate.value = res.data
    // fetch answers via candidate detail (answers are nested)
    if (res.data.answers) {
      candidateAnswers.value = res.data.answers
    }
  } catch {}
}

async function saveCandidate() {
  if (!candForm.value.first_name || !candForm.value.last_name || !candForm.value.email) return
  savingCandidate.value = true
  try {
    const res = await recruitApi.createCandidate({ ...candForm.value, vacancy: vacancyId, source: 'hr' })
    candidates.value.unshift(res.data)
    showAddCandidate.value = false
    candForm.value = { first_name: '', last_name: '', email: '', phone: '', resume_text: '', cover_letter: '', rating: 0 }
    try {
      const analyzed = await recruitApi.analyzeCandidate(res.data.id)
      const idx = candidates.value.findIndex(c => c.id === res.data.id)
      if (idx !== -1) candidates.value[idx] = analyzed.data
    } catch {}
  } finally {
    savingCandidate.value = false
  }
}

async function savePublish() {
  const payload = {
    is_public: publishForm.value.is_public,
    application_deadline: publishForm.value.application_deadline || null,
  }
  const res = await recruitApi.publishVacancy(vacancyId, payload)
  vacancy.value = { ...vacancy.value, ...res.data }
}

async function addQuestion() {
  if (!newQuestion.value.question_text.trim()) return
  const res = await recruitApi.createVacancyQuestion(vacancyId, { ...newQuestion.value })
  questions.value.push(res.data)
  newQuestion.value = { question_text: '', question_type: 'text', options: [], is_required: false }
  optionInput.value = ''
  showQuestionForm.value = false
}

async function removeQuestion(qid) {
  await recruitApi.deleteVacancyQuestion(vacancyId, qid)
  questions.value = questions.value.filter(q => q.id !== qid)
}

function addOption() {
  const v = optionInput.value.trim()
  if (v) { newQuestion.value.options.push(v); optionInput.value = '' }
}

async function copyLink() {
  await navigator.clipboard.writeText(publicUrl.value)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

onMounted(async () => {
  await loadVacancy()
  await Promise.all([loadCandidates(), loadQuestions()])
})
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1100px; }
.tabs { display: flex; gap: 4px; margin-bottom: 24px; }
.tab-btn { padding: 8px 20px; border: none; background: none; cursor: pointer; border-radius: 8px; font-size: 14px; color: #64748b; font-weight: 500; transition: all 0.15s; }
.tab-btn.active { background: #e0e7ff; color: #4f46e5; }
.tab-btn:hover:not(.active) { background: #f1f5f9; }

.btn-back { background: none; border: none; cursor: pointer; color: #6366f1; font-size: 14px; margin-right: 12px; padding: 4px 8px; border-radius: 6px; }
.btn-back:hover { background: #e0e7ff; }

/* Info tab */
.info-tab { display: flex; flex-direction: column; gap: 20px; }
.info-header { display: flex; justify-content: space-between; align-items: flex-start; background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 1px 4px rgba(0,0,0,.07); }
.info-title { font-size: 22px; font-weight: 700; color: #1e293b; margin-bottom: 8px; }
.info-meta { display: flex; gap: 8px; flex-wrap: wrap; }
.salary-val { font-size: 20px; font-weight: 700; color: #4f46e5; }
.chip { background: #f1f5f9; border-radius: 6px; padding: 3px 10px; font-size: 12px; color: #475569; }
.info-section { background: #fff; border-radius: 12px; padding: 20px 24px; box-shadow: 0 1px 4px rgba(0,0,0,.07); }
.info-section-title { font-weight: 600; color: #1e293b; margin-bottom: 10px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.04em; color: #94a3b8; }
.info-text { color: #334155; line-height: 1.7; white-space: pre-wrap; }
.skills-list { display: flex; flex-wrap: wrap; gap: 6px; }
.skill-tag { background: #e0e7ff; color: #4f46e5; border-radius: 6px; padding: 4px 10px; font-size: 12px; font-weight: 500; }

/* Kanban */
.kanban-toolbar { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
.kanban { display: flex; gap: 12px; overflow-x: auto; padding-bottom: 8px; }
.kanban-col { min-width: 200px; max-width: 220px; flex-shrink: 0; background: #f8fafc; border-radius: 12px; padding: 12px; }
.kanban-col-title { font-weight: 600; font-size: 13px; margin-bottom: 10px; display: flex; justify-content: space-between; color: #475569; }
.col-count { background: #e2e8f0; border-radius: 9px; padding: 1px 8px; font-size: 12px; }
.kanban-empty { font-size: 12px; color: #94a3b8; text-align: center; padding: 16px 0; }
.kanban-card { background: #fff; border-radius: 10px; padding: 12px; margin-bottom: 8px; cursor: pointer; box-shadow: 0 1px 3px rgba(0,0,0,.06); transition: box-shadow 0.15s; border: 1px solid #e2e8f0; }
.kanban-card:hover { box-shadow: 0 4px 12px rgba(99,102,241,.12); border-color: #c7d2fe; }
.card-top { display: flex; gap: 4px; align-items: center; margin-bottom: 4px; flex-wrap: wrap; }
.cand-name { font-weight: 600; font-size: 13px; color: #1e293b; flex: 1; }
.source-icon { font-size: 13px; cursor: default; }
.ai-badge { font-size: 11px; padding: 2px 7px; border-radius: 9px; font-weight: 600; white-space: nowrap; }
.ai-badge-high { background: #dcfce7; color: #16a34a; }
.ai-badge-mid  { background: #fef9c3; color: #ca8a04; }
.ai-badge-low  { background: #fee2e2; color: #dc2626; }
.card-skills { display: flex; gap: 4px; flex-wrap: wrap; margin: 4px 0; }
.skill-tag-sm { background: #e0e7ff; color: #4f46e5; border-radius: 4px; padding: 2px 6px; font-size: 10px; }
.card-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 6px; }
.rating-stars { font-size: 11px; color: #f59e0b; }
.prob-badge { font-size: 11px; background: #f0fdf4; color: #16a34a; border-radius: 6px; padding: 1px 6px; }

/* Publish tab */
.publish-tab { display: flex; flex-direction: column; gap: 20px; }
.publish-card { padding: 24px; display: flex; flex-direction: column; gap: 20px; }
.card { background: #fff; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.07); padding: 20px 24px; }
.publish-row { display: flex; justify-content: space-between; align-items: center; gap: 24px; }
.publish-label { font-weight: 600; color: #1e293b; }
.publish-hint { font-size: 13px; color: #94a3b8; margin-top: 2px; }
.publish-link-block { border-top: 1px solid #f1f5f9; padding-top: 20px; }
.link-row { display: flex; gap: 8px; }
.link-input { background: #f8fafc; color: #475569; }
.qr-block { display: flex; }
.qr-img { border-radius: 8px; border: 1px solid #e2e8f0; }

/* Toggle switch */
.toggle { position: relative; display: inline-block; width: 44px; height: 24px; }
.toggle input { opacity: 0; width: 0; height: 0; }
.toggle-slider { position: absolute; inset: 0; background: #cbd5e1; border-radius: 24px; cursor: pointer; transition: 0.2s; }
.toggle-slider:before { content: ''; position: absolute; height: 18px; width: 18px; left: 3px; bottom: 3px; background: #fff; border-radius: 50%; transition: 0.2s; }
input:checked + .toggle-slider { background: #6366f1; }
input:checked + .toggle-slider:before { transform: translateX(20px); }

/* Questions */
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.section-title { font-weight: 600; font-size: 16px; color: #1e293b; }
.question-form { background: #f8fafc; border-radius: 10px; padding: 16px; margin-bottom: 16px; display: flex; flex-direction: column; gap: 12px; }
.question-item { display: flex; gap: 12px; align-items: flex-start; padding: 12px 0; border-bottom: 1px solid #f1f5f9; }
.q-num { font-weight: 700; color: #6366f1; min-width: 24px; }
.q-body { flex: 1; }
.q-text { font-weight: 500; color: #1e293b; margin-bottom: 4px; }
.q-meta { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.chip-sm { background: #f1f5f9; border-radius: 4px; padding: 2px 8px; font-size: 11px; color: #64748b; }
.chip-required { background: #fef3c7; color: #d97706; }
.q-opts { font-size: 11px; color: #94a3b8; }
.btn-icon-del { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 16px; padding: 0 4px; line-height: 1; }
.btn-icon-del:hover { color: #ef4444; }
.empty-hint { color: #94a3b8; font-size: 13px; padding: 16px 0; text-align: center; }

/* Tag input */
.tag-input-wrap { display: flex; flex-wrap: wrap; gap: 6px; border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px 10px; min-height: 40px; cursor: text; background: #fff; }
.tag-input-wrap .skill-tag { cursor: default; }
.tag-remove { cursor: pointer; margin-left: 4px; color: #64748b; }
.tag-remove:hover { color: #ef4444; }
.tag-inner-input { border: none; outline: none; font-size: 13px; flex: 1; min-width: 80px; background: transparent; }

/* Form helpers */
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-label { font-size: 13px; font-weight: 500; color: #475569; }
.form-control { border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 12px; font-size: 14px; color: #1e293b; background: #fff; transition: border-color 0.15s; }
.form-control:focus { outline: none; border-color: #6366f1; }
.form-row { display: flex; gap: 16px; }

/* Candidate detail modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.4); z-index: 1000; display: flex; align-items: center; justify-content: center; }
.modal { background: #fff; border-radius: 16px; padding: 32px; width: 560px; max-height: 85vh; overflow-y: auto; position: relative; }
.modal-wide { width: 700px; }
.modal-close { position: absolute; top: 16px; right: 16px; background: none; border: none; font-size: 22px; cursor: pointer; color: #94a3b8; }
.modal-title { font-size: 20px; font-weight: 700; margin-bottom: 12px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
.detail-meta { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-bottom: 12px; }
.source-icon-lg { font-size: 13px; color: #64748b; }
.ai-score-block { border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; margin-bottom: 8px; }
.ai-badge-high.ai-score-block { background: #dcfce7; color: #16a34a; }
.ai-badge-mid.ai-score-block  { background: #fef9c3; color: #ca8a04; }
.ai-badge-low.ai-score-block  { background: #fee2e2; color: #dc2626; }
.ai-comment { font-size: 13px; color: #64748b; margin-bottom: 16px; line-height: 1.6; }
.detail-section { margin-bottom: 16px; }
.detail-section-title { font-weight: 600; font-size: 13px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 6px; }
.detail-section-title-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.detail-section-title-row .detail-section-title { margin-bottom: 0; }
.btn-resume-open { font-size: 12px; font-weight: 500; color: #6366f1; text-decoration: none; background: #e0e7ff; border-radius: 6px; padding: 3px 10px; transition: background 0.15s; white-space: nowrap; }
.btn-resume-open:hover { background: #c7d2fe; }
.btn-resume-disabled { font-size: 12px; font-weight: 500; color: #94a3b8; background: #f1f5f9; border-radius: 6px; padding: 3px 10px; cursor: not-allowed; white-space: nowrap; }
.resume-empty { font-size: 12px; color: #94a3b8; font-style: italic; }
.resume-pre { white-space: pre-wrap; font-family: inherit; font-size: 13px; color: #334155; line-height: 1.7; background: #f8fafc; border-radius: 8px; padding: 12px; max-height: 260px; overflow-y: auto; }
.detail-text { font-size: 13px; color: #334155; line-height: 1.7; }
.answer-item { margin-bottom: 10px; }
.answer-q { font-weight: 500; font-size: 13px; color: #475569; margin-bottom: 2px; }
.answer-a { font-size: 13px; color: #334155; background: #f8fafc; border-radius: 6px; padding: 6px 10px; }

/* Buttons */
.btn { padding: 8px 18px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 500; border: none; transition: all 0.15s; }
.btn-primary { background: #6366f1; color: #fff; }
.btn-primary:hover { background: #4f46e5; }
.btn-outline { background: #fff; border: 1.5px solid #e2e8f0; color: #475569; }
.btn-outline:hover { border-color: #6366f1; color: #6366f1; }
.btn-ai { background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #fff; }
.btn-sm { padding: 6px 14px; font-size: 13px; }
.btn-xs { padding: 4px 10px; font-size: 12px; }
.btn:disabled { opacity: 0.55; cursor: not-allowed; }
.spinner { width: 24px; height: 24px; border: 3px solid #e2e8f0; border-top-color: #6366f1; border-radius: 50%; animation: spin 0.8s linear infinite; }
.spinner-xs { width: 14px; height: 14px; border: 2px solid rgba(255,255,255,0.4); border-top-color: #fff; border-radius: 50%; display: inline-block; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.badge { display: inline-flex; align-items: center; border-radius: 9px; padding: 2px 10px; font-size: 12px; font-weight: 600; }
.badge-green  { background: #dcfce7; color: #16a34a; }
.badge-yellow { background: #fef9c3; color: #ca8a04; }
.badge-gray   { background: #f1f5f9; color: #64748b; }
.badge-blue   { background: #dbeafe; color: #2563eb; }
</style>
