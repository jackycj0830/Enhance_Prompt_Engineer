/**
 * 提示词编辑器组件
 */

import React, { useState, useEffect, useCallback } from 'react'
import { 
  Card, 
  Input, 
  Button, 
  Space, 
  Typography, 
  Tag, 
  Select, 
  Tooltip,
  Row,
  Col,
  Statistic,
  message
} from 'antd'
import { 
  EditOutlined, 
  SaveOutlined, 
  AnalyticsOutlined,
  CopyOutlined,
  ClearOutlined,
  InfoCircleOutlined,
  BulbOutlined
} from '@ant-design/icons'
import { debounce } from 'lodash-es'
import './PromptEditor.css'

const { TextArea } = Input
const { Text, Title } = Typography
const { Option } = Select

interface PromptEditorProps {
  value?: string
  onChange?: (value: string) => void
  onAnalyze?: (content: string) => void
  onSave?: (content: string, metadata: any) => void
  placeholder?: string
  maxLength?: number
  showAnalytics?: boolean
  showTemplates?: boolean
  disabled?: boolean
  loading?: boolean
}

interface PromptMetrics {
  wordCount: number
  charCount: number
  sentenceCount: number
  estimatedTokens: number
  complexity: 'low' | 'medium' | 'high'
  readability: number
}

const PromptEditor: React.FC<PromptEditorProps> = ({
  value = '',
  onChange,
  onAnalyze,
  onSave,
  placeholder = '请输入您的提示词...',
  maxLength = 5000,
  showAnalytics = true,
  showTemplates = true,
  disabled = false,
  loading = false
}) => {
  const [content, setContent] = useState(value)
  const [category, setCategory] = useState<string>('')
  const [tags, setTags] = useState<string[]>([])
  const [metrics, setMetrics] = useState<PromptMetrics>({
    wordCount: 0,
    charCount: 0,
    sentenceCount: 0,
    estimatedTokens: 0,
    complexity: 'low',
    readability: 0
  })

  // 计算文本指标
  const calculateMetrics = useCallback((text: string): PromptMetrics => {
    const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0
    const charCount = text.length
    const sentenceCount = text.split(/[.!?]+/).filter(s => s.trim()).length
    const estimatedTokens = Math.ceil(wordCount * 1.3) // 粗略估算
    
    // 复杂度评估
    let complexity: 'low' | 'medium' | 'high' = 'low'
    if (wordCount > 100) complexity = 'high'
    else if (wordCount > 50) complexity = 'medium'
    
    // 可读性评分（简化版）
    const avgWordsPerSentence = wordCount / Math.max(sentenceCount, 1)
    const readability = Math.max(0, Math.min(100, 100 - avgWordsPerSentence * 2))
    
    return {
      wordCount,
      charCount,
      sentenceCount,
      estimatedTokens,
      complexity,
      readability: Math.round(readability)
    }
  }, [])

  // 防抖更新指标
  const debouncedUpdateMetrics = useCallback(
    debounce((text: string) => {
      setMetrics(calculateMetrics(text))
    }, 300),
    [calculateMetrics]
  )

  // 内容变化处理
  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newContent = e.target.value
    setContent(newContent)
    onChange?.(newContent)
    debouncedUpdateMetrics(newContent)
  }

  // 初始化和值变化时更新
  useEffect(() => {
    setContent(value)
    debouncedUpdateMetrics(value)
  }, [value, debouncedUpdateMetrics])

  // 分析按钮处理
  const handleAnalyze = () => {
    if (!content.trim()) {
      message.warning('请先输入提示词内容')
      return
    }
    onAnalyze?.(content)
  }

  // 保存按钮处理
  const handleSave = () => {
    if (!content.trim()) {
      message.warning('请先输入提示词内容')
      return
    }
    
    const metadata = {
      category,
      tags,
      metrics,
      timestamp: new Date().toISOString()
    }
    
    onSave?.(content, metadata)
  }

  // 复制内容
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content)
      message.success('内容已复制到剪贴板')
    } catch (error) {
      message.error('复制失败')
    }
  }

  // 清空内容
  const handleClear = () => {
    setContent('')
    onChange?.('')
    setMetrics(calculateMetrics(''))
  }

  // 插入模板
  const handleInsertTemplate = (template: string) => {
    const newContent = content + (content ? '\n\n' : '') + template
    setContent(newContent)
    onChange?.(newContent)
    debouncedUpdateMetrics(newContent)
  }

  // 常用模板
  const commonTemplates = [
    {
      name: '角色定义',
      content: '你是一个专业的[角色]，擅长[专业领域]。'
    },
    {
      name: '任务描述',
      content: '请帮我[具体任务]，要求：\n1. [要求1]\n2. [要求2]\n3. [要求3]'
    },
    {
      name: '输出格式',
      content: '请按以下格式输出：\n- 标题：[标题]\n- 内容：[内容]\n- 总结：[总结]'
    },
    {
      name: '示例说明',
      content: '例如：\n输入：[示例输入]\n输出：[示例输出]'
    }
  ]

  // 获取复杂度颜色
  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'low': return 'green'
      case 'medium': return 'orange'
      case 'high': return 'red'
      default: return 'default'
    }
  }

  // 获取可读性颜色
  const getReadabilityColor = (score: number) => {
    if (score >= 70) return 'green'
    if (score >= 50) return 'orange'
    return 'red'
  }

  return (
    <div className="prompt-editor">
      <Card
        title={
          <Space>
            <EditOutlined />
            <span>提示词编辑器</span>
            {loading && <Text type="secondary">分析中...</Text>}
          </Space>
        }
        extra={
          <Space>
            {showTemplates && (
              <Select
                placeholder="插入模板"
                style={{ width: 120 }}
                onSelect={(value: string) => {
                  const template = commonTemplates.find(t => t.name === value)
                  if (template) {
                    handleInsertTemplate(template.content)
                  }
                }}
              >
                {commonTemplates.map(template => (
                  <Option key={template.name} value={template.name}>
                    {template.name}
                  </Option>
                ))}
              </Select>
            )}
            
            <Tooltip title="复制内容">
              <Button 
                icon={<CopyOutlined />} 
                onClick={handleCopy}
                disabled={!content.trim()}
              />
            </Tooltip>
            
            <Tooltip title="清空内容">
              <Button 
                icon={<ClearOutlined />} 
                onClick={handleClear}
                disabled={!content.trim()}
              />
            </Tooltip>
          </Space>
        }
      >
        {/* 编辑区域 */}
        <div className="editor-content">
          <TextArea
            value={content}
            onChange={handleContentChange}
            placeholder={placeholder}
            maxLength={maxLength}
            disabled={disabled}
            autoSize={{ minRows: 6, maxRows: 20 }}
            showCount
            className="prompt-textarea"
          />
        </div>

        {/* 元数据输入 */}
        <div className="editor-metadata" style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Select
                placeholder="选择分类"
                style={{ width: '100%' }}
                value={category}
                onChange={setCategory}
                allowClear
              >
                <Option value="创作">创作</Option>
                <Option value="编程">编程</Option>
                <Option value="分析">分析</Option>
                <Option value="翻译">翻译</Option>
                <Option value="总结">总结</Option>
                <Option value="其他">其他</Option>
              </Select>
            </Col>
            <Col span={12}>
              <Select
                mode="tags"
                placeholder="添加标签"
                style={{ width: '100%' }}
                value={tags}
                onChange={setTags}
                maxTagCount={5}
              />
            </Col>
          </Row>
        </div>

        {/* 实时指标 */}
        {showAnalytics && (
          <div className="editor-metrics" style={{ marginTop: 16 }}>
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="字数"
                  value={metrics.wordCount}
                  suffix="词"
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="字符数"
                  value={metrics.charCount}
                  suffix={`/${maxLength}`}
                />
              </Col>
              <Col span={6}>
                <div>
                  <Text type="secondary">复杂度</Text>
                  <div>
                    <Tag color={getComplexityColor(metrics.complexity)}>
                      {metrics.complexity.toUpperCase()}
                    </Tag>
                  </div>
                </div>
              </Col>
              <Col span={6}>
                <div>
                  <Text type="secondary">可读性</Text>
                  <div>
                    <Tag color={getReadabilityColor(metrics.readability)}>
                      {metrics.readability}分
                    </Tag>
                  </div>
                </div>
              </Col>
            </Row>
          </div>
        )}

        {/* 操作按钮 */}
        <div className="editor-actions" style={{ marginTop: 16, textAlign: 'right' }}>
          <Space>
            <Button
              type="default"
              icon={<AnalyticsOutlined />}
              onClick={handleAnalyze}
              disabled={!content.trim() || loading}
              loading={loading}
            >
              分析提示词
            </Button>
            
            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={handleSave}
              disabled={!content.trim() || loading}
            >
              保存提示词
            </Button>
          </Space>
        </div>

        {/* 提示信息 */}
        <div className="editor-tips" style={{ marginTop: 16 }}>
          <Space>
            <InfoCircleOutlined style={{ color: '#1890ff' }} />
            <Text type="secondary">
              提示：使用具体、明确的指令可以获得更好的AI响应效果
            </Text>
          </Space>
        </div>
      </Card>
    </div>
  )
}

export default PromptEditor
