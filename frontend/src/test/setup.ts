/**
 * 测试环境设置
 */

import '@testing-library/jest-dom'
import { vi } from 'vitest'

// 模拟浏览器API
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// 模拟ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// 模拟IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// 模拟localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
global.localStorage = localStorageMock

// 模拟sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
global.sessionStorage = sessionStorageMock

// 模拟URL.createObjectURL
global.URL.createObjectURL = vi.fn(() => 'mocked-url')
global.URL.revokeObjectURL = vi.fn()

// 模拟fetch
global.fetch = vi.fn()

// 模拟console方法以减少测试输出噪音
global.console = {
  ...console,
  log: vi.fn(),
  debug: vi.fn(),
  info: vi.fn(),
  warn: vi.fn(),
  error: vi.fn(),
}

// 模拟window.location
delete (window as any).location
window.location = {
  ...window.location,
  assign: vi.fn(),
  replace: vi.fn(),
  reload: vi.fn(),
  href: 'http://localhost:3000',
  origin: 'http://localhost:3000',
  protocol: 'http:',
  host: 'localhost:3000',
  hostname: 'localhost',
  port: '3000',
  pathname: '/',
  search: '',
  hash: '',
}

// 模拟navigator
Object.defineProperty(window, 'navigator', {
  writable: true,
  value: {
    ...window.navigator,
    clipboard: {
      writeText: vi.fn().mockResolvedValue(undefined),
      readText: vi.fn().mockResolvedValue(''),
    },
    serviceWorker: {
      register: vi.fn().mockResolvedValue({}),
      ready: Promise.resolve({}),
    },
  },
})

// 模拟ECharts
vi.mock('echarts', () => ({
  init: vi.fn(() => ({
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
  })),
  dispose: vi.fn(),
  registerTheme: vi.fn(),
}))

// 模拟Ant Design的一些组件
vi.mock('antd', async () => {
  const actual = await vi.importActual('antd')
  return {
    ...actual,
    message: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      info: vi.fn(),
      loading: vi.fn(),
    },
    notification: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      info: vi.fn(),
      open: vi.fn(),
    },
  }
})

// 清理函数
afterEach(() => {
  vi.clearAllMocks()
  localStorageMock.clear()
  sessionStorageMock.clear()
})
