<template>
  <div class="apply-page">
    <div class="apply-container">
      <!-- Loading -->
      <div v-if="loading" class="apply-card" style="text-align:center;padding:48px">
        <div class="spinner" style="margin:0 auto"></div>
      </div>

      <!-- Error -->
      <div v-else-if="errorMsg" class="apply-card apply-error">
        <div class="error-icon">⚠️</div>
        <div class="error-title">{{ errorMsg }}</div>
        <div class="error-hint">Пожалуйста, свяжитесь с работодателем напрямую.</div>
      </div>

      <!-- Thank you -->
      <div v-else-if="submitted" class="apply-card apply-success">
        <div class="success-icon">✅</div>
        <div class="success-title">Заявка отправлена!</div>
        <div class="success-text">
          Спасибо за интерес к вакансии <strong>{{ vacancy.title }}</strong>.<br>
          Мы рассмотрим вашу кандидатуру и свяжемся с вами.
        </div>
      </div>

      <!-- Form -->
      <div v-else-if="vacancy">
        <!-- Vacancy header -->
        <div class="apply-header">
          <div class="apply-logo">HRM</div>
          <div>
            <div class="apply-company">Подача заявки</div>
            <h1 class="apply-title">{{ vacancy.title }}</h1>
            <div class="apply-meta">
              <span v-if="vacancy.department_name" class="apply-chip">{{ vacancy.department_name }}</span>
              <span v-if="vacancy.employment_type" class="apply-chip">{{ employmentLabel(vacancy.employment_type) }}</span>
              <span v-if="vacancy.experience_years" class="apply-chip">Опыт от {{ vacancy.experience_years }} лет</span>
              <span v-if="vacancy.salary_from || vacancy.salary_to" class="apply-salary">
                {{ vacancy.salary_from ? vacancy.salary_from.toLocaleString('ru-RU') : '' }}
                {{ vacancy.salary_from && vacancy.salary_to ? ' — ' : '' }}
                {{ vacancy.salary_to ? vacancy.salary_to.toLocaleString('ru-RU') : '' }} ₽
              </span>
            </div>
          </div>
        </div>

        <!-- Vacancy description collapsed -->
        <div class="apply-card vac-desc-card">
          <details>
            <summary class="vac-desc-toggle">О вакансии</summary>
            <div v-if="vacancy.description" class="vac-desc-text" style="margin-top:10px">{{ vacancy.description }}</div>
            <div v-if="vacancy.responsibilities" class="vac-desc-section">
              <strong>Обязанности:</strong><br>{{ vacancy.responsibilities }}
            </div>
            <div v-if="vacancy.requirements" class="vac-desc-section">
              <strong>Требования:</strong><br>{{ vacancy.requirements }}
            </div>
            <div v-if="vacancy.conditions" class="vac-desc-section">
              <strong>Условия:</strong><br>{{ vacancy.conditions }}
            </div>
          </details>
        </div>

        <!-- Application form -->
        <div class="apply-card">
          <h2 class="form-section-title">Ваши данные</h2>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Имя *</label>
              <input type="text" class="form-control" v-model="form.first_name" :class="{error: errors.first_name}">
              <div v-if="errors.first_name" class="field-error">{{ errors.first_name }}</div>
            </div>
            <div class="form-group">
              <label class="form-label">Фамилия *</label>
              <input type="text" class="form-control" v-model="form.last_name" :class="{error: errors.last_name}">
              <div v-if="errors.last_name" class="field-error">{{ errors.last_name }}</div>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Email *</label>
              <input type="email" class="form-control" v-model="form.email" :class="{error: errors.email}">
              <div v-if="errors.email" class="field-error">{{ errors.email }}</div>
            </div>
            <div class="form-group">
              <label class="form-label">Телефон</label>
              <input type="tel" class="form-control" v-model="form.phone" placeholder="+7 (___) ___-__-__">
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Резюме (файл PDF/DOCX)</label>
            <div class="file-upload-wrap">
              <label class="file-upload-label">
                <input type="file" accept=".pdf,.docx" @change="onFileChange" hidden>
                <span class="file-upload-btn">Выбрать файл</span>
                <span class="file-name">{{ form.resumeFile ? form.resumeFile.name : 'Файл не выбран' }}</span>
              </label>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Текст резюме (или вставьте вручную)</label>
            <textarea class="form-control" rows="7" v-model="form.resume_text"
                      placeholder="Опыт работы, навыки, образование..."></textarea>
          </div>

          <div class="form-group">
            <label class="form-label">Сопроводительное письмо</label>
            <textarea class="form-control" rows="4" v-model="form.cover_letter"
                      placeholder="Расскажите, почему вас заинтересовала эта вакансия..."></textarea>
          </div>
        </div>

        <!-- Questionnaire -->
        <div v-if="vacancy.questions && vacancy.questions.length" class="apply-card">
          <h2 class="form-section-title">Дополнительные вопросы</h2>
          <div v-for="q in vacancy.questions" :key="q.id" class="q-block">
            <div class="q-label">
              {{ q.question_text }}
              <span v-if="q.is_required" class="req-mark">*</span>
            </div>

            <!-- Text -->
            <textarea v-if="q.question_type === 'text'" class="form-control" rows="3"
                      v-model="answers[q.id]"
                      :class="{error: qErrors[q.id]}"></textarea>

            <!-- Single choice -->
            <div v-else-if="q.question_type === 'single'" class="radio-list">
              <label v-for="opt in q.options" :key="opt" class="radio-item">
                <input type="radio" :name="`q_${q.id}`" :value="opt" v-model="answers[q.id]">
                <span>{{ opt }}</span>
              </label>
            </div>

            <!-- Multiple choice -->
            <div v-else-if="q.question_type === 'multiple'" class="radio-list">
              <label v-for="opt in q.options" :key="opt" class="radio-item">
                <input type="checkbox" :value="opt"
                       :checked="(answers[q.id] || []).includes(opt)"
                       @change="toggleMulti(q.id, opt)">
                <span>{{ opt }}</span>
              </label>
            </div>

            <div v-if="qErrors[q.id]" class="field-error">{{ qErrors[q.id] }}</div>
          </div>
        </div>

        <div class="apply-submit">
          <div v-if="submitError" class="submit-error">{{ submitError }}</div>
          <button class="btn-submit" @click="submitForm" :disabled="submitting">
            <span v-if="submitting" class="spinner-sm"></span>
            {{ submitting ? 'Отправка...' : 'Отправить заявку' }}
          </button>
          <div class="submit-hint">
            Нажимая «Отправить», вы соглашаетесь на обработку персональных данных.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getPublicVacancy, applyToVacancy } from '@/api/public'

