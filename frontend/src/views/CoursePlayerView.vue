<template>
  <div class="player-root">

    <!-- ── Top bar ── -->
    <div class="player-topbar">
      <router-link to="/training" class="btn btn-outline btn-sm">← Назад</router-link>
      <div class="player-course-title">{{ assignment?.course_title }}</div>
      <div class="player-progress-wrap">
        <div class="player-prog-bar">
          <div class="player-prog-fill" :style="{width: (assignment?.progress ?? 0) + '%'}"></div>
        </div>
        <span class="player-prog-label">{{ assignment?.progress ?? 0 }}%</span>
      </div>
    </div>

    <!-- ── Loading ── -->
    <div v-if="loading" class="player-center">
      <div class="spinner" style="width:40px;height:40px"></div>
    </div>

    <!-- ── Completion screen ── -->
    <div v-else-if="allDone" class="completion-screen">
      <div class="completion-icon">🎓</div>
      <h2 class="completion-title">Поздравляем!</h2>
      <p class="completion-sub">
        Вы успешно завершили курс<br>
        <strong>«{{ assignment?.course_title }}»</strong>
      </p>

      <div v-if="certificate" class="cert-display">
        <div class="cert-display-label">Ваш сертификат</div>
        <div class="cert-display-num">{{ certificate.certificate_number }}</div>
        <div class="cert-display-date">Выдан {{ fmtDate(certificate.issued_at) }}</div>
      </div>
      <div v-else class="cert-display" style="opacity:.6">
        <div class="cert-display-label">Получение сертификата...</div>
      </div>

      <router-link to="/training" class="btn btn-primary" style="margin-top:28px">
        Вернуться к курсам
      </router-link>
    </div>

    <!-- ── Course player ── -->
    <div v-else class="player-body">

      <!-- Left: lesson list -->
      <aside class="lesson-sidebar">
        <div class="sidebar-head">Уроки курса</div>
        <div class="sidebar-prog-row">
          <span>{{ completedIds.length }} / {{ lessons.length }} пройдено</span>
          <span style="font-weight:600">{{ assignment?.progress ?? 0 }}%</span>
        </div>
        <div class="sidebar-prog-bar">
          <div class="sidebar-prog-fill" :style="{width: (assignment?.progress ?? 0) + '%'}"></div>
        </div>
        <div class="lesson-list">
          <button
            v-for="lesson in lessons"
            :key="lesson.id"
            class="lesson-item"
            :class="{
              'lesson-active': currentLessonId === lesson.id,
              'lesson-done':   isCompleted(lesson.id),
            }"
            @click="currentLessonId = lesson.id"
          >
            <span class="lesson-check-circle">
              <span v-if="isCompleted(lesson.id)">✓</span>
              <span v-else>{{ lesson.order }}</span>
            </span>
            <span class="lesson-item-title">{{ lesson.title }}</span>
          </button>
        </div>
      </aside>

      <!-- Right: lesson content -->
      <main class="lesson-main" v-if="currentLesson">
        <div class="lesson-meta">Урок {{ currentLesson.order }} из {{ lessons.length }}</div>
        <h1 class="lesson-heading">{{ currentLesson.title }}</h1>
        <div class="lesson-divider"></div>
        <div class="lesson-content">
          <p
            v-for="(para, i) in paragraphs"
            :key="i"
            class="lesson-para"
          >{{ para }}</p>
        </div>

        <!-- ── Quiz block ── -->
        <div v-if="currentLesson.questions?.length" class="quiz-block">
          <div class="quiz-title">Проверьте себя</div>
          <div
            v-for="(q, qi) in currentLesson.questions"
            :key="qi"
            class="quiz-question"
          >
            <div class="quiz-q-text">{{ qi + 1 }}. {{ q.question }}</div>
            <div class="quiz-options">
              <button
                v-for="(opt, oi) in q.options"
                :key="oi"
                class="quiz-opt"
                :class="optionClass(qi, oi, q)"
                :disabled="isAnswered(qi)"
                @click="selectAnswer(qi, oi)"
              >
                <span class="quiz-opt-letter">{{ ['А', 'Б', 'В'][oi] }}</span>
                {{ opt }}
              </button>
            </div>
            <transition name="fade">
              <div v-if="isAnswered(qi)" class="quiz-explanation">
                <span v-if="quizAnswers[qi] === q.correct" class="expl-icon expl-ok">✓</span>
                <span v-else class="expl-icon expl-err">✗</span>
                {{ q.explanation }}
              </div>
            </transition>
          </div>

          <div v-if="!canCompleteLesson" class="quiz-hint">
            Ответьте правильно на все вопросы, чтобы завершить урок
          </div>
        </div>

        <div class="lesson-actions">
          <button
            v-if="!isCompleted(currentLesson.id)"
            class="btn btn-primary"
            style="min-width:180px"
            :disabled="completing || !canCompleteLesson"
            @click="completeCurrentLesson"
          >
            <span v-if="completing">Сохранение...</span>
            <span v-else>✓ Урок пройден</span>
          </button>
          <div v-else class="lesson-done-label">✓ Урок пройден</div>

          <button
            v-if="nextLesson"
            class="btn btn-secondary"
            style="margin-left:12px"
            @click="goToLesson(nextLesson.id)"
          >
            Следующий урок →
          </button>
          <button
            v-else-if="!isCompleted(currentLesson.id) && !nextLesson"
            class="btn btn-secondary"
            style="margin-left:12px"
            disabled
          >
            Последний урок
          </button>
        </div>
      </main>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute }          from 'vue-router'
