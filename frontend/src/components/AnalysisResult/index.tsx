/**
 * 分析结果展示组件
 */

import React, { useState } from 'react'
import {
  Card,
  Row,
  Col,
  Progress,
  Typography,
  Tag,
  Collapse,
  List,
  Statistic,
  Space,
  Button,
  Tooltip,
  Badge,
  Divider,
  Tabs
} from 'antd'
import {
  TrophyOutlined,
  EyeOutlined,
  BuildOutlined,
  LinkOutlined,
  BulbOutlined,
  ClockCircleOutlined,
  RobotOutlined,
  BarChartOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  LineChartOutlined,
  PieChartOutlined
} from '@ant-design/icons'
import AnalysisChart from '../DataVisualization/AnalysisChart'
import TrendAnalysis from '../DataVisualization/TrendAnalysis'
import './AnalysisResult.css'

const { Title, Text, Paragraph } = Typography
const { Panel } = Collapse
const { TabPane } = Tabs

interface AnalysisData {
  id: string
  overall_score: number
  semantic_clarity: number
  structural_integrity: number
  logical_coherence: number
  specificity_score?: number
  instruction_clarity?: number
  context_completeness?: number
  readability_score?: number
  complexity_score?: number
  analysis_details: {
    word_count: number
    sentence_count: number
    token_count?: number
    basic_metrics?: any
    strengths?: string[]
    weaknesses?: string[]
    suggestions?: string[]
  }
  processing_time_ms: number
  ai_model_used: string
  created_at: string
}

interface AnalysisResultProps {
  data: AnalysisData
  loading?: boolean
  onOptimize?: (analysisId: string) => void
  onReanalyze?: (analysisId: string) => void
  showDetails?: boolean
  historicalData?: AnalysisData[]
  showVisualization?: boolean
}

const AnalysisResult: React.FC<AnalysisResultProps> = ({
  data,
  loading = false,
  onOptimize,
  onReanalyze,
  showDetails = true,
  historicalData = [],
  showVisualization = true
}) => {
  const [activeKey, setActiveKey] = useState<string[]>(['overview'])
  const [activeTab, setActiveTab] = useState('overview')

  // 获取评分颜色
  const getScoreColor = (score: number) => {
    if (score >= 80) return '#52c41a'
    if (score >= 60) return '#faad14'
    return '#ff4d4f'
  }

  // 获取评分等级
  const getScoreGrade = (score: number) => {
    if (score >= 90) return { text: '优秀', color: '#52c41a' }
    if (score >= 80) return { text: '良好', color: '#1890ff' }
    if (score >= 60) return { text: '一般', color: '#faad14' }
    return { text: '需改进', color: '#ff4d4f' }
  }

  // 维度配置
  const dimensions = [
    {
      key: 'semantic_clarity',
      name: '语义清晰度',
      icon: <EyeOutlined />,
      description: '提示词的意思是否明确、无歧义',
      score: data.semantic_clarity
    },
    {
      key: 'structural_integrity',
      name: '结构完整性',
      icon: <BuildOutlined />,
      description: '提示词的组织结构是否合理、完整',
      score: data.structural_integrity
    },
    {
      key: 'logical_coherence',
      name: '逻辑连贯性',
      icon: <LinkOutlined />,
      description: '指令之间是否逻辑清晰、连贯',
      score: data.logical_coherence
    },
    {
      key: 'specificity_score',
      name: '具体性程度',
      icon: <BulbOutlined />,
      description: '指令是否具体、明确，避免模糊表达',
      score: data.specificity_score || 0
    },
    {
      key: 'instruction_clarity',
      name: '指令清晰度',
      icon: <InfoCircleOutlined />,
      description: '期望的输出和行为是否明确',
      score: data.instruction_clarity || 0
    },
    {
      key: 'context_completeness',
      name: '上下文完整性',
      icon: <CheckCircleOutlined />,
      description: '是否提供了足够的背景信息',
      score: data.context_completeness || 0
    }
  ]

  const grade = getScoreGrade(data.overall_score)

  return (
    <div className="analysis-result">
      {/* 总体评分卡片 */}
      <Card className="score-overview-card">
        <Row align="middle" gutter={24}>
          <Col span={8}>
            <div className="overall-score">
              <Progress
                type="circle"
                percent={data.overall_score}
                size={120}
                strokeColor={getScoreColor(data.overall_score)}
                format={(percent) => (
                  <div className="score-content">
                    <div className="score-number">{percent}</div>
                    <div className="score-label">总分</div>
                  </div>
                )}
              />
            </div>
          </Col>
          
          <Col span={16}>
            <div className="score-info">
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <div>
                  <Title level={3} style={{ margin: 0 }}>
                    分析结果
                    <Tag color={grade.color} style={{ marginLeft: 12 }}>
                      {grade.text}
                    </Tag>
                  </Title>
                  <Text type="secondary">
                    基于多维度分析算法的综合评估
                  </Text>
                </div>
                
                <Row gutter={16}>
                  <Col span={8}>
                    <Statistic
                      title="字数统计"
                      value={data.analysis_details.word_count}
                      suffix="词"
                      prefix={<BarChartOutlined />}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="处理时间"
                      value={data.processing_time_ms}
                      suffix="ms"
                      prefix={<ClockCircleOutlined />}
                    />
                  </Col>
                  <Col span={8}>
                    <div>
                      <Text type="secondary">AI模型</Text>
                      <div>
                        <Tag icon={<RobotOutlined />} color="blue">
                          {data.ai_model_used}
                        </Tag>
                      </div>
                    </div>
                  </Col>
                </Row>
              </Space>
            </div>
          </Col>
        </Row>
        
        {/* 操作按钮 */}
        <div className="score-actions">
          <Space>
            <Button
              type="primary"
              icon={<BulbOutlined />}
              onClick={() => onOptimize?.(data.id)}
              loading={loading}
            >
              获取优化建议
            </Button>
            <Button
              icon={<BarChartOutlined />}
              onClick={() => onReanalyze?.(data.id)}
              loading={loading}
            >
              重新分析
            </Button>
          </Space>
        </div>
      </Card>

      {/* 详细分析 */}
      {showDetails && (
        <Card title="详细分析" style={{ marginTop: 16 }}>
          <Tabs activeKey={activeTab} onChange={setActiveTab} type="card">
            <TabPane
              tab={
                <Space>
                  <InfoCircleOutlined />
                  <span>分析详情</span>
                </Space>
              }
              key="details"
            >
              <Collapse
                activeKey={activeKey}
                onChange={setActiveKey}
                ghost
              >
            {/* 维度评分 */}
            <Panel
              header={
                <Space>
                  <TrophyOutlined />
                  <span>维度评分</span>
                  <Badge count={dimensions.length} showZero color="#1890ff" />
                </Space>
              }
              key="dimensions"
            >
              <Row gutter={[16, 16]}>
                {dimensions.map((dimension) => (
                  <Col span={12} key={dimension.key}>
                    <Card size="small" className="dimension-card">
                      <div className="dimension-header">
                        <Space>
                          {dimension.icon}
                          <Text strong>{dimension.name}</Text>
                        </Space>
                        <Tag color={getScoreColor(dimension.score)}>
                          {dimension.score}分
                        </Tag>
                      </div>
                      <Progress
                        percent={dimension.score}
                        strokeColor={getScoreColor(dimension.score)}
                        showInfo={false}
                        size="small"
                      />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {dimension.description}
                      </Text>
                    </Card>
                  </Col>
                ))}
              </Row>
            </Panel>

            {/* 优点分析 */}
            {data.analysis_details.strengths && data.analysis_details.strengths.length > 0 && (
              <Panel
                header={
                  <Space>
                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                    <span>优点分析</span>
                    <Badge count={data.analysis_details.strengths.length} showZero color="#52c41a" />
                  </Space>
                }
                key="strengths"
              >
                <List
                  dataSource={data.analysis_details.strengths}
                  renderItem={(item, index) => (
                    <List.Item>
                      <Space>
                        <Badge count={index + 1} style={{ backgroundColor: '#52c41a' }} />
                        <Text>{item}</Text>
                      </Space>
                    </List.Item>
                  )}
                />
              </Panel>
            )}

            {/* 问题分析 */}
            {data.analysis_details.weaknesses && data.analysis_details.weaknesses.length > 0 && (
              <Panel
                header={
                  <Space>
                    <ExclamationCircleOutlined style={{ color: '#faad14' }} />
                    <span>问题分析</span>
                    <Badge count={data.analysis_details.weaknesses.length} showZero color="#faad14" />
                  </Space>
                }
                key="weaknesses"
              >
                <List
                  dataSource={data.analysis_details.weaknesses}
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

            {/* 基础建议 */}
            {data.analysis_details.suggestions && data.analysis_details.suggestions.length > 0 && (
              <Panel
                header={
                  <Space>
                    <BulbOutlined style={{ color: '#1890ff' }} />
                    <span>基础建议</span>
                    <Badge count={data.analysis_details.suggestions.length} showZero color="#1890ff" />
                  </Space>
                }
                key="suggestions"
              >
                <List
                  dataSource={data.analysis_details.suggestions}
                  renderItem={(item, index) => (
                    <List.Item>
                      <Space>
                        <Badge count={index + 1} style={{ backgroundColor: '#1890ff' }} />
                        <Text>{item}</Text>
                      </Space>
                    </List.Item>
                  )}
                />
              </Panel>
            )}

            {/* 技术详情 */}
            <Panel
              header={
                <Space>
                  <InfoCircleOutlined />
                  <span>技术详情</span>
                </Space>
              }
              key="technical"
            >
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic
                    title="句子数量"
                    value={data.analysis_details.sentence_count}
                    suffix="句"
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="预估Token"
                    value={data.analysis_details.token_count || 0}
                    suffix="个"
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="复杂度评分"
                    value={data.complexity_score || 0}
                    precision={1}
                    suffix="分"
                  />
                </Col>
              </Row>
              
              <Divider />
              
              <Paragraph>
                <Text strong>分析时间：</Text>
                {new Date(data.created_at).toLocaleString()}
              </Paragraph>
              <Paragraph>
                <Text strong>AI模型：</Text>
                <Tag>{data.ai_model_used}</Tag>
              </Paragraph>
              <Paragraph>
                <Text strong>分析ID：</Text>
                <Text code>{data.id}</Text>
              </Paragraph>
            </Panel>
              </Collapse>
            </TabPane>

            {/* 可视化分析标签页 */}
            {showVisualization && (
              <TabPane
                tab={
                  <Space>
                    <BarChartOutlined />
                    <span>可视化分析</span>
                  </Space>
                }
                key="visualization"
              >
                <AnalysisChart
                  data={historicalData.length > 0 ? historicalData : [data]}
                  loading={loading}
                  title="分析结果趋势"
                  height={400}
                />
              </TabPane>
            )}

            {/* 趋势分析标签页 */}
            {showVisualization && historicalData.length > 1 && (
              <TabPane
                tab={
                  <Space>
                    <LineChartOutlined />
                    <span>趋势分析</span>
                  </Space>
                }
                key="trend"
              >
                <TrendAnalysis
                  title="评分趋势分析"
                  data={historicalData.map(item => ({
                    timestamp: item.created_at,
                    value: item.overall_score
                  }))}
                  loading={loading}
                  unit="分"
                  precision={1}
                  showComparison={true}
                  showPrediction={true}
                />
              </TabPane>
            )}
          </Tabs>
        </Card>
      )}
    </div>
  )
}

export default AnalysisResult
