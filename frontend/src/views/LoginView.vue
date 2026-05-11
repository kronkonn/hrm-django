<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">
        <span>◆</span>
        <h1>HRM System</h1>
        <p>Система управления персоналом</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label class="form-label">Логин</label>
          <input
            v-model="form.username"
            class="form-control"
            placeholder="Введите логин"
            required
            autocomplete="username"
          />
        </div>
        <div class="form-group">
          <label class="form-label">Пароль</label>
          <input
            v-model="form.password"
            type="password"
            class="form-control"
            placeholder="Введите пароль"
            required
            autocomplete="current-password"
          />
        </div>

        <div v-if="authStore.error" class="error-box">
          {{ authStore.error }}
        </div>

        <button
          type="submit"
          class="btn btn-primary"
          style="width:100%;justify-content:center;padding:10px;font-size:14px"
          :disabled="authStore.loading"
        >
          <span v-if="authStore.loading" class="spinner" style="width:16px;height:16px"></span>
          {{ authStore.loading ? 'Вход...' : 'Войти' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const form = reactive({ username: '', password: '' })

async function handleLogin() {
  const ok = await authStore.login(form.username, form.password)
  if (ok) {
    // Роль определяет стартовую страницу
    if (authStore.isEmployee) {
      router.push('/my-profile')
    } else {
      router.push('/dashboard')
    }
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #4f46e5 0%, #3730a3 50%, #1e1b4b 100%);
  padding: 16px;
}
.login-card {
  background: #fff;
  border-radius: 12px;
  padding: 40px;
  width: 100%;
  max-width: 380px;
  box-shadow: 0 20px 40px rgba(0,0,0,.25);
}
.login-logo { text-align: center; margin-bottom: 32px; }
.login-logo span { font-size: 36px; color: #4f46e5; display: block; margin-bottom: 8px; }
.login-logo h1 { font-size: 22px; font-weight: 700; color: #1f2937; margin-bottom: 4px; }
.login-logo p { font-size: 13px; color: #6b7280; }
.error-box {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 13px;
  margin-bottom: 12px;
}
</style>