import { useTrainingStore }  from '@/stores/training'
import api from '@/api/index'

const route  = useRoute()
const store  = useTrainingStore()
const aId    = computed(() => Number(route.params.id))

const assignment      = ref(null)
const certificate     = ref(null)
const loading         = ref(false)
const completing      = ref(false)
const currentLessonId = ref(null)
const quizAnswers     = ref({})  // { [questionIndex]: selectedOptionIndex }

// ── Derived ─────────────────────────────────────────────────────────────
const lessons = computed(() => {
  const raw = assignment.value?.course_lessons || []
  return [...raw].sort((a, b) => a.order - b.order)
})

const completedIds = computed(() => assignment.value?.completed_lessons || [])
const isCompleted  = (id) => completedIds.value.includes(id)
const allDone      = computed(() =>
  lessons.value.length > 0 && lessons.value.every(l => isCompleted(l.id))
)

const currentLesson = computed(() =>
  lessons.value.find(l => l.id === currentLessonId.value) || null
)

const paragraphs = computed(() => {
  const content = currentLesson.value?.content || ''
  return content.split('\n\n').map(p => p.trim()).filter(Boolean)
})

const nextLesson = computed(() => {
  if (!currentLesson.value) return null
  const idx = lessons.value.findIndex(l => l.id === currentLesson.value.id)
  return lessons.value[idx + 1] || null
})

const canCompleteLesson = computed(() => {
  const qs = currentLesson.value?.questions || []
  if (!qs.length) return true
  return qs.every((q, i) => quizAnswers.value[i] === q.correct)
})

// ── Helpers ──────────────────────────────────────────────────────────────
function fmtDate(d) { return d ? new Date(d).toLocaleDateString('ru-RU') : '' }

function goToLesson(id) { currentLessonId.value = id }

// ── Quiz helpers ─────────────────────────────────────────────────────────
watch(currentLessonId, () => { quizAnswers.value = {} })

function selectAnswer(qi, oi) {
  if (quizAnswers.value[qi] !== undefined) return
  quizAnswers.value = { ...quizAnswers.value, [qi]: oi }
}

function optionClass(qi, oi, q) {
  const selected = quizAnswers.value[qi]
  if (selected === undefined) return ''
  if (oi === q.correct) return 'opt-correct'
  if (oi === selected) return 'opt-wrong'
  return ''
}

function isAnswered(qi) {
  return quizAnswers.value[qi] !== undefined
}

function pickInitialLesson() {
  const first = lessons.value.find(l => !isCompleted(l.id))
  currentLessonId.value = first ? first.id : (lessons.value[0]?.id ?? null)
}