const route = useRoute()
const token = route.params.token

const loading = ref(true)
const vacancy = ref(null)
const errorMsg = ref('')
const submitted = ref(false)
const submitting = ref(false)
const submitError = ref('')

const form = reactive({
  first_name: '', last_name: '', email: '', phone: '',
  resume_text: '', cover_letter: '',
  resumeFile: null,
})
const answers = reactive({})
const errors = reactive({})
const qErrors = reactive({})

function employmentLabel(type) {
  const m = { full_time: 'Полная занятость', part_time: 'Частичная', remote: 'Удалённо', hybrid: 'Гибрид', contract: 'Контракт', internship: 'Стажировка' }
  return m[type] || type
}

function onFileChange(e) {
  form.resumeFile = e.target.files[0] || null
}

function toggleMulti(qid, opt) {
  if (!answers[qid]) answers[qid] = []
  const idx = answers[qid].indexOf(opt)
  if (idx === -1) answers[qid].push(opt)
  else answers[qid].splice(idx, 1)
}

function validate() {
  Object.keys(errors).forEach(k => delete errors[k])
  Object.keys(qErrors).forEach(k => delete qErrors[k])
  let ok = true
  if (!form.first_name.trim()) { errors.first_name = 'Обязательное поле'; ok = false }
  if (!form.last_name.trim())  { errors.last_name = 'Обязательное поле'; ok = false }
  if (!form.email.trim())      { errors.email = 'Обязательное поле'; ok = false }
  if (form.email && !/\S+@\S+\.\S+/.test(form.email)) { errors.email = 'Некорректный email'; ok = false }
  if (vacancy.value && vacancy.value.questions) {
    for (const q of vacancy.value.questions) {
      if (q.is_required && !answers[q.id]) {
        qErrors[q.id] = 'Обязательный вопрос'; ok = false
      }
    }
  }
  return ok
}

