import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Layout, Typography, Button, Space } from 'antd'
import { RocketOutlined, ApiOutlined } from '@ant-design/icons'
import './App.css'

const { Header, Content, Footer } = Layout
const { Title, Paragraph } = Typography

// 临时首页组件
const HomePage: React.FC = () => {
  const handleTestAPI = async () => {
    try {
      const response = await fetch('/api/health')
      const data = await response.json()
      console.log('API测试结果:', data)
      alert(`API连接成功！状态: ${data.status}`)
    } catch (error) {
      console.error('API测试失败:', error)
      alert('API连接失败，请检查后端服务')
    }
  }

  return (
    <div style={{ textAlign: 'center', padding: '50px 20px' }}>
      <RocketOutlined style={{ fontSize: '64px', color: '#1890ff', marginBottom: '24px' }} />
      <Title level={1}>Enhance Prompt Engineer</Title>
      <Paragraph style={{ fontSize: '18px', maxWidth: '600px', margin: '0 auto 32px' }}>
        专业的提示词分析与优化工具，帮助您提升AI应用的输出质量和效率
      </Paragraph>
      <Space size="large">
        <Button type="primary" size="large" icon={<ApiOutlined />} onClick={handleTestAPI}>
          测试API连接
        </Button>
        <Button size="large" href="/docs" target="_blank">
          查看API文档
        </Button>
      </Space>
      
      <div style={{ marginTop: '48px', padding: '24px', background: '#f5f5f5', borderRadius: '8px' }}>
        <Title level={3}>开发环境状态</Title>
        <Paragraph>
          🚀 前端服务: <strong>运行中</strong> (http://localhost:3000)<br/>
          🔗 后端API: <strong>待连接</strong> (http://localhost:8000)<br/>
          📚 API文档: <strong>可访问</strong> (http://localhost:8000/docs)<br/>
          🗄️ 数据库: <strong>待配置</strong> (PostgreSQL + Redis)
        </Paragraph>
      </div>
    </div>
  )
}

const App: React.FC = () => {
  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Header style={{ 
          background: '#fff', 
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <RocketOutlined style={{ fontSize: '24px', color: '#1890ff', marginRight: '12px' }} />
            <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
              Enhance Prompt Engineer
            </Title>
          </div>
        </Header>
        
        <Content style={{ padding: '24px' }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            {/* 后续添加更多路由 */}
          </Routes>
        </Content>
        
        <Footer style={{ textAlign: 'center', background: '#f0f2f5' }}>
          Enhance Prompt Engineer ©2025 Created by AI Development Team
        </Footer>
      </Layout>
    </Router>
  )
}

export default App
