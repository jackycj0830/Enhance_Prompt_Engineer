/**
 * 错误处理工具
 */

import { message, notification } from 'antd'

// 错误类型枚举
export enum ErrorType {
  NETWORK = 'NETWORK',
  VALIDATION = 'VALIDATION',
  AUTHENTICATION = 'AUTHENTICATION',
  AUTHORIZATION = 'AUTHORIZATION',
  SERVER = 'SERVER',
  CLIENT = 'CLIENT',
  UNKNOWN = 'UNKNOWN'
}

// 错误严重程度
export enum ErrorSeverity {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}

// 错误信息接口
export interface ErrorInfo {
  type: ErrorType
  severity: ErrorSeverity
  message: string
  code?: string | number
  details?: any
  timestamp: string
  stack?: string
  context?: Record<string, any>
}

// 错误处理配置
interface ErrorHandlerConfig {
  showNotification: boolean
  showMessage: boolean
  logToConsole: boolean
  reportToServer: boolean
  retryable: boolean
  maxRetries: number
}

// 默认错误处理配置
const defaultConfig: ErrorHandlerConfig = {
  showNotification: true,
  showMessage: false,
  logToConsole: true,
  reportToServer: true,
  retryable: false,
  maxRetries: 3
}

// 错误处理器类
export class ErrorHandler {
  private static instance: ErrorHandler
  private config: ErrorHandlerConfig = defaultConfig
  private errorQueue: ErrorInfo[] = []
  private retryCount = new Map<string, number>()

  static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler()
    }
    return ErrorHandler.instance
  }

  // 设置配置
  setConfig(config: Partial<ErrorHandlerConfig>) {
    this.config = { ...this.config, ...config }
  }

  // 处理错误
  handle(error: Error | ErrorInfo, context?: Record<string, any>) {
    const errorInfo = this.normalizeError(error, context)
    
    // 记录错误
    this.logError(errorInfo)
    
    // 显示用户友好的错误信息
    this.showUserError(errorInfo)
    
    // 上报错误
    if (this.config.reportToServer) {
      this.reportError(errorInfo)
    }
    
    // 添加到错误队列
    this.addToQueue(errorInfo)
    
    return errorInfo
  }

  // 标准化错误
  private normalizeError(error: Error | ErrorInfo, context?: Record<string, any>): ErrorInfo {
    if (this.isErrorInfo(error)) {
      return { ...error, context: { ...error.context, ...context } }
    }

    // 根据错误类型和消息判断错误类型
    const type = this.determineErrorType(error)
    const severity = this.determineSeverity(error, type)

    return {
      type,
      severity,
      message: this.getUserFriendlyMessage(error, type),
      details: error.message,
      timestamp: new Date().toISOString(),
      stack: error.stack,
      context
    }
  }

  private isErrorInfo(error: any): error is ErrorInfo {
    return error && typeof error === 'object' && 'type' in error && 'severity' in error
  }

  // 确定错误类型
  private determineErrorType(error: Error): ErrorType {
    const message = error.message.toLowerCase()
    
    if (message.includes('network') || message.includes('fetch')) {
      return ErrorType.NETWORK
    }
    if (message.includes('unauthorized') || message.includes('401')) {
      return ErrorType.AUTHENTICATION
    }
    if (message.includes('forbidden') || message.includes('403')) {
      return ErrorType.AUTHORIZATION
    }
    if (message.includes('validation') || message.includes('invalid')) {
      return ErrorType.VALIDATION
    }
    if (message.includes('server') || message.includes('500')) {
      return ErrorType.SERVER
    }
    
    return ErrorType.CLIENT
  }

  // 确定错误严重程度
  private determineSeverity(error: Error, type: ErrorType): ErrorSeverity {
    switch (type) {
      case ErrorType.AUTHENTICATION:
      case ErrorType.AUTHORIZATION:
        return ErrorSeverity.HIGH
      case ErrorType.SERVER:
        return ErrorSeverity.CRITICAL
      case ErrorType.NETWORK:
        return ErrorSeverity.MEDIUM
      case ErrorType.VALIDATION:
        return ErrorSeverity.LOW
      default:
        return ErrorSeverity.MEDIUM
    }
  }

  // 获取用户友好的错误消息
  private getUserFriendlyMessage(error: Error, type: ErrorType): string {
    const errorMessages = {
      [ErrorType.NETWORK]: '网络连接失败，请检查网络设置后重试',
      [ErrorType.AUTHENTICATION]: '登录已过期，请重新登录',
      [ErrorType.AUTHORIZATION]: '您没有权限执行此操作',
      [ErrorType.VALIDATION]: '输入信息有误，请检查后重试',
      [ErrorType.SERVER]: '服务器暂时不可用，请稍后重试',
      [ErrorType.CLIENT]: '操作失败，请重试',
      [ErrorType.UNKNOWN]: '发生未知错误，请联系技术支持'
    }

    return errorMessages[type] || error.message
  }

  // 记录错误
  private logError(errorInfo: ErrorInfo) {
    if (this.config.logToConsole) {
      console.group(`🚨 ${errorInfo.severity} Error - ${errorInfo.type}`)
      console.error('Message:', errorInfo.message)
      console.error('Details:', errorInfo.details)
      console.error('Context:', errorInfo.context)
      if (errorInfo.stack) {
        console.error('Stack:', errorInfo.stack)
      }
      console.groupEnd()
    }
  }

  // 显示用户错误
  private showUserError(errorInfo: ErrorInfo) {
    const { message, severity } = errorInfo

    if (this.config.showMessage) {
      switch (severity) {
        case ErrorSeverity.CRITICAL:
        case ErrorSeverity.HIGH:
          message.error(message)
          break
        case ErrorSeverity.MEDIUM:
          message.warning(message)
          break
        case ErrorSeverity.LOW:
          message.info(message)
          break
      }
    }

    if (this.config.showNotification && severity !== ErrorSeverity.LOW) {
      notification.error({
        message: '操作失败',
        description: message,
        duration: severity === ErrorSeverity.CRITICAL ? 0 : 4.5,
        placement: 'topRight'
      })
    }
  }

  // 上报错误
  private async reportError(errorInfo: ErrorInfo) {
    try {
      await fetch('/api/v1/errors/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorInfo)
      })
    } catch (error) {
      console.error('Failed to report error:', error)
    }
  }

  // 添加到错误队列
  private addToQueue(errorInfo: ErrorInfo) {
    this.errorQueue.push(errorInfo)
    
    // 限制队列大小
    if (this.errorQueue.length > 100) {
      this.errorQueue.shift()
    }
  }

  // 获取错误队列
  getErrorQueue(): ErrorInfo[] {
    return [...this.errorQueue]
  }

  // 清空错误队列
  clearErrorQueue() {
    this.errorQueue = []
  }

  // 重试操作
  async retry<T>(
    operation: () => Promise<T>,
    errorKey: string,
    maxRetries: number = this.config.maxRetries
  ): Promise<T> {
    const currentRetries = this.retryCount.get(errorKey) || 0
    
    try {
      const result = await operation()
      this.retryCount.delete(errorKey)
      return result
    } catch (error) {
      if (currentRetries < maxRetries) {
        this.retryCount.set(errorKey, currentRetries + 1)
        
        // 指数退避
        const delay = Math.pow(2, currentRetries) * 1000
        await new Promise(resolve => setTimeout(resolve, delay))
        
        return this.retry(operation, errorKey, maxRetries)
      } else {
        this.retryCount.delete(errorKey)
        throw error
      }
    }
  }
}