async function fetchCertificate() {
  try {
    const { data } = await api.get('/training/certificates/', {
      params: { course: assignment.value.course },
    })
    const list = data.results ?? data
    certificate.value = list.find(c => c.course === assignment.value.course) || null
  } catch { /* ignore */ }
}

// ── Actions ──────────────────────────────────────────────────────────────
async function completeCurrentLesson() {
  if (!currentLesson.value || completing.value) return
  completing.value = true
  try {
    const updated    = await store.completeLesson(aId.value, currentLesson.value.id)
    assignment.value = updated
    if (updated.status === 'completed') {
      await fetchCertificate()
    } else if (nextLesson.value) {
      currentLessonId.value = nextLesson.value.id
    }
  } finally {
    completing.value = false
  }
}

// ── Mount ────────────────────────────────────────────────────────────────
onMounted(async () => {
  loading.value = true
  try {
    assignment.value = await store.fetchAssignment(aId.value)
    pickInitialLesson()
    if (assignment.value?.status === 'completed') {
      await fetchCertificate()
    }
  } catch {
    // Assignment not found — stay on page with empty state
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
/* ── Layout ─────────────────────────────────────────────────────── */
.player-root {
  min-height: 100vh;
  background: var(--gray-50, #f9fafb);
  display: flex;
  flex-direction: column;
}

/* ── Top bar ─────────────────────────────────────────────────────── */
.player-topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 24px;
  background: #fff;
  border-bottom: 1px solid var(--gray-200, #e5e7eb);
  position: sticky;
  top: 0;
  z-index: 50;
  flex-shrink: 0;
}
.player-course-title {
  font-weight: 700;
  font-size: 15px;
  color: #111827;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.player-progress-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.player-prog-bar {
  width: 140px;
  height: 8px;
  background: var(--gray-200, #e5e7eb);
  border-radius: 4px;
  overflow: hidden;
}
.player-prog-fill {
  height: 100%;
  background: var(--primary, #6366f1);
  border-radius: 4px;
  transition: width .4s;
}
.player-prog-label { font-size: 13px; font-weight: 700; color: #374151; }

/* ── Loading center ──────────────────────────────────────────────── */
.player-center {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ── Completion screen ───────────────────────────────────────────── */
.completion-screen {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
}
.completion-icon { font-size: 72px; margin-bottom: 16px; }
.completion-title { font-size: 28px; font-weight: 800; color: #111827; margin: 0 0 8px; }
.completion-sub { font-size: 16px; color: #6b7280; margin: 0 0 28px; line-height: 1.6; }
.cert-display {
  background: #fff;
  border: 2px solid #10b981;
  border-radius: 16px;
  padding: 24px 40px;
  text-align: center;
}
.cert-display-label { font-size: 11px; text-transform: uppercase; letter-spacing: .8px; color: #10b981; font-weight: 700; margin-bottom: 8px; }
.cert-display-num   { font-size: 22px; font-weight: 800; color: #111827; font-family: monospace; }
.cert-display-date  { font-size: 13px; color: #6b7280; margin-top: 6px; }

/* ── Player body ─────────────────────────────────────────────────── */
.player-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-height: 0;
}

/* ── Lesson sidebar ──────────────────────────────────────────────── */
.lesson-sidebar {
  width: 280px;
  flex-shrink: 0;
  background: #fff;
  border-right: 1px solid var(--gray-200, #e5e7eb);
  overflow-y: auto;
  padding: 20px 0 40px;
  display: flex;
  flex-direction: column;
}
.sidebar-head {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .6px;
  color: #6b7280;
  padding: 0 20px 12px;
}
.sidebar-prog-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #6b7280;
  padding: 0 20px 6px;
}
.sidebar-prog-bar {
  height: 6px;
  background: var(--gray-100, #f3f4f6);
  margin: 0 20px 16px;
  border-radius: 3px;
  overflow: hidden;
}
.sidebar-prog-fill {
  height: 100%;
  background: var(--primary, #6366f1);
  border-radius: 3px;
  transition: width .4s;
}

.lesson-list { flex: 1; }
.lesson-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  width: 100%;
  text-align: left;
  padding: 10px 20px;
  border: none;
  background: none;
  cursor: pointer;
  transition: background .15s;
  font-size: 13px;
  color: #374151;
  line-height: 1.4;
}
.lesson-item:hover { background: var(--gray-50, #f9fafb); }
.lesson-item.lesson-active { background: var(--primary-light, #eef2ff); color: var(--primary, #6366f1); }
.lesson-item.lesson-done .lesson-check-circle { background: #10b981; color: #fff; border-color: #10b981; }

.lesson-check-circle {
  width: 24px;
  height: 24px;
  min-width: 24px;
  border-radius: 50%;
  border: 2px solid var(--gray-300, #d1d5db);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: #9ca3af;
  transition: all .2s;
}
.lesson-active .lesson-check-circle {
  border-color: var(--primary, #6366f1);
  color: var(--primary, #6366f1);
}
.lesson-item-title { flex: 1; }

/* ── Lesson main ─────────────────────────────────────────────────── */
.lesson-main {
  flex: 1;
  overflow-y: auto;
  padding: 40px 48px;
  max-width: 860px;
}
.lesson-meta {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .6px;
  color: var(--primary, #6366f1);
  margin-bottom: 12px;
}
.lesson-heading {
  font-size: 26px;
  font-weight: 800;
  color: #111827;
  margin: 0 0 16px;
  line-height: 1.3;
}
.lesson-divider {
  height: 3px;
  width: 48px;
  background: var(--primary, #6366f1);
  border-radius: 2px;
  margin-bottom: 28px;
}
.lesson-content { margin-bottom: 40px; }
.lesson-para {
  font-size: 15px;
  line-height: 1.8;
  color: #374151;
  white-space: pre-line;
  margin: 0 0 20px;
}
.lesson-para:last-child { margin-bottom: 0; }

.lesson-actions {
  display: flex;
  align-items: center;
  padding-top: 8px;
  border-top: 1px solid var(--gray-100, #f3f4f6);
}
.lesson-done-label {
  font-size: 14px;
  font-weight: 700;
  color: #10b981;
  padding: 8px 0;
}

/* ── Quiz block ──────────────────────────────────────────────────── */
.quiz-block {
  margin: 0 0 32px;
  padding: 24px 28px;
  background: #f8f9ff;
  border: 1.5px solid #e0e7ff;
  border-radius: 14px;
}
.quiz-title {
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .6px;
  color: var(--primary, #6366f1);
  margin-bottom: 20px;
}
.quiz-question { margin-bottom: 24px; }
.quiz-question:last-of-type { margin-bottom: 0; }
.quiz-q-text {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 12px;
  line-height: 1.5;
}
.quiz-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.quiz-opt {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 14px;
  background: #fff;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #374151;
  text-align: left;
  line-height: 1.45;
  transition: border-color .15s, background .15s;
}
.quiz-opt:not(:disabled):hover { border-color: var(--primary, #6366f1); background: #f5f3ff; }
.quiz-opt:disabled { cursor: default; }
.quiz-opt.opt-correct { border-color: #10b981; background: #ecfdf5; color: #065f46; }
.quiz-opt.opt-wrong   { border-color: #ef4444; background: #fef2f2; color: #991b1b; }
.quiz-opt-letter {
  width: 22px;
  min-width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: #6b7280;
}
.quiz-opt.opt-correct .quiz-opt-letter { background: #10b981; color: #fff; }
.quiz-opt.opt-wrong   .quiz-opt-letter { background: #ef4444; color: #fff; }

.quiz-explanation {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 10px;
  padding: 10px 14px;
  background: #fff;
  border-radius: 8px;
  font-size: 13px;
  color: #374151;
  line-height: 1.5;
  border: 1px solid #e5e7eb;
}
.expl-icon {
  font-size: 14px;
  font-weight: 800;
  flex-shrink: 0;
  margin-top: 1px;
}
.expl-ok  { color: #10b981; }
.expl-err { color: #ef4444; }

.quiz-hint {
  margin-top: 16px;
  font-size: 12px;
  color: #f59e0b;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}
.quiz-hint::before { content: '⚠'; }

.fade-enter-active, .fade-leave-active { transition: opacity .25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
