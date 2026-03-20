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
}

.settings-card {
  margin-top: 20px;
}

.card-title {
  font-size: 18px;
  font-weight: bold;
}
</style>
