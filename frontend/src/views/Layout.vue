<template>
  <div class="app-container">
    <!-- 顶部导航 -->
    <header class="header">
      <div class="header-content">
        <div class="header-row">
          <div class="logo">
            <div class="logo-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M4.26 10.147a60.436 60.436 0 00-.491 3.007 60.453 60.453 0 00-1.265 3.96c-.165.377-.318.756-.458 1.147l-.012.033A10.5 10.5 0 016.5 6.5c.965 0 1.91.127 2.812.367M12 6.5c0 3.59 2.91 6.5 6.5 6.5.795 0 1.56-.09 2.29-.257M12 6.5a6.5 6.5 0 016.5-6.5c2.393 0 4.538 1.086 5.934 2.782M12 6.5c0-3.59 2.91-6.5 6.5-6.5 2.393 0 4.538 1.086 5.934 2.782"/>
              </svg>
            </div>
            <div class="logo-text">
              <span class="school-name">武汉外国语学校</span>
              <span class="platform-name">智能学习平台</span>
            </div>
          </div>
          <div class="header-right">
            <div class="user-info desktop-only" v-if="authStore.isAuthenticated">
              <span class="user-name">{{ authStore.user?.display_name || authStore.user?.username }}</span>
              <el-tag size="small" :type="roleTagType">{{ roleLabel }}</el-tag>
              <el-button text @click="handleLogout" class="logout-btn">退出</el-button>
            </div>
            <!-- 移动端汉堡菜单按钮 -->
            <button class="hamburger-btn" :class="{ active: mobileMenuOpen }" @click="toggleMobileMenu">
              <span></span>
              <span></span>
              <span></span>
            </button>
          </div>
        </div>
        <!-- 桌面端导航 -->
        <nav class="nav desktop-only">
          <router-link
            v-for="item in visibleNavItems"
            :key="item.path"
            :to="item.path"
            class="nav-item"
            :class="{ active: $route.path === item.path }"
          >
            <span class="nav-icon" v-html="item.icon"></span>
            <span class="nav-label">{{ item.label }}</span>
          </router-link>
        </nav>
      </div>
      <!-- 移动端下拉菜单 -->
      <transition name="slide-down">
        <div class="mobile-menu" v-if="mobileMenuOpen">
          <nav class="mobile-nav">
            <router-link
              v-for="item in visibleNavItems"
              :key="item.path"
              :to="item.path"
              class="mobile-nav-item"
              :class="{ active: $route.path === item.path }"
              @click="mobileMenuOpen = false"
            >
              <span class="nav-icon" v-html="item.icon"></span>
              <span class="nav-label">{{ item.label }}</span>
            </router-link>
          </nav>
          <div class="mobile-user" v-if="authStore.isAuthenticated">
            <span class="user-name">{{ authStore.user?.display_name || authStore.user?.username }}</span>
            <el-tag size="small" :type="roleTagType">{{ roleLabel }}</el-tag>
            <el-button text @click="handleLogout" class="logout-btn">退出</el-button>
          </div>
        </div>
      </transition>
    </header>

    <!-- 主要内容区 -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const $route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const mobileMenuOpen = ref(false)

const toggleMobileMenu = () => {
  mobileMenuOpen.value = !mobileMenuOpen.value
}

// 路由变化时关闭移动端菜单
watch(() => $route.path, () => {
  mobileMenuOpen.value = false
})

const allNavItems = ref([
  {
    path: '/ai-chat',
    label: 'AI智能导学',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.394 48.394 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z"/></svg>'
  },
  {
    path: '/smart-upload',
    label: '智能学习',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18"/></svg>'
  },
  {
    path: '/ai-search',
    label: '检索',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/></svg>'
  },
  {
    path: '/ai-knowledge',
    label: '知识交互',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5m.75-9l3-3 2.148 2.148A12.061 12.061 0 0116.5 10.607"/></svg>'
  },
  {
    path: '/smart-library',
    label: '知识库',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25"/></svg>',
    roles: ['admin', 'teacher']
  },
  {
    path: '/progress',
    label: '学习进度',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"/></svg>'
  },
  {
    path: '/settings',
    label: '设置',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.95-1.11.95h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z"/><path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>',
    roles: ['admin']
  }
])

const visibleNavItems = computed(() => {
  const role = authStore.user?.role || 'student'
  return allNavItems.value.filter(item => {
    if (!item.roles) return true
    return item.roles.includes(role)
  })
})

const roleTagType = computed(() => {
  const map = { admin: 'danger', teacher: 'warning', student: 'info' }
  return map[authStore.user?.role] || 'info'
})

const roleLabel = computed(() => {
  const map = { admin: '管理员', teacher: '教师', student: '学生' }
  return map[authStore.user?.role] || '用户'
})

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
/* ========== 基础容器 ========== */
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  background: #F8F6F1;
}

