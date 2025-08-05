/**
 * 监控页面
 */

import React from 'react'
import { Layout, Typography } from 'antd'
import MonitoringDashboard from '../components/MonitoringDashboard'

const { Content } = Layout
const { Title } = Typography

const MonitoringPage: React.FC = () => {
  return (
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Content>
        <MonitoringDashboard />
      </Content>
    </Layout>
  )
}

export default MonitoringPage
