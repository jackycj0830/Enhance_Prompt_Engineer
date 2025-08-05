/**
 * 仪表板页面
 */

import React, { useEffect, useState } from 'react'
import { 
  Layout, 
  Menu, 
  Typography, 
  Card, 
  Row, 
  Col, 
  Statistic, 
  Button, 
  Space, 
  Avatar, 
  Dropdown,
  message,
  Spin
} from 'antd'
import {
  DashboardOutlined,
  FileTextOutlined,
  AnalyticsOutlined,
  BookOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  PlusOutlined,
  RocketOutlined,
  ApiOutlined
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useAppStore } from '../stores/appStore'
import { userApi } from '../services/api'

const { Header, Sider, Content } = Layout
const { Title, Text } = Typography

const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const { sidebarCollapsed, setSidebarCollapsed } = useAppStore()
  const [userStats, setUserStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  // 菜单项配置
  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/prompts',
      icon: <FileTextOutlined />,
      label: '提示词管理',
    },
    {
      key: '/analysis',
      icon: <AnalyticsOutlined />,
      label: '分析中心',
    },
    {
      key: '/templates',
      icon: <BookOutlined />,
      label: '模板库',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
  ]

  // 用户菜单
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
    },
  ]

  // 获取用户统计信息
  useEffect(() => {
    const fetchUserStats = async () => {
      try {
        const stats = await userApi.getStats()
        setUserStats(stats)
      } catch (error) {
        console.error('获取用户统计失败:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchUserStats()
  }, [])

  // 处理菜单点击
  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  // 处理用户菜单点击
  const handleUserMenuClick = ({ key }: { key: string }) => {
    switch (key) {
      case 'profile':
        navigate('/profile')
        break
      case 'settings':
        navigate('/settings')
        break
      case 'logout':
        logout()
        break
    }
  }

  // 测试API连接
  const testApiConnection = async () => {
    try {
      const response = await fetch('/api/v1/status')
      const data = await response.json()
      message.success(`API连接成功！状态: ${data.status}`)
    } catch (error) {
      message.error('API连接失败，请检查后端服务')
    }
  }

  // 快速操作
  const quickActions = [
    {
      title: '创建提示词',
      description: '开始创建新的提示词',
      icon: <PlusOutlined />,
      action: () => navigate('/prompts'),
    },
    {
      title: '分析提示词',
      description: '分析现有提示词的质量',
      icon: <AnalyticsOutlined />,
      action: () => navigate('/prompts'),
    },
    {
      title: '浏览模板',
      description: '查看和使用提示词模板',
      icon: <BookOutlined />,
      action: () => navigate('/templates'),
    },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 侧边栏 */}
      <Sider
        collapsible
        collapsed={sidebarCollapsed}
        onCollapse={setSidebarCollapsed}
        theme="light"
        style={{
          boxShadow: '2px 0 8px rgba(0,0,0,0.1)',
        }}
      >
        <div style={{
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderBottom: '1px solid #f0f0f0',
        }}>
          <RocketOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
          {!sidebarCollapsed && (
            <Title level={4} style={{ margin: '0 0 0 12px', color: '#1890ff' }}>
              EPE
            </Title>
          )}
        </div>
        
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 0 }}
        />
      </Sider>

      <Layout>
        {/* 顶部导航 */}
        <Header style={{
          background: '#fff',
          padding: '0 24px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <Title level={3} style={{ margin: 0 }}>
            仪表板
          </Title>
          
          <Space>
            <Button
              type="text"
              icon={<ApiOutlined />}
              onClick={testApiConnection}
            >
              测试API
            </Button>
            
            <Dropdown
              menu={{
                items: userMenuItems,
                onClick: handleUserMenuClick,
              }}
              placement="bottomRight"
            >
              <Space style={{ cursor: 'pointer' }}>
                <Avatar icon={<UserOutlined />} />
                <Text>{user?.username}</Text>
              </Space>
            </Dropdown>
          </Space>
        </Header>

        {/* 主内容区 */}
        <Content style={{ margin: '24px', background: '#f0f2f5' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '100px 0' }}>
              <Spin size="large" tip="加载中..." />
            </div>
          ) : (
            <div>
              {/* 欢迎信息 */}
              <Card style={{ marginBottom: '24px' }}>
                <Row align="middle">
                  <Col flex="auto">
                    <Title level={2} style={{ margin: 0 }}>
                      欢迎回来，{user?.username}！
                    </Title>
                    <Text type="secondary">
                      今天是个分析和优化提示词的好日子
                    </Text>
                  </Col>
                  <Col>
                    <Button type="primary" size="large" icon={<PlusOutlined />}>
                      创建新提示词
                    </Button>
                  </Col>
                </Row>
              </Card>

              {/* 统计卡片 */}
              <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
                <Col xs={24} sm={12} lg={6}>
                  <Card>
                    <Statistic
                      title="提示词总数"
                      value={userStats?.prompt_count || 0}
                      prefix={<FileTextOutlined />}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                  <Card>
                    <Statistic
                      title="分析次数"
                      value={userStats?.analysis_count || 0}
                      prefix={<AnalyticsOutlined />}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                  <Card>
                    <Statistic
                      title="创建模板"
                      value={userStats?.template_count || 0}
                      prefix={<BookOutlined />}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                  <Card>
                    <Statistic
                      title="使用天数"
                      value={userStats?.user_since ? 
                        Math.ceil((Date.now() - new Date(userStats.user_since).getTime()) / (1000 * 60 * 60 * 24)) : 0
                      }
                      suffix="天"
                      prefix={<UserOutlined />}
                    />
                  </Card>
                </Col>
              </Row>

              {/* 快速操作 */}
              <Card title="快速操作" style={{ marginBottom: '24px' }}>
                <Row gutter={[16, 16]}>
                  {quickActions.map((action, index) => (
                    <Col xs={24} sm={12} lg={8} key={index}>
                      <Card
                        hoverable
                        onClick={action.action}
                        style={{ textAlign: 'center', cursor: 'pointer' }}
                      >
                        <div style={{ fontSize: '32px', color: '#1890ff', marginBottom: '16px' }}>
                          {action.icon}
                        </div>
                        <Title level={4}>{action.title}</Title>
                        <Text type="secondary">{action.description}</Text>
                      </Card>
                    </Col>
                  ))}
                </Row>
              </Card>

              {/* 系统状态 */}
              <Card title="系统状态">
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Text strong>前端服务: </Text>
                    <Text type="success">运行中</Text>
                  </Col>
                  <Col span={12}>
                    <Text strong>后端API: </Text>
                    <Text type="success">已连接</Text>
                  </Col>
                  <Col span={12}>
                    <Text strong>数据库: </Text>
                    <Text type="success">正常</Text>
                  </Col>
                  <Col span={12}>
                    <Text strong>缓存服务: </Text>
                    <Text type="success">正常</Text>
                  </Col>
                </Row>
              </Card>
            </div>
          )}
        </Content>
      </Layout>
    </Layout>
  )
}

export default Dashboard
