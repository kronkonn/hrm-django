<template>
  <div>
    <div class="topbar">
      <div class="topbar-title">Подбор персонала</div>
      <button class="btn btn-primary btn-sm" @click="openVacancyModal()">+ Вакансия</button>
    </div>

    <div class="page-container">
      <div class="tabs">
        <button class="tab-btn" :class="{active: tab==='vacancies'}"  @click="tab='vacancies'">Вакансии</button>
        <button class="tab-btn" :class="{active: tab==='kanban'}"     @click="switchKanban">Канбан кандидатов</button>
        <button class="tab-btn" :class="{active: tab==='candidates'}" @click="switchCandidates">Кандидаты</button>
      </div>

      <!-- ── Вакансии ─────────────────────────────────────────────────── -->
      <div v-if="tab === 'vacancies'">
        <div v-if="store.loading" class="card" style="padding:32px;text-align:center">
          <div class="spinner" style="margin:0 auto"></div>
        </div>
        <div v-else-if="!store.vacancies.length" class="card empty-state" style="padding:40px">
          <div class="empty-icon">📋</div>Вакансий нет
        </div>
        <div v-else class="vac-list">
          <div
            v-for="v in store.vacancies" :key="v.id"
            class="vac-card"
          >
            <div class="vac-card-top">
              <div class="vac-card-main" @click="selectVacancy(v)" style="cursor:pointer;flex:1">
                <div class="vac-title">{{ v.title }}</div>
                <div class="vac-meta-row">
                  <span class="vac-dept">{{ v.department_name }}</span>
                  <span v-if="v.salary_from || v.salary_to" class="vac-salary">
                    {{ v.salary_from ? v.salary_from.toLocaleString('ru-RU') : '' }}
                    {{ v.salary_from && v.salary_to ? ' — ' : '' }}
                    {{ v.salary_to ? v.salary_to.toLocaleString('ru-RU') : '' }}
                    {{ (v.salary_from || v.salary_to) ? ' ₽' : '' }}
                  </span>
                  <span class="vac-meta-chip">{{ employmentLabel(v.employment_type) }}</span>
                  <span v-if="v.experience_years" class="vac-meta-chip">
                    Опыт от {{ v.experience_years }} лет
                  </span>
                </div>
                <div v-if="v.required_skills && v.required_skills.length" class="vac-skills">
                  <span v-for="sk in v.required_skills.slice(0, 6)" :key="sk" class="skill-tag-sm">{{ sk }}</span>
                  <span v-if="v.required_skills.length > 6" class="skill-more">+{{ v.required_skills.length - 6 }}</span>
                </div>
              </div>
              <div class="vac-card-right">
                <span :class="vacBadge(v.status)" class="badge">{{ v.status_display }}</span>
                <div class="vac-cand-count">
                  <span class="cand-count-num">{{ v.candidate_count }}</span>
                  <span class="cand-count-label">кандидатов</span>
                </div>
              </div>
            </div>
            <div class="vac-card-footer">
              <span class="vac-date">{{ formatDate(v.published_at) }}</span>
              <div style="display:flex;gap:8px">
                <button class="btn btn-outline btn-xs" @click="openVacancyModal(v)">Изменить</button>
                <button class="btn btn-outline btn-xs" @click="selectVacancy(v)">Кандидаты →</button>
                <router-link :to="`/vacancies/${v.id}`" class="btn btn-outline btn-xs" style="text-decoration:none">Подробнее</router-link>
                <button v-if="canDelete" class="btn btn-delete-vac btn-xs" @click.stop="askDeleteVacancy(v)" title="Удалить вакансию">🗑</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Канбан ───────────────────────────────────────────────────── -->
      <div v-if="tab === 'kanban'">
        <div class="kanban-toolbar">
          <select class="form-control" style="width:240px" v-model="selectedVacancyId" @change="loadCandidates()">
            <option value="">Все вакансии</option>
            <option v-for="v in store.vacancies" :key="v.id" :value="v.id">{{ v.title }}</option>
          </select>
          <button class="btn btn-outline btn-sm" @click="showCandidateModal = true">+ Кандидат</button>
          <button v-if="selectedVacancyId" class="btn btn-ai btn-sm"
                  :disabled="store.analyzing" @click="runAnalyzeAll">
            <span v-if="store.analyzing" class="spinner-xs"></span>
            <span v-else>✦</span>
            {{ store.analyzing ? 'Анализируем...' : 'AI Анализ' }}
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
              <div class="card-vacancy">{{ c.vacancy_title }}</div>
              <div v-if="c.extracted_skills && c.extracted_skills.length" class="card-skills">
                <span v-for="sk in c.extracted_skills.slice(0,3)" :key="sk" class="skill-tag-sm">{{ sk }}</span>
              </div>
              <div class="card-footer">
                <span class="rating-stars">{{ '★'.repeat(c.rating) }}{{ '☆'.repeat(5 - c.rating) }}</span>
                <span v-if="c.ml_hiring_probability != null" class="prob-badge">
                  {{ mlPercent(c.ml_hiring_probability) }} найм
                </span>
              </div>
              <div v-if="stage.value !== 'hired' && stage.value !== 'rejected'"
                   style="margin-top:8px;display:flex;gap:4px">
                <button class="btn btn-outline btn-xs" style="flex:1"
                        @click.stop="advance(c)">→ Следующий этап</button>
                <button class="btn btn-reject-xs"
                        @click.stop="rejectWithConfirm(c)" title="Отклонить">✕</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Кандидаты ─────────────────────────────────────────────── -->
      <div v-if="tab === 'candidates'">
        <div class="list-toolbar">
          <select class="form-control" style="width:220px" v-model="listFilter" @change="loadAllCandidates">
            <option value="">Все вакансии</option>
            <option v-for="v in store.vacancies" :key="v.id" :value="v.id">{{ v.title }}</option>
          </select>
          <div class="sort-group">
            <span class="sort-label">Сортировка:</span>
            <button class="sort-btn" :class="{ active: sortField==='ai_score' && sortDir==='desc' }" @click="setSort('ai_score','desc')">AI Score ↓</button>
            <button class="sort-btn" :class="{ active: sortField==='ai_score' && sortDir==='asc'  }" @click="setSort('ai_score','asc')">AI Score ↑</button>
            <button class="sort-btn" :class="{ active: sortField==='applied_at' && sortDir==='desc'}" @click="setSort('applied_at','desc')">Новые</button>
            <button class="sort-btn" :class="{ active: sortField==='applied_at' && sortDir==='asc' }" @click="setSort('applied_at','asc')">Старые</button>
          </div>
        </div>
        <div class="card">
          <div v-if="store.loading" class="loading"><div class="spinner"></div></div>
          <div v-else class="table-wrap">
            <table class="cand-table">
              <thead>
                <tr>
                  <th>Имя</th>
                  <th>Email</th>
                  <th>Вакансия</th>
                  <th>Этап</th>
                  <th class="th-score">AI Score</th>
                  <th>Дата</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!filteredSortedCandidates.length">
                  <td colspan="7" class="empty-cell">Кандидатов нет</td>
                </tr>
                <tr v-for="(c, idx) in filteredSortedCandidates" :key="c.id"
                    class="clickable-row" @click="openDetail(c)">
                  <td>
                    <div style="display:flex;align-items:center;gap:8px">
                      <span class="rank-num">#{{ idx + 1 }}</span>
                      <span style="font-weight:600">{{ c.full_name }}</span>
                    </div>
                  </td>
                  <td class="text-sm text-gray">{{ c.email }}</td>
                  <td class="text-sm">{{ c.vacancy_title }}</td>
                  <td><span class="badge" :class="stageBadge(c.stage)">{{ c.stage_display }}</span></td>
                  <td>
                    <span v-if="c.ai_score != null" class="ai-badge" :class="aiBadgeClass(c.ai_score)">
                      ✦ {{ aiPercent(c.ai_score) }}
                    </span>
                    <span v-else class="text-gray text-sm">—</span>
                  </td>
                  <td class="text-sm text-gray">{{ formatDate(c.applied_at) }}</td>
                  <td @click.stop>
                    <button
                      v-if="c.stage !== 'rejected'"
                      class="btn btn-reject-xs"
                      @click="rejectFromList(c)"
                      title="Отклонить кандидата"
                    >Отклонить</button>
                    <span v-else class="badge badge-gray" style="font-size:11px">Отклонён</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Vacancy modal (create / edit) ──────────────────────────── -->
    <Teleport to="body">
      <div v-if="showVacancyModal" class="modal-overlay" @click.self="closeVacancyModal">
        <div class="modal modal-xl">
          <div class="modal-header">
            <h3>{{ editingVacancy ? 'Редактировать вакансию' : 'Новая вакансия' }}</h3>
            <button class="btn btn-icon" @click="closeVacancyModal">✕</button>
          </div>
          <div class="modal-body vac-form">
            <!-- Row 1 -->
            <div class="form-group form-full">
              <label class="form-label">Название вакансии *</label>
              <input v-model="vacForm.title" class="form-control" placeholder="Например: Senior Python Developer" />
            </div>
            <!-- Row 2 -->
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">Отдел</label>
                <select v-model="vacForm.department" class="form-control">
                  <option value="">— Выберите —</option>
                  <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">Тип занятости</label>
                <select v-model="vacForm.employment_type" class="form-control">
                  <option value="full_time">Полная занятость</option>
                  <option value="part_time">Частичная занятость</option>
                  <option value="remote">Удалённая работа</option>
                  <option value="hybrid">Гибрид</option>
                  <option value="contract">Контракт</option>
                  <option value="internship">Стажировка</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">Статус</label>
                <select v-model="vacForm.status" class="form-control">
                  <option value="open">Открыта</option>
                  <option value="on_hold">Приостановлена</option>
                  <option value="closed">Закрыта</option>
                </select>
              </div>
            </div>
            <!-- Row 3 -->
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">Зарплата от, ₽</label>
                <input v-model.number="vacForm.salary_from" type="number" class="form-control" placeholder="80 000" />
              </div>
              <div class="form-group">
                <label class="form-label">Зарплата до, ₽</label>
                <input v-model.number="vacForm.salary_to" type="number" class="form-control" placeholder="150 000" />
              </div>
              <div class="form-group">
                <label class="form-label">Требуемый опыт (лет)</label>
                <input v-model.number="vacForm.experience_years" type="number" min="0" max="20" class="form-control" placeholder="3" />
              </div>
            </div>
            <!-- Skills tags -->
            <div class="form-group form-full">
              <label class="form-label">Требуемые навыки</label>
              <div class="tags-input" @click="focusSkillInput">
                <span v-for="sk in vacForm.required_skills" :key="sk" class="skill-chip">
                  {{ sk }}<button type="button" class="chip-remove" @click.stop="removeSk(sk)">×</button>
                </span>
                <input
                  ref="skillInputRef"
                  v-model="skillInput"
                  class="tags-inner-input"
                  placeholder="Введите навык и нажмите Enter..."
                  @keydown.enter.prevent="addSkill"
                  @keydown.188.prevent="addSkill"
                  @keydown.tab.prevent="addSkill"
                />
              </div>
              <div class="form-hint">Enter или Tab — добавить тег, × — удалить</div>
            </div>
            <!-- Textareas -->
            <div class="form-group form-full">
              <label class="form-label">Обязанности</label>
              <textarea v-model="vacForm.responsibilities" class="form-control" rows="4"
                        placeholder="Опишите задачи и обязанности сотрудника..."></textarea>
            </div>
            <div class="form-group form-full">
              <label class="form-label">Требования к кандидату</label>
              <textarea v-model="vacForm.requirements" class="form-control" rows="4"
                        placeholder="Обязательные и желательные требования..."></textarea>
            </div>
            <div class="form-group form-full">
              <label class="form-label">Условия работы</label>
              <textarea v-model="vacForm.conditions" class="form-control" rows="3"
                        placeholder="Зарплата, график, бонусы, ДМС, обучение..."></textarea>
            </div>
            <div class="form-group form-full">
              <label class="form-label">Описание компании / вакансии</label>
              <textarea v-model="vacForm.description" class="form-control" rows="3"
                        placeholder="Краткое описание компании и роли..."></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-outline" @click="closeVacancyModal">Отмена</button>
            <button class="btn btn-primary" @click="saveVacancy">
              {{ editingVacancy ? 'Сохранить' : 'Создать вакансию' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ── Candidate create modal ─────────────────────────────────── -->
    <Teleport to="body">
      <div v-if="showCandidateModal" class="modal-overlay" @click.self="showCandidateModal = false">
        <div class="modal modal-lg">
          <div class="modal-header">
            <h3>Новый кандидат</h3>
            <button class="btn btn-icon" @click="showCandidateModal = false">✕</button>
          </div>
          <div class="modal-body">
            <div class="grid-2">
              <div class="form-group">
                <label class="form-label">Фамилия *</label>
                <input v-model="candForm.last_name" class="form-control" />
              </div>
              <div class="form-group">
                <label class="form-label">Имя *</label>
                <input v-model="candForm.first_name" class="form-control" />
              </div>
            </div>
            <div class="grid-2">
              <div class="form-group">
                <label class="form-label">Email *</label>
                <input v-model="candForm.email" type="email" class="form-control" />
              </div>
              <div class="form-group">
                <label class="form-label">Телефон</label>
                <input v-model="candForm.phone" type="tel" class="form-control" placeholder="+7 (999) 000-00-00" />
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">Вакансия *</label>
              <select v-model="candForm.vacancy" class="form-control">
                <option value="">— Выберите —</option>
                <option v-for="v in store.vacancies" :key="v.id" :value="v.id">{{ v.title }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Текст резюме</label>
              <textarea v-model="candForm.resume_text" class="form-control" rows="7"
                        placeholder="Вставьте текст резюме кандидата. AI автоматически извлечёт навыки и оценит соответствие вакансии..."></textarea>
              <div class="form-hint">После сохранения запустится автоматический AI-анализ</div>
            </div>
            <div class="form-group">
              <label class="form-label">Сопроводительное письмо</label>
              <textarea v-model="candForm.cover_letter" class="form-control" rows="3"
                        placeholder="Необязательно — мотивационное письмо кандидата..."></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-outline" @click="showCandidateModal = false">Отмена</button>
            <button class="btn btn-primary" :disabled="savingCandidate" @click="saveCandidate">
              <span v-if="savingCandidate" class="spinner-xs"></span>
              {{ savingCandidate ? 'Сохранение...' : 'Добавить и анализировать' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ── Confirmation dialog ────────────────────────────────────── -->
    <Teleport to="body">
      <div v-if="confirmDialog.show" class="modal-overlay" @click.self="cancelConfirm">
        <div class="modal confirm-modal">
          <div class="modal-header">
            <h3 :class="confirmDialog.type === 'hire' ? 'confirm-title-hire' : 'confirm-title-reject'">
              {{ confirmDialog.type === 'hire' ? 'Принять кандидата?' : 'Отклонить кандидата?' }}
            </h3>
          </div>
          <div class="modal-body">
            <p class="confirm-text">
              <template v-if="confirmDialog.type === 'hire'">
                Вы принимаете <strong>{{ confirmDialog.candidate?.full_name }}</strong>.
                Решение будет сохранено и использовано для обучения AI модели.
              </template>
              <template v-else>
                Вы отклоняете <strong>{{ confirmDialog.candidate?.full_name }}</strong>.
                Решение будет сохранено и использовано для обучения AI модели.
              </template>
            </p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-outline" @click="cancelConfirm">Отмена</button>
            <button
              :class="confirmDialog.type === 'hire' ? 'btn btn-hire' : 'btn btn-reject'"
              @click="doConfirm"
            >Подтвердить</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ── Delete vacancy dialog ─────────────────────────────────────── -->
    <Teleport to="body">
      <div v-if="deleteDialog.show" class="modal-overlay" @click.self="cancelDelete">
        <div class="modal confirm-modal">
          <div class="modal-header">
            <h3 class="confirm-title-reject">Удалить вакансию?</h3>
          </div>
          <div class="modal-body">
            <p class="confirm-text">
              Вакансия <strong>{{ deleteDialog.vacancy?.title }}</strong> будет удалена.<br>
              Удаление возможно только если все кандидаты отклонены.
            </p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-outline" @click="cancelDelete">Отмена</button>
            <button class="btn btn-reject" @click="confirmDeleteVacancy">Удалить</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ── Toast notification ──────────────────────────────────────── -->
    <Teleport to="body">
      <div v-if="toast.show" class="toast-notify">{{ toast.message }}</div>
    </Teleport>

    <!-- ── Candidate detail modal ──────────────────────────────────── -->
    <Teleport to="body">
      <div v-if="detailCandidate" class="modal-overlay" @click.self="detailCandidate = null">
        <div class="modal modal-xl">
          <div class="modal-header">
            <h3>{{ detailCandidate.full_name }}</h3>
            <div style="display:flex;align-items:center;gap:10px">
              <button class="btn btn-ai btn-sm" :disabled="analyzeLoading" @click="analyzeSingle">
                <span v-if="analyzeLoading" class="spinner-xs"></span>
                <span v-else>✦</span>
                {{ analyzeLoading ? '...' : 'AI Анализ' }}
              </button>
              <button class="btn btn-icon" @click="detailCandidate = null">✕</button>
            </div>
          </div>
          <div class="modal-body detail-body">
            <!-- Left -->
            <div class="detail-left">
              <div class="detail-section">
                <div class="detail-label">Вакансия</div>
                <div class="detail-value">{{ detailCandidate.vacancy_title }}</div>
              </div>
              <div class="detail-section">
                <div class="detail-label">Этап</div>
                <div class="detail-value">
                  <span class="badge" :class="stageBadge(detailCandidate.stage)">{{ detailCandidate.stage_display }}</span>
                </div>
              </div>
              <div class="detail-section">
                <div class="detail-label">Рейтинг</div>
                <div class="detail-value rating-big">
                  <span v-for="i in 5" :key="i" :style="{ color: i <= detailCandidate.rating ? '#f59e0b' : '#e5e7eb' }">★</span>
                  <span style="font-size:12px;color:#6b7280;margin-left:4px">{{ detailCandidate.rating }}/5</span>
                </div>
              </div>
              <div class="detail-section">
                <div class="detail-label">Email</div>
                <div class="detail-value">{{ detailCandidate.email }}</div>
              </div>
              <div class="detail-section">
                <div class="detail-label-row">
                  <span class="detail-label">Резюме</span>
                  <a
                    v-if="detailCandidate.resume"
                    :href="resumeUrl(detailCandidate.id)"
                    target="_blank"
                    rel="noopener"
                    class="btn-resume-open"
                  >📎 Открыть резюме</a>
                  <span v-else class="btn-resume-disabled" title="Файл не прикреплён">📎 Открыть резюме</span>
                </div>
                <div v-if="detailCandidate.resume_text" class="resume-text">{{ detailCandidate.resume_text }}</div>
                <div v-else class="resume-empty">Текст не добавлен</div>
              </div>
              <div v-if="detailCandidate.cover_letter" class="detail-section">
                <div class="detail-label">Сопроводительное письмо</div>
                <div class="cover-letter">{{ detailCandidate.cover_letter }}</div>
              </div>
            </div>
            <!-- Right: AI -->
            <div class="detail-right">
              <div class="ai-panel" :class="detailCandidate.ai_score != null ? 'ai-panel--active' : 'ai-panel--empty'">
                <div class="ai-panel-title">✦ AI-ранжирование</div>
                <template v-if="detailCandidate.ai_score != null">
                  <div class="ai-score-row">
                    <div class="ai-score-label">AI Score</div>
                    <div class="ai-score-bar-wrap">
                      <div class="ai-score-bar"
                           :style="{ width: aiPercent(detailCandidate.ai_score), background: aiColor(detailCandidate.ai_score) }"></div>
                    </div>
                    <div class="ai-score-val" :style="{ color: aiColor(detailCandidate.ai_score) }">
                      {{ aiPercent(detailCandidate.ai_score) }}
                    </div>
                  </div>
                  <div class="ai-score-row">
                    <div class="ai-score-label">Вероятность найма</div>
                    <div class="ai-score-bar-wrap">
                      <div class="ai-score-bar"
                           :style="{ width: mlPercent(detailCandidate.ml_hiring_probability), background: aiColor(detailCandidate.ml_hiring_probability) }"></div>
                    </div>
                    <div class="ai-score-val" :style="{ color: aiColor(detailCandidate.ml_hiring_probability) }">
                      {{ mlPercent(detailCandidate.ml_hiring_probability) }}
                    </div>
                  </div>
                  <div v-if="detailCandidate.extracted_skills && detailCandidate.extracted_skills.length" class="ai-skills">
                    <div class="ai-sub-title">Ключевые навыки</div>
                    <div class="skills-wrap">
                      <span v-for="sk in detailCandidate.extracted_skills" :key="sk" class="skill-tag">{{ sk }}</span>
                    </div>
                  </div>
                  <div v-if="detailCandidate.ai_comment" class="ai-comment">
                    <div class="ai-sub-title">Вывод AI</div>
                    <p>{{ detailCandidate.ai_comment }}</p>
                  </div>
                </template>
                <div v-else class="ai-empty-hint">Нажмите «AI Анализ» для оценки кандидата</div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-outline" @click="detailCandidate = null">Закрыть</button>
            <button v-if="detailCandidate.stage !== 'hired' && detailCandidate.stage !== 'rejected'"
                    class="btn btn-primary" @click="advanceDetail">→ Следующий этап</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRecruitmentStore } from '@/stores/recruitment'
import { useAuthStore } from '@/stores/auth'
import api from '@/api/index'
import { getResumeUrl } from '@/api/recruitment'

const store = useRecruitmentStore()
const auth  = useAuthStore()
const canDelete = computed(() => auth.isHRManager || auth.isAdmin)
const tab = ref('vacancies')
const selectedVacancyId = ref('')
const showVacancyModal = ref(false)
const showCandidateModal = ref(false)
const detailCandidate = ref(null)
const analyzeLoading = ref(false)
const savingCandidate = ref(false)
const editingVacancy = ref(null)
const skillInput = ref('')
const skillInputRef = ref(null)
const departments = ref([])

const listFilter = ref('')
const sortField  = ref('ai_score')
const sortDir    = ref('desc')

const confirmDialog = ref({ show: false, type: '', candidate: null })
const deleteDialog  = ref({ show: false, vacancy: null })
const toast = ref({ show: false, message: '' })
let _toastTimer = null

const emptyVacForm = () => ({
  title: '', department: '', employment_type: 'full_time', status: 'open',
  salary_from: null, salary_to: null, experience_years: null,
  required_skills: [],
  requirements: '', responsibilities: '', conditions: '', description: '',
})
const vacForm  = ref(emptyVacForm())
const candForm = ref({ first_name: '', last_name: '', email: '', phone: '', vacancy: '', resume_text: '', cover_letter: '' })

const stages = [
  { value: 'new',       label: 'Новые' },
  { value: 'screening', label: 'Скрининг' },
  { value: 'interview', label: 'Интервью' },
  { value: 'offer',     label: 'Оффер' },
  { value: 'hired',     label: 'Принят' },
  { value: 'rejected',  label: 'Отклонён' },
]

// ── Helpers ───────────────────────────────────────────────────────────────
function formatDate(d) { return d ? new Date(d).toLocaleDateString('ru-RU') : '—' }
function resumeUrl(id) { return getResumeUrl(id) }
function vacBadge(s)   { return { open: 'badge-green', closed: 'badge-gray', on_hold: 'badge-yellow' }[s] || 'badge-gray' }
function employmentLabel(t) {
  return { full_time: 'Полная', part_time: 'Частичная', remote: 'Удалённая', hybrid: 'Гибрид', contract: 'Контракт', internship: 'Стажировка' }[t] || t
}
function stageBadge(s) {
  return { new: 'badge-gray', screening: 'badge-yellow', interview: 'badge-blue',
           offer: 'badge-purple', hired: 'badge-green', rejected: 'badge-red' }[s] || 'badge-gray'
}
function aiPercent(score) { return Math.round(parseFloat(score) * 100) + '%' }
function mlPercent(prob)  { return Math.round(parseFloat(prob)  * 100) + '%' }
function aiColor(val) {
  const v = parseFloat(val)
  return v >= 0.7 ? '#10b981' : v >= 0.4 ? '#f59e0b' : '#ef4444'
}
function aiBadgeClass(score) {
  const v = parseFloat(score)
  return v >= 0.7 ? 'ai-badge--green' : v >= 0.4 ? 'ai-badge--yellow' : 'ai-badge--red'
}

function candidatesByStage(stage) {
  return store.candidates.filter(c => c.stage === stage).slice()
    .sort((a, b) => {
      const sa = a.ai_score != null ? parseFloat(a.ai_score) : -1
      const sb = b.ai_score != null ? parseFloat(b.ai_score) : -1
      return sb - sa
    })
}

const filteredSortedCandidates = computed(() => {
  let list = store.candidates.slice()
  if (listFilter.value) list = list.filter(c => String(c.vacancy) === String(listFilter.value))
  list.sort((a, b) => {
    if (sortField.value === 'ai_score') {
      const sa = a.ai_score != null ? parseFloat(a.ai_score) : -1
      const sb = b.ai_score != null ? parseFloat(b.ai_score) : -1
      return sortDir.value === 'desc' ? sb - sa : sa - sb
    } else {
      const da = a.applied_at ? new Date(a.applied_at).getTime() : 0
      const db = b.applied_at ? new Date(b.applied_at).getTime() : 0
      return sortDir.value === 'desc' ? db - da : da - db
    }
  })
  return list
})

function setSort(field, dir) { sortField.value = field; sortDir.value = dir }

// ── Skills tag input ──────────────────────────────────────────────────────
function focusSkillInput() { skillInputRef.value?.focus() }
function addSkill() {
  const val = skillInput.value.trim().replace(/,$/, '')
  if (val && !vacForm.value.required_skills.includes(val)) {
    vacForm.value.required_skills.push(val)
  }
  skillInput.value = ''
}
function removeSk(sk) {
  vacForm.value.required_skills = vacForm.value.required_skills.filter(s => s !== sk)
}

// ── Vacancy modal ─────────────────────────────────────────────────────────
function openVacancyModal(vacancy = null) {
  editingVacancy.value = vacancy
  skillInput.value = ''
  if (vacancy) {
    vacForm.value = {
      title: vacancy.title,
      department: vacancy.department,
      employment_type: vacancy.employment_type || 'full_time',
      status: vacancy.status,
      salary_from: vacancy.salary_from,
      salary_to: vacancy.salary_to,
      experience_years: vacancy.experience_years,
      required_skills: vacancy.required_skills ? [...vacancy.required_skills] : [],
      requirements: vacancy.requirements || '',
      responsibilities: vacancy.responsibilities || '',
      conditions: vacancy.conditions || '',
      description: vacancy.description || '',
    }
  } else {
    vacForm.value = emptyVacForm()
  }
  showVacancyModal.value = true
}
function closeVacancyModal() {
  showVacancyModal.value = false
  editingVacancy.value = null
}
async function saveVacancy() {
  if (skillInput.value.trim()) addSkill()
  if (editingVacancy.value) {
    await store.updateVacancy(editingVacancy.value.id, vacForm.value)
  } else {
    await store.createVacancy(vacForm.value)
  }
  closeVacancyModal()
}

// ── Candidate actions ─────────────────────────────────────────────────────
async function saveCandidate() {
  savingCandidate.value = true
  try {
    const newCand = await store.createCandidate(candForm.value)
    showCandidateModal.value = false
    candForm.value = { first_name: '', last_name: '', email: '', phone: '', vacancy: '', resume_text: '', cover_letter: '' }
    await loadCandidates()
    // Auto-analyze after save
    if (newCand && newCand.id) {
      try {
        const analyzed = await store.analyzeCandidate(newCand.id)
        // Update in list if detail is open
        if (detailCandidate.value?.id === analyzed.id) detailCandidate.value = { ...analyzed }
      } catch {}
    }
  } finally {
    savingCandidate.value = false
  }
}

function selectVacancy(v) {
  selectedVacancyId.value = v.id
  tab.value = 'kanban'
  loadCandidates()
}
function switchKanban() { tab.value = 'kanban'; loadCandidates() }
async function switchCandidates() { tab.value = 'candidates'; await loadAllCandidates() }
async function loadAllCandidates() {
  const params = listFilter.value ? { vacancy: listFilter.value } : {}
  await store.fetchCandidates(params)
}
async function loadCandidates() {
  const params = selectedVacancyId.value ? { vacancy: selectedVacancyId.value } : {}
  await store.fetchCandidates(params)
}
function _nextStageName(stage) {
  const seq = ['new', 'screening', 'interview', 'offer', 'hired']
  const idx = seq.indexOf(stage)
  return idx >= 0 && idx < seq.length - 1 ? seq[idx + 1] : null
}

function showToast(message) {
  if (_toastTimer) clearTimeout(_toastTimer)
  toast.value = { show: true, message }
  _toastTimer = setTimeout(() => { toast.value.show = false }, 4000)
}

function _handleRetrained(data) {
  if (data?.model_retrained) showToast('🤖 AI модель обновлена на основе новых данных')
  if (detailCandidate.value?.id === data?.id) detailCandidate.value = { ...data }
}

async function advance(candidate) {
  if (_nextStageName(candidate.stage) === 'hired') {
    confirmDialog.value = { show: true, type: 'hire', candidate }
  } else {
    const data = await store.advanceCandidate(candidate.id)
    _handleRetrained(data)
  }
}

function rejectWithConfirm(candidate) {
  confirmDialog.value = { show: true, type: 'reject', candidate }
}

function cancelConfirm() {
  confirmDialog.value = { show: false, type: '', candidate: null }
}

async function doConfirm() {
  const { type, candidate } = confirmDialog.value
  confirmDialog.value = { show: false, type: '', candidate: null }
  let data
  if (type === 'hire') {
    data = await store.advanceCandidate(candidate.id)
  } else {
    data = await store.rejectCandidate(candidate.id)
  }
  _handleRetrained(data)
}

async function advanceDetail() {
  const next = _nextStageName(detailCandidate.value.stage)
  if (next === 'hired') {
    confirmDialog.value = { show: true, type: 'hire', candidate: detailCandidate.value }
  } else {
    const updated = await store.advanceCandidate(detailCandidate.value.id)
    detailCandidate.value = updated
    _handleRetrained(updated)
  }
}
function openDetail(c) { detailCandidate.value = { ...c } }
async function analyzeSingle() {
  if (!detailCandidate.value) return
  analyzeLoading.value = true
  try {
    const updated = await store.analyzeCandidate(detailCandidate.value.id)
    detailCandidate.value = { ...updated }
  } finally { analyzeLoading.value = false }
}
async function runAnalyzeAll() {
  if (!selectedVacancyId.value) return
  await store.analyzeVacancyAll(selectedVacancyId.value)
}

// ── Delete vacancy ────────────────────────────────────────────────────────
function askDeleteVacancy(vacancy) {
  deleteDialog.value = { show: true, vacancy }
}
function cancelDelete() {
  deleteDialog.value = { show: false, vacancy: null }
}
async function confirmDeleteVacancy() {
  const vacancy = deleteDialog.value.vacancy
  deleteDialog.value = { show: false, vacancy: null }
  try {
    await store.deleteVacancy(vacancy.id)
    showToast('Вакансия удалена')
  } catch (err) {
    const msg = err.response?.data?.detail || 'Ошибка при удалении вакансии'
    showToast(msg)
  }
}

// ── Reject candidate from list tab ───────────────────────────────────────
function rejectFromList(candidate) {
  confirmDialog.value = { show: true, type: 'reject', candidate }
}

async function loadDepartments() {
  try {
    const { data } = await api.get('/employees/departments/')
    departments.value = data.results ?? data
  } catch {}
}

onMounted(async () => {
  await Promise.all([store.fetchVacancies(), loadDepartments()])
  await loadCandidates()
})
</script>

<style scoped>
/* ── Vacancy cards ─────────────────────────────────────────────────── */
.vac-list { display: flex; flex-direction: column; gap: 12px; }

.vac-card {
  background: #fff;
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  padding: 18px 20px 14px;
  transition: box-shadow .15s, border-color .15s;
}
.vac-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.08); border-color: #c7d2fe; }

.vac-card-top { display: flex; gap: 16px; align-items: flex-start; }
.vac-card-main { flex: 1; min-width: 0; }
.vac-card-right { display: flex; flex-direction: column; align-items: flex-end; gap: 8px; flex-shrink: 0; }

.vac-title { font-size: 15px; font-weight: 700; color: #111827; margin-bottom: 6px; }
.vac-card-main:hover .vac-title { color: #4f46e5; }

.vac-meta-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.vac-dept { font-size: 13px; color: #6b7280; font-weight: 500; }
.vac-salary { font-size: 13px; font-weight: 700; color: #059669; }
.vac-meta-chip {
  font-size: 11px;
  background: #f3f4f6;
  color: #374151;
  padding: 2px 8px;
  border-radius: 6px;
  white-space: nowrap;
}

.vac-skills { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 2px; }
.skill-more { font-size: 11px; color: #9ca3af; padding: 2px 4px; }

.vac-cand-count { text-align: right; }
.cand-count-num { font-size: 20px; font-weight: 800; color: #4f46e5; display: block; }
.cand-count-label { font-size: 10px; color: #9ca3af; text-transform: uppercase; letter-spacing: .4px; }

.vac-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--gray-100);
}
.vac-date { font-size: 12px; color: #9ca3af; }

/* ── Skill tags shared ─────────────────────────────────────────────── */
.skill-tag-sm {
  font-size: 11px;
  background: #ede9fe;
  color: #6d28d9;
  padding: 2px 8px;
  border-radius: 8px;
  white-space: nowrap;
}

/* ── Vacancy form modal ────────────────────────────────────────────── */
.modal-xl { max-width: 780px; width: 100%; }

.vac-form { display: flex; flex-direction: column; gap: 0; }
.form-full { width: 100%; }
.form-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 0; }
@media (max-width: 640px) { .form-row { grid-template-columns: 1fr; } }

.form-hint { font-size: 11px; color: #9ca3af; margin-top: 4px; }

/* Tags input */
.tags-input {
  min-height: 42px;
  padding: 6px 10px;
  border: 1px solid var(--gray-200);
  border-radius: 8px;
  background: #fff;
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  align-items: center;
  cursor: text;
  transition: border-color .15s;
}
.tags-input:focus-within { border-color: var(--primary); outline: none; }

.skill-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px 3px 10px;
  background: #ede9fe;
  color: #5b21b6;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
}
.chip-remove {
  background: none;
  border: none;
  color: #8b5cf6;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  padding: 0 1px;
}
.chip-remove:hover { color: #ef4444; }

.tags-inner-input {
  border: none;
  outline: none;
  font-size: 13px;
  color: #374151;
  flex: 1;
  min-width: 160px;
  padding: 2px 0;
  background: transparent;
}

/* ── Candidate form ────────────────────────────────────────────────── */
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

/* ── AI button ─────────────────────────────────────────────────────── */
.btn-ai {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff; border: none;
  display: inline-flex; align-items: center; gap: 5px;
  font-weight: 600; transition: opacity .15s;
}
.btn-ai:hover:not(:disabled) { opacity: .88; }
.btn-ai:disabled { opacity: .55; cursor: default; }

.spinner-xs {
  display: inline-block; width: 12px; height: 12px;
  border: 2px solid rgba(255,255,255,.35);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Kanban ────────────────────────────────────────────────────────── */
.kanban-toolbar { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.kanban { display: flex; gap: 12px; overflow-x: auto; padding-bottom: 12px; align-items: flex-start; }
.kanban-col { flex: 0 0 200px; background: var(--gray-50, #f9fafb); border-radius: 10px; padding: 12px; }
.kanban-col-title {
  font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .6px;
  color: var(--gray-500); margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;
}
.col-count { background: #e5e7eb; padding: 1px 7px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.kanban-empty { font-size: 12px; color: #9ca3af; padding: 8px 0; }
.kanban-card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 10px; margin-bottom: 8px;
  cursor: pointer; transition: box-shadow .15s, border-color .15s;
}
.kanban-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,.1); border-color: #c7d2fe; }
.card-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 4px; margin-bottom: 3px; }
.cand-name { font-size: 13px; font-weight: 600; color: #111; line-height: 1.3; }
.source-icon { font-size: 12px; cursor: default; }
.card-vacancy { font-size: 11px; color: #6b7280; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.card-skills { display: flex; flex-wrap: wrap; gap: 3px; margin-bottom: 6px; }
.card-footer { display: flex; align-items: center; justify-content: space-between; font-size: 11px; margin-top: 2px; }
.rating-stars { color: #f59e0b; letter-spacing: -1px; }
.prob-badge { font-size: 10px; color: #6b7280; background: #f3f4f6; padding: 1px 5px; border-radius: 6px; }

/* ── AI badge ──────────────────────────────────────────────────────── */
.ai-badge { font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 8px; white-space: nowrap; flex-shrink: 0; }
.ai-badge--green  { background: #d1fae5; color: #065f46; }
.ai-badge--yellow { background: #fef3c7; color: #92400e; }
.ai-badge--red    { background: #fee2e2; color: #991b1b; }

/* ── Table ─────────────────────────────────────────────────────────── */
.list-toolbar { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }
.sort-group { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.sort-label { font-size: 12px; color: #6b7280; margin-right: 4px; white-space: nowrap; }
.sort-btn {
  background: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 6px;
  padding: 5px 12px; font-size: 12px; color: #374151; cursor: pointer; white-space: nowrap;
  transition: background .12s, border-color .12s, color .12s;
}
.sort-btn:hover { background: #e9d5ff; border-color: #c4b5fd; color: #5b21b6; }
.sort-btn.active { background: #ede9fe; border-color: #8b5cf6; color: #5b21b6; font-weight: 600; }
.cand-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.cand-table th {
  text-align: left; padding: 10px 14px; border-bottom: 2px solid var(--gray-200);
  color: #6b7280; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .5px;
}
.cand-table td { padding: 11px 14px; border-bottom: 1px solid var(--gray-100); vertical-align: middle; }
.cand-table tr:last-child td { border-bottom: none; }
.th-score { width: 110px; }
.rank-num { display: inline-block; min-width: 24px; font-size: 11px; font-weight: 700; color: #9ca3af; }
.empty-cell { text-align: center; padding: 32px; color: #9ca3af; }
.clickable-row { cursor: pointer; }
.clickable-row:hover td { background: var(--gray-50); }

/* ── Detail modal ──────────────────────────────────────────────────── */
.modal-lg { max-width: 700px; width: 100%; }
.detail-body { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
@media (max-width: 600px) { .detail-body { grid-template-columns: 1fr; } }
.detail-section { margin-bottom: 14px; }
.detail-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .5px; color: #6b7280; margin-bottom: 3px; }
.detail-label-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.detail-label-row .detail-label { margin-bottom: 0; }
.btn-resume-open { font-size: 12px; font-weight: 500; color: #6366f1; text-decoration: none; background: #e0e7ff; border-radius: 6px; padding: 3px 10px; transition: background 0.15s; white-space: nowrap; }
.btn-resume-open:hover { background: #c7d2fe; }
.btn-resume-disabled { font-size: 12px; font-weight: 500; color: #94a3b8; background: #f1f5f9; border-radius: 6px; padding: 3px 10px; cursor: not-allowed; white-space: nowrap; }
.resume-empty { font-size: 12px; color: #94a3b8; font-style: italic; }
.detail-value { font-size: 14px; color: #111; }
.rating-big { font-size: 18px; display: flex; align-items: center; }
.resume-text {
  font-size: 12px; color: #374151; line-height: 1.6;
  background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px;
  padding: 10px; max-height: 200px; overflow-y: auto; white-space: pre-wrap;
}
.cover-letter {
  font-size: 12px; color: #374151; line-height: 1.6;
  background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px;
  padding: 10px; max-height: 100px; overflow-y: auto;
}

/* ── AI panel ──────────────────────────────────────────────────────── */
.ai-panel { background: #fafafa; border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px; }
.ai-panel--active { border-color: #c7d2fe; background: #f5f3ff; }
.ai-panel-title { font-size: 13px; font-weight: 700; color: #4f46e5; margin-bottom: 14px; letter-spacing: .3px; }
.ai-score-row { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.ai-score-label { font-size: 11px; color: #6b7280; width: 115px; flex-shrink: 0; }
.ai-score-bar-wrap { flex: 1; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; }
.ai-score-bar { height: 100%; border-radius: 4px; transition: width .5s ease; }
.ai-score-val { font-size: 13px; font-weight: 700; width: 36px; text-align: right; flex-shrink: 0; }
.ai-sub-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .5px; color: #6b7280; margin-bottom: 6px; }
.ai-skills { margin-bottom: 12px; }
.skills-wrap { display: flex; flex-wrap: wrap; gap: 5px; }
.skill-tag { font-size: 11px; background: #ede9fe; color: #5b21b6; padding: 3px 10px; border-radius: 10px; font-weight: 500; }
.ai-comment p { font-size: 12px; color: #374151; line-height: 1.6; margin: 0; background: #fff; border: 1px solid #ddd6fe; border-radius: 6px; padding: 10px; }
.ai-empty-hint { font-size: 13px; color: #9ca3af; text-align: center; padding: 24px 0; }

/* ── Extra badges ──────────────────────────────────────────────────── */
.badge-blue   { background: rgba(59,130,246,.15);  color: #1d4ed8; }
.badge-purple { background: rgba(139,92,246,.15);  color: #6d28d9; }
.badge-red    { background: rgba(239,68,68,.15);   color: #b91c1c; }
.btn-xs { font-size: 11px; padding: 4px 10px; }

/* ── Delete vacancy button ─────────────────────────────────────────── */
.btn-delete-vac {
  background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5;
  cursor: pointer; font-size: 13px; padding: 4px 8px; border-radius: 6px;
  transition: background .12s; line-height: 1;
}
.btn-delete-vac:hover { background: #fecaca; }

/* ── Reject button on kanban card ──────────────────────────────────── */
.btn-reject-xs {
  font-size: 12px; padding: 4px 8px; border-radius: 6px;
  background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5;
  cursor: pointer; flex-shrink: 0; transition: background .12s;
  font-weight: 700; line-height: 1;
}
.btn-reject-xs:hover { background: #fecaca; }

/* ── Confirmation modal ────────────────────────────────────────────── */
.confirm-modal { max-width: 420px; width: 100%; }
.confirm-title-hire   { color: #059669; margin: 0; font-size: 18px; }
.confirm-title-reject { color: #dc2626; margin: 0; font-size: 18px; }
.confirm-text { font-size: 14px; color: #374151; line-height: 1.6; margin: 0; }
.confirm-text strong  { color: #111827; }

.btn-hire {
  background: #10b981; color: #fff; border: none;
  padding: 8px 20px; border-radius: 8px; font-weight: 600;
  cursor: pointer; transition: background .15s;
}
.btn-hire:hover { background: #059669; }

.btn-reject {
  background: #ef4444; color: #fff; border: none;
  padding: 8px 20px; border-radius: 8px; font-weight: 600;
  cursor: pointer; transition: background .15s;
}
.btn-reject:hover { background: #dc2626; }

/* ── Toast notification ────────────────────────────────────────────── */
.toast-notify {
  position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%);
  background: #1e1b4b; color: #fff;
  padding: 12px 24px; border-radius: 10px;
  font-size: 14px; font-weight: 500;
  box-shadow: 0 8px 24px rgba(0,0,0,.25);
  z-index: 9999; white-space: nowrap;
  animation: toast-in .25s ease;
}
@keyframes toast-in {
  from { opacity: 0; transform: translateX(-50%) translateY(12px); }
  to   { opacity: 1; transform: translateX(-50%) translateY(0); }
}
</style>