async function submitForm() {
  if (!validate()) return
  submitting.value = true
  submitError.value = ''
  try {
    const fd = new FormData()
    fd.append('first_name', form.first_name)
    fd.append('last_name', form.last_name)
    fd.append('email', form.email)
    fd.append('phone', form.phone)
    fd.append('resume_text', form.resume_text)
    fd.append('cover_letter', form.cover_letter)
    if (form.resumeFile) fd.append('resume', form.resumeFile)
    if (vacancy.value && vacancy.value.questions) {
      for (const q of vacancy.value.questions) {
        const ans = answers[q.id]
        fd.append(`answer_${q.id}`, Array.isArray(ans) ? ans.join(', ') : (ans || ''))
      }
    }
    await applyToVacancy(token, fd)
    submitted.value = true
  } catch (e) {
    submitError.value = e?.response?.data?.detail || 'Ошибка при отправке. Попробуйте ещё раз.'
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    const res = await getPublicVacancy(token)
    vacancy.value = res.data
    if (res.data.questions) {
      for (const q of res.data.questions) {
        answers[q.id] = q.question_type === 'multiple' ? [] : ''
      }
    }
  } catch (e) {
    const status = e?.response?.status
    if (status === 404) errorMsg.value = 'Вакансия не найдена или закрыта'
    else if (status === 410) errorMsg.value = 'Срок подачи заявок истёк'
    else errorMsg.value = 'Не удалось загрузить вакансию'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.apply-page { min-height: 100vh; background: linear-gradient(135deg, #f0f4ff 0%, #faf9ff 100%); padding: 40px 16px; }
.apply-container { max-width: 680px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px; }

.apply-header { display: flex; gap: 20px; align-items: flex-start; background: #fff; border-radius: 16px; padding: 28px; box-shadow: 0 2px 12px rgba(99,102,241,.1); }
.apply-logo { width: 48px; height: 48px; background: linear-gradient(135deg, #6366f1, #8b5cf6); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #fff; font-weight: 800; font-size: 14px; flex-shrink: 0; }
.apply-company { font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 4px; }
.apply-title { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0 0 8px; }
.apply-meta { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.apply-chip { background: #f1f5f9; border-radius: 6px; padding: 3px 10px; font-size: 12px; color: #475569; }
.apply-salary { font-weight: 700; color: #4f46e5; font-size: 15px; }

.apply-card { background: #fff; border-radius: 16px; padding: 24px; box-shadow: 0 1px 4px rgba(0,0,0,.07); }
.apply-success { text-align: center; padding: 48px; }
.apply-error { text-align: center; padding: 48px; }
.success-icon { font-size: 48px; margin-bottom: 16px; }
.success-title { font-size: 22px; font-weight: 700; color: #16a34a; margin-bottom: 12px; }
.success-text { color: #475569; line-height: 1.7; }
.error-icon { font-size: 48px; margin-bottom: 16px; }
.error-title { font-size: 18px; font-weight: 600; color: #dc2626; margin-bottom: 8px; }
.error-hint { color: #94a3b8; }

.vac-desc-toggle { cursor: pointer; font-weight: 600; color: #4f46e5; font-size: 14px; }
.vac-desc-text { color: #475569; line-height: 1.7; font-size: 14px; }
.vac-desc-section { margin-top: 12px; color: #475569; font-size: 14px; line-height: 1.7; }

.form-section-title { font-size: 16px; font-weight: 700; color: #1e293b; margin: 0 0 20px; }
.form-row { display: flex; gap: 16px; }
.form-group { display: flex; flex-direction: column; gap: 4px; flex: 1; margin-bottom: 14px; }
.form-label { font-size: 13px; font-weight: 500; color: #475569; }
.form-control { border: 1.5px solid #e2e8f0; border-radius: 10px; padding: 10px 14px; font-size: 14px; color: #1e293b; transition: border-color 0.15s; font-family: inherit; }
.form-control:focus { outline: none; border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99,102,241,.12); }
.form-control.error { border-color: #ef4444; }
.field-error { font-size: 12px; color: #ef4444; }
.req-mark { color: #ef4444; margin-left: 2px; }

.file-upload-wrap { display: flex; }
.file-upload-label { display: flex; align-items: center; gap: 12px; cursor: pointer; }
.file-upload-btn { background: #f1f5f9; border: 1.5px solid #e2e8f0; border-radius: 8px; padding: 8px 16px; font-size: 13px; color: #475569; white-space: nowrap; transition: all 0.15s; }
.file-upload-btn:hover { border-color: #6366f1; color: #6366f1; }
.file-name { font-size: 13px; color: #94a3b8; }

.q-block { margin-bottom: 20px; }
.q-label { font-weight: 500; color: #1e293b; margin-bottom: 8px; font-size: 14px; }
.radio-list { display: flex; flex-direction: column; gap: 8px; }
.radio-item { display: flex; align-items: center; gap: 10px; cursor: pointer; font-size: 14px; color: #334155; }
.radio-item input { accent-color: #6366f1; width: 16px; height: 16px; cursor: pointer; }

.apply-submit { background: #fff; border-radius: 16px; padding: 24px; box-shadow: 0 1px 4px rgba(0,0,0,.07); text-align: center; }
.submit-error { color: #dc2626; font-size: 13px; margin-bottom: 12px; }
.btn-submit { background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #fff; border: none; border-radius: 12px; padding: 14px 40px; font-size: 16px; font-weight: 600; cursor: pointer; transition: all 0.15s; display: inline-flex; align-items: center; gap: 10px; }
.btn-submit:hover { opacity: 0.92; transform: translateY(-1px); box-shadow: 0 4px 16px rgba(99,102,241,.3); }
.btn-submit:disabled { opacity: 0.55; cursor: not-allowed; transform: none; }
.submit-hint { font-size: 11px; color: #94a3b8; margin-top: 10px; }

.spinner { width: 28px; height: 28px; border: 3px solid #e2e8f0; border-top-color: #6366f1; border-radius: 50%; animation: spin 0.8s linear infinite; }
.spinner-sm { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.4); border-top-color: #fff; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
