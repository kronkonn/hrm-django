import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/apply/:token',
    component: () => import('@/views/ApplyView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/components/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: () => _defaultRoute() },

      // DIRECTOR + HR_MANAGER + ADMIN
      {
        path: 'dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: { roles: ['DIRECTOR', 'HR_MANAGER', 'ADMIN'] },
      },
      {
        path: 'employees',
        component: () => import('@/views/EmployeesView.vue'),
        meta: { roles: ['DIRECTOR', 'HR_MANAGER', 'ADMIN'] },
      },
      {
        path: 'employees/:id',
        component: () => import('@/views/EmployeeDetailView.vue'),
        meta: { roles: ['DIRECTOR', 'HR_MANAGER', 'ADMIN'] },
      },
      {
        path: 'leaves',
        component: () => import('@/views/LeavesView.vue'),
        meta: { roles: ['DIRECTOR', 'HR_MANAGER', 'ADMIN'] },
      },
      {
        path: 'recruiting',
        component: () => import('@/views/RecruitingView.vue'),
        meta: { roles: ['DIRECTOR', 'HR_MANAGER', 'ADMIN'] },
      },
      {
        path: 'vacancies/:id',
        component: () => import('@/views/VacancyDetailView.vue'),
        meta: { roles: ['DIRECTOR', 'HR_MANAGER', 'ADMIN'] },
      },
      {
        path: 'timesheets',
        component: () => import('@/views/TimesheetView.vue'),
        meta: { roles: ['DIRECTOR', 'HR_MANAGER', 'ADMIN'] },
      },

      // DIRECTOR + ADMIN
      {
        path: 'analytics',
        component: () => import('@/views/AnalyticsView.vue'),
        meta: { roles: ['DIRECTOR', 'ADMIN'] },
      },

      // All roles
      {
        path: 'my-profile',
        component: () => import('@/views/MyProfileView.vue'),
      },
      {
        path: 'training',
        component: () => import('@/views/TrainingView.vue'),
      },
      {
        path: 'training/course/:id',
        component: () => import('@/views/CoursePlayerView.vue'),
      },

      // EMPLOYEE only
      {
        path: 'my-leaves',
        component: () => import('@/views/MyLeavesView.vue'),
        meta: { roles: ['EMPLOYEE'] },
      },

      // ADMIN only
      {
        path: 'admin-panel',
        component: () => import('@/views/AdminPanelView.vue'),
        meta: { roles: ['ADMIN'] },
      },
      {
        path: 'audit',
        component: () => import('@/views/AuditView.vue'),
        meta: { roles: ['ADMIN'] },
      },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

function _defaultRoute() {
  const role = localStorage.getItem('role')
  if (role === 'EMPLOYEE') return '/my-profile'
  return '/dashboard'
}

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const token = localStorage.getItem('access_token')
  const role  = localStorage.getItem('role')
  if (to.meta.requiresAuth && !token)                         return '/login'
  if (to.path === '/login' && token)                          return _defaultRoute()
  if (to.meta.roles && role && !to.meta.roles.includes(role)) return _defaultRoute()
})

export default router
