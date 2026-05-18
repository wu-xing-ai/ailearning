/**
 * API请求工具 - 封装统一API调用，支持JWT认证
 */
async function parseResponse(response) {
  const contentType = response.headers.get('content-type') || ''

  if (contentType.includes('application/json')) {
    return response.json()
  }

  const text = await response.text()
  return { detail: text || '请求失败' }
}

function handleAuthError(response) {
  if (response.status === 401) {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
    return true
  }
  return false
}

function getAuthHeaders() {
  const token = localStorage.getItem('auth_token')
  if (token) {
    return { 'Authorization': `Bearer ${token}` }
  }
  return {}
}

const api = {
  // 对话接口
  async postChat(prompt, stream = true, modelConfig = {}) {
    const requestBody = {
      prompt,
      stream,
      ...(modelConfig && { modelConfig })
    }

    const options = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    }

    const response = await fetch('/api/ai/chat', options)
    return response
  },

  // 通用POST请求
  async post(url, data = {}, options = {}) {
    const defaultOptions = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(data)
    }

    const config = { ...defaultOptions, ...options }
    const response = await fetch(url, config)

    // 处理流式响应
    if (options.responseType === 'stream') {
      return response
    }

    // 处理流式响应
    if (options.responseType === 'stream') {
      if (response.status === 401) {
        handleAuthError(response)
        throw new Error('登录已过期，请重新登录')
      }
      return response
    }

    const result = await parseResponse(response)

    if (!response.ok) {
      handleAuthError(response)
      throw new Error(result.detail || result.error || '请求失败')
    }

    return result
  },

  // 通用GET请求
  async get(url) {
    const response = await fetch(url, { headers: getAuthHeaders() })
    const result = await parseResponse(response)

    if (!response.ok) {
      handleAuthError(response)
      throw new Error(result.detail || result.error || '请求失败')
    }

    return result
  },

  // 配置管理
  async getConfig() {
    return this.get('/api/ai/config')
  },

  async saveConfig(config) {
    return this.post('/api/ai/config', config)
  },

  async getModels() {
    return this.get('/api/ai/models')
  },

  async resetContext() {
    return this.post('/api/ai/reset')
  },

  // 文档上传 - 单文件
  async uploadDocument(file) {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch('/api/documents', {
      method: 'POST',
      body: formData
      // 注意：不要设置 Content-Type，让浏览器自动设置 multipart/form-data
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.detail || '上传失败')
    }

    return result
  },

  // 批量上传文档
  async uploadDocuments(files) {
    const results = []
    for (const file of files) {
      try {
        const result = await this.uploadDocument(file.raw || file)
        results.push({ success: true, ...result })
      } catch (error) {
        results.push({ success: false, filename: file.name, error: error.message })
      }
    }
    return results
  },

  // 获取文档列表
  async getDocuments() {
    return this.get('/api/documents')
  },

  // 删除文档
  async deleteDocument(docId) {
    const response = await fetch(`/api/documents/${docId}`, {
      method: 'DELETE'
    })
    const result = await parseResponse(response)

    if (!response.ok) {
      throw new Error(result.detail || result.error || '删除失败')
    }

    return result
  },

  // AI智能结构化处理
  async processKnowledgeAI(docId, provider = 'ollama', modelName = '', force = false) {
    return this.post('/api/knowledge/process-ai', {
      doc_id: docId,
      provider,
      model_name: modelName,
      force
    })
  },

  // 语义搜索
  async semanticSearch(query, mode = 'hybrid', topK = 10, docIds = null) {
    let url = `/api/search/semantic?q=${encodeURIComponent(query)}&mode=${mode}&top_k=${topK}`
    if (docIds) url += `&doc_ids=${docIds.join(',')}`
    return this.get(url)
  },

  // 生成向量嵌入
  async indexEmbeddings(docId) {
    return this.post('/api/embeddings/index', { doc_id: docId })
  },

  // 获取嵌入服务状态
  async getEmbeddingStats() {
    return this.get('/api/embeddings/stats')
  },

  // 学习进度
  async getProgressDashboard() { return this.get('/api/progress/dashboard') },
  async getDocumentProgress(docId) { return this.get(`/api/progress/document/${docId}`) },
  async updateReadingProgress(docId, chunkIndex, timeSeconds) {
    return this.post('/api/progress/reading', { document_id: docId, chunk_index: chunkIndex, time_seconds: timeSeconds })
  },
  async updateMastery(docId, pointText, delta = 0.1) {
    return this.post('/api/progress/mastery', { document_id: docId, knowledge_point_text: pointText, delta })
  },
  async startStudySession(docId, sessionType = 'reading') {
    return this.post('/api/progress/session/start', { document_id: docId, session_type: sessionType })
  },
  async endStudySession(sessionId) {
    return this.post('/api/progress/session/end', { session_id: sessionId })
  },
  beaconEndStudySession(sessionId) {
    if (!sessionId) return
    const blob = new Blob([JSON.stringify({ session_id: sessionId })], { type: 'application/json' })
    navigator.sendBeacon('/api/progress/session/beacon', blob)
  },

  // 做题练习
  async getQuizDocuments() {
    return this.get('/api/quizzes/documents')
  },
  async getDocumentQuizzes(docId) {
    return this.get(`/api/quizzes/document/${docId}`)
  },
  async generateQuizzes(docId, provider = 'modelscope', modelName = 'MiniMax/MiniMax-M2.5', force = false) {
    return this.post('/api/quizzes/generate', {
      doc_id: docId, provider, model_name: modelName, force
    })
  },
  async submitQuizAnswer(quizQuestionId, selectedIndex) {
    return this.post('/api/quizzes/answer', {
      quiz_question_id: quizQuestionId, selected_index: selectedIndex
    })
  },
  async getQuizStats(docId) {
    return this.get(`/api/quizzes/stats/${docId}`)
  }
}

export default api