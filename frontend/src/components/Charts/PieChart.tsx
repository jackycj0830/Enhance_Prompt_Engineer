/**
 * 饼图组件
 */

import React, { useEffect, useRef } from 'react'
import * as echarts from 'echarts'
import { Card, Typography, Empty } from 'antd'

const { Title } = Typography

interface DataPoint {
  name: string
  value: number
  [key: string]: any
}

interface PieChartProps {
  title?: string
  data: DataPoint[]
  height?: number
  colors?: string[]
  showLegend?: boolean
  showTooltip?: boolean
  showLabel?: boolean
  donut?: boolean
  loading?: boolean
  empty?: boolean
  unit?: string
  formatter?: (value: number) => string
}

const PieChart: React.FC<PieChartProps> = ({
  title,
  data = [],
  height = 300,
  colors = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#fa8c16', '#13c2c2', '#eb2f96'],
  showLegend = true,
  showTooltip = true,
  showLabel = true,
  donut = false,
  loading = false,
  empty = false,
  unit = '',
  formatter
}) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    if (!chartRef.current) return

    // 初始化图表
    chartInstance.current = echarts.init(chartRef.current)

    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose()
      }
    }
  }, [])

  useEffect(() => {
    if (!chartInstance.current || loading || empty || data.length === 0) return

    const total = data.reduce((sum, item) => sum + item.value, 0)
    
    const option = {
      series: [
        {
          name: title || '数据',
          type: 'pie',
          radius: donut ? ['40%', '70%'] : '70%',
          center: ['50%', '50%'],
          data: data.map((item, index) => ({
            name: item.name,
            value: item.value,
            itemStyle: {
              color: colors[index % colors.length]
            }
          })),
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          },
          label: showLabel ? {
            show: true,
            formatter: (params: any) => {
              const percent = ((params.value / total) * 100).toFixed(1)
              const value = formatter ? formatter(params.value) : `${params.value}${unit}`
              return `${params.name}\n${value} (${percent}%)`
            },
            fontSize: 12,
            color: '#666'
          } : {
            show: false
          },
          labelLine: showLabel ? {
            show: true,
            lineStyle: {
              color: '#d9d9d9'
            }
          } : {
            show: false
          }
        }
      ],
      tooltip: showTooltip ? {
        trigger: 'item',
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        borderColor: 'transparent',
        textStyle: {
          color: '#fff',
          fontSize: 12
        },
        formatter: (params: any) => {
          const percent = ((params.value / total) * 100).toFixed(1)
          const value = formatter ? formatter(params.value) : `${params.value}${unit}`
          return `${params.name}<br/>${value} (${percent}%)`
        }
      } : undefined,
      legend: showLegend ? {
        orient: 'vertical',
        left: 'left',
        top: 'middle',
        data: data.map(item => item.name),
        textStyle: {
          color: '#666',
          fontSize: 12
        },
        itemWidth: 14,
        itemHeight: 14,
        itemGap: 10,
        formatter: (name: string) => {
          const item = data.find(d => d.name === name)
          if (item) {
            const percent = ((item.value / total) * 100).toFixed(1)
            const value = formatter ? formatter(item.value) : `${item.value}${unit}`
            return `${name} ${value} (${percent}%)`
          }
          return name
        }
      } : undefined
    }

    chartInstance.current.setOption(option, true)

    // 响应式处理
    const handleResize = () => {
      if (chartInstance.current) {
        chartInstance.current.resize()
      }
    }

    window.addEventListener('resize', handleResize)
    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [data, colors, showLegend, showTooltip, showLabel, donut, title, unit, formatter, loading, empty])

  const renderContent = () => {
    if (loading) {
      return (
        <div style={{ 
          height, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center' 
        }}>
          <div>加载中...</div>
        </div>
      )
    }

    if (empty || data.length === 0) {
      return (
        <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Empty 
            image={Empty.PRESENTED_IMAGE_SIMPLE} 
            description="暂无数据" 
            style={{ margin: 0 }}
          />
        </div>
      )
    }

    return <div ref={chartRef} style={{ height }} />
  }

  if (title) {
    return (
      <Card 
        title={title} 
        style={{ height: height + 80 }}
        bodyStyle={{ padding: '20px 24px' }}
      >
        {renderContent()}
      </Card>
    )
  }

  return (
    <div style={{ height }}>
      {renderContent()}
    </div>
  )
}

export default PieChart
