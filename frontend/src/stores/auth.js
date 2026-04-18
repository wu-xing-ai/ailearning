import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(null)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isTeacher = computed(() => user.value?.role === 'teacher' || user.value?.role === 'admin')

  async function login(username, password) {
    const result = await api.post('/api/auth/login', { username, password })
    token.value = result.token
    user.value = result.user
    localStorage.setItem('auth_token', result.token)
    localStorage.setItem('auth_user', JSON.stringify(result.user))
    return result
  }

  async function register(data) {
    const result = await api.post('/api/auth/register', data)
    token.value = result.token
    user.value = {
      id: result.id,
      username: result.username,
      display_name: result.display_name,
      role: result.role,
    }
    localStorage.setItem('auth_token', result.token)
    localStorage.setItem('auth_user', JSON.stringify(user.value))
    return result
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
  }

  function initFromStorage() {
    const savedToken = localStorage.getItem('auth_token')
    const savedUser = localStorage.getItem('auth_user')
    if (savedToken) {
      token.value = savedToken
      try {
        user.value = JSON.parse(savedUser)
      } catch {
        user.value = null
      }
    }
  }

  return { user, token, isAuthenticated, isAdmin, isTeacher, login, register, logout, initFromStorage }
})
