/**
 * 对比分析组件
 */

import React, { useState } from 'react'
import {
  Card,
  Row,
  Col,
  Select,
  Button,
  Space,
  Typography,
  Table,
  Tag,
  Tooltip,
  Progress
} from 'antd'
import {
  SwapOutlined,
  BarChartOutlined,
  TableOutlined,
  InfoCircleOutlined,
  TrophyOutlined
} from '@ant-design/icons'
import BarChart from '../Charts/BarChart'
import LineChart from '../Charts/LineChart'
import './ComparisonChart.css'

const { Title, Text } = Typography
const { Option } = Select

interface ComparisonData {
  id: string
  name: string
  values: {
    [key: string]: number
  }
  metadata?: {
    [key: string]: any
  }
}

interface ComparisonChartProps {
  title?: string
  data: ComparisonData[]
  metrics: string[]
  loading?: boolean
  showTable?: boolean
  showRanking?: boolean
  height?: number
}

const ComparisonChart: React.FC<ComparisonChartProps> = ({
  title = "对比分析",
  data = [],
  metrics = [],
  loading = false,
  showTable = true,
  showRanking = true,
  height = 400
}) => {
  const [selectedMetric, setSelectedMetric] = useState(metrics[0] || '')
  const [chartType, setChartType] = useState<'bar' | 'line'>('bar')
  const [viewMode, setViewMode] = useState<'chart' | 'table'>('chart')

  // 获取指定指标的对比数据
  const getMetricData = (metric: string) => {
    return data.map(item => ({
      name: item.name,
      value: item.values[metric] || 0,
      id: item.id
    })).sort((a, b) => b.value - a.value)
  }

  // 获取排名数据
  const getRankingData = () => {
    return data.map(item => {
      const totalScore = metrics.reduce((sum, metric) => sum + (item.values[metric] || 0), 0)
      const avgScore = totalScore / metrics.length
      
      return {
        id: item.id,
        name: item.name,
        totalScore,
        avgScore,
        values: item.values,
        metadata: item.metadata
      }
    }).sort((a, b) => b.avgScore - a.avgScore)
  }

  // 获取表格列定义
  const getTableColumns = () => {
    const baseColumns = [
      {
        title: '排名',
        key: 'rank',
        width: 60,
        render: (_: any, __: any, index: number) => (
          <div className="rank-cell">
            {index < 3 ? (
              <TrophyOutlined style={{ 
                color: index === 0 ? '#faad14' : index === 1 ? '#d9d9d9' : '#cd7f32' 
              }} />
            ) : (
              <span>{index + 1}</span>
            )}
          </div>
        )
      },
      {
        title: '名称',
        dataIndex: 'name',
        key: 'name',
        ellipsis: true,
        render: (text: string) => (
          <Text strong>{text}</Text>
        )
      }
    ]

    const metricColumns = metrics.map(metric => ({
      title: metric,
      key: metric,
      width: 100,
      render: (record: any) => {
        const value = record.values[metric] || 0
        const maxValue = Math.max(...data.map(d => d.values[metric] || 0))
        const percentage = maxValue > 0 ? (value / maxValue) * 100 : 0
        
        return (
          <div className="metric-cell">
            <div className="metric-value">{value.toFixed(1)}</div>
            <Progress
              percent={percentage}
              showInfo={false}
              size="small"
              strokeColor={percentage > 80 ? '#52c41a' : percentage > 60 ? '#1890ff' : '#faad14'}
            />
          </div>
        )
      }
    }))

    const avgColumn = {
      title: '平均分',
      key: 'avgScore',
      width: 100,
      render: (record: any) => (
        <div className="avg-score">
          <Text strong style={{ color: '#1890ff' }}>
            {record.avgScore.toFixed(1)}
          </Text>
        </div>
      )
    }

    return [...baseColumns, ...metricColumns, avgColumn]
  }

  const metricData = getMetricData(selectedMetric)
  const rankingData = getRankingData()
  const tableColumns = getTableColumns()

  const renderChart = () => {
    if (chartType === 'bar') {
      return (
        <BarChart
          data={metricData}
          height={height}
          color={['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#fa8c16']}
          unit="分"
          formatter={(value) => `${value.toFixed(1)}分`}
          loading={loading}
          empty={data.length === 0}
        />
      )
    } else {
      // 为折线图准备数据
      const lineData = metrics.map((metric, index) => ({
        timestamp: metric,
        value: data.reduce((sum, item) => sum + (item.values[metric] || 0), 0) / data.length
      }))
      
      return (
        <LineChart
          data={lineData}
          height={height}
          color="#1890ff"
          smooth={true}
          unit="分"
          formatter={(value) => `${value.toFixed(1)}分`}
          loading={loading}
          empty={data.length === 0}
        />
      )
    }
  }

  const renderTable = () => {
    return (
      <Table
        columns={tableColumns}
        dataSource={rankingData}
        rowKey="id"
        pagination={false}
        size="small"
        className="comparison-table"
        scroll={{ x: 'max-content' }}
      />
    )
  }

  return (
    <div className="comparison-chart">
      <Card
        title={
          <Space>
            <SwapOutlined />
            <span>{title}</span>
          </Space>
        }
        extra={
          <Space>
            {viewMode === 'chart' && (
              <>
                <Select
                  value={selectedMetric}
                  onChange={setSelectedMetric}
                  style={{ width: 120 }}
                  placeholder="选择指标"
                >
                  {metrics.map(metric => (
                    <Option key={metric} value={metric}>{metric}</Option>
                  ))}
                </Select>
                
                <Select
                  value={chartType}
                  onChange={setChartType}
                  style={{ width: 100 }}
                >
                  <Option value="bar">
                    <BarChartOutlined /> 柱状图
                  </Option>
                  <Option value="line">
                    <BarChartOutlined /> 折线图
                  </Option>
                </Select>
              </>
            )}
            
            <Button.Group>
              <Button
                type={viewMode === 'chart' ? 'primary' : 'default'}
                icon={<BarChartOutlined />}
                onClick={() => setViewMode('chart')}
              >
                图表
              </Button>
              <Button
                type={viewMode === 'table' ? 'primary' : 'default'}
                icon={<TableOutlined />}
                onClick={() => setViewMode('table')}
              >
                表格
              </Button>
            </Button.Group>
          </Space>
        }
      >
        {/* 概览统计 */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <div className="overview-stat">
              <div className="stat-value">{data.length}</div>
              <div className="stat-label">对比项目</div>
            </div>
          </Col>
          <Col span={6}>
            <div className="overview-stat">
              <div className="stat-value">{metrics.length}</div>
              <div className="stat-label">评估指标</div>
            </div>
          </Col>
          <Col span={6}>
            <div className="overview-stat">
              <div className="stat-value">
                {rankingData.length > 0 ? rankingData[0].avgScore.toFixed(1) : '0.0'}
              </div>
              <div className="stat-label">最高平均分</div>
            </div>
          </Col>
          <Col span={6}>
            <div className="overview-stat">
              <div className="stat-value">
                {rankingData.length > 0 ? 
                  ((rankingData[0].avgScore - rankingData[rankingData.length - 1].avgScore) / 
                   rankingData[rankingData.length - 1].avgScore * 100).toFixed(1) : '0.0'}%
              </div>
              <div className="stat-label">最大差距</div>
            </div>
          </Col>
        </Row>

        {/* 排名前三展示 */}
        {showRanking && rankingData.length > 0 && (
          <div className="top-ranking" style={{ marginBottom: 24 }}>
            <Title level={5}>
              <TrophyOutlined style={{ color: '#faad14', marginRight: 8 }} />
              排名前三
            </Title>
            <Row gutter={16}>
              {rankingData.slice(0, 3).map((item, index) => (
                <Col span={8} key={item.id}>
                  <Card size="small" className={`ranking-card rank-${index + 1}`}>
                    <div className="ranking-header">
                      <div className="ranking-position">
                        <TrophyOutlined style={{ 
                          color: index === 0 ? '#faad14' : index === 1 ? '#d9d9d9' : '#cd7f32',
                          fontSize: 20
                        }} />
                        <span className="position-text">第{index + 1}名</span>
                      </div>
                      <div className="ranking-score">
                        {item.avgScore.toFixed(1)}分
                      </div>
                    </div>
                    <div className="ranking-name">
                      <Text strong ellipsis>{item.name}</Text>
                    </div>
                    <div className="ranking-metrics">
                      {metrics.slice(0, 3).map(metric => (
                        <div key={metric} className="metric-item">
                          <span className="metric-name">{metric}:</span>
                          <span className="metric-value">{(item.values[metric] || 0).toFixed(1)}</span>
                        </div>
                      ))}
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        )}

        {/* 主要内容区域 */}
        <div className="comparison-content">
          {viewMode === 'chart' ? renderChart() : renderTable()}
        </div>

        {/* 分析洞察 */}
        <div className="comparison-insights">
          <Title level={5}>
            <InfoCircleOutlined style={{ marginRight: 8 }} />
            分析洞察
          </Title>
          <Row gutter={16}>
            <Col span={12}>
              <div className="insight-card">
                <div className="insight-title">表现最佳指标</div>
                <div className="insight-content">
                  {(() => {
                    const avgScores = metrics.map(metric => ({
                      metric,
                      avg: data.reduce((sum, item) => sum + (item.values[metric] || 0), 0) / data.length
                    }))
                    const best = avgScores.reduce((max, current) => 
                      current.avg > max.avg ? current : max
                    )
                    return (
                      <Space>
                        <Tag color="green">{best.metric}</Tag>
                        <Text>{best.avg.toFixed(1)}分</Text>
                      </Space>
                    )
                  })()}
                </div>
              </div>
            </Col>
            <Col span={12}>
              <div className="insight-card">
                <div className="insight-title">需要改进指标</div>
                <div className="insight-content">
                  {(() => {
                    const avgScores = metrics.map(metric => ({
                      metric,
                      avg: data.reduce((sum, item) => sum + (item.values[metric] || 0), 0) / data.length
                    }))
                    const worst = avgScores.reduce((min, current) => 
                      current.avg < min.avg ? current : min
                    )
                    return (
                      <Space>
                        <Tag color="orange">{worst.metric}</Tag>
                        <Text>{worst.avg.toFixed(1)}分</Text>
                      </Space>
                    )
                  })()}
                </div>
              </div>
            </Col>
          </Row>
        </div>
      </Card>
    </div>
  )
}

export default ComparisonChart
