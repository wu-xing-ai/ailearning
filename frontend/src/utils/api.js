/**
 * API请求工具 - 封装统一API调用
 */
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
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    }

    const config = { ...defaultOptions, ...options }
    const response = await fetch(url, config)

    // 处理流式响应
    if (options.responseType === 'stream') {
      return response
    }

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.error || '请求失败')
    }

    return result
  },

  // 通用GET请求
  async get(url) {
    const response = await fetch(url)
    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.error || '请求失败')
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
    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.detail || '删除失败')
    }

    return result
  }
}

export default api