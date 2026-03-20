<template>
  <div class="chat-container">
    <!-- 聊天窗口 -->
    <div class="chat-window">
      <div class="chat-messages">
        <!-- 消息显示区域 -->
        <div class="message" v-for="(message, index) in messages" :key="index">
          <div class="message-content">
            <div class="message-header" v-if="message.type === 'assistant'">
              <span class="assistant-label">{{ message.providerName || 'AI助手' }}</span>
              <span class="message-time">{{ formatDate(message.timestamp) }}</span>
            </div>
            <div class="message-bubble" :class="{'assistant': message.type === 'assistant', 'user': message.type === 'user'}">
              {{ message.content }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 聊天输入区 -->
    <div class="chat-input">
      <el-input
        v-model="inputMessage"
        type="textarea"
        :rows="3"
        placeholder="输入您的问题..."
        resize="none"
        @keyup.enter="sendMessage"
      ></el-input>
      <div class="input-actions">
        <el-select v-model="selectedProvider" placeholder="选择厂商" style="width: 150px" @change="onProviderChange">
          <el-option
            v-for="provider in providers"
            :key="provider.value"
            :label="provider.label"
            :value="provider.value"
          ></el-option>
        </el-select>
        <el-select v-model="selectedModel" placeholder="选择模型" style="width: 180px">
          <el-option
            v-for="model in currentModels"
            :key="model.value"
            :label="model.label"
            :value="model.value"
          ></el-option>
        </el-select>
        <el-button type="primary" @click="sendMessage" :loading="isLoading">发送</el-button>
        <el-button @click="clearChat">清空</el-button>
        <el-button @click="openConfigDialog" icon="Setting">设置</el-button>
      </div>
    </div>

    <!-- 配置对话框 -->
    <el-dialog title="AI模型配置" v-model="configDialogVisible" width="600">
      <el-tabs v-model="activeConfigTab">
        <!-- 厂商配置 -->
        <el-tab-pane label="厂商设置" name="providers">
          <div v-for="(info, provider) in providerInfo" :key="provider" class="provider-config">
            <h4>{{ info.name }}</h4>
            <el-form v-if="info.requires_api_key" label-width="100px">
              <el-form-item label="API密钥">
                <el-input
                  v-model="apiKeys[provider]"
                  type="password"
                  placeholder="请输入API密钥"
                  show-password
                ></el-input>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" size="small" @click="saveApiKey(provider)">保存</el-button>
              </el-form-item>
            </el-form>
            <p v-else class="no-key-required">无需API密钥</p>
          </div>
        </el-tab-pane>

        <!-- 自定义模型 -->
        <el-tab-pane label="自定义模型" name="custom">
          <el-form :model="customModelConfig" label-width="120px">
            <el-form-item label="模型名称">
              <el-input v-model="customModelConfig.name" placeholder="例如：my-model"></el-input>
            </el-form-item>
            <el-form-item label="API地址">
              <el-input v-model="customModelConfig.apiUrl" placeholder="例如：https://api.example.com/v1"></el-input>
            </el-form-item>
            <el-form-item label="API密钥">
              <el-input v-model="customModelConfig.apiKey" type="password" placeholder="可选"></el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="testCustomModel">测试连接</el-button>
              <el-button @click="addCustomModel">添加模型</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- Ollama设置 -->
        <el-tab-pane label="Ollama设置" name="ollama">
          <el-form :model="ollamaConfig" label-width="120px">
            <el-form-item label="服务地址">
              <el-input v-model="ollamaConfig.baseUrl" placeholder="http://localhost:11434"></el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveOllamaConfig">保存配置</el-button>
              <el-button @click="refreshOllamaModels">刷新模型列表</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../../utils/api'

const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)

