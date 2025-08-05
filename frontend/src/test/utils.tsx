/**
 * 测试工具函数
 */

import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { vi } from 'vitest'

// 测试包装器组件
const AllTheProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <BrowserRouter>
      <ConfigProvider locale={zhCN}>
        {children}
      </ConfigProvider>
    </BrowserRouter>
  )
}

// 自定义渲染函数
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options })

// 重新导出所有testing-library的功能
export * from '@testing-library/react'
export { customRender as render }

// 测试数据工厂
export const createMockUser = (overrides = {}) => ({
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  full_name: 'Test User',
  is_active: true,
  is_verified: true,
  created_at: '2024-01-01T00:00:00Z',
  ...overrides,
})

export const createMockPrompt = (overrides = {}) => ({
  id: 1,
  title: '测试提示词',
  content: '这是一个测试提示词内容',
  description: '测试描述',
  category: '测试分类',
  tags: ['测试', '单元测试'],
  user_id: 1,
  is_public: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  ...overrides,
})

export const createMockTemplate = (overrides = {}) => ({
  id: 1,
  name: '测试模板',
  content: '这是一个测试模板：{variable}',
  description: '测试模板描述',
  category: '测试分类',
  tags: ['测试', '模板'],
  variables: ['variable'],
  user_id: 1,
  is_public: true,
  is_featured: false,
  usage_count: 0,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  ...overrides,
})

export const createMockAnalysis = (overrides = {}) => ({
  id: 1,
  prompt_id: 1,
  user_id: 1,
  overall_score: 85.5,
  semantic_clarity: 90.0,
  structural_integrity: 85.0,
  logical_coherence: 80.0,
  specificity_score: 88.0,
  instruction_clarity: 92.0,
  context_completeness: 85.0,
  analysis_details: {
    word_count: 50,
    sentence_count: 3,
    avg_sentence_length: 16.7,
    complexity_score: 0.6,
    readability_score: 0.8,
  },
  suggestions: [
    '建议增加更多具体的示例',
    '可以进一步明确输出格式要求',
  ],
  ai_model_used: 'gpt-3.5-turbo',
  processing_time_ms: 1500,
  created_at: '2024-01-01T00:00:00Z',
  ...overrides,
})

// API模拟工具
export const mockApiResponse = (data: any, status = 200) => {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
  })
}

export const mockApiError = (message = 'API Error', status = 500) => {
  return Promise.reject({
    response: {
      status,
      data: { detail: message },
    },
  })
}

// 事件模拟工具
export const mockEvent = (overrides = {}) => ({
  preventDefault: vi.fn(),
  stopPropagation: vi.fn(),
  target: { value: '' },
  ...overrides,
})

export const mockFileEvent = (files: File[]) => ({
  preventDefault: vi.fn(),
  stopPropagation: vi.fn(),
  target: { files },
  dataTransfer: { files },
})

// 创建模拟文件
export const createMockFile = (
  name = 'test.txt',
  content = 'test content',
  type = 'text/plain'
) => {
  const file = new File([content], name, { type })
  return file
}

// 等待异步操作完成
export const waitForAsync = () => new Promise(resolve => setTimeout(resolve, 0))

// 模拟定时器
export const mockTimers = () => {
  vi.useFakeTimers()
  return {
    advanceTimersByTime: vi.advanceTimersByTime,
    runAllTimers: vi.runAllTimers,
    runOnlyPendingTimers: vi.runOnlyPendingTimers,
    restore: vi.useRealTimers,
  }
}

// 模拟网络请求
export const mockFetch = (response: any, status = 200) => {
  const mockResponse = {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(response),
    text: () => Promise.resolve(JSON.stringify(response)),
  }
  
  global.fetch = vi.fn().mockResolvedValue(mockResponse)
  return global.fetch
}

// 模拟localStorage
export const mockLocalStorage = () => {
  const store: Record<string, string> = {}
  
  const mockStorage = {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      Object.keys(store).forEach(key => delete store[key])
    }),
  }
  
  Object.defineProperty(window, 'localStorage', {
    value: mockStorage,
  })
  
  return mockStorage
}

// 模拟路由
export const mockRouter = () => {
  const mockNavigate = vi.fn()
  const mockLocation = {
    pathname: '/',
    search: '',
    hash: '',
    state: null,
  }
  
  vi.mock('react-router-dom', async () => {
    const actual = await vi.importActual('react-router-dom')
    return {
      ...actual,
      useNavigate: () => mockNavigate,
      useLocation: () => mockLocation,
      useParams: () => ({}),
      useSearchParams: () => [new URLSearchParams(), vi.fn()],
    }
  })
  
  return { mockNavigate, mockLocation }
}

// 断言工具
export const expectElementToBeInDocument = (element: HTMLElement | null) => {
  expect(element).toBeInTheDocument()
}

export const expectElementToHaveText = (element: HTMLElement | null, text: string) => {
  expect(element).toHaveTextContent(text)
}

export const expectElementToHaveClass = (element: HTMLElement | null, className: string) => {
  expect(element).toHaveClass(className)
}
