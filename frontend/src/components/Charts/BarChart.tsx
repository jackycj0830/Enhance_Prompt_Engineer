/**
 * 柱状图组件
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

interface BarChartProps {
  title?: string
  data: DataPoint[]
  height?: number
  color?: string | string[]
  horizontal?: boolean
  showGrid?: boolean
  showTooltip?: boolean
  showLegend?: boolean
  loading?: boolean
  empty?: boolean
  unit?: string
  formatter?: (value: number) => string
}

const BarChart: React.FC<BarChartProps> = ({
  title,
  data = [],
  height = 300,
  color = '#1890ff',
  horizontal = false,
  showGrid = true,
  showTooltip = true,
  showLegend = false,
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

    const colors = Array.isArray(color) ? color : [color]
    
    const option = {
      grid: {
        left: horizontal ? '15%' : '3%',
        right: '4%',
        bottom: horizontal ? '3%' : '15%',
        top: title ? '15%' : '3%',
        containLabel: true,
        show: showGrid,
        borderColor: '#f0f0f0'
      },
      xAxis: {
        type: horizontal ? 'value' : 'category',
        data: horizontal ? undefined : data.map(item => item.name),
        axisLine: {
          lineStyle: {
            color: '#d9d9d9'
          }
        },
        axisTick: {
          show: false
        },
        axisLabel: {
          color: '#666',
          fontSize: 12,
          interval: 0,
          rotate: horizontal ? 0 : (data.length > 6 ? 45 : 0),
          formatter: horizontal ? (value: number) => {
            if (formatter) {
              return formatter(value)
            }
            return `${value}${unit}`
          } : undefined
        },
        splitLine: horizontal ? {
          lineStyle: {
            color: '#f0f0f0',
            type: 'dashed'
          }
        } : undefined
      },
      yAxis: {
        type: horizontal ? 'category' : 'value',
        data: horizontal ? data.map(item => item.name) : undefined,
        axisLine: {
          show: false
        },
        axisTick: {
          show: false
        },
        axisLabel: {
          color: '#666',
          fontSize: 12,
          formatter: horizontal ? undefined : (value: number) => {
            if (formatter) {
              return formatter(value)
            }
            return `${value}${unit}`
          }
        },
        splitLine: horizontal ? undefined : {
          lineStyle: {
            color: '#f0f0f0',
            type: 'dashed'
          }
        }
      },
      series: [
        {
          data: data.map((item, index) => ({
            name: item.name,
            value: item.value,
            itemStyle: {
              color: colors[index % colors.length]
            }
          })),
          type: 'bar',
          barWidth: '60%',
          itemStyle: {
            borderRadius: horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.3)'
            }
          }
        }
      ],
      tooltip: showTooltip ? {
        trigger: 'axis',
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        borderColor: 'transparent',
        textStyle: {
          color: '#fff',
          fontSize: 12
        },
        formatter: (params: any) => {
          const param = params[0]
          const value = formatter ? formatter(param.value) : `${param.value}${unit}`
          return `${param.name}: ${value}`
        }
      } : undefined,
      legend: showLegend ? {
        data: data.map(item => item.name),
        top: 0,
        textStyle: {
          color: '#666',
          fontSize: 12
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
  }, [data, color, horizontal, showGrid, showTooltip, showLegend, title, unit, formatter, loading, empty])

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

export default BarChart
