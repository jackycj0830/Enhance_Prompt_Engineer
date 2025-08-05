/**
 * 趋势分析组件
 */

import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Select,
  Button,
  Space,
  Typography,
  Tag,
  Alert,
  Tooltip
} from 'antd'
import {
  TrendingUpOutlined,
  TrendingDownOutlined,
  MinusOutlined,
  InfoCircleOutlined,
  CalendarOutlined,
  BarChartOutlined
} from '@ant-design/icons'
import LineChart from '../Charts/LineChart'
import './TrendAnalysis.css'

const { Title, Text } = Typography
const { Option } = Select

interface TrendData {
  timestamp: string
  value: number
  change?: number
  changePercent?: number
}

interface TrendAnalysisProps {
  title?: string
  data: TrendData[]
  loading?: boolean
  timeRange?: string
  onTimeRangeChange?: (range: string) => void
  unit?: string
  precision?: number
  showComparison?: boolean
  showPrediction?: boolean
}

const TrendAnalysis: React.FC<TrendAnalysisProps> = ({
  title = "趋势分析",
  data = [],
  loading = false,
  timeRange = "7d",
  onTimeRangeChange,
  unit = "",
  precision = 1,
  showComparison = true,
  showPrediction = false
}) => {
  const [selectedPeriod, setSelectedPeriod] = useState(timeRange)

  // 计算趋势统计
  const getTrendStats = () => {
    if (data.length < 2) {
      return {
        current: 0,
        previous: 0,
        change: 0,
        changePercent: 0,
        trend: 'stable' as 'up' | 'down' | 'stable',
        max: 0,
        min: 0,
        avg: 0
      }
    }

    const values = data.map(d => d.value)
    const current = values[values.length - 1]
    const previous = values[values.length - 2]
    const change = current - previous
    const changePercent = previous !== 0 ? (change / previous) * 100 : 0

    const max = Math.max(...values)
    const min = Math.min(...values)
    const avg = values.reduce((sum, val) => sum + val, 0) / values.length

    let trend: 'up' | 'down' | 'stable' = 'stable'
    if (Math.abs(changePercent) > 5) {
      trend = changePercent > 0 ? 'up' : 'down'
    }

    return {
      current,
      previous,
      change,
      changePercent,
      trend,
      max,
      min,
      avg
    }
  }

  // 获取趋势描述
  const getTrendDescription = (stats: ReturnType<typeof getTrendStats>) => {
    const { trend, changePercent } = stats
    
    if (trend === 'up') {
      return {
        text: `上升 ${Math.abs(changePercent).toFixed(1)}%`,
        color: '#52c41a',
        icon: <TrendingUpOutlined />
      }
    } else if (trend === 'down') {
      return {
        text: `下降 ${Math.abs(changePercent).toFixed(1)}%`,
        color: '#ff4d4f',
        icon: <TrendingDownOutlined />
      }
    } else {
      return {
        text: '保持稳定',
        color: '#1890ff',
        icon: <MinusOutlined />
      }
    }
  }

  // 获取预测数据（简单线性预测）
  const getPredictionData = () => {
    if (!showPrediction || data.length < 3) return []

    const recentData = data.slice(-5) // 使用最近5个数据点
    const n = recentData.length
    
    // 简单线性回归
    let sumX = 0, sumY = 0, sumXY = 0, sumXX = 0
    recentData.forEach((point, index) => {
      sumX += index
      sumY += point.value
      sumXY += index * point.value
      sumXX += index * index
    })

    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX)
    const intercept = (sumY - slope * sumX) / n

    // 生成未来3个预测点
    const predictions = []
    for (let i = 1; i <= 3; i++) {
      const futureIndex = n + i - 1
      const predictedValue = slope * futureIndex + intercept
      const futureDate = new Date(data[data.length - 1].timestamp)
      futureDate.setDate(futureDate.getDate() + i)
      
      predictions.push({
        timestamp: futureDate.toISOString(),
        value: Math.max(0, predictedValue), // 确保预测值不为负
        isPrediction: true
      })
    }

    return predictions
  }

  const stats = getTrendStats()
  const trendDesc = getTrendDescription(stats)
  const predictionData = getPredictionData()
  const chartData = [...data, ...predictionData]

  const handleTimeRangeChange = (range: string) => {
    setSelectedPeriod(range)
    onTimeRangeChange?.(range)
  }

  return (
    <div className="trend-analysis">
      <Card
        title={
          <Space>
            <BarChartOutlined />
            <span>{title}</span>
          </Space>
        }
        extra={
          <Space>
            <Select
              value={selectedPeriod}
              onChange={handleTimeRangeChange}
              style={{ width: 120 }}
            >
              <Option value="1d">最近1天</Option>
              <Option value="7d">最近7天</Option>
              <Option value="30d">最近30天</Option>
              <Option value="90d">最近90天</Option>
            </Select>
          </Space>
        }
      >
        {/* 统计概览 */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card size="small" className="stat-card">
              <Statistic
                title="当前值"
                value={stats.current}
                precision={precision}
                suffix={unit}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          
          <Col span={6}>
            <Card size="small" className="stat-card">
              <Statistic
                title="变化趋势"
                value={Math.abs(stats.changePercent)}
                precision={1}
                suffix="%"
                prefix={trendDesc.icon}
                valueStyle={{ color: trendDesc.color }}
              />
              <div style={{ marginTop: 4 }}>
                <Tag color={trendDesc.color === '#52c41a' ? 'green' : trendDesc.color === '#ff4d4f' ? 'red' : 'blue'}>
                  {trendDesc.text}
                </Tag>
              </div>
            </Card>
          </Col>
          
          <Col span={6}>
            <Card size="small" className="stat-card">
              <Statistic
                title="平均值"
                value={stats.avg}
                precision={precision}
                suffix={unit}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
          
          <Col span={6}>
            <Card size="small" className="stat-card">
              <Statistic
                title="波动范围"
                value={`${stats.min.toFixed(precision)} - ${stats.max.toFixed(precision)}`}
                suffix={unit}
                valueStyle={{ color: '#fa8c16', fontSize: 16 }}
              />
            </Card>
          </Col>
        </Row>

        {/* 趋势提示 */}
        {showComparison && (
          <Alert
            message={
              <Space>
                <span>趋势分析:</span>
                <Text strong style={{ color: trendDesc.color }}>
                  {trendDesc.text}
                </Text>
                <Tooltip title="基于最近数据点的变化计算">
                  <InfoCircleOutlined style={{ color: '#999' }} />
                </Tooltip>
              </Space>
            }
            type={stats.trend === 'up' ? 'success' : stats.trend === 'down' ? 'warning' : 'info'}
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {/* 预测提示 */}
        {showPrediction && predictionData.length > 0 && (
          <Alert
            message="图表中虚线部分为基于历史数据的趋势预测，仅供参考"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {/* 趋势图表 */}
        <div className="trend-chart">
          <LineChart
            data={chartData}
            height={400}
            color="#1890ff"
            smooth={true}
            area={true}
            unit={unit}
            formatter={(value) => `${value.toFixed(precision)}${unit}`}
            loading={loading}
            empty={data.length === 0}
          />
        </div>

        {/* 数据洞察 */}
        <div className="trend-insights">
          <Title level={5}>数据洞察</Title>
          <Row gutter={16}>
            <Col span={8}>
              <div className="insight-item">
                <div className="insight-label">数据点数量</div>
                <div className="insight-value">{data.length} 个</div>
              </div>
            </Col>
            <Col span={8}>
              <div className="insight-item">
                <div className="insight-label">数据时间跨度</div>
                <div className="insight-value">
                  {data.length > 0 ? (
                    <>
                      {Math.ceil((new Date(data[data.length - 1].timestamp).getTime() - 
                                  new Date(data[0].timestamp).getTime()) / (1000 * 60 * 60 * 24))} 天
                    </>
                  ) : '0 天'}
                </div>
              </div>
            </Col>
            <Col span={8}>
              <div className="insight-item">
                <div className="insight-label">变化幅度</div>
                <div className="insight-value">
                  {stats.max > 0 ? ((stats.max - stats.min) / stats.max * 100).toFixed(1) : 0}%
                </div>
              </div>
            </Col>
          </Row>
        </div>
      </Card>
    </div>
  )
}

export default TrendAnalysis