/* ========== 顶部导航 ========== */
.header {
  background: linear-gradient(135deg, #3D2914 0%, #5D4037 50%, #4A3728 100%);
  color: white;
  position: relative;
}

.header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  pointer-events: none;
}

.header-content {
  position: relative;
  z-index: 1;
  padding: 0 24px;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* ========== Logo 区域 ========== */
.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 0;
}

.logo-icon {
  width: 42px;
  height: 42px;
  background: linear-gradient(135deg, #D4A574 0%, #C4956A 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.logo-icon svg {
  width: 24px;
  height: 24px;
  color: white;
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.school-name {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #FFF9E8;
}

.platform-name {
  font-size: 13px;
  color: rgba(255, 249, 232, 0.7);
  margin-top: 2px;
  letter-spacing: 0.04em;
}

/* ========== 导航栏 ========== */
.nav {
  display: flex;
  gap: 4px;
  padding: 8px 0 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  margin-top: 4px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(255, 249, 232, 0.85);
  font-size: 14px;
}

.user-name {
  font-weight: 500;
}

.logout-btn {
  color: rgba(255, 249, 232, 0.6) !important;
  font-size: 13px;
}

.logout-btn:hover {
  color: #D4A574 !important;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.75);
  text-decoration: none;
  padding: 10px 16px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
}

.nav-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(212, 165, 116, 0.2) 0%, rgba(212, 165, 116, 0.1) 100%);
  opacity: 0;
  transition: opacity 0.25s;
}

.nav-item:hover {
  color: white;
}

.nav-item:hover::before {
  opacity: 1;
}

.nav-item.active {
  color: white;
  background: linear-gradient(135deg, rgba(212, 165, 116, 0.25) 0%, rgba(212, 165, 116, 0.15) 100%);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.nav-icon {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 1;
}

.nav-icon :deep(svg) {
  width: 18px;
  height: 18px;
}

.nav-label {
  position: relative;
  z-index: 1;
}

/* ========== 主内容区 ========== */
.main-content {
  flex: 1;
  min-height: 0;
  padding: 24px;
  background: linear-gradient(180deg, #FFFEF7 0%, #F8F6F1 100%);
}

/* ========== 页面切换动画 ========== */
.page-enter-active {
  animation: pageSlideIn 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}

.page-leave-active {
  animation: pageSlideOut 0.25s ease-in;
}

@keyframes pageSlideIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pageSlideOut {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(-8px);
  }
}

/* ========== 汉堡菜单按钮 ========== */
.hamburger-btn {
  display: none;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 5px;
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  cursor: pointer;
  padding: 0;
  transition: background 0.2s;
}

.hamburger-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.hamburger-btn span {
  display: block;
  width: 18px;
  height: 2px;
  background: rgba(255, 249, 232, 0.85);
  border-radius: 2px;
  transition: all 0.3s ease;
}

.hamburger-btn.active span:nth-child(1) {
  transform: rotate(45deg) translate(5px, 5px);
}

.hamburger-btn.active span:nth-child(2) {
  opacity: 0;
}

.hamburger-btn.active span:nth-child(3) {
  transform: rotate(-45deg) translate(5px, -5px);
}

/* ========== 移动端下拉菜单 ========== */
.mobile-menu {
  padding: 8px 16px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  background: linear-gradient(180deg, rgba(61, 41, 20, 0.5) 0%, rgba(74, 55, 40, 0.3) 100%);
}

.mobile-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.mobile-nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  color: rgba(255, 255, 255, 0.75);
  text-decoration: none;
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.mobile-nav-item:hover,
.mobile-nav-item.active {
  color: white;
  background: rgba(212, 165, 116, 0.2);
}

.mobile-user {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  margin-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 249, 232, 0.85);
  font-size: 14px;
}

/* 移动端菜单下拉动画 */
.slide-down-enter-active {
  animation: slideDown 0.25s ease-out;
}

.slide-down-leave-active {
  animation: slideDown 0.2s ease-in reverse;
}

@keyframes slideDown {
  from {
    opacity: 0;
    max-height: 0;
    padding-top: 0;
    padding-bottom: 0;
  }
  to {
    opacity: 1;
    max-height: 500px;
  }
}

/* ========== 响应式调整 ========== */
@media (max-width: 768px) {
  .desktop-only {
    display: none !important;
  }

  .hamburger-btn {
    display: flex;
  }

  .header-content {
    padding: 0 16px;
  }

  .logo-icon {
    width: 36px;
    height: 36px;
  }

  .logo-icon svg {
    width: 20px;
    height: 20px;
  }

  .school-name {
    font-size: 16px;
  }

  .platform-name {
    font-size: 12px;
  }

  .main-content {
    padding: 8px;
    overflow: hidden;
    flex: 1;
    min-height: 0;
  }
}
</style>