// 全局错误处理器实例
export const errorHandler = ErrorHandler.getInstance()

// 便捷函数
export function handleError(error: Error | ErrorInfo, context?: Record<string, any>) {
  return errorHandler.handle(error, context)
}

export function handleNetworkError(error: Error, context?: Record<string, any>) {
  const errorInfo: ErrorInfo = {
    type: ErrorType.NETWORK,
    severity: ErrorSeverity.MEDIUM,
    message: '网络请求失败',
    details: error.message,
    timestamp: new Date().toISOString(),
    stack: error.stack,
    context
  }
  return errorHandler.handle(errorInfo)
}

export function handleValidationError(message: string, details?: any) {
  const errorInfo: ErrorInfo = {
    type: ErrorType.VALIDATION,
    severity: ErrorSeverity.LOW,
    message,
    details,
    timestamp: new Date().toISOString()
  }
  return errorHandler.handle(errorInfo)
}

export function handleAuthError(message: string = '认证失败') {
  const errorInfo: ErrorInfo = {
    type: ErrorType.AUTHENTICATION,
    severity: ErrorSeverity.HIGH,
    message,
    timestamp: new Date().toISOString()
  }
  return errorHandler.handle(errorInfo)
}

// 错误边界错误处理
export function handleBoundaryError(error: Error, errorInfo: any) {
  const boundaryError: ErrorInfo = {
    type: ErrorType.CLIENT,
    severity: ErrorSeverity.HIGH,
    message: '页面组件发生错误',
    details: error.message,
    timestamp: new Date().toISOString(),
    stack: error.stack,
    context: {
      componentStack: errorInfo.componentStack
    }
  }
  return errorHandler.handle(boundaryError)
}

// Promise错误处理
export function handlePromiseRejection(event: PromiseRejectionEvent) {
  const error = event.reason instanceof Error ? event.reason : new Error(String(event.reason))
  
  const promiseError: ErrorInfo = {
    type: ErrorType.CLIENT,
    severity: ErrorSeverity.MEDIUM,
    message: '未处理的Promise错误',
    details: error.message,
    timestamp: new Date().toISOString(),
    stack: error.stack
  }
  
  errorHandler.handle(promiseError)
  event.preventDefault()
}

// 全局错误监听
export function setupGlobalErrorHandling() {
  // 监听未捕获的错误
  window.addEventListener('error', (event) => {
    const error = event.error || new Error(event.message)
    handleError(error, {
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno
    })
  })

  // 监听未处理的Promise拒绝
  window.addEventListener('unhandledrejection', handlePromiseRejection)
}
