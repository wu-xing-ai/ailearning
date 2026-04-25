<template>
  <div class="chat-container">
    <!-- 聊天窗口 -->
    <div class="chat-window" ref="chatWindowRef" @scroll="handleChatScroll">
      <div class="chat-messages">
        <!-- 欢迎消息 -->
        <div v-if="messages.length === 0 && !isLoading" class="welcome-state">
          <div class="welcome-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25"/>
            </svg>
          </div>
          <h2>智能学习助手</h2>
          <p>有什么可以帮助你的吗？</p>
          <div class="quick-actions">
            <button @click="quickAsk('解释一下量子计算的基本原理')" class="quick-btn">
              <span class="quick-icon">💡</span>
              解释量子计算原理
            </button>
            <button @click="quickAsk('如何写好一篇议论文？')" class="quick-btn">
              <span class="quick-icon">✍️</span>
              议论文写作技巧
            </button>
            <button @click="quickAsk('帮我总结一下中国历史的主要朝代')" class="quick-btn">
              <span class="quick-icon">📚</span>
              中国历史朝代
            </button>
          </div>
        </div>

        <!-- 消息列表 - 带过渡动画 -->
        <TransitionGroup name="message">
          <div
            v-for="(message, index) in messages"
            :key="message.id || index"
            v-show="message.type !== 'assistant' || message.content || !isWaitingForResponse"
            class="message"
            :class="message.type"
          >
            <!-- AI 消息 -->
            <template v-if="message.type === 'assistant'">
              <div class="avatar ai-avatar" :class="{ 'thinking-avatar': message.isStreaming && !message.content }">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456z"/>
                </svg>
              </div>
              <div class="message-body">
                <div class="message-header">
                  <span class="assistant-label">{{ message.providerName || 'AI助手' }}</span>
                  <span class="message-time">{{ formatDate(message.timestamp) }}</span>
                </div>
                <div class="message-bubble assistant" :class="{ 'has-error': message.isError }">
                  <!-- Markdown 渲染 - 只有有内容时才显示 -->
                  <div
                    v-if="message.content"
                    class="markdown-content"
                    v-html="renderMarkdown(message.content)"
                  ></div>
                  <!-- 打字机光标 - 流式传输中有内容时显示 -->
                  <span v-if="message.isStreaming && message.content" class="typing-cursor"></span>
                </div>
                <!-- 错误重试按钮 -->
                <button v-if="message.isError" @click="retryMessage(index)" class="retry-btn">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                  </svg>
                  重试
                </button>
              </div>
            </template>

            <!-- 用户消息 -->
            <template v-else>
              <div class="message-body">
                <div class="message-bubble user">
                  {{ message.content }}
                </div>
                <div class="message-status">
                  <span class="message-time">{{ formatDate(message.timestamp) }}</span>
                  <span v-if="message.status === 'sending'" class="status-icon sending">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <circle cx="12" cy="12" r="3"/>
                    </svg>
                  </span>
                  <span v-else-if="message.status === 'sent'" class="status-icon sent">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M5 13l4 4L19 7"/>
                    </svg>
                  </span>
                </div>
              </div>
              <div class="avatar user-avatar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"/>
                </svg>
              </div>
            </template>
          </div>
        </TransitionGroup>

        <!-- AI 思考中动画 -->
        <div v-if="isLoading && isWaitingForResponse" class="message assistant thinking">
          <div class="avatar ai-avatar thinking-avatar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456z"/>
            </svg>
          </div>
          <div class="message-body">
            <div class="thinking-indicator">
              <div class="thinking-header">
                <span class="thinking-label">AI 正在思考</span>
              </div>
              <div class="thinking-dots">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 聊天输入区 -->
    <div class="chat-input" :class="{ 'is-loading': isLoading }">
      <div class="input-wrapper">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="2"
          :autosize="{ minRows: 2, maxRows: 6 }"
          placeholder="输入您的问题..."
          resize="none"
          :disabled="isLoading"
          @keydown.enter.exact.prevent="sendMessage"
          @keydown.enter.shift.exact="() => {}"
        />
        <div class="input-hint">
          <span>Shift + Enter 换行</span>
        </div>
      </div>
      <div class="input-actions">
        <div class="model-selector">
          <el-select v-model="selectedProvider" placeholder="厂商" size="default" @change="onProviderChange">
            <el-option
              v-for="provider in providers"
              :key="provider.value"
              :label="provider.label"
              :value="provider.value"
            />
          </el-select>
          <el-select v-model="selectedModel" placeholder="模型" size="default">
            <el-option
              v-for="model in currentModels"
              :key="model.value"
              :label="model.label"
              :value="model.value"
            />
          </el-select>
        </div>
        <div class="action-buttons">
          <el-button @click="confirmClearChat" :disabled="messages.length === 0" class="clear-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
          </el-button>
          <el-button @click="openConfigDialog" class="config-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
          </el-button>
          <el-button type="primary" @click="sendMessage" :loading="isLoading" class="send-btn">
            <template #default>
              <span v-if="!isLoading">发送</span>
            </template>
            <template #loading>
              <span class="sending-text">发送中</span>
            </template>
          </el-button>
        </div>
      </div>
    </div>

    <!-- 配置对话框 -->
    <el-dialog
      title="AI模型配置"
      v-model="configDialogVisible"
      width="560"
      :close-on-click-modal="false"
      class="config-dialog"
    >
      <el-tabs v-model="activeConfigTab" class="config-tabs">
        <!-- 厂商配置 -->
        <el-tab-pane label="厂商设置" name="providers">
          <div v-for="(info, provider) in providerInfo" :key="provider" class="provider-config">
            <h4>{{ info.name }}</h4>
            <el-form v-if="info.requires_api_key" label-width="80px" size="default">
              <el-form-item label="API密钥">
                <el-input
                  v-model="apiKeys[provider]"
                  type="password"
                  placeholder="请输入API密钥"
                  show-password
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" size="small" @click="saveApiKey(provider)">保存</el-button>
              </el-form-item>
            </el-form>
            <p v-else class="no-key-required">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              无需API密钥
            </p>
          </div>
        </el-tab-pane>

        <!-- 自定义模型 -->
        <el-tab-pane label="自定义模型" name="custom">
          <el-form :model="customModelConfig" label-width="90px" size="default">
            <el-form-item label="模型名称">
              <el-input v-model="customModelConfig.name" placeholder="例如：my-model" />
            </el-form-item>
            <el-form-item label="API地址">
              <el-input v-model="customModelConfig.apiUrl" placeholder="例如：https://api.example.com/v1" />
            </el-form-item>
            <el-form-item label="API密钥">
              <el-input v-model="customModelConfig.apiKey" type="password" placeholder="可选" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="testCustomModel">测试连接</el-button>
              <el-button @click="addCustomModel">添加模型</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- Ollama设置 -->
        <el-tab-pane label="Ollama" name="ollama">
          <el-form :model="ollamaConfig" label-width="90px" size="default">
            <el-form-item label="服务地址">
              <el-input v-model="ollamaConfig.baseUrl" placeholder="http://localhost:11434" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveOllamaConfig">保存配置</el-button>
              <el-button @click="refreshOllamaModels">刷新模型</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import hljs from 'highlight.js'
