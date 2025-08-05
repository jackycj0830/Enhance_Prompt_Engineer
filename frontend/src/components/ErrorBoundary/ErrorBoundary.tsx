/**
 * 全局错误边界组件
 */

import React, { Component, ErrorInfo, ReactNode } from 'react'
import { Result, Button, Typography, Collapse, Space } from 'antd'
import { BugOutlined, ReloadOutlined, HomeOutlined } from '@ant-design/icons'

const { Paragraph, Text } = Typography
const { Panel } = Collapse

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
  errorId: string
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: ''
    }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
      errorId: Date.now().toString(36)
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo
    })

    // 调用错误回调
    this.props.onError?.(error, errorInfo)

    // 发送错误报告
    this.reportError(error, errorInfo)
  }

  private reportError = (error: Error, errorInfo: ErrorInfo) => {
    try {
      // 收集错误信息
      const errorReport = {
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
        userId: this.getUserId(),
        errorId: this.state.errorId
      }

      // 发送到错误监控服务
      this.sendErrorReport(errorReport)

      // 本地存储错误信息
      this.storeErrorLocally(errorReport)
    } catch (reportError) {
      console.error('Failed to report error:', reportError)
    }
  }

  private getUserId = (): string => {
    // 从localStorage或其他地方获取用户ID
    return localStorage.getItem('userId') || 'anonymous'
  }

  private sendErrorReport = async (errorReport: any) => {
    try {
      await fetch('/api/v1/errors/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorReport)
      })
    } catch (error) {
      console.error('Failed to send error report:', error)
    }
  }

  private storeErrorLocally = (errorReport: any) => {
    try {
      const errors = JSON.parse(localStorage.getItem('errorReports') || '[]')
      errors.push(errorReport)
      
      // 只保留最近10个错误
      if (errors.length > 10) {
        errors.splice(0, errors.length - 10)
      }
      
      localStorage.setItem('errorReports', JSON.stringify(errors))
    } catch (error) {
      console.error('Failed to store error locally:', error)
    }
  }

  private handleReload = () => {
    window.location.reload()
  }

  private handleGoHome = () => {
    window.location.href = '/'
  }

  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: ''
    })
  }

  private copyErrorInfo = () => {
    const { error, errorInfo, errorId } = this.state
    const errorText = `
错误ID: ${errorId}
时间: ${new Date().toLocaleString()}
错误信息: ${error?.message}
错误堆栈: ${error?.stack}
组件堆栈: ${errorInfo?.componentStack}
页面URL: ${window.location.href}
用户代理: ${navigator.userAgent}
    `.trim()

    navigator.clipboard.writeText(errorText).then(() => {
      // 可以添加复制成功的提示
    })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      const { error, errorInfo, errorId } = this.state

      return (
        <div style={{ padding: '50px', minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
          <Result
            status="error"
            icon={<BugOutlined />}
            title="页面出现错误"
            subTitle={`错误ID: ${errorId} | 我们已经记录了这个错误，请尝试刷新页面或返回首页`}
            extra={
              <Space direction="vertical" size="middle">
                <Space>
                  <Button type="primary" icon={<ReloadOutlined />} onClick={this.handleReload}>
                    刷新页面
                  </Button>
                  <Button icon={<HomeOutlined />} onClick={this.handleGoHome}>
                    返回首页
                  </Button>
                  <Button onClick={this.handleRetry}>
                    重试
                  </Button>
                </Space>
                
                <Collapse ghost>
                  <Panel header="查看错误详情" key="error-details">
                    <div style={{ textAlign: 'left' }}>
                      <Paragraph>
                        <Text strong>错误信息:</Text>
                        <br />
                        <Text code>{error?.message}</Text>
                      </Paragraph>
                      
                      <Paragraph>
                        <Text strong>错误堆栈:</Text>
                        <br />
                        <Text code style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>
                          {error?.stack}
                        </Text>
                      </Paragraph>
                      
                      {errorInfo && (
                        <Paragraph>
                          <Text strong>组件堆栈:</Text>
                          <br />
                          <Text code style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>
                            {errorInfo.componentStack}
                          </Text>
                        </Paragraph>
                      )}
                      
                      <Button size="small" onClick={this.copyErrorInfo}>
                        复制错误信息
                      </Button>
                    </div>
                  </Panel>
                </Collapse>
              </Space>
            }
          />
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary

// 错误边界HOC
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  fallback?: ReactNode,
  onError?: (error: Error, errorInfo: ErrorInfo) => void
) {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary fallback={fallback} onError={onError}>
      <Component {...props} />
    </ErrorBoundary>
  )

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`
  
  return WrappedComponent
}

// 异步错误处理Hook
export function useAsyncError() {
  const [, setError] = React.useState()
  
  return React.useCallback((error: Error) => {
    setError(() => {
      throw error
    })
  }, [])
}

// 错误恢复Hook
export function useErrorRecovery() {
  const [retryCount, setRetryCount] = React.useState(0)
  const [lastError, setLastError] = React.useState<Error | null>(null)

  const retry = React.useCallback(() => {
    setRetryCount(count => count + 1)
    setLastError(null)
  }, [])

  const reportError = React.useCallback((error: Error) => {
    setLastError(error)
  }, [])

  return {
    retryCount,
    lastError,
    retry,
    reportError
  }
}