// 厂商和模型选择
const providers = ref([
  { value: 'ollama', label: 'Ollama本地' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Claude' },
  { value: 'zhipu', label: '智谱AI' },
  { value: 'qwen', label: '通义千问' },
  { value: 'siliconflow', label: '硅基流动' },
  { value: 'custom', label: '自定义' }
])

const selectedProvider = ref('ollama')
const selectedModel = ref('')
const providerInfo = ref({})
const apiKeys = ref({
  openai: '',
  anthropic: '',
  zhipu: '',
  qwen: '',
  siliconflow: '',
  custom: ''
})

// 模型列表
const modelLists = ref({
  ollama: [],
  openai: [],
  anthropic: [],
  zhipu: [],
  qwen: [],
  siliconflow: [],
  custom: []
})

// 当前可用模型
const currentModels = computed(() => {
  const provider = selectedProvider.value
  const models = modelLists.value[provider] || []

  if (models.length === 0) {
    // 返回默认模型
    const defaults = {
      ollama: [{ value: 'qwen2.5:latest', label: 'Qwen 2.5' }],
      openai: [{ value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' }],
      anthropic: [{ value: 'claude-3-sonnet-20240229', label: 'Claude 3 Sonnet' }],
      zhipu: [{ value: 'glm-4', label: 'GLM-4' }],
      qwen: [{ value: 'qwen-turbo', label: '通义千问 Turbo' }],
      siliconflow: [{ value: 'Qwen/Qwen2.5-7B-Instruct', label: 'Qwen2.5 7B' }],
      custom: []
    }
    return defaults[provider] || []
  }
  return models
})

// 配置对话框
const configDialogVisible = ref(false)
const activeConfigTab = ref('providers')

// 自定义模型配置
const customModelConfig = ref({
  name: '',
  apiUrl: '',
  apiKey: ''
})

// Ollama配置
const ollamaConfig = ref({
  baseUrl: 'http://localhost:11434'
})

// 厂商变更
const onProviderChange = async (provider) => {
  selectedModel.value = ''
  if (provider !== 'ollama' && !apiKeys.value[provider]) {
    ElMessage.warning('请先在设置中配置API密钥')
  }
}

// 打开配置对话框
const openConfigDialog = async () => {
  try {
    const response = await api.get('/api/ai/providers')
    providerInfo.value = response.info || {}
  } catch (error) {
    console.error('获取厂商信息失败:', error)
  }
  configDialogVisible.value = true
}

// 保存API密钥
const saveApiKey = async (provider) => {
  try {
    await api.post('/api/ai/api-keys', {
      provider,
      apiKey: apiKeys.value[provider]
    })
    ElMessage.success('API密钥已保存')
  } catch (error) {
    ElMessage.error('保存失败: ' + error.message)
  }
}

// 保存Ollama配置
const saveOllamaConfig = async () => {
  try {
    await api.put('/api/ai/config', {
      base_url: ollamaConfig.value.baseUrl
    })
    ElMessage.success('配置已保存')
    refreshOllamaModels()
  } catch (error) {
    ElMessage.error('保存失败: ' + error.message)
  }
}

// 刷新Ollama模型列表
const refreshOllamaModels = async () => {
  try {
    const response = await api.get('/api/ai/models')
    if (response.models) {
      modelLists.value.ollama = response.models.map(name => ({
        value: name,
        label: name
      }))
      if (response.models.length > 0 && !selectedModel.value) {
        selectedModel.value = response.current || response.models[0]
      }
    }
  } catch (error) {
    console.error('刷新模型列表失败:', error)
  }
}

// 添加自定义模型
const addCustomModel = () => {
  if (!customModelConfig.value.name || !customModelConfig.value.apiUrl) {
    ElMessage.error('请填写模型名称和API地址')
    return
  }

  modelLists.value.custom.push({
    value: customModelConfig.value.name,
    label: customModelConfig.value.name
  })

  if (customModelConfig.value.apiKey) {
    apiKeys.value.custom = customModelConfig.value.apiKey
  }

  selectedProvider.value = 'custom'
  selectedModel.value = customModelConfig.value.name

  ElMessage.success('自定义模型已添加')
  customModelConfig.value = { name: '', apiUrl: '', apiKey: '' }
}

// 测试自定义模型
const testCustomModel = async () => {
  ElMessage.info('模型测试功能开发中...')
}

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return

  isLoading.value = true

  // 添加用户消息
  messages.value.push({
    type: 'user',
    content: inputMessage.value,
    timestamp: new Date()
  })

  const userMessage = inputMessage.value
  inputMessage.value = ''

  // 构造请求
  const requestData = {
    prompt: userMessage,
    stream: true,
    modelConfig: {
      type: selectedProvider.value,
      name: selectedModel.value,
      apiKey: apiKeys.value[selectedProvider.value],
      apiUrl: selectedProvider.value === 'custom' ? customModelConfig.value.apiUrl : undefined
    }
  }

  try {
    const response = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData)
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let fullResponse = ''

    // 处理流式响应
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n').filter(line => line.trim())

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.content) {
              fullResponse += data.content
            }
            if (data.done) {
              messages.value.push({
                type: 'assistant',
                content: fullResponse,
                providerName: `${selectedProvider.value} - ${selectedModel.value}`,
                timestamp: new Date()
              })
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }

    if (!fullResponse) {
      messages.value.push({
        type: 'assistant',
        content: '[无响应内容]',
        timestamp: new Date()
      })
    }

  } catch (error) {
    ElMessage.error('发送失败: ' + error.message)
    messages.value.push({
      type: 'assistant',
      content: `[错误] ${error.message}`,
      timestamp: new Date()
    })
  } finally {
    isLoading.value = false
  }
}