import katex from 'katex'
import 'highlight.js/styles/github-dark.css'
import 'katex/dist/katex.min.css'
import api from '../../utils/api'

// 配置 marked
marked.setOptions({
  breaks: true,
  gfm: true
})

// LaTeX 公式渲染 - 在 marked 解析前提取保护，解析后渲染
const renderLatexInHtml = (html) => {
  // 渲染块级公式 $$...$$
  html = html.replace(/\$\$([\s\S]*?)\$\$/g, (_, formula) => {
    try {
      return katex.renderToString(formula.trim(), {
        displayMode: true,
        throwOnError: false,
      })
    } catch {
      return `<code>${formula}</code>`
    }
  })
  // 渲染行内公式 $...$
  html = html.replace(/\$([^\$\n]+?)\$/g, (_, formula) => {
    try {
      return katex.renderToString(formula.trim(), {
        displayMode: false,
        throwOnError: false,
      })
    } catch {
      return `<code>${formula}</code>`
    }
  })
  // 兼容 \(...\) 行内公式
  html = html.replace(/\\\(([\s\S]*?)\\\)/g, (_, formula) => {
    try {
      return katex.renderToString(formula.trim(), {
        displayMode: false,
        throwOnError: false,
      })
    } catch {
      return `<code>${formula}</code>`
    }
  })
  // 兼容 \[...\] 块级公式
  html = html.replace(/\\\[([\s\S]*?)\\\]/g, (_, formula) => {
    try {
      return katex.renderToString(formula.trim(), {
        displayMode: true,
        throwOnError: false,
      })
    } catch {
      return `<code>${formula}</code>`
    }
  })
  return html
}

const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const isWaitingForResponse = ref(false)
const chatWindowRef = ref(null)
let messageIdCounter = 0

