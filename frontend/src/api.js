import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 300000, // 5分钟，LLM 调用耗时较长
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // blob 类型（文件下载）直接返回整个 response，避免丢失
    if (response.config?.responseType === 'blob') {
      return response
    }
    return response.data
  },
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

// 公司 API
export const companyApi = {
  list: (params) => api.get('/companies', { params }),
  get: (id) => api.get(`/companies/${id}`),
  create: (data) => api.post('/companies', data),
  update: (id, data) => api.put(`/companies/${id}`, data),
  delete: (id) => api.delete(`/companies/${id}`),
  batchDelete: (ids) => api.post('/companies/batch-delete', { ids }),
}

// JD API
export const jdApi = {
  list: (params) => api.get('/jd', { params }),
  get: (id) => api.get(`/jd/${id}`),
  create: (data) => api.post('/jd', data),
  update: (id, data) => api.put(`/jd/${id}`, data),
  delete: (id) => api.delete(`/jd/${id}`),
  batchDelete: (ids) => api.post('/jd/batch-delete', { ids }),
  parse: (id, params) => api.post(`/jd/${id}/parse`, null, { params }),
}

// 简历 API
export const resumeApi = {
  list: (params) => api.get('/resume', { params }),
  get: (id) => api.get(`/resume/${id}`),
  upload: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/resume/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  parse: (id, provider, customPrompt) => {
    const params = {}
    if (provider) params.llm_provider = provider
    if (customPrompt) params.custom_prompt = customPrompt
    return api.post(`/resume/${id}/parse`, null, { params })
  },
  deepAnalyze: (id, provider, customPrompt) => {
    const params = {}
    if (provider) params.llm_provider = provider
    if (customPrompt) params.custom_prompt = customPrompt
    return api.post(`/resume/${id}/deep-analyze`, null, { params })
  },
  updateProfile: (id, data) => api.put(`/resume/${id}/profile`, data),
  delete: (id) => api.delete(`/resume/${id}`),
  getParsePrompt: () => api.get('/resume/prompts/parse'),
  getDeepAnalyzePrompt: () => api.get('/resume/prompts/deep-analyze'),
  getVersions: (id) => api.get(`/resume/${id}/versions`),
  getVersion: (resumeId, versionId) => api.get(`/resume/${resumeId}/versions/${versionId}`),
  restoreVersion: (resumeId, versionId) => api.post(`/resume/${resumeId}/versions/${versionId}/restore`),
}

// 优化 API
export const optimizationApi = {
  list: (params) => api.get('/optimization', { params }),
  get: (id) => api.get(`/optimization/${id}`),
  create: (data) => api.post('/optimization', data),
  execute: (id) => api.post(`/optimization/${id}/execute`),
  delete: (id) => api.delete(`/optimization/${id}`),
  batchDelete: (ids) => api.post('/optimization/batch-delete', { ids }),
}

// 面试攻略 API
export const interviewApi = {
  list: (params) => api.get('/interview', { params }),
  get: (id) => api.get(`/interview/${id}`),
  create: (data) => api.post('/interview', data),
  generate: (id, params) => api.post(`/interview/${id}/generate`, null, { params }),
  getByOptimization: (optimizationId) => api.get(`/interview/by-optimization/${optimizationId}`),
  delete: (id) => api.delete(`/interview/${id}`),
  batchDelete: (ids) => api.post('/interview/batch-delete', { ids }),
}

// LLM API
export const llmApi = {
  getProviders: () => api.get('/llm/providers'),
  getModels: (provider) => api.get(`/llm/providers/${provider}/models`),
  getAllModels: () => api.get('/llm/models'),
}

// 统计 API
export const statsApi = {
  getDashboard: () => api.get('/stats/dashboard'),
}

// 模板 API
export const templateApi = {
  list: () => api.get('/templates'),
  get: (id) => api.get(`/templates/${id}`),
}

// LLM 日志 API
export const llmLogApi = {
  list: (params) => api.get('/llm-logs', { params }),
  get: (id) => api.get(`/llm-logs/${id}`),
  stats: () => api.get('/llm-logs/stats/summary'),
}

/**
 * 文件下载辅助函数
 * 绕过响应拦截器，直接返回 Blob
 */
export const downloadFile = async (url, filename) => {
  const response = await api.get(url, { responseType: 'blob' })
  // blob 拦截器返回完整 response
  const blob = response.data || response
  const blobUrl = window.URL.createObjectURL(new Blob([blob]))
  const link = document.createElement('a')
  link.href = blobUrl
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(blobUrl)
}

export default api
