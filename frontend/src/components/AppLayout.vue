<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="sidebar-logo">
        <span>◆</span> HRM System
      </div>

      <nav class="sidebar-nav">
        <!-- DIRECTOR + HR_MANAGER + ADMIN -->
        <template v-if="auth.canAccessHR">
          <router-link to="/dashboard">
            <span class="icon">🏠</span> Дашборд
          </router-link>
          <router-link to="/employees">
            <span class="icon">👥</span> Сотрудники
          </router-link>
          <router-link to="/leaves">
            <span class="icon">🌴</span> Отпуска
          </router-link>
          <router-link to="/recruiting">
            <span class="icon">🎯</span> Подбор персонала
          </router-link>
          <router-link to="/timesheets">
            <span class="icon">📅</span> Табель
          </router-link>
        </template>

        <!-- DIRECTOR + ADMIN -->
        <router-link v-if="auth.canAccessAnalytics" to="/analytics">
          <span class="icon">📊</span> Аналитика
        </router-link>

        <!-- All authenticated roles -->
        <router-link to="/training">
          <span class="icon">🎓</span> Обучение
        </router-link>
        <router-link to="/my-profile">
          <span class="icon">👤</span> Мой профиль
        </router-link>

        <!-- EMPLOYEE only -->
        <router-link v-if="auth.isEmployee" to="/my-leaves">
          <span class="icon">🌴</span> Мои заявки
        </router-link>

        <!-- ADMIN only -->
        <router-link v-if="auth.isAdmin" to="/admin-panel">
          <span class="icon">⚙</span> Управление
        </router-link>
        <router-link v-if="auth.isAdmin" to="/audit">
          <span class="icon">📋</span> Журнал аудита
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="sidebar-user">
          <div class="avatar">{{ avatarLetter }}</div>
          <div style="min-width:0">
            <div style="font-weight:600;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
              {{ auth.fullName || auth.username }}
            </div>
            <div style="display:flex;align-items:center;gap:8px">
              <span class="role-badge" :class="roleBadgeClass">{{ roleLabel }}</span>
              <button @click="logout" style="background:none;border:none;color:var(--gray-400);cursor:pointer;font-size:11px;padding:0">
                Выйти
              </button>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main content: optional global search header + pages -->
    <div class="main-content" :class="{ 'has-search': showSearch }">
      <header v-if="showSearch" class="global-header">
        <GlobalSearch />
      </header>
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import GlobalSearch from './GlobalSearch.vue'
import api from '@/api/index'

const auth   = useAuthStore()
const router = useRouter()

const showSearch  = computed(() => !auth.isEmployee)
const avatarLetter = computed(() => (auth.username || 'A')[0].toUpperCase())

const roleLabel = computed(() => ({
  DIRECTOR:   'Директор',
  HR_MANAGER: 'HR-менеджер',
  EMPLOYEE:   'Сотрудник',
  ADMIN:      'Администратор',
}[auth.role] || auth.role))

const roleBadgeClass = computed(() => ({
  DIRECTOR:   'role-director',
  HR_MANAGER: 'role-hr',
  EMPLOYEE:   'role-employee',
  ADMIN:      'role-admin',
}[auth.role] || ''))

async function logout() {
  try { await api.post('/auth/logout/') } catch {}
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
/* Global search header bar */
.global-header {
  height: 52px;
  background: #fff;
  border-bottom: 1px solid var(--gray-200);
  display: flex;
  align-items: center;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 60;
  box-shadow: 0 1px 3px rgba(0,0,0,.06);
}

/* Role badges */
.role-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 10px;
  text-transform: uppercase;
  letter-spacing: .4px;
}
.role-director  { background: rgba(99,102,241,.25); color: #a5b4fc; }
.role-hr        { background: rgba(16,185,129,.2);  color: #6ee7b7; }
.role-employee  { background: rgba(245,158,11,.2);  color: #fcd34d; }
.role-admin     { background: rgba(239,68,68,.2);   color: #fca5a5; }
</style>