// 厂商和模型选择
const providers = ref([
  { value: 'ollama', label: 'Ollama本地' },
  { value: 'modelscope', label: '官方模型' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Claude' },
  { value: 'zhipu', label: '智谱AI' },
  { value: 'qwen', label: '通义千问' },
  { value: 'siliconflow', label: '硅基流动' },
  { value: 'custom', label: '自定义' }
])

const selectedProvider = ref('modelscope')
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

// 自定义模型的配置存储 (每个模型独立的配置)
const customModelConfigs = ref({})  // { modelName: { apiUrl, apiKey } }

// 当前可用模型
const currentModels = computed(() => {
  const provider = selectedProvider.value
  const models = modelLists.value[provider] || []

  if (models.length === 0) {
    const defaults = {
      ollama: [{ value: 'qwen2.5:latest', label: 'Qwen 2.5' }],
      modelscope: [{ value: 'MiniMax/MiniMax-M2.5', label: 'MiniMax-M2.5 (免费)' }],
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

// 渲染 Markdown
const renderMarkdown = (content) => {
  if (!content) return ''
  try {
    // 先保护 LaTeX 公式不被 marked 破坏
    const latexBlocks = []
    let protected_content = content

    // 保护块级公式 $$...$$
    protected_content = protected_content.replace(/\$\$([\s\S]*?)\$\$/g, (match) => {
      const idx = latexBlocks.length
      latexBlocks.push(match)
      return `%%LATEX_BLOCK_${idx}%%`
    })
    // 保护行内公式 $...$
    protected_content = protected_content.replace(/\$([^\$\n]+?)\$/g, (match) => {
      const idx = latexBlocks.length
      latexBlocks.push(match)
      return `%%LATEX_BLOCK_${idx}%%`
    })
    // 保护 \(...\) 行内公式
    protected_content = protected_content.replace(/\\\(([\s\S]*?)\\\)/g, (match) => {
      const idx = latexBlocks.length
      latexBlocks.push(match)
      return `%%LATEX_BLOCK_${idx}%%`
    })
    // 保护 \[...\] 块级公式
    protected_content = protected_content.replace(/\\\[([\s\S]*?)\\\]/g, (match) => {
      const idx = latexBlocks.length
      latexBlocks.push(match)
      return `%%LATEX_BLOCK_${idx}%%`
    })

    // 使用 marked 解析
    let html = marked.parse(protected_content, { async: false })

    // 还原 LaTeX 公式并渲染
    html = html.replace(/%%LATEX_BLOCK_(\d+)%%/g, (_, idx) => {
      const original = latexBlocks[parseInt(idx)]
      return renderLatexInHtml(original)
    })

    // 为代码块添加包装器和复制按钮
    html = html.replace(/<pre><code(?: class="language-(\w+)")?>/g, (match, lang) => {
      const langLabel = lang || 'code'
      return `<div class="code-block"><div class="code-header"><span class="code-lang">${langLabel}</span><button class="copy-btn" onclick="copyCode(this)">复制</button></div><pre><code class="language-${lang || 'text'}">`
    })
    html = html.replace(/<\/code><\/pre>/g, '</code></pre></div>')

    return html
  } catch (e) {
    console.error('Markdown渲染错误:', e)
    return content
  }
}

// 用户是否上滑取消了跟随（每次发消息重置）
const userScrolled = ref(false)

// 监听滚动：用户上滑即取消跟随
const handleChatScroll = () => {
  if (!chatWindowRef.value) return
  const el = chatWindowRef.value
  const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80
  if (!atBottom) {
    userScrolled.value = true
  }
}

// 滚动到底部（仅跟随模式下）
const scrollToBottom = () => {
  nextTick(() => {
    if (chatWindowRef.value && !userScrolled.value) {
      chatWindowRef.value.scrollTop = chatWindowRef.value.scrollHeight
    }
  })
}

// 快捷提问
const quickAsk = (question) => {
  inputMessage.value = question
  sendMessage()
}

// 厂商变更
const onProviderChange = async (provider) => {
  selectedModel.value = ''
  // modelscope 不需要用户配置API密钥
  if (provider !== 'ollama' && provider !== 'modelscope' && !apiKeys.value[provider]) {
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

// 加载自定义模型列表
const loadCustomModels = async () => {
  try {
    const response = await api.get('/api/ai/custom-models')
    if (response.models) {
      modelLists.value.custom = response.models.map(m => ({
        value: m.name,
        label: m.name
      }))
      // 恢复每个模型的配置
      response.models.forEach(m => {
        customModelConfigs.value[m.name] = {
          apiUrl: m.api_url,
          apiKey: m.api_key || ''
        }
      })
    }
  } catch (error) {
    console.error('加载自定义模型失败:', error)
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
const addCustomModel = async () => {
  if (!customModelConfig.value.name || !customModelConfig.value.apiUrl) {
    ElMessage.error('请填写模型名称和API地址')
    return
  }

  const modelName = customModelConfig.value.name

  // 检查是否已存在
  if (modelLists.value.custom.some(m => m.value === modelName)) {
    ElMessage.error('该模型名称已存在')
    return
  }

  // 添加到模型列表
  modelLists.value.custom.push({
    value: modelName,
    label: modelName
  })

  // 保存自定义模型的独立配置
  customModelConfigs.value[modelName] = {
    apiUrl: customModelConfig.value.apiUrl,
    apiKey: customModelConfig.value.apiKey || ''
  }

  // 同步到后端存储
  try {
    await api.post('/api/ai/custom-models', {
      name: modelName,
      apiUrl: customModelConfig.value.apiUrl,
      apiKey: customModelConfig.value.apiKey || ''
    })
  } catch (error) {
    console.error('保存自定义模型失败:', error)
  }

  selectedProvider.value = 'custom'
  selectedModel.value = modelName

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
  isWaitingForResponse.value = true
  const userText = inputMessage.value
  inputMessage.value = ''

  // 添加用户消息
  messages.value.push({
    id: ++messageIdCounter,
    type: 'user',
    content: userText,
    timestamp: new Date(),
    status: 'sending'
  })
  userScrolled.value = false
  scrollToBottom()

  // 构造请求
  let requestConfig = {
    type: selectedProvider.value,
    name: selectedModel.value,
    apiKey: '',
    apiUrl: undefined
  }

  // 官方模型不需要用户传API Key
  if (selectedProvider.value === 'modelscope') {
    requestConfig.apiKey = ''
  } else if (selectedProvider.value === 'custom' && customModelConfigs.value[selectedModel.value]) {
    // 自定义模型使用该模型的独立配置
    const customConfig = customModelConfigs.value[selectedModel.value]
    requestConfig.apiKey = customConfig.apiKey || ''
    requestConfig.apiUrl = customConfig.apiUrl
  } else {
    requestConfig.apiKey = apiKeys.value[selectedProvider.value] || ''
  }

  const requestData = {
    prompt: userText,
    stream: true,
    modelConfig: requestConfig
  }

  // 创建AI消息索引
  const aiMsgIndex = messages.value.length
  messages.value.push({
    id: ++messageIdCounter,
    type: 'assistant',
    content: '',
    providerName: `${selectedProvider.value} - ${selectedModel.value}`,
    timestamp: new Date(),
    isStreaming: true,
    isError: false
  })
  scrollToBottom()

  try {
    const response = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData)
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let fullResponse = ''

    // 更新用户消息状态
    messages.value[aiMsgIndex - 1].status = 'sent'

    // 处理流式响应
    let streamDone = false
    while (!streamDone) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n').filter(line => line.trim())

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.error) {
              isWaitingForResponse.value = false
              fullResponse += data.error
              messages.value[aiMsgIndex].content = fullResponse
              messages.value[aiMsgIndex].isError = true
            }
            if (data.content) {
              // 收到第一个响应，关闭等待动画
              if (isWaitingForResponse.value) {
                isWaitingForResponse.value = false
              }
              fullResponse += data.content
              // 直接更新数组中的对象
              messages.value[aiMsgIndex].content = fullResponse
              scrollToBottom()
            }
            if (data.done) {
              messages.value[aiMsgIndex].isStreaming = false
              streamDone = true
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }

    // 主动释放reader，确保连接关闭
    try { reader.releaseLock() } catch (e) {}

    // 完成流式响应
    messages.value[aiMsgIndex].isStreaming = false
    isWaitingForResponse.value = false

    if (!fullResponse) {
      messages.value[aiMsgIndex].content = '[无响应内容]'
    }

  } catch (error) {
    isWaitingForResponse.value = false
    messages.value[aiMsgIndex].isStreaming = false
    messages.value[aiMsgIndex].isError = true
    messages.value[aiMsgIndex].content = `连接失败: ${error.message}`
    messages.value[aiMsgIndex - 1].status = 'sent'
    ElMessage.error('发送失败: ' + error.message)
  } finally {
    isLoading.value = false
    isWaitingForResponse.value = false
  }
}

// 重试消息
const retryMessage = async (index) => {
  // 找到对应的用户消息
  let userMsgIndex = index - 1
  while (userMsgIndex >= 0 && messages.value[userMsgIndex].type !== 'user') {
    userMsgIndex--
  }

  if (userMsgIndex >= 0) {
    const userContent = messages.value[userMsgIndex].content

    // 移除错误消息
    messages.value.splice(index, 1)

    // 重新发送
    inputMessage.value = userContent
    await sendMessage()
  }
}

// 确认清空对话
const confirmClearChat = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有对话记录吗？此操作不可撤销。',
      '清空对话',
      {
        confirmButtonText: '确定清空',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )

    messages.value = []
    try {
      await api.post('/api/ai/reset')
    } catch (error) {
      console.error('重置上下文失败:', error)
    }
    ElMessage.success('对话已清空')
  } catch {
    // 用户取消
  }
}

// 格式化日期
const formatDate = (date) => {
  return new Date(date).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 移动端：动态设置header高度CSS变量，确保聊天容器精确填满剩余视口
const updateHeaderHeight = () => {
  const header = document.querySelector('.header')
  if (header && window.innerWidth <= 768) {
    document.documentElement.style.setProperty('--header-height', header.offsetHeight + 'px')
  }
}

// 初始化
onMounted(async () => {
  updateHeaderHeight()
  window.addEventListener('resize', updateHeaderHeight)

  // 加载Ollama模型
  await refreshOllamaModels()

  // 加载自定义模型
  await loadCustomModels()

  // 加载其他厂商默认模型
  modelLists.value.modelscope = [
    { value: 'MiniMax/MiniMax-M2.5', label: 'MiniMax-M2.5 (免费)' }
  ]

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

  modelLists.value.siliconflow = [
    { value: 'Qwen/Qwen2.5-7B-Instruct', label: 'Qwen2.5 7B (免费)' },
    { value: 'Qwen/Qwen2.5-72B-Instruct', label: 'Qwen2.5 72B' },
    { value: 'deepseek-ai/DeepSeek-V2.5', label: 'DeepSeek V2.5' },
    { value: 'THUDM/glm-4-9b-chat', label: 'GLM-4 9B (免费)' },
    { value: 'meta-llama/Meta-Llama-3.1-8B-Instruct', label: 'Llama 3.1 8B' }
  ]

  if (modelLists.value.modelscope.length > 0) {
    selectedModel.value = modelLists.value.modelscope[0].value
  }
})

// 全局复制代码函数
if (typeof window !== 'undefined') {
  window.copyCode = (btn) => {
    const codeBlock = btn.closest('.code-block')
    const code = codeBlock.querySelector('code').textContent
    navigator.clipboard.writeText(code).then(() => {
      const originalText = btn.textContent
      btn.textContent = '已复制!'
      btn.classList.add('copied')
      setTimeout(() => {
        btn.textContent = originalText
        btn.classList.remove('copied')
      }, 2000)
    })
  }
}
</script>

<style scoped>
/* ========== 基础容器 ========== */
.chat-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #FFFEF7 0%, #FFF9E8 100%);
  border-radius: 16px;
  overflow: hidden;
  box-shadow:
    0 4px 24px rgba(139, 90, 43, 0.08),
    0 1px 2px rgba(139, 90, 43, 0.04);
  position: relative;
}

.chat-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
  opacity: 0.03;
  pointer-events: none;
}

/* ========== 聊天窗口 ========== */
.chat-window {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 24px;
  overflow-y: auto;
  scroll-behavior: smooth;
}

.chat-window::-webkit-scrollbar {
  width: 6px;
}

.chat-window::-webkit-scrollbar-track {
  background: transparent;
}

.chat-window::-webkit-scrollbar-thumb {
  background: rgba(139, 90, 43, 0.15);
  border-radius: 3px;
}

.chat-window::-webkit-scrollbar-thumb:hover {
  background: rgba(139, 90, 43, 0.25);
}

.chat-messages {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}

/* ========== 欢迎状态 ========== */
.welcome-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  animation: fadeIn 0.6s ease-out;
}

.welcome-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #D4A574 0%, #C4956A 100%);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(212, 165, 116, 0.3);
}

.welcome-icon svg {
  width: 40px;
  height: 40px;
  color: white;
}

.welcome-state h2 {
  font-family: 'Noto Serif SC', 'Source Han Serif CN', Georgia, serif;
  font-size: 28px;
  font-weight: 600;
  color: #3D2914;
  margin-bottom: 8px;
  letter-spacing: 0.02em;
}

.welcome-state p {
  font-size: 16px;
  color: #8B7355;
  margin-bottom: 32px;
}

.quick-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.quick-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: white;
  border: 1px solid rgba(139, 90, 43, 0.15);
  border-radius: 12px;
  font-size: 14px;
  color: #5D4E37;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 2px 8px rgba(139, 90, 43, 0.06);
}

.quick-btn:hover {
  background: linear-gradient(135deg, #FFF9E8 0%, #FFF5D6 100%);
  border-color: #D4A574;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(212, 165, 116, 0.15);
}

.quick-icon {
  font-size: 18px;
}

/* ========== 消息样式 ========== */
.message {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  max-width: 85%;
}

.message.user {
  flex-direction: row-reverse;
  margin-left: auto;
}

.message.assistant {
  margin-right: auto;
}

/* 消息入场动画 */
.message-enter-active {
  animation: messageSlideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.message-leave-active {
  animation: messageSlideOut 0.3s ease-in;
}

@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes messageSlideOut {
  from {
    opacity: 1;
    transform: translateX(0);
  }
  to {
    opacity: 0;
    transform: translateX(30px);
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* ========== 头像 ========== */
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar svg {
  width: 20px;
  height: 20px;
}

.ai-avatar {
  background: linear-gradient(135deg, #D4A574 0%, #C4956A 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(212, 165, 116, 0.3);
}

.user-avatar {
  background: linear-gradient(135deg, #5D4E37 0%, #4A3C2A 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(93, 78, 55, 0.3);
}

/* ========== 消息主体 ========== */
.message-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.assistant-label {
  background: linear-gradient(135deg, #D4A574 0%, #C4956A 100%);
  color: white;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.02em;
}

.message-time {
  font-size: 11px;
  color: #A89880;
}

/* ========== 消息气泡 ========== */
.message-bubble {
  padding: 14px 18px;
  border-radius: 18px;
  line-height: 1.7;
  word-break: break-word;
  font-size: 15px;
  position: relative;
}

.message-bubble.assistant {
  background: white;
  color: #3D2914;
  border: 1px solid rgba(139, 90, 43, 0.1);
  border-top-left-radius: 4px;
  box-shadow: 0 2px 12px rgba(139, 90, 43, 0.06);
}

.message-bubble.assistant.has-error {
  background: linear-gradient(135deg, #FFF5F5 0%, #FEEAEA 100%);
  border-color: rgba(220, 76, 100, 0.2);
  color: #DC4C64;
}

.message-bubble.user {
  background: linear-gradient(135deg, #D4A574 0%, #C4956A 100%);
  color: white;
  border-top-right-radius: 4px;
  box-shadow: 0 2px 12px rgba(212, 165, 116, 0.2);
}

/* ========== Markdown 内容样式 ========== */
.markdown-content {
  font-family: 'Noto Serif SC', 'Source Han Serif CN', Georgia, serif;
}

.markdown-content :deep(p) {
  margin: 0 0 12px 0;
}

.markdown-content :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4) {
  font-family: 'Noto Serif SC', 'Source Han Serif CN', Georgia, serif;
  margin: 16px 0 8px 0;
  color: #3D2914;
  font-weight: 600;
}

.markdown-content :deep(h1:first-child),
.markdown-content :deep(h2:first-child),
.markdown-content :deep(h3:first-child) {
  margin-top: 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.markdown-content :deep(li) {
  margin: 4px 0;
}

.markdown-content :deep(code) {
  background: rgba(139, 90, 43, 0.08);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.9em;
  color: #8B5A2B;
}

.markdown-content :deep(a) {
  color: #D4A574;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-color 0.2s;
}

.markdown-content :deep(a:hover) {
  border-bottom-color: #D4A574;
}

/* 代码块样式 */
.markdown-content :deep(.code-block) {
  margin: 12px 0;
  border-radius: 12px;
  overflow: hidden;
  background: #1E1E1E;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.markdown-content :deep(.code-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #2D2D2D;
  border-bottom: 1px solid #3D3D3D;
}

.markdown-content :deep(.code-lang) {
  font-size: 12px;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.markdown-content :deep(.copy-btn) {
  background: transparent;
  border: 1px solid #444;
  color: #888;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.markdown-content :deep(.copy-btn:hover) {
  background: #3D3D3D;
  color: #fff;
}

.markdown-content :deep(.copy-btn.copied) {
  background: #2E7D32;
  border-color: #2E7D32;
  color: white;
}

.markdown-content :deep(.code-block pre) {
  margin: 0;
  padding: 16px;
  overflow-x: auto;
}

.markdown-content :deep(.code-block code) {
  background: transparent;
  padding: 0;
  color: #E0E0E0;
  font-size: 13px;
  line-height: 1.6;
}

/* 打字机光标 */
.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 1.2em;
  background: #D4A574;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: cursorBlink 1s step-end infinite;
}

@keyframes cursorBlink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* 消息状态 */
.message-status {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
}

.status-icon {
  width: 14px;
  height: 14px;
}

.status-icon.sending svg {
  animation: pulse 1.5s ease-in-out infinite;
  color: rgba(255, 255, 255, 0.7);
}

.status-icon.sent svg {
  color: rgba(255, 255, 255, 0.9);
}

@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

/* 重试按钮 */
.retry-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding: 6px 12px;
  background: white;
  border: 1px solid rgba(220, 76, 100, 0.3);
  border-radius: 8px;
  font-size: 13px;
  color: #DC4C64;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-btn svg {
  width: 14px;
  height: 14px;
}

.retry-btn:hover {
  background: #DC4C64;
  color: white;
  border-color: #DC4C64;
}

/* ========== 思考中动画 ========== */
.thinking-indicator {
  background: white;
  border: 1px solid rgba(139, 90, 43, 0.1);
  border-radius: 18px;
  border-top-left-radius: 4px;
  padding: 16px 24px;
  box-shadow: 0 2px 12px rgba(139, 90, 43, 0.06);
  display: flex;
  align-items: center;
  gap: 16px;
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.thinking-label {
  font-size: 14px;
  font-weight: 500;
  color: #8B7355;
  animation: thinkingPulse 2s ease-in-out infinite;
}

.thinking-dots {
  display: flex;
  align-items: center;
  gap: 4px;
}

.thinking-dots .dot {
  width: 8px;
  height: 8px;
  background: linear-gradient(135deg, #D4A574 0%, #C4956A 100%);
  border-radius: 50%;
  animation: dotBounce 1.4s ease-in-out infinite;
}

.thinking-dots .dot:nth-child(1) {
  animation-delay: 0s;
}

.thinking-dots .dot:nth-child(2) {
  animation-delay: 0.2s;
}

.thinking-dots .dot:nth-child(3) {
  animation-delay: 0.4s;
}

.thinking-avatar {
  animation: avatarPulse 2s ease-in-out infinite;
}

@keyframes dotBounce {
  0%, 80%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  40% {
    transform: translateY(-8px);
    opacity: 1;
  }
}

@keyframes thinkingPulse {
  0%, 100% {
    opacity: 0.7;
  }
  50% {
    opacity: 1;
  }
}

@keyframes avatarPulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 2px 8px rgba(212, 165, 116, 0.3);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 4px 16px rgba(212, 165, 116, 0.4);
  }
}

/* ========== 输入区域 ========== */
.chat-input {
  padding: 20px 24px;
  background: white;
  border-top: 1px solid rgba(139, 90, 43, 0.1);
  transition: opacity 0.3s;
}

.chat-input.is-loading {
  opacity: 0.85;
}

.input-wrapper {
  margin-bottom: 12px;
  position: relative;
}

.input-wrapper :deep(.el-textarea__inner) {
  background: #FFFEF7;
  border: 1px solid rgba(139, 90, 43, 0.15);
  border-radius: 12px;
  padding: 14px 16px;
  font-size: 15px;
  color: #3D2914;
  resize: none;
  transition: all 0.25s;
  line-height: 1.6;
}

.input-wrapper :deep(.el-textarea__inner):focus {
  border-color: #D4A574;
  box-shadow: 0 0 0 3px rgba(212, 165, 116, 0.15);
}

.input-wrapper :deep(.el-textarea__inner::placeholder) {
  color: #A89880;
}

.input-wrapper :deep(.el-textarea__inner:disabled) {
  background: #F9F6F0;
  cursor: not-allowed;
}

.input-hint {
  position: absolute;
  right: 12px;
  bottom: 8px;
  font-size: 11px;
  color: #C4B8A0;
  pointer-events: none;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.model-selector {
  display: flex;
  gap: 10px;
}

.model-selector :deep(.el-select) {
  width: 130px;
}

.model-selector :deep(.el-input__wrapper) {
  background: #FFFEF7;
  border: 1px solid rgba(139, 90, 43, 0.15);
  border-radius: 8px;
  box-shadow: none;
}

.model-selector :deep(.el-input__wrapper:hover) {
  border-color: #D4A574;
}

.model-selector :deep(.el-input__inner) {
  color: #5D4E37;
  font-size: 13px;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.clear-btn,
.config-btn {
  width: 40px;
  height: 40px;
  padding: 0;
  background: #FFFEF7;
  border: 1px solid rgba(139, 90, 43, 0.15);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.clear-btn svg,
.config-btn svg {
  width: 18px;
  height: 18px;
  color: #8B7355;
}

.clear-btn:hover,
.config-btn:hover {
  background: #FFF5E6;
  border-color: #D4A574;
  color: #D4A574;
}

.clear-btn:hover svg,
.config-btn:hover svg {
  color: #D4A574;
}

.send-btn {
  height: 40px;
  padding: 0 24px;
  background: linear-gradient(135deg, #D4A574 0%, #C4956A 100%);
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 500;
  color: white;
  transition: all 0.25s;
  box-shadow: 0 2px 12px rgba(212, 165, 116, 0.25);
}

.send-btn:hover {
  background: linear-gradient(135deg, #C4956A 0%, #B4855A 100%);
  box-shadow: 0 4px 16px rgba(212, 165, 116, 0.35);
  transform: translateY(-1px);
}

.send-btn :deep(.el-loading-spinner) {
  margin-right: 6px;
}

.sending-text {
  margin-left: 4px;
}

/* ========== 配置对话框 ========== */
.config-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
}

.config-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #FFFEF7 0%, #FFF9E8 100%);
  border-bottom: 1px solid rgba(139, 90, 43, 0.1);
  padding: 20px 24px;
}

.config-dialog :deep(.el-dialog__title) {
  font-family: 'Noto Serif SC', 'Source Han Serif CN', Georgia, serif;
  color: #3D2914;
  font-weight: 600;
}

.config-dialog :deep(.el-dialog__body) {
  padding: 24px;
}

.config-tabs :deep(.el-tabs__item) {
  color: #8B7355;
}

.config-tabs :deep(.el-tabs__item.is-active) {
  color: #D4A574;
}

.config-tabs :deep(.el-tabs__active-bar) {
  background: #D4A574;
}

.provider-config {
  margin-bottom: 20px;
  padding: 16px;
  background: #FFFEF7;
  border: 1px solid rgba(139, 90, 43, 0.1);
  border-radius: 12px;
}

.provider-config h4 {
  margin-bottom: 12px;
  color: #3D2914;
  font-family: 'Noto Serif SC', 'Source Han Serif CN', Georgia, serif;
}

.no-key-required {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #52C41A;
  font-size: 14px;
}

.no-key-required svg {
  width: 18px;
  height: 18px;
}

/* ========== 移动端响应式 ========== */
@media (max-width: 768px) {
  /* 移动端：聊天容器精确填满剩余视口，避免页面级滚动 */
  .chat-container {
    height: calc(100dvh - var(--header-height, 73px) - 16px);
    border-radius: 0;
    box-shadow: none;
  }

  .chat-window {
    padding: 12px 8px;
    flex: 1;
    min-height: 0;
  }

  .welcome-state {
    padding: 20px 12px;
  }

  .welcome-icon {
    width: 48px;
    height: 48px;
    border-radius: 14px;
    margin-bottom: 12px;
  }

  .welcome-icon svg {
    width: 24px;
    height: 24px;
  }

  .welcome-state h2 {
    font-size: 20px;
    margin-bottom: 4px;
  }

  .welcome-state p {
    font-size: 14px;
    margin-bottom: 16px;
  }

  .quick-actions {
    gap: 8px;
  }

  .quick-btn {
    padding: 8px 14px;
    font-size: 13px;
  }

  .chat-input {
    padding: 10px 10px;
    padding-bottom: calc(10px + env(safe-area-inset-bottom, 0px));
    flex-shrink: 0;
  }

  .input-wrapper :deep(.el-textarea__inner) {
    padding: 8px 10px;
    font-size: 14px;
  }

  .input-hint {
    display: none;
  }

  .input-actions {
    flex-direction: column;
    gap: 8px;
  }

  .model-selector {
    width: 100%;
  }

  .model-selector :deep(.el-select) {
    flex: 1;
    width: auto;
  }

  .action-buttons {
    width: 100%;
    justify-content: flex-end;
  }

  .send-btn {
    flex: 1;
  }

  .message {
    max-width: 92%;
  }

  .message-bubble {
    padding: 10px 14px;
    font-size: 14px;
  }
}
</style>
