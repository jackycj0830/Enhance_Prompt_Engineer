/**
 * TemplateManager组件测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import { render, createMockTemplate, mockApiResponse } from '@/test/utils'
import TemplateManager from './index'
import * as api from '@/services/api'

// 模拟API调用
vi.mock('@/services/api', () => ({
  templateApi: {
    getTemplates: vi.fn(),
    createTemplate: vi.fn(),
    updateTemplate: vi.fn(),
    deleteTemplate: vi.fn(),
    getCategories: vi.fn(),
    getTags: vi.fn(),
  },
}))

describe('TemplateManager', () => {
  const mockTemplates = [
    createMockTemplate({ id: 1, name: '模板1' }),
    createMockTemplate({ id: 2, name: '模板2' }),
  ]
  
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.templateApi.getTemplates).mockResolvedValue(mockTemplates)
    vi.mocked(api.templateApi.getCategories).mockResolvedValue(['分类1', '分类2'])
    vi.mocked(api.templateApi.getTags).mockResolvedValue(['标签1', '标签2'])
  })

  it('应该正确渲染模板列表', async () => {
    render(<TemplateManager />)
    
    await waitFor(() => {
      expect(screen.getByText('模板1')).toBeInTheDocument()
      expect(screen.getByText('模板2')).toBeInTheDocument()
    })
  })

  it('应该显示加载状态', () => {
    vi.mocked(api.templateApi.getTemplates).mockImplementation(
      () => new Promise(() => {}) // 永不resolve
    )
    
    render(<TemplateManager />)
    
    expect(screen.getByText('加载中...')).toBeInTheDocument()
  })

  it('应该支持搜索功能', async () => {
    render(<TemplateManager />)
    
    await waitFor(() => {
      expect(screen.getByText('模板1')).toBeInTheDocument()
    })
    
    const searchInput = screen.getByPlaceholderText('搜索模板...')
    fireEvent.change(searchInput, { target: { value: '模板1' } })
    
    // 模拟搜索API调用
    const filteredTemplates = [mockTemplates[0]]
    vi.mocked(api.templateApi.getTemplates).mockResolvedValue(filteredTemplates)
    
    await waitFor(() => {
      expect(api.templateApi.getTemplates).toHaveBeenCalledWith(
        expect.objectContaining({ search: '模板1' })
      )
    })
  })

  it('应该支持分类筛选', async () => {
    render(<TemplateManager />)
    
    await waitFor(() => {
      expect(screen.getByText('模板1')).toBeInTheDocument()
    })
    
    const categorySelect = screen.getByLabelText('分类')
    fireEvent.change(categorySelect, { target: { value: '分类1' } })
    
    await waitFor(() => {
      expect(api.templateApi.getTemplates).toHaveBeenCalledWith(
        expect.objectContaining({ category: '分类1' })
      )
    })
  })

  it('应该支持标签筛选', async () => {
    render(<TemplateManager />)
    
    await waitFor(() => {
      expect(screen.getByText('模板1')).toBeInTheDocument()
    })
    
    const tagSelect = screen.getByLabelText('标签')
    fireEvent.change(tagSelect, { target: { value: ['标签1'] } })
    
    await waitFor(() => {
      expect(api.templateApi.getTemplates).toHaveBeenCalledWith(
        expect.objectContaining({ tags: ['标签1'] })
      )
    })
  })

  it('应该打开创建模板对话框', async () => {
    render(<TemplateManager />)
    
    const createButton = screen.getByText('新建模板')
    fireEvent.click(createButton)
    
    expect(screen.getByText('创建模板')).toBeInTheDocument()
    expect(screen.getByLabelText('模板名称')).toBeInTheDocument()
    expect(screen.getByLabelText('模板内容')).toBeInTheDocument()
  })

  it('应该成功创建模板', async () => {
    const newTemplate = createMockTemplate({ id: 3, name: '新模板' })
    vi.mocked(api.templateApi.createTemplate).mockResolvedValue(newTemplate)
    
    render(<TemplateManager />)
    
    const createButton = screen.getByText('新建模板')
    fireEvent.click(createButton)
    
    // 填写表单
    const nameInput = screen.getByLabelText('模板名称')
    const contentInput = screen.getByLabelText('模板内容')
    
    fireEvent.change(nameInput, { target: { value: '新模板' } })
    fireEvent.change(contentInput, { target: { value: '新模板内容：{variable}' } })
    
    const submitButton = screen.getByText('创建')
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(api.templateApi.createTemplate).toHaveBeenCalledWith({
        name: '新模板',
        content: '新模板内容：{variable}',
        variables: ['variable'],
      })
    })
  })

  it('应该自动检测模板变量', async () => {
    render(<TemplateManager />)
    
    const createButton = screen.getByText('新建模板')
    fireEvent.click(createButton)
    
    const contentInput = screen.getByLabelText('模板内容')
    fireEvent.change(contentInput, { 
      target: { value: '你好，{name}！今天是{date}，天气{weather}。' } 
    })
    
    // 应该自动检测到变量
    await waitFor(() => {
      expect(screen.getByText('name')).toBeInTheDocument()
      expect(screen.getByText('date')).toBeInTheDocument()
      expect(screen.getByText('weather')).toBeInTheDocument()
    })
  })

  it('应该打开编辑模板对话框', async () => {
    render(<TemplateManager />)
    
    await waitFor(() => {
      expect(screen.getByText('模板1')).toBeInTheDocument()
    })
    
    const editButton = screen.getAllByText('编辑')[0]
    fireEvent.click(editButton)
    
    expect(screen.getByText('编辑模板')).toBeInTheDocument()
    expect(screen.getByDisplayValue('模板1')).toBeInTheDocument()
  })

  it('应该成功更新模板', async () => {
    const updatedTemplate = createMockTemplate({ id: 1, name: '更新后的模板' })
    vi.mocked(api.templateApi.updateTemplate).mockResolvedValue(updatedTemplate)
    
    render(<TemplateManager />)
    
    await waitFor(() => {
      expect(screen.getByText('模板1')).toBeInTheDocument()
    })
    
    const editButton = screen.getAllByText('编辑')[0]
    fireEvent.click(editButton)
    
    const nameInput = screen.getByDisplayValue('模板1')
    fireEvent.change(nameInput, { target: { value: '更新后的模板' } })
    
    const submitButton = screen.getByText('更新')
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(api.templateApi.updateTemplate).toHaveBeenCalledWith(
        1,
        expect.objectContaining({ name: '更新后的模板' })
      )
    })
  })

  it('应该确认删除模板', async () => {
    vi.mocked(api.templateApi.deleteTemplate).mockResolvedValue(true)
    
    render(<TemplateManager />)
    
    await waitFor(() => {
      expect(screen.getByText('模板1')).toBeInTheDocument()
    })
    
    const deleteButton = screen.getAllByText('删除')[0]
    fireEvent.click(deleteButton)
    
    // 确认删除对话框
    expect(screen.getByText('确认删除')).toBeInTheDocument()
    
    const confirmButton = screen.getByText('确定')
    fireEvent.click(confirmButton)
    
    await waitFor(() => {
      expect(api.templateApi.deleteTemplate).toHaveBeenCalledWith(1)
    })
  })

  it('应该支持批量操作', async () => {
    render(<TemplateManager />)
    
    await waitFor(() => {
      expect(screen.getByText('模板1')).toBeInTheDocument()
    })
    
    // 选择多个模板
    const checkboxes = screen.getAllByRole('checkbox')
    fireEvent.click(checkboxes[1]) // 第一个模板
    fireEvent.click(checkboxes[2]) // 第二个模板
    
    expect(screen.getByText('批量删除')).toBeInTheDocument()
    expect(screen.getByText('批量导出')).toBeInTheDocument()
  })

  it('应该支持模板预览', async () => {
    render(<TemplateManager />)
    
    await waitFor(() => {
      expect(screen.getByText('模板1')).toBeInTheDocument()
    })
    
    const previewButton = screen.getAllByText('预览')[0]
    fireEvent.click(previewButton)
    
    expect(screen.getByText('模板预览')).toBeInTheDocument()
    expect(screen.getByText(mockTemplates[0].content)).toBeInTheDocument()
  })

  it('应该支持模板复制', async () => {
    render(<TemplateManager />)
    
    await waitFor(() => {
      expect(screen.getByText('模板1')).toBeInTheDocument()
    })
    
    const copyButton = screen.getAllByText('复制')[0]
    fireEvent.click(copyButton)
    
    // 验证复制功能
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(mockTemplates[0].content)
  })

  it('应该支持分页', async () => {
    const manyTemplates = Array.from({ length: 25 }, (_, i) => 
      createMockTemplate({ id: i + 1, name: `模板${i + 1}` })
    )
    vi.mocked(api.templateApi.getTemplates).mockResolvedValue(manyTemplates)
    
    render(<TemplateManager />)
    
    await waitFor(() => {
      expect(screen.getByText('模板1')).toBeInTheDocument()
    })
    
    // 应该显示分页组件
    expect(screen.getByText('下一页')).toBeInTheDocument()
  })

  it('应该处理API错误', async () => {
    vi.mocked(api.templateApi.getTemplates).mockRejectedValue(
      new Error('网络错误')
    )
    
    render(<TemplateManager />)
    
    await waitFor(() => {
      expect(screen.getByText('加载失败，请重试')).toBeInTheDocument()
    })
  })

  it('应该支持排序', async () => {
    render(<TemplateManager />)
    
    await waitFor(() => {
      expect(screen.getByText('模板1')).toBeInTheDocument()
    })
    
    const sortSelect = screen.getByLabelText('排序')
    fireEvent.change(sortSelect, { target: { value: 'name_asc' } })
    
    await waitFor(() => {
      expect(api.templateApi.getTemplates).toHaveBeenCalledWith(
        expect.objectContaining({ sort: 'name_asc' })
      )
    })
  })
})
