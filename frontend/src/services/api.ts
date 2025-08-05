/**
 * API客户端配置和请求封装
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { message } from 'antd'

// API基础配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

// 创建axios实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 添加认证token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误和token过期
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          // Token过期或无效，清除本地存储并跳转到登录页
          localStorage.removeItem('access_token')
          localStorage.removeItem('user_info')
          message.error('登录已过期，请重新登录')
          window.location.href = '/login'
          break
        case 403:
          message.error('权限不足')
          break
        case 404:
          message.error('请求的资源不存在')
          break
        case 500:
          message.error('服务器内部错误')
          break
        default:
          message.error(data?.message || '请求失败')
      }
    } else if (error.request) {
      message.error('网络连接失败，请检查网络设置')
    } else {
      message.error('请求配置错误')
    }
    
    return Promise.reject(error)
  }
)

// API响应类型定义
export interface ApiResponse<T = any> {
  data: T
  message?: string
  status?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}

// 通用API请求方法
export const api = {
  // GET请求
  get: <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    return apiClient.get(url, config).then(response => response.data)
  },

  // POST请求
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    return apiClient.post(url, data, config).then(response => response.data)
  },

  // PUT请求
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    return apiClient.put(url, data, config).then(response => response.data)
  },

  // DELETE请求
  delete: <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    return apiClient.delete(url, config).then(response => response.data)
  },

  // PATCH请求
  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    return apiClient.patch(url, data, config).then(response => response.data)
  },
}

// 认证相关API
export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface User {
  id: string
  username: string
  email: string
  role: string
  is_active: boolean
  created_at?: string
  updated_at?: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

export const authApi = {
  // 用户登录
  login: (data: LoginRequest): Promise<TokenResponse> => {
    return api.post('/auth/login', data)
  },

  // 用户注册
  register: (data: RegisterRequest): Promise<User> => {
    return api.post('/auth/register', data)
  },

  // 获取当前用户信息
  getCurrentUser: (): Promise<User> => {
    return api.get('/auth/me')
  },

  // 刷新token
  refreshToken: (): Promise<TokenResponse> => {
    return api.post('/auth/refresh')
  },
}

// 用户相关API
export const userApi = {
  // 获取用户资料
  getProfile: (): Promise<User> => {
    return api.get('/users/profile')
  },

  // 获取用户偏好设置
  getPreferences: (): Promise<any> => {
    return api.get('/users/preferences')
  },

  // 更新用户偏好设置
  updatePreferences: (data: any): Promise<any> => {
    return api.put('/users/preferences', data)
  },

  // 获取用户统计信息
  getStats: (): Promise<any> => {
    return api.get('/users/stats')
  },
}

// 提示词相关API
export interface Prompt {
  id: string
  user_id: string
  title?: string
  content: string
  category?: string
  tags: string[]
  is_template: boolean
  is_public: boolean
  created_at?: string
  updated_at?: string
}

export const promptApi = {
  // 获取提示词列表
  getPrompts: (params?: {
    skip?: number
    limit?: number
    category?: string
  }): Promise<PaginatedResponse<Prompt>> => {
    return api.get('/prompts', { params })
  },

  // 创建提示词
  createPrompt: (data: Partial<Prompt>): Promise<Prompt> => {
    return api.post('/prompts', data)
  },

  // 获取特定提示词
  getPrompt: (id: string): Promise<Prompt> => {
    return api.get(`/prompts/${id}`)
  },

  // 更新提示词
  updatePrompt: (id: string, data: Partial<Prompt>): Promise<Prompt> => {
    return api.put(`/prompts/${id}`, data)
  },

  // 删除提示词
  deletePrompt: (id: string): Promise<{ message: string }> => {
    return api.delete(`/prompts/${id}`)
  },

  // 获取提示词分析结果
  getPromptAnalysis: (id: string): Promise<any> => {
    return api.get(`/prompts/${id}/analysis`)
  },

  // 获取分类列表
  getCategories: (): Promise<string[]> => {
    return api.get('/prompts/categories')
  },
}

// 分析相关API
export const analysisApi = {
  // 分析提示词
  analyzePrompt: (data: {
    content: string
    prompt_id?: string
    ai_model?: string
  }): Promise<any> => {
    return api.post('/analysis/analyze', data)
  },

  // 获取分析结果
  getAnalysisResult: (id: string): Promise<any> => {
    return api.get(`/analysis/${id}`)
  },

  // 获取分析历史
  getAnalysisHistory: (params?: {
    skip?: number
    limit?: number
  }): Promise<PaginatedResponse<any>> => {
    return api.get('/analysis', { params })
  },

  // 删除分析结果
  deleteAnalysis: (id: string): Promise<{ message: string }> => {
    return api.delete(`/analysis/${id}`)
  },
}

// 优化建议相关API
export const optimizationApi = {
  // 生成优化建议
  generateSuggestions: (data: { analysis_id: string }): Promise<any> => {
    return api.post('/optimization/suggest', data)
  },

  // 获取优化建议
  getSuggestions: (analysisId: string): Promise<any[]> => {
    return api.get(`/optimization/${analysisId}/suggestions`)
  },

  // 应用优化建议
  applySuggestion: (id: string): Promise<any> => {
    return api.put(`/optimization/${id}/apply`)
  },

  // 删除优化建议
  deleteSuggestion: (id: string): Promise<{ message: string }> => {
    return api.delete(`/optimization/${id}`)
  },

  // 批量应用优化建议
  applyMultipleSuggestions: (data: {
    suggestion_ids: string[]
    original_prompt: string
  }): Promise<any> => {
    return api.post('/optimization/apply-suggestions', data)
  },

  // 获取优化效果统计
  getOptimizationEffectiveness: (analysisId: string): Promise<any> => {
    return api.get(`/optimization/effectiveness/${analysisId}`)
  },

  // 获取用户优化统计
  getUserOptimizationStats: (): Promise<any> => {
    return api.get('/optimization/user-stats')
  },
}

// 模板API
export const templateApi = {
  // 获取模板列表
  getTemplates: (params?: any): Promise<any> => {
    return api.get('/templates', { params })
  },

  // 获取单个模板
  getTemplate: (id: string): Promise<any> => {
    return api.get(`/templates/${id}`)
  },

  // 创建模板
  createTemplate: (data: any): Promise<any> => {
    return api.post('/templates', data)
  },

  // 更新模板
  updateTemplate: (id: string, data: any): Promise<any> => {
    return api.put(`/templates/${id}`, data)
  },

  // 删除模板
  deleteTemplate: (id: string): Promise<any> => {
    return api.delete(`/templates/${id}`)
  },

  // 使用模板
  useTemplate: (id: string): Promise<any> => {
    return api.post(`/templates/${id}/use`)
  },

  // 评分模板
  rateTemplate: (id: string, data: { rating: number; comment?: string }): Promise<any> => {
    return api.post(`/templates/${id}/rate`, data)
  },

  // 获取热门模板
  getPopularTemplates: (params?: { limit?: number }): Promise<any> => {
    return api.get('/templates/popular/list', { params })
  },

  // 获取推荐模板
  getFeaturedTemplates: (params?: { limit?: number }): Promise<any> => {
    return api.get('/templates/featured/list', { params })
  },

  // 获取最新模板
  getRecentTemplates: (params?: { limit?: number }): Promise<any> => {
    return api.get('/templates/recent/list', { params })
  },

  // 获取分类列表
  getCategories: (): Promise<any> => {
    return api.get('/templates/categories/list')
  },

  // 获取标签列表
  getTags: (params?: { featured_only?: boolean; limit?: number }): Promise<any> => {
    return api.get('/templates/tags/list', { params })
  },
}

// 模板相关API
export interface Template {
  id: string
  creator_id?: string
  name: string
  description?: string
  content: string
  category?: string
  tags: string[]
  usage_count: number
  rating: number
  is_featured: boolean
  is_public: boolean
  created_at?: string
  updated_at?: string
}

export const templateApi = {
  // 获取模板列表
  getTemplates: (params?: {
    skip?: number
    limit?: number
    category?: string
    is_featured?: boolean
    is_public?: boolean
  }): Promise<PaginatedResponse<Template>> => {
    return api.get('/templates', { params })
  },

  // 创建模板
  createTemplate: (data: Partial<Template>): Promise<Template> => {
    return api.post('/templates', data)
  },

  // 获取特定模板
  getTemplate: (id: string): Promise<Template> => {
    return api.get(`/templates/${id}`)
  },

  // 更新模板
  updateTemplate: (id: string, data: Partial<Template>): Promise<Template> => {
    return api.put(`/templates/${id}`, data)
  },

  // 删除模板
  deleteTemplate: (id: string): Promise<{ message: string }> => {
    return api.delete(`/templates/${id}`)
  },

  // 使用模板
  useTemplate: (id: string): Promise<any> => {
    return api.post(`/templates/${id}/use`)
  },

  // 评价模板
  rateTemplate: (id: string, data: { rating: number; comment?: string }): Promise<any> => {
    return api.post(`/templates/${id}/rate`, data)
  },

  // 获取模板分类
  getCategories: (): Promise<string[]> => {
    return api.get('/templates/categories')
  },
}

export default api
