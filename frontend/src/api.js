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
  (response) => response.data,
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
}

// JD API
export const jdApi = {
  list: (params) => api.get('/jd', { params }),
  get: (id) => api.get(`/jd/${id}`),
  create: (data) => api.post('/jd', data),
  update: (id, data) => api.put(`/jd/${id}`, data),
  delete: (id) => api.delete(`/jd/${id}`),
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
  parse: (id, params) => api.post(`/resume/${id}/parse`, null, { params }),
  delete: (id) => api.delete(`/resume/${id}`),
}

// 优化 API
export const optimizationApi = {
  list: (params) => api.get('/optimization', { params }),
  get: (id) => api.get(`/optimization/${id}`),
  create: (data) => api.post('/optimization', data),
  execute: (id) => api.post(`/optimization/${id}/execute`),
}

// 面试攻略 API
export const interviewApi = {
  list: (params) => api.get('/interview', { params }),
  get: (id) => api.get(`/interview/${id}`),
  create: (data) => api.post('/interview', data),
  generate: (id, params) => api.post(`/interview/${id}/generate`, null, { params }),
  getByOptimization: (optimizationId) => api.get(`/interview/by-optimization/${optimizationId}`),
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

export default api
