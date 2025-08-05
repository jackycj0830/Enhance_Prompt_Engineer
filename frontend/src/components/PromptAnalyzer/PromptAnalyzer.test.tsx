/**
 * PromptAnalyzer组件测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import { render, createMockAnalysis, mockApiResponse, mockApiError } from '@/test/utils'
import PromptAnalyzer from './index'
import * as api from '@/services/api'

// 模拟API调用
vi.mock('@/services/api', () => ({
  analysisApi: {
    createAnalysis: vi.fn(),
  },
}))

describe('PromptAnalyzer', () => {
  const mockOnAnalysisComplete = vi.fn()
  
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('应该正确渲染组件', () => {
    render(<PromptAnalyzer onAnalysisComplete={mockOnAnalysisComplete} />)
    
    expect(screen.getByText('提示词分析')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('请输入您的提示词内容...')).toBeInTheDocument()
    expect(screen.getByText('开始分析')).toBeInTheDocument()
  })

  it('应该显示输入验证错误', async () => {
    render(<PromptAnalyzer onAnalysisComplete={mockOnAnalysisComplete} />)
    
    const analyzeButton = screen.getByText('开始分析')
    fireEvent.click(analyzeButton)
    
    await waitFor(() => {
      expect(screen.getByText('请输入提示词内容')).toBeInTheDocument()
    })
  })

  it('应该在输入过短时显示警告', async () => {
    render(<PromptAnalyzer onAnalysisComplete={mockOnAnalysisComplete} />)
    
    const textarea = screen.getByPlaceholderText('请输入您的提示词内容...')
    fireEvent.change(textarea, { target: { value: '短' } })
    
    const analyzeButton = screen.getByText('开始分析')
    fireEvent.click(analyzeButton)
    
    await waitFor(() => {
      expect(screen.getByText('提示词内容过短，建议至少包含10个字符')).toBeInTheDocument()
    })
  })

  it('应该成功提交分析请求', async () => {
    const mockAnalysis = createMockAnalysis()
    vi.mocked(api.analysisApi.createAnalysis).mockResolvedValue(mockAnalysis)
    
    render(<PromptAnalyzer onAnalysisComplete={mockOnAnalysisComplete} />)
    
    const textarea = screen.getByPlaceholderText('请输入您的提示词内容...')
    fireEvent.change(textarea, { target: { value: '这是一个测试提示词，用于验证分析功能是否正常工作。' } })
    
    const analyzeButton = screen.getByText('开始分析')
    fireEvent.click(analyzeButton)
    
    await waitFor(() => {
      expect(api.analysisApi.createAnalysis).toHaveBeenCalledWith({
        content: '这是一个测试提示词，用于验证分析功能是否正常工作。',
      })
    })
    
    await waitFor(() => {
      expect(mockOnAnalysisComplete).toHaveBeenCalledWith(mockAnalysis)
    })
  })

  it('应该显示加载状态', async () => {
    // 创建一个永不resolve的Promise来模拟加载状态
    vi.mocked(api.analysisApi.createAnalysis).mockImplementation(
      () => new Promise(() => {}) // 永不resolve
    )
    
    render(<PromptAnalyzer onAnalysisComplete={mockOnAnalysisComplete} />)
    
    const textarea = screen.getByPlaceholderText('请输入您的提示词内容...')
    fireEvent.change(textarea, { target: { value: '测试提示词内容' } })
    
    const analyzeButton = screen.getByText('开始分析')
    fireEvent.click(analyzeButton)
    
    await waitFor(() => {
      expect(screen.getByText('分析中...')).toBeInTheDocument()
    })
    
    // 验证按钮被禁用
    expect(analyzeButton).toBeDisabled()
  })

  it('应该处理API错误', async () => {
    vi.mocked(api.analysisApi.createAnalysis).mockRejectedValue(
      new Error('分析服务暂时不可用')
    )
    
    render(<PromptAnalyzer onAnalysisComplete={mockOnAnalysisComplete} />)
    
    const textarea = screen.getByPlaceholderText('请输入您的提示词内容...')
    fireEvent.change(textarea, { target: { value: '测试提示词内容' } })
    
    const analyzeButton = screen.getByText('开始分析')
    fireEvent.click(analyzeButton)
    
    await waitFor(() => {
      expect(screen.getByText('分析失败，请稍后重试')).toBeInTheDocument()
    })
  })

  it('应该显示字符计数', () => {
    render(<PromptAnalyzer onAnalysisComplete={mockOnAnalysisComplete} />)
    
    const textarea = screen.getByPlaceholderText('请输入您的提示词内容...')
    fireEvent.change(textarea, { target: { value: '测试内容' } })
    
    expect(screen.getByText('4 / 5000')).toBeInTheDocument()
  })

  it('应该限制最大字符数', () => {
    render(<PromptAnalyzer onAnalysisComplete={mockOnAnalysisComplete} />)
    
    const textarea = screen.getByPlaceholderText('请输入您的提示词内容...')
    const longText = 'a'.repeat(5001)
    
    fireEvent.change(textarea, { target: { value: longText } })
    
    // 应该被截断到5000字符
    expect(textarea).toHaveValue('a'.repeat(5000))
    expect(screen.getByText('5000 / 5000')).toBeInTheDocument()
  })

  it('应该支持清空内容', () => {
    render(<PromptAnalyzer onAnalysisComplete={mockOnAnalysisComplete} />)
    
    const textarea = screen.getByPlaceholderText('请输入您的提示词内容...')
    fireEvent.change(textarea, { target: { value: '测试内容' } })
    
    const clearButton = screen.getByText('清空')
    fireEvent.click(clearButton)
    
    expect(textarea).toHaveValue('')
    expect(screen.getByText('0 / 5000')).toBeInTheDocument()
  })

  it('应该支持示例提示词', () => {
    render(<PromptAnalyzer onAnalysisComplete={mockOnAnalysisComplete} />)
    
    const exampleButton = screen.getByText('使用示例')
    fireEvent.click(exampleButton)
    
    const textarea = screen.getByPlaceholderText('请输入您的提示词内容...')
    expect(textarea).not.toHaveValue('')
  })

  it('应该在组件卸载时清理状态', () => {
    const { unmount } = render(<PromptAnalyzer onAnalysisComplete={mockOnAnalysisComplete} />)
    
    // 模拟正在进行的分析
    vi.mocked(api.analysisApi.createAnalysis).mockImplementation(
      () => new Promise(() => {})
    )
    
    const textarea = screen.getByPlaceholderText('请输入您的提示词内容...')
    fireEvent.change(textarea, { target: { value: '测试内容' } })
    
    const analyzeButton = screen.getByText('开始分析')
    fireEvent.click(analyzeButton)
    
    // 卸载组件
    unmount()
    
    // 验证没有内存泄漏或错误
    expect(() => unmount()).not.toThrow()
  })

  it('应该支持键盘快捷键', () => {
    render(<PromptAnalyzer onAnalysisComplete={mockOnAnalysisComplete} />)
    
    const textarea = screen.getByPlaceholderText('请输入您的提示词内容...')
    fireEvent.change(textarea, { target: { value: '测试提示词内容' } })
    
    // 模拟Ctrl+Enter快捷键
    fireEvent.keyDown(textarea, { key: 'Enter', ctrlKey: true })
    
    expect(api.analysisApi.createAnalysis).toHaveBeenCalled()
  })

  it('应该正确处理分析选项', async () => {
    const mockAnalysis = createMockAnalysis()
    vi.mocked(api.analysisApi.createAnalysis).mockResolvedValue(mockAnalysis)
    
    render(<PromptAnalyzer onAnalysisComplete={mockOnAnalysisComplete} />)
    
    // 展开高级选项
    const advancedButton = screen.getByText('高级选项')
    fireEvent.click(advancedButton)
    
    // 选择分析模型
    const modelSelect = screen.getByLabelText('分析模型')
    fireEvent.change(modelSelect, { target: { value: 'gpt-4' } })
    
    // 选择分析维度
    const dimensionCheckbox = screen.getByLabelText('语义清晰度')
    fireEvent.click(dimensionCheckbox)
    
    const textarea = screen.getByPlaceholderText('请输入您的提示词内容...')
    fireEvent.change(textarea, { target: { value: '测试提示词内容' } })
    
    const analyzeButton = screen.getByText('开始分析')
    fireEvent.click(analyzeButton)
    
    await waitFor(() => {
      expect(api.analysisApi.createAnalysis).toHaveBeenCalledWith({
        content: '测试提示词内容',
        model: 'gpt-4',
        dimensions: expect.arrayContaining(['semantic_clarity']),
      })
    })
  })
})
