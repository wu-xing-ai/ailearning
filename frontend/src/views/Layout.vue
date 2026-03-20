<template>
  <div class="app-container">
    <!-- 顶部导航 -->
    <header class="header">
      <div class="logo">
        <span class="school-name">武汉外国语学校</span>
        <span class="platform-name">- 智能学习平台</span>
      </div>
      <nav class="nav">
        <router-link to="/ai-chat" class="nav-item">AI智能导学</router-link>
        <router-link to="/smart-upload" class="nav-item">智能学习</router-link>
        <router-link to="/ai-search" class="nav-item">检索</router-link>
        <router-link to="/ai-knowledge" class="nav-item">知识交互</router-link>
        <router-link to="/smart-library" class="nav-item">知识库</router-link>
        <router-link to="/settings" class="nav-item">设置</router-link>
      </nav>
    </header>

    <!-- 主要内容区 -->
    <main class="main-content">
      <router-view></router-view>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const activeModule = ref('chat')
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: 'Microsoft YaHei', Arial, sans-serif;
}

.header {
  background: linear-gradient(135deg, #4a90e2, #357abd);
  color: white;
  padding: 0 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.logo {
  font-size: 20px;
  font-weight: bold;
  padding: 15px 0;
}

.school-name {
  font-weight: bold;
}

.platform-name {
  margin-left: 10px;
  opacity: 0.9;
}

.nav {
  padding: 10px 0;
  border-top: 1px solid rgba(255,255,255,0.2);
}

.nav-item {
  color: white;
  text-decoration: none;
  margin: 0 15px;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background 0.3s;
}

.nav-item:hover {
  background: rgba(255,255,255,0.1);
}

.main-content {
  flex: 1;
  padding: 20px;
  background: #f5f7fa;
}
</style>