/**
 * 优化建议界面组件
 */

import React, { useState } from 'react'
import {
  Card,
  List,
  Button,
  Space,
  Typography,
  Tag,
  Collapse,
  Progress,
  Checkbox,
  Tooltip,
  Badge,
  Row,
  Col,
  Statistic,
  Alert,
  Divider,
  message
} from 'antd'
import {
  BulbOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  ThunderboltOutlined,
  RocketOutlined,
  StarOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  ArrowUpOutlined,
  PlayCircleOutlined
} from '@ant-design/icons'
// import './OptimizationSuggestions.css'

const { Title, Text, Paragraph } = Typography
const { Panel } = Collapse

interface Suggestion {
  id: string
  type: string
  priority: number
  impact: 'high' | 'medium' | 'low'
  title: string
  description: string
  improvement_plan: string
  expected_improvement: Record<string, number>
  examples: string[]
  reasoning: string
  confidence: number
  is_applied?: boolean
}

interface OptimizationData {
  suggestions: Suggestion[]
  personalized_recommendations: string[]
  improvement_roadmap: string[]
  estimated_score_improvement: number
  processing_time: number
  model_used: string
}

interface OptimizationSuggestionsProps {
  data: OptimizationData
  loading?: boolean
  onApplySuggestions?: (suggestionIds: string[], originalPrompt: string) => void
  onApplySingle?: (suggestionId: string) => void
  originalPrompt?: string
}

const OptimizationSuggestions: React.FC<OptimizationSuggestionsProps> = ({
  data,
  loading = false,
  onApplySuggestions,
  onApplySingle,
  originalPrompt = ''
}) => {
  const [selectedSuggestions, setSelectedSuggestions] = useState<string[]>([])
  const [activeKey, setActiveKey] = useState<string[]>(['suggestions', 'roadmap'])

  // 优先级配置
  const priorityConfig = {
    1: { text: '关键', color: '#ff4d4f', icon: <ExclamationCircleOutlined /> },
    2: { text: '高', color: '#fa8c16', icon: <ThunderboltOutlined /> },
    3: { text: '中', color: '#1890ff', icon: <InfoCircleOutlined /> },
    4: { text: '低', color: '#52c41a', icon: <CheckCircleOutlined /> },
    5: { text: '可选', color: '#d9d9d9', icon: <StarOutlined /> }
  }

  // 影响程度配置
  const impactConfig = {
    high: { text: '高影响', color: '#ff4d4f' },
    medium: { text: '中等影响', color: '#faad14' },
    low: { text: '低影响', color: '#52c41a' }
  }

  // 建议类型配置
  const typeConfig = {
    clarity: { text: '清晰度', icon: '🔍', color: '#1890ff' },
    structure: { text: '结构', icon: '🏗️', color: '#722ed1' },
    specificity: { text: '具体性', icon: '🎯', color: '#eb2f96' },
    context: { text: '上下文', icon: '📝', color: '#13c2c2' },
    format: { text: '格式', icon: '📋', color: '#52c41a' },
    role: { text: '角色', icon: '👤', color: '#fa8c16' },
    examples: { text: '示例', icon: '💡', color: '#faad14' },
    constraints: { text: '约束', icon: '⚖️', color: '#f5222d' }
  }

  // 处理建议选择
  const handleSuggestionSelect = (suggestionId: string, checked: boolean) => {
    if (checked) {
      setSelectedSuggestions([...selectedSuggestions, suggestionId])
    } else {
      setSelectedSuggestions(selectedSuggestions.filter(id => id !== suggestionId))
    }
  }

  // 全选/取消全选
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedSuggestions(data.suggestions.map(s => s.id))
    } else {
      setSelectedSuggestions([])
    }
  }

  // 应用选中的建议
  const handleApplySelected = () => {
    if (selectedSuggestions.length === 0) {
      message.warning('请先选择要应用的建议')
      return
    }
    onApplySuggestions?.(selectedSuggestions, originalPrompt)
  }

  // 应用单个建议
  const handleApplySingle = (suggestionId: string) => {
    onApplySingle?.(suggestionId)
  }

  // 按优先级排序的建议
  const sortedSuggestions = [...data.suggestions].sort((a, b) => a.priority - b.priority)

  return (
    <div className="optimization-suggestions">
      {/* 概览卡片 */}
      <Card className="overview-card">
        <Row gutter={24} align="middle">
          <Col span={6}>
            <div className="improvement-score">
              <Progress
                type="circle"
                percent={Math.min(data.estimated_score_improvement * 3, 100)}
                size={100}
                strokeColor="#52c41a"
                format={() => (
                  <div className="improvement-content">
                    <div className="improvement-number">+{data.estimated_score_improvement}</div>
                    <div className="improvement-label">预期提升</div>
                  </div>
                )}
              />
            </div>
          </Col>
          
          <Col span={18}>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <div>
                <Title level={3} style={{ margin: 0 }}>
                  <BulbOutlined style={{ color: '#faad14', marginRight: 8 }} />
                  优化建议
                  <Badge count={data.suggestions.length} showZero color="#1890ff" style={{ marginLeft: 12 }} />
                </Title>
                <Text type="secondary">
                  基于AI分析生成的个性化优化建议
                </Text>
              </div>
              
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic
                    title="建议数量"
                    value={data.suggestions.length}
                    suffix="个"
                    prefix={<BulbOutlined />}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="预期提升"
                    value={data.estimated_score_improvement}
                    suffix="分"
                    prefix={<ArrowUpOutlined />}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="处理时间"
                    value={data.processing_time}
                    suffix="s"
                    precision={2}
                    prefix={<ClockCircleOutlined />}
                  />
                </Col>
                <Col span={6}>
                  <div>
                    <Text type="secondary">AI模型</Text>
                    <div>
                      <Tag icon={<RocketOutlined />} color="blue">
                        {data.model_used}
                      </Tag>
                    </div>
                  </div>
                </Col>
              </Row>
            </Space>
          </Col>
        </Row>
        
        {/* 批量操作 */}
        <div className="batch-actions">
          <Space>
            <Checkbox
              checked={selectedSuggestions.length === data.suggestions.length}
              indeterminate={selectedSuggestions.length > 0 && selectedSuggestions.length < data.suggestions.length}
              onChange={(e) => handleSelectAll(e.target.checked)}
            >
              全选 ({selectedSuggestions.length}/{data.suggestions.length})
            </Checkbox>
            
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={handleApplySelected}
              disabled={selectedSuggestions.length === 0}
              loading={loading}
            >
              应用选中建议 ({selectedSuggestions.length})
            </Button>
          </Space>
        </div>
      </Card>

      {/* 详细内容 */}
      <Card style={{ marginTop: 16 }}>
        <Collapse
          activeKey={activeKey}
          onChange={setActiveKey}
          ghost
        >
          {/* 优化建议列表 */}
          <Panel
            header={
              <Space>
                <BulbOutlined />
                <span>优化建议</span>
                <Badge count={data.suggestions.length} showZero color="#1890ff" />
              </Space>
            }
            key="suggestions"
          >
            <List
              dataSource={sortedSuggestions}
              renderItem={(suggestion) => {
                const priorityInfo = priorityConfig[suggestion.priority as keyof typeof priorityConfig]
                const impactInfo = impactConfig[suggestion.impact]
                const typeInfo = typeConfig[suggestion.type as keyof typeof typeConfig] || { text: suggestion.type, icon: '📝', color: '#666' }
                
                return (
                  <List.Item className="suggestion-item">
                    <Card size="small" className="suggestion-card">
                      <div className="suggestion-header">
                        <Space>
                          <Checkbox
                            checked={selectedSuggestions.includes(suggestion.id)}
                            onChange={(e) => handleSuggestionSelect(suggestion.id, e.target.checked)}
                          />
                          
                          <div className="suggestion-meta">
                            <Space>
                              <Tag color={typeInfo.color}>
                                {typeInfo.icon} {typeInfo.text}
                              </Tag>
                              <Tag color={priorityInfo.color}>
                                {priorityInfo.icon} {priorityInfo.text}
                              </Tag>
                              <Tag color={impactInfo.color}>
                                {impactInfo.text}
                              </Tag>
                              <Tag color="purple">
                                置信度 {Math.round(suggestion.confidence * 100)}%
                              </Tag>
                            </Space>
                          </div>
                        </Space>
                        
                        <Button
                          type="link"
                          size="small"
                          onClick={() => handleApplySingle(suggestion.id)}
                          disabled={suggestion.is_applied}
                        >
                          {suggestion.is_applied ? '已应用' : '单独应用'}
                        </Button>
                      </div>
                      
                      <div className="suggestion-content">
                        <Title level={5}>{suggestion.title}</Title>
                        <Paragraph>{suggestion.description}</Paragraph>
                        
                        <Collapse size="small" ghost>
                          <Panel header="改进计划" key="plan">
                            <Paragraph>
                              <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                                {suggestion.improvement_plan}
                              </pre>
                            </Paragraph>
                          </Panel>
                          
                          {suggestion.examples.length > 0 && (
                            <Panel header="示例说明" key="examples">
                              <List
                                size="small"
                                dataSource={suggestion.examples}
                                renderItem={(example, index) => (
                                  <List.Item>
                                    <Badge count={index + 1} style={{ backgroundColor: '#1890ff' }} />
                                    <Text code>{example}</Text>
                                  </List.Item>
                                )}
                              />
                            </Panel>
                          )}
                          
                          <Panel header="预期效果" key="impact">
                            <Row gutter={16}>
                              {Object.entries(suggestion.expected_improvement).map(([key, value]) => (
                                <Col span={8} key={key}>
                                  <Statistic
                                    title={key}
                                    value={value}
                                    suffix="分"
                                    prefix="+"
                                    valueStyle={{ color: '#52c41a', fontSize: 16 }}
                                  />
                                </Col>
                              ))}
                            </Row>
                          </Panel>
                          
                          <Panel header="推理过程" key="reasoning">
                            <Paragraph type="secondary">
                              {suggestion.reasoning}
                            </Paragraph>
                          </Panel>
                        </Collapse>
                      </div>
                    </Card>
                  </List.Item>
                )
              }}
            />
          </Panel>

          {/* 个性化推荐 */}
          {data.personalized_recommendations.length > 0 && (
            <Panel
              header={
                <Space>
                  <StarOutlined />
                  <span>个性化推荐</span>
                  <Badge count={data.personalized_recommendations.length} showZero color="#faad14" />
                </Space>
              }
              key="personalized"
            >
              <Alert
                message="基于您的使用偏好和历史数据生成的个性化建议"
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <List
                dataSource={data.personalized_recommendations}
                renderItem={(item, index) => (
                  <List.Item>
                    <Space>
                      <Badge count={index + 1} style={{ backgroundColor: '#faad14' }} />
                      <Text>{item}</Text>
                    </Space>
                  </List.Item>
                )}
              />
            </Panel>
          )}

          {/* 改进路线图 */}
          {data.improvement_roadmap.length > 0 && (
            <Panel
              header={
                <Space>
                  <TrophyOutlined />
                  <span>改进路线图</span>
                </Space>
              }
              key="roadmap"
            >
              <Alert
                message="建议按照以下顺序逐步优化您的提示词"
                type="success"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <div className="roadmap-content">
                {data.improvement_roadmap.map((step, index) => (
                  <div key={index} className="roadmap-step">
                    <Text>{step}</Text>
                  </div>
                ))}
              </div>
            </Panel>
          )}
        </Collapse>
      </Card>
    </div>
  )
}

export default OptimizationSuggestions
