/**
 * 监控面板组件
 */

import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Table,
  Tag,
  Button,
  Select,
  Space,
  Typography,
  Alert,
  Spin,
  Empty,
  Tooltip,
  Badge
} from 'antd'
import {
  DashboardOutlined,
  ApiOutlined,
  RobotOutlined,
  AlertOutlined,
  ReloadOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  TrendingUpOutlined
} from '@ant-design/icons'
import { monitoringApi } from '../../services/api'
import './MonitoringDashboard.css'

const { Title, Text } = Typography
const { Option } = Select

interface MonitoringData {
  summary: {
    api: {
      total_requests: number
      avg_response_time: number
      error_count: number
      error_rate: number
    }
    ai: {
      total_calls: number
      total_tokens: number
      total_cost: number
      avg_response_time: number
    }
    users: {
      total_activities: number
      active_users: number
    }
    system: {
      [key: string]: number
    }
  }
  time_range: string
}

interface Alert {
  id: string
  status: string
  severity: string
  message: string
  fired_at: string
  current_value: number
  threshold_value: number
}

const MonitoringDashboard: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [timeRange, setTimeRange] = useState('1h')
  const [monitoringData, setMonitoringData] = useState<MonitoringData | null>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [systemMetrics, setSystemMetrics] = useState<any>(null)

  // 加载监控数据
  const loadMonitoringData = async () => {
    setLoading(true)
    try {
      const [overview, alertsData, systemData] = await Promise.all([
        monitoringApi.getOverview({ time_range: timeRange }),
        monitoringApi.getAlerts({ status_filter: 'firing', page_size: 10 }),
        monitoringApi.getSystemMetrics()
      ])
      
      setMonitoringData(overview)
      setAlerts(alertsData.alerts || [])
      setSystemMetrics(systemData.metrics || {})
    } catch (error) {
      console.error('加载监控数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  // 刷新数据
  const handleRefresh = async () => {
    setRefreshing(true)
    await loadMonitoringData()
    setRefreshing(false)
  }

  // 时间范围变化
  const handleTimeRangeChange = (value: string) => {
    setTimeRange(value)
  }

  useEffect(() => {
    loadMonitoringData()
  }, [timeRange])

  // 自动刷新
  useEffect(() => {
    const interval = setInterval(() => {
      loadMonitoringData()
    }, 30000) // 30秒刷新一次

    return () => clearInterval(interval)
  }, [timeRange])

  // 获取状态颜色
  const getStatusColor = (value: number, thresholds: { warning: number; critical: number }) => {
    if (value >= thresholds.critical) return '#ff4d4f'
    if (value >= thresholds.warning) return '#faad14'
    return '#52c41a'
  }

  // 获取告警严重程度颜色
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'red'
      case 'error': return 'orange'
      case 'warning': return 'yellow'
      case 'info': return 'blue'
      default: return 'default'
    }
  }

  // 告警表格列定义
  const alertColumns = [
    {
      title: '严重程度',
      dataIndex: 'severity',
      key: 'severity',
      render: (severity: string) => (
        <Tag color={getSeverityColor(severity)}>
          {severity.toUpperCase()}
        </Tag>
      )
    },
    {
      title: '告警信息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true
    },
    {
      title: '当前值',
      dataIndex: 'current_value',
      key: 'current_value',
      render: (value: number) => value.toFixed(2)
    },
    {
      title: '阈值',
      dataIndex: 'threshold_value',
      key: 'threshold_value',
      render: (value: number) => value.toFixed(2)
    },
    {
      title: '触发时间',
      dataIndex: 'fired_at',
      key: 'fired_at',
      render: (time: string) => new Date(time).toLocaleString()
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record: Alert) => (
        <Button size="small" type="link">
          确认
        </Button>
      )
    }
  ]

  if (loading && !monitoringData) {
    return (
      <div className="monitoring-dashboard">
        <Spin size="large" style={{ display: 'block', textAlign: 'center', padding: '100px 0' }} />
      </div>
    )
  }

  return (
    <div className="monitoring-dashboard">
      {/* 头部控制栏 */}
      <div className="dashboard-header">
        <div className="header-left">
          <Title level={2}>
            <DashboardOutlined style={{ marginRight: 8, color: '#1890ff' }} />
            监控面板
          </Title>
          <Text type="secondary">实时系统性能监控和告警管理</Text>
        </div>
        
        <div className="header-right">
          <Space>
            <Select
              value={timeRange}
              onChange={handleTimeRangeChange}
              style={{ width: 120 }}
            >
              <Option value="1h">最近1小时</Option>
              <Option value="24h">最近24小时</Option>
              <Option value="7d">最近7天</Option>
              <Option value="30d">最近30天</Option>
            </Select>
            
            <Button
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              loading={refreshing}
            >
              刷新
            </Button>
          </Space>
        </div>
      </div>

      {/* 告警横幅 */}
      {alerts.length > 0 && (
        <Alert
          message={`当前有 ${alerts.length} 个活跃告警`}
          type="warning"
          showIcon
          style={{ marginBottom: 24 }}
          action={
            <Button size="small" type="text">
              查看详情
            </Button>
          }
        />
      )}

      {/* 系统指标卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="CPU使用率"
              value={systemMetrics?.cpu_usage || 0}
              precision={1}
              suffix="%"
              valueStyle={{ 
                color: getStatusColor(systemMetrics?.cpu_usage || 0, { warning: 70, critical: 90 })
              }}
              prefix={<TrendingUpOutlined />}
            />
            <Progress
              percent={systemMetrics?.cpu_usage || 0}
              strokeColor={getStatusColor(systemMetrics?.cpu_usage || 0, { warning: 70, critical: 90 })}
              showInfo={false}
              size="small"
            />
          </Card>
        </Col>
        
        <Col span={6}>
          <Card>
            <Statistic
              title="内存使用率"
              value={systemMetrics?.memory_usage || 0}
              precision={1}
              suffix="%"
              valueStyle={{ 
                color: getStatusColor(systemMetrics?.memory_usage || 0, { warning: 80, critical: 95 })
              }}
              prefix={<TrendingUpOutlined />}
            />
            <Progress
              percent={systemMetrics?.memory_usage || 0}
              strokeColor={getStatusColor(systemMetrics?.memory_usage || 0, { warning: 80, critical: 95 })}
              showInfo={false}
              size="small"
            />
          </Card>
        </Col>
        
        <Col span={6}>
          <Card>
            <Statistic
              title="磁盘使用率"
              value={systemMetrics?.disk_usage || 0}
              precision={1}
              suffix="%"
              valueStyle={{ 
                color: getStatusColor(systemMetrics?.disk_usage || 0, { warning: 85, critical: 95 })
              }}
              prefix={<TrendingUpOutlined />}
            />
            <Progress
              percent={systemMetrics?.disk_usage || 0}
              strokeColor={getStatusColor(systemMetrics?.disk_usage || 0, { warning: 85, critical: 95 })}
              showInfo={false}
              size="small"
            />
          </Card>
        </Col>
        
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃告警"
              value={alerts.length}
              valueStyle={{ color: alerts.length > 0 ? '#ff4d4f' : '#52c41a' }}
              prefix={<AlertOutlined />}
            />
            <div style={{ marginTop: 8 }}>
              <Tag color={alerts.length > 0 ? 'red' : 'green'}>
                {alerts.length > 0 ? '需要关注' : '系统正常'}
              </Tag>
            </div>
          </Card>
        </Col>
      </Row>

      {/* API和AI指标 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card
            title={
              <Space>
                <ApiOutlined />
                <span>API调用统计</span>
              </Space>
            }
          >
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="总请求数"
                  value={monitoringData?.summary.api.total_requests || 0}
                  prefix={<ApiOutlined />}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="平均响应时间"
                  value={monitoringData?.summary.api.avg_response_time || 0}
                  precision={2}
                  suffix="ms"
                  prefix={<ClockCircleOutlined />}
                />
              </Col>
            </Row>
            
            <Row gutter={16} style={{ marginTop: 16 }}>
              <Col span={12}>
                <Statistic
                  title="错误数量"
                  value={monitoringData?.summary.api.error_count || 0}
                  valueStyle={{ color: '#ff4d4f' }}
                  prefix={<WarningOutlined />}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="错误率"
                  value={monitoringData?.summary.api.error_rate || 0}
                  precision={2}
                  suffix="%"
                  valueStyle={{ 
                    color: (monitoringData?.summary.api.error_rate || 0) > 5 ? '#ff4d4f' : '#52c41a'
                  }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
        
        <Col span={12}>
          <Card
            title={
              <Space>
                <RobotOutlined />
                <span>AI模型统计</span>
              </Space>
            }
          >
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="总调用数"
                  value={monitoringData?.summary.ai.total_calls || 0}
                  prefix={<RobotOutlined />}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="总Token数"
                  value={monitoringData?.summary.ai.total_tokens || 0}
                  formatter={(value) => `${Number(value).toLocaleString()}`}
                />
              </Col>
            </Row>
            
            <Row gutter={16} style={{ marginTop: 16 }}>
              <Col span={12}>
                <Statistic
                  title="总成本"
                  value={monitoringData?.summary.ai.total_cost || 0}
                  precision={4}
                  prefix="$"
                  valueStyle={{ color: '#faad14' }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="平均响应时间"
                  value={monitoringData?.summary.ai.avg_response_time || 0}
                  precision={2}
                  suffix="s"
                  prefix={<ClockCircleOutlined />}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* 活跃告警列表 */}
      <Card
        title={
          <Space>
            <AlertOutlined />
            <span>活跃告警</span>
            <Badge count={alerts.length} showZero color="#ff4d4f" />
          </Space>
        }
        extra={
          <Button type="link" size="small">
            查看全部
          </Button>
        }
      >
        {alerts.length > 0 ? (
          <Table
            columns={alertColumns}
            dataSource={alerts}
            rowKey="id"
            pagination={false}
            size="small"
          />
        ) : (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无活跃告警"
            style={{ padding: '20px 0' }}
          >
            <Space>
              <CheckCircleOutlined style={{ color: '#52c41a' }} />
              <Text type="secondary">系统运行正常</Text>
            </Space>
          </Empty>
        )}
      </Card>
    </div>
  )
}

export default MonitoringDashboard
