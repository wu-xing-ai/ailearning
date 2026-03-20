<template>
  <div class="settings-container">
    <el-card class="settings-card">
      <template #header>
        <span class="card-title">系统设置</span>
      </template>

      <el-form label-width="120px">
        <el-form-item label="API 地址">
          <el-input v-model="settings.apiUrl" placeholder="请输入后端 API 地址" />
        </el-form-item>

        <el-form-item label="主题模式">
          <el-radio-group v-model="settings.theme">
            <el-radio value="light">浅色</el-radio>
            <el-radio value="dark">深色</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="语言">
          <el-select v-model="settings.language" placeholder="请选择语言">
            <el-option label="简体中文" value="zh-CN" />
            <el-option label="English" value="en-US" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="saveSettings">保存设置</el-button>
          <el-button @click="resetSettings">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'

const settings = reactive({
  apiUrl: 'http://localhost:8000',
  theme: 'light',
  language: 'zh-CN'
})

const saveSettings = () => {
  localStorage.setItem('settings', JSON.stringify(settings))
  ElMessage.success('设置已保存')
}

const resetSettings = () => {
  settings.apiUrl = 'http://localhost:8000'
  settings.theme = 'light'
  settings.language = 'zh-CN'
}
</script>

<style scoped>
.settings-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 24px;
}

.settings-card {
  border-radius: 16px;
  border: 1px solid rgba(139, 90, 43, 0.1);
  box-shadow: 0 4px 24px rgba(139, 90, 43, 0.08);
  margin-top: 20px;
  background: linear-gradient(180deg, #FFFEF7 0%, #FFF9E8 100%);
}

.settings-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #FFFEF7 0%, #FFF5E6 100%);
  border-bottom: 1px solid rgba(139, 90, 43, 0.1);
  padding: 20px 24px;
}

.card-title {
  font-family: 'Noto Serif SC', 'Source Han Serif CN', Georgia, serif;
  font-size: 18px;
  font-weight: 600;
  color: #3D2914;
}

.settings-card :deep(.el-card__body) {
  padding: 24px;
}

/* 表单样式 */
:deep(.el-form-item__label) {
  color: #5D4E37;
  font-weight: 500;
}

:deep(.el-input__wrapper) {
  background: white;
  border: 1px solid rgba(139, 90, 43, 0.15);
  border-radius: 8px;
  box-shadow: none;
  transition: all 0.25s ease;
}

:deep(.el-input__wrapper:hover) {
  border-color: #D4A574;
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #D4A574;
  box-shadow: 0 0 0 3px rgba(212, 165, 116, 0.15);
}

:deep(.el-radio__input.is-checked + .el-radio__label) {
  color: #D4A574;
}

:deep(.el-radio__input.is-checked .el-radio__inner) {
  background-color: #D4A574;
  border-color: #D4A574;
}

/* 按钮样式 */
:deep(.el-form-item:last-child) {
  display: flex;
  gap: 12px;
}
</style>
