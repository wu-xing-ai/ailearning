import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('../pages/AI-Teaching/Chat.vue'),
        meta: { title: 'AI智能导学' }
      },
      {
        path: 'ai-chat',
        name: 'AIChat',
        component: () => import('../pages/AI-Teaching/Chat.vue'),
        meta: { title: 'AI聊天' }
      },
      {
        path: 'ai-knowledge',
        name: 'AIKnowledge',
        component: () => import('../pages/AI-Teaching/Knowledge.vue'),
        meta: { title: '知识交互' }
      },
      {
        path: 'ai-search',
        name: 'AISearch',
        component: () => import('../pages/AI-Teaching/Search.vue'),
        meta: { title: '智能检索' }
      },
      {
        path: 'smart-upload',
        name: 'SmartUpload',
        component: () => import('../pages/Smart-Learning/Upload.vue'),
        meta: { title: '文档上传' }
      },
      {
        path: 'smart-structure',
        name: 'SmartStructure',
        component: () => import('../pages/Smart-Learning/Structure.vue'),
        meta: { title: '知识结构化' }
      },
      {
        path: 'smart-library',
        name: 'SmartLibrary',
        component: () => import('../pages/Smart-Learning/Library.vue'),
        meta: { title: '知识库管理' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('../pages/Settings/index.vue'),
        meta: { title: '设置' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router