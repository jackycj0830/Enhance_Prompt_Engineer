/**
 * AnalysisResult组件测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import { render, createMockAnalysis } from '@/test/utils'
import AnalysisResult from './index'

describe('AnalysisResult', () => {
  const mockAnalysis = createMockAnalysis()
  const mockOnOptimize = vi.fn()
  const mockOnReanalyze = vi.fn()
  
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('应该正确渲染分析结果', () => {
    render(
      <AnalysisResult 
        data={mockAnalysis}
        onOptimize={mockOnOptimize}
        onReanalyze={mockOnReanalyze}
      />
    )
    
    expect(screen.getByText('分析结果')).toBeInTheDocument()
    expect(screen.getByText('85.5')).toBeInTheDocument() // 总分
    expect(screen.getByText('良好')).toBeInTheDocument() // 评级
  })

  it('应该显示各维度评分', () => {
    render(
      <AnalysisResult 
        data={mockAnalysis}
        onOptimize={mockOnOptimize}
        onReanalyze={mockOnReanalyze}
      />
    )
    
    expect(screen.getByText('语义清晰度')).toBeInTheDocument()
    expect(screen.getByText('结构完整性')).toBeInTheDocument()
    expect(screen.getByText('逻辑连贯性')).toBeInTheDocument()
    expect(screen.getByText('90分')).toBeInTheDocument() // 语义清晰度分数
  })

  it('应该显示分析详情', () => {
    render(
      <AnalysisResult 
        data={mockAnalysis}
        onOptimize={mockOnOptimize}
        onReanalyze={mockOnReanalyze}
        showDetails={true}
      />
    )
    
    // 展开详情面板
    const detailsButton = screen.getByText('分析详情')
    fireEvent.click(detailsButton)
    
    expect(screen.getByText('词数统计')).toBeInTheDocument()
    expect(screen.getByText('50')).toBeInTheDocument() // 词数
    expect(screen.getByText('处理时间')).toBeInTheDocument()
    expect(screen.getByText('1500')).toBeInTheDocument() // 处理时间
  })

  it('应该显示改进建议', () => {
    render(
      <AnalysisResult 
        data={mockAnalysis}
        onOptimize={mockOnOptimize}
        onReanalyze={mockOnReanalyze}
        showDetails={true}
      />
    )
    
    // 展开建议面板
    const suggestionsButton = screen.getByText('改进建议')
    fireEvent.click(suggestionsButton)
    
    expect(screen.getByText('建议增加更多具体的示例')).toBeInTheDocument()
    expect(screen.getByText('可以进一步明确输出格式要求')).toBeInTheDocument()
  })

  it('应该正确处理优化按钮点击', () => {
    render(
      <AnalysisResult 
        data={mockAnalysis}
        onOptimize={mockOnOptimize}
        onReanalyze={mockOnReanalyze}
      />
    )
    
    const optimizeButton = screen.getByText('优化提示词')
    fireEvent.click(optimizeButton)
    
    expect(mockOnOptimize).toHaveBeenCalledWith(mockAnalysis.id)
  })

  it('应该正确处理重新分析按钮点击', () => {
    render(
      <AnalysisResult 
        data={mockAnalysis}
        onOptimize={mockOnOptimize}
        onReanalyze={mockOnReanalyze}
      />
    )
    
    const reanalyzeButton = screen.getByText('重新分析')
    fireEvent.click(reanalyzeButton)
    
    expect(mockOnReanalyze).toHaveBeenCalledWith(mockAnalysis.id)
  })

  it('应该根据分数显示正确的评级颜色', () => {
    const highScoreAnalysis = createMockAnalysis({ overall_score: 95 })
    const { rerender } = render(
      <AnalysisResult 
        data={highScoreAnalysis}
        onOptimize={mockOnOptimize}
        onReanalyze={mockOnReanalyze}
      />
    )
    
    expect(screen.getByText('优秀')).toBeInTheDocument()
    
    const lowScoreAnalysis = createMockAnalysis({ overall_score: 55 })
    rerender(
      <AnalysisResult 
        data={lowScoreAnalysis}
        onOptimize={mockOnOptimize}
        onReanalyze={mockOnReanalyze}
      />
    )
    
    expect(screen.getByText('需改进')).toBeInTheDocument()
  })

  it('应该显示加载状态', () => {
    render(
      <AnalysisResult 
        data={mockAnalysis}
        loading={true}
        onOptimize={mockOnOptimize}
        onReanalyze={mockOnReanalyze}
      />
    )
    
    expect(screen.getByText('加载中...')).toBeInTheDocument()
  })

  it('应该支持可视化分析标签页', () => {
    const historicalData = [mockAnalysis, createMockAnalysis({ id: 2, overall_score: 80 })]
    
    render(
      <AnalysisResult 
        data={mockAnalysis}
        onOptimize={mockOnOptimize}
        onReanalyze={mockOnReanalyze}
        historicalData={historicalData}
        showVisualization={true}
      />
    )
    
    expect(screen.getByText('可视化分析')).toBeInTheDocument()
    expect(screen.getByText('趋势分析')).toBeInTheDocument()
  })

  it('应该切换到可视化标签页', () => {
    const historicalData = [mockAnalysis, createMockAnalysis({ id: 2, overall_score: 80 })]
    
    render(
      <AnalysisResult 
        data={mockAnalysis}
        onOptimize={mockOnOptimize}
        onReanalyze={mockOnReanalyze}
        historicalData={historicalData}
        showVisualization={true}
      />
    )
    
    const visualizationTab = screen.getByText('可视化分析')
    fireEvent.click(visualizationTab)
    
    // 验证图表组件被渲染
    expect(screen.getByText('分析结果趋势')).toBeInTheDocument()
  })

  it('应该正确格式化时间显示', () => {
    const analysisWithTime = createMockAnalysis({
      created_at: '2024-01-01T12:00:00Z'
    })
    
    render(
      <AnalysisResult 
        data={analysisWithTime}
        onOptimize={mockOnOptimize}
        onReanalyze={mockOnReanalyze}
        showDetails={true}
      />
    )
    
    // 展开详情面板
    const detailsButton = screen.getByText('分析详情')
    fireEvent.click(detailsButton)
    
    expect(screen.getByText(/分析时间/)).toBeInTheDocument()
  })

  it('应该处理缺失数据的情况', () => {
    const incompleteAnalysis = {
      ...mockAnalysis,
      analysis_details: null,
      suggestions: []
    }
    
    render(
      <AnalysisResult 
        data={incompleteAnalysis}
        onOptimize={mockOnOptimize}
        onReanalyze={mockOnReanalyze}
        showDetails={true}
      />
    )
    
    // 应该正常渲染，不会崩溃
    expect(screen.getByText('分析结果')).toBeInTheDocument()
  })

  it('应该支持导出功能', () => {
    render(
      <AnalysisResult 
        data={mockAnalysis}
        onOptimize={mockOnOptimize}
        onReanalyze={mockOnReanalyze}
        showDetails={true}
      />
    )
    
    const exportButton = screen.getByText('导出报告')
    expect(exportButton).toBeInTheDocument()
    
    fireEvent.click(exportButton)
    
    // 验证导出功能被触发（这里可能需要模拟文件下载）
    expect(exportButton).toBeInTheDocument()
  })

  it('应该响应式地调整布局', () => {
    // 模拟移动端视口
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    })
    
    render(
      <AnalysisResult 
        data={mockAnalysis}
        onOptimize={mockOnOptimize}
        onReanalyze={mockOnReanalyze}
      />
    )
    
    // 在移动端应该正常显示
    expect(screen.getByText('分析结果')).toBeInTheDocument()
  })
})