// 清空对话
const clearChat = async () => {
  messages.value = []
  try {
    await api.post('/api/ai/reset')
  } catch (error) {
    console.error('重置上下文失败:', error)
  }
  ElMessage.success('对话已清空')
}

// 格式化日期
const formatDate = (date) => {
  return new Date(date).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 初始化
onMounted(async () => {
  // 加载Ollama模型
  await refreshOllamaModels()

  // 加载其他厂商默认模型
  modelLists.value.openai = [
    { value: 'gpt-4', label: 'GPT-4' },
    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' }
  ]

  modelLists.value.anthropic = [
    { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' },
    { value: 'claude-3-sonnet-20240229', label: 'Claude 3 Sonnet' },
    { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku' }
  ]

  modelLists.value.zhipu = [
    { value: 'glm-4', label: 'GLM-4' },
    { value: 'glm-4-air', label: 'GLM-4 Air' },
    { value: 'glm-3-turbo', label: 'GLM-3 Turbo' }
  ]

  modelLists.value.qwen = [
    { value: 'qwen-turbo', label: '通义千问 Turbo' },
    { value: 'qwen-plus', label: '通义千问 Plus' },
    { value: 'qwen-max', label: '通义千问 Max' }
  ]

  // 硅基流动模型列表
  modelLists.value.siliconflow = [
    { value: 'Qwen/Qwen2.5-7B-Instruct', label: 'Qwen2.5 7B (免费)' },
    { value: 'Qwen/Qwen2.5-72B-Instruct', label: 'Qwen2.5 72B' },
    { value: 'deepseek-ai/DeepSeek-V2.5', label: 'DeepSeek V2.5' },
    { value: 'THUDM/glm-4-9b-chat', label: 'GLM-4 9B (免费)' },
    { value: 'meta-llama/Meta-Llama-3.1-8B-Instruct', label: 'Llama 3.1 8B' }
  ]

  // 设置默认模型
  if (modelLists.value.ollama.length > 0) {
    selectedModel.value = modelLists.value.ollama[0].value
  }
})
</script>

<style scoped>
.chat-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

.chat-window {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
  overflow-y: auto;
}

.chat-messages {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  flex-direction: column;
  max-width: 80%;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  color: #666;
  font-size: 12px;
}

.assistant-label {
  background: #e6f7ff;
  color: #1890ff;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
}

.message-time {
  color: #999;
}

.message-bubble {
  padding: 12px;
  border-radius: 18px;
  line-height: 1.5;
  word-break: break-word;
}

.assistant {
  align-self: flex-start;
  background: #f0f2f5;
  color: #333;
}

.user {
  align-self: flex-end;
  background: #1890ff;
  color: white;
}

.chat-input {
  padding: 20px;
  border-top: 1px solid #eee;
  margin-top: auto;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 10px;
}

.provider-config {
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #eee;
  border-radius: 8px;
}

.provider-config h4 {
  margin-bottom: 15px;
  color: #333;
}

.no-key-required {
  color: #52c41a;
  font-size: 14px;
}
</style>