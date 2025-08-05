/**
 * 分析结果可视化组件
 */

import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Select,
  Button,
  Space,
  Typography,
  Tabs,
  Spin
} from 'antd'
import {
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  DownloadOutlined,
  FullscreenOutlined
} from '@ant-design/icons'
import LineChart from '../Charts/LineChart'
import BarChart from '../Charts/BarChart'
import PieChart from '../Charts/PieChart'
import './AnalysisChart.css'

const { Title, Text } = Typography
const { Option } = Select
const { TabPane } = Tabs

interface AnalysisData {
  id: string
  overall_score: number
  semantic_clarity: number
  structural_integrity: number
  logical_coherence: number
  specificity_score: number
  instruction_clarity: number
  context_completeness: number
  created_at: string
}

interface AnalysisChartProps {
  data: AnalysisData[]
  loading?: boolean
  title?: string
  height?: number
}

const AnalysisChart: React.FC<AnalysisChartProps> = ({
  data = [],
  loading = false,
  title = "分析结果可视化",
  height = 400
}) => {
  const [chartType, setChartType] = useState<'line' | 'bar' | 'pie'>('line')
  const [timeRange, setTimeRange] = useState('7d')
  const [activeTab, setActiveTab] = useState('trend')

  // 处理趋势数据
  const getTrendData = () => {
    return data.map(item => ({
      timestamp: item.created_at,
      value: item.overall_score,
      semantic_clarity: item.semantic_clarity,
      structural_integrity: item.structural_integrity,
      logical_coherence: item.logical_coherence
    }))
  }

  // 处理维度对比数据
  const getDimensionData = () => {
    if (data.length === 0) return []
    
    const latest = data[data.length - 1]
    return [
      { name: '语义清晰度', value: latest.semantic_clarity },
      { name: '结构完整性', value: latest.structural_integrity },
      { name: '逻辑连贯性', value: latest.logical_coherence },
      { name: '具体性程度', value: latest.specificity_score || 0 },
      { name: '指令清晰度', value: latest.instruction_clarity || 0 },
      { name: '上下文完整性', value: latest.context_completeness || 0 }
    ]
  }

  // 处理分布数据
  const getDistributionData = () => {
    const ranges = [
      { name: '优秀 (90-100)', min: 90, max: 100 },
      { name: '良好 (80-89)', min: 80, max: 89 },
      { name: '一般 (70-79)', min: 70, max: 79 },
      { name: '需改进 (60-69)', min: 60, max: 69 },
      { name: '较差 (<60)', min: 0, max: 59 }
    ]

    return ranges.map(range => ({
      name: range.name,
      value: data.filter(item => 
        item.overall_score >= range.min && item.overall_score <= range.max
      ).length
    })).filter(item => item.value > 0)
  }

  // 导出数据
  const handleExport = () => {
    const csvContent = [
      ['时间', '总分', '语义清晰度', '结构完整性', '逻辑连贯性'],
      ...data.map(item => [
        new Date(item.created_at).toLocaleString(),
        item.overall_score,
        item.semantic_clarity,
        item.structural_integrity,
        item.logical_coherence
      ])
    ].map(row => row.join(',')).join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `analysis_data_${Date.now()}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // 全屏显示
  const handleFullscreen = () => {
    // 实现全屏逻辑
    console.log('全屏显示')
  }

  const renderTrendChart = () => {
    const trendData = getTrendData()
    
    switch (chartType) {
      case 'line':
        return (
          <LineChart
            data={trendData}
            height={height}
            color="#1890ff"
            smooth={true}
            area={true}
            unit="分"
            formatter={(value) => `${value.toFixed(1)}分`}
            loading={loading}
            empty={data.length === 0}
          />
        )
      case 'bar':
        return (
          <BarChart
            data={trendData.map((item, index) => ({
              name: `第${index + 1}次`,
              value: item.value
            }))}
            height={height}
            color="#52c41a"
            unit="分"
            formatter={(value) => `${value.toFixed(1)}分`}
            loading={loading}
            empty={data.length === 0}
          />
        )
      default:
        return (
          <LineChart
            data={trendData}
            height={height}
            color="#1890ff"
            loading={loading}
            empty={data.length === 0}
          />
        )
    }
  }

  const renderDimensionChart = () => {
    const dimensionData = getDimensionData()
    
    return (
      <BarChart
        data={dimensionData}
        height={height}
        color={['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#fa8c16']}
        horizontal={true}
        unit="分"
        formatter={(value) => `${value.toFixed(1)}分`}
        loading={loading}
        empty={data.length === 0}
      />
    )
  }

  const renderDistributionChart = () => {
    const distributionData = getDistributionData()
    
    return (
      <PieChart
        data={distributionData}
        height={height}
        colors={['#52c41a', '#1890ff', '#faad14', '#fa8c16', '#f5222d']}
        donut={true}
        unit="次"
        loading={loading}
        empty={data.length === 0}
      />
    )
  }

  return (
    <div className="analysis-chart">
      <Card
        title={title}
        extra={
          <Space>
            <Select
              value={timeRange}
              onChange={setTimeRange}
              style={{ width: 120 }}
            >
              <Option value="1d">最近1天</Option>
              <Option value="7d">最近7天</Option>
              <Option value="30d">最近30天</Option>
            </Select>
            
            <Button
              icon={<DownloadOutlined />}
              onClick={handleExport}
              disabled={data.length === 0}
            >
              导出
            </Button>
            
            <Button
              icon={<FullscreenOutlined />}
              onClick={handleFullscreen}
            />
          </Space>
        }
      >
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane
            tab={
              <Space>
                <LineChartOutlined />
                <span>趋势分析</span>
              </Space>
            }
            key="trend"
          >
            <div className="chart-controls">
              <Space>
                <Text>图表类型：</Text>
                <Select
                  value={chartType}
                  onChange={setChartType}
                  style={{ width: 100 }}
                >
                  <Option value="line">
                    <LineChartOutlined /> 折线图
                  </Option>
                  <Option value="bar">
                    <BarChartOutlined /> 柱状图
                  </Option>
                </Select>
              </Space>
            </div>
            
            <div className="chart-container">
              {renderTrendChart()}
            </div>
          </TabPane>

          <TabPane
            tab={
              <Space>
                <BarChartOutlined />
                <span>维度对比</span>
              </Space>
            }
            key="dimension"
          >
            <div className="chart-container">
              {renderDimensionChart()}
            </div>
          </TabPane>

          <TabPane
            tab={
              <Space>
                <PieChartOutlined />
                <span>分布统计</span>
              </Space>
            }
            key="distribution"
          >
            <div className="chart-container">
              {renderDistributionChart()}
            </div>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default AnalysisChart
