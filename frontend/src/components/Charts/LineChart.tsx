/**
 * 折线图组件
 */

import React, { useEffect, useRef } from 'react'
import * as echarts from 'echarts'
import { Card, Typography, Empty } from 'antd'

const { Title } = Typography

interface DataPoint {
  timestamp: string
  value: number
  [key: string]: any
}

interface LineChartProps {
  title?: string
  data: DataPoint[]
  xAxisKey?: string
  yAxisKey?: string
  height?: number
  color?: string
  showGrid?: boolean
  showTooltip?: boolean
  showLegend?: boolean
  smooth?: boolean
  area?: boolean
  loading?: boolean
  empty?: boolean
  unit?: string
  formatter?: (value: number) => string
}

const LineChart: React.FC<LineChartProps> = ({
  title,
  data = [],
  xAxisKey = 'timestamp',
  yAxisKey = 'value',
  height = 300,
  color = '#1890ff',
  showGrid = true,
  showTooltip = true,
  showLegend = false,
  smooth = true,
  area = false,
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

    const option = {
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: title ? '15%' : '3%',
        containLabel: true,
        show: showGrid,
        borderColor: '#f0f0f0'
      },
      xAxis: {
        type: 'category',
        data: data.map(item => {
          const date = new Date(item[xAxisKey])
          return date.toLocaleTimeString('zh-CN', { 
            hour: '2-digit', 
            minute: '2-digit' 
          })
        }),
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
          fontSize: 12
        }
      },
      yAxis: {
        type: 'value',
        axisLine: {
          show: false
        },
        axisTick: {
          show: false
        },
        axisLabel: {
          color: '#666',
          fontSize: 12,
          formatter: (value: number) => {
            if (formatter) {
              return formatter(value)
            }
            return `${value}${unit}`
          }
        },
        splitLine: {
          lineStyle: {
            color: '#f0f0f0',
            type: 'dashed'
          }
        }
      },
      series: [
        {
          data: data.map(item => item[yAxisKey]),
          type: 'line',
          smooth: smooth,
          symbol: 'circle',
          symbolSize: 4,
          lineStyle: {
            color: color,
            width: 2
          },
          itemStyle: {
            color: color
          },
          areaStyle: area ? {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                {
                  offset: 0,
                  color: color + '40'
                },
                {
                  offset: 1,
                  color: color + '10'
                }
              ]
            }
          } : undefined
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
          const dataPoint = data[param.dataIndex]
          const time = new Date(dataPoint[xAxisKey]).toLocaleString('zh-CN')
          const value = formatter ? formatter(param.value) : `${param.value}${unit}`
          return `${time}<br/>${param.seriesName || title || '数值'}: ${value}`
        }
      } : undefined,
      legend: showLegend ? {
        data: [title || '数据'],
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
  }, [data, xAxisKey, yAxisKey, color, showGrid, showTooltip, showLegend, smooth, area, title, unit, formatter, loading, empty])

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

export default LineChart
