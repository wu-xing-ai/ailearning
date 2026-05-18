import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../pages/Auth/Login.vue'),
    meta: { title: '登录', noAuth: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../pages/Auth/Register.vue'),
    meta: { title: '注册', noAuth: true }
  },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('../pages/AI-Teaching/Chat.vue'),
        meta: { title: 'AI智能导学', requiresAuth: true }
      },
      {
        path: 'ai-chat',
        name: 'AIChat',
        component: () => import('../pages/AI-Teaching/Chat.vue'),
        meta: { title: 'AI聊天', requiresAuth: true }
      },
      {
        path: 'ai-knowledge',
        name: 'AIKnowledge',
        component: () => import('../pages/AI-Teaching/Knowledge.vue'),
        meta: { title: '知识交互', requiresAuth: true }
      },
      {
        path: 'ai-search',
        name: 'AISearch',
        component: () => import('../pages/AI-Teaching/Search.vue'),
        meta: { title: '智能检索', requiresAuth: true }
      },
      {
        path: 'smart-upload',
        name: 'SmartUpload',
        component: () => import('../pages/Smart-Learning/Upload.vue'),
        meta: { title: '文档上传', requiresAuth: true }
      },
      {
        path: 'smart-structure',
        name: 'SmartStructure',
        component: () => import('../pages/Smart-Learning/Structure.vue'),
        meta: { title: '知识结构化', requiresAuth: true }
      },
      {
        path: 'smart-library',
        name: 'SmartLibrary',
        component: () => import('../pages/Smart-Learning/Library.vue'),
        meta: { title: '知识库管理', requiresAuth: true }
      },
      {
        path: 'quiz',
        name: 'Quiz',
        component: () => import('../pages/Smart-Learning/Quiz.vue'),
        meta: { title: '做题练习', requiresAuth: true }
      },
      {
        path: 'progress',
        name: 'Progress',
        component: () => import('../pages/Dashboard/ProgressDashboard.vue'),
        meta: { title: '学习进度', requiresAuth: true }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('../pages/Settings/index.vue'),
        meta: { title: '设置', requiresAuth: true, roles: ['admin'] }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('auth_token')

  // Pages that don't need auth
  if (to.meta.noAuth) {
    if (token && (to.name === 'Login' || to.name === 'Register')) {
      next({ path: '/' })
      return
    }
    next()
    return
  }

  // Pages that need auth
  if (to.meta.requiresAuth && !token) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  next()
})

export default router
