import React, { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Layout, Spin } from 'antd'
import { useAuthStore } from './stores/authStore'
import { initializeAuth } from './stores/authStore'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import PromptManagement from './pages/PromptManagement'
import TemplateManagement from './pages/TemplateManagement'
import MonitoringPage from './pages/MonitoringPage'
import PWAInstall from './components/PWAInstall'
import './App.css'
import './styles/mobile.css'

const { Content } = Layout

// 应用初始化组件
const AppInitializer: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isInitialized, setIsInitialized] = React.useState(false)

  useEffect(() => {
    const initialize = async () => {
      try {
        await initializeAuth()

        // 注册Service Worker
        if ('serviceWorker' in navigator) {
          navigator.serviceWorker.register('/sw.js')
            .then((registration) => {
              console.log('SW registered: ', registration)
            })
            .catch((registrationError) => {
              console.log('SW registration failed: ', registrationError)
            })
        }
      } catch (error) {
        console.error('应用初始化失败:', error)
      } finally {
        setIsInitialized(true)
      }
    }

    initialize()
  }, [])

  if (!isInitialized) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh'
      }}>
        <Spin size="large" tip="应用初始化中..." />
      </div>
    )
  }

  return <>{children}</>
}

const App: React.FC = () => {
  return (
    <Router>
      <AppInitializer>
        <Layout style={{ minHeight: '100vh' }}>
          <Content>
            <Routes>
              {/* 公开路由 */}
              <Route path="/login" element={<Login />} />

              {/* 受保护的路由 */}
              <Route path="/" element={
                <ProtectedRoute>
                  <Navigate to="/dashboard" replace />
                </ProtectedRoute>
              } />

              <Route path="/dashboard" element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              } />

              {/* 其他受保护的路由将在后续添加 */}
              <Route path="/prompts" element={
                <ProtectedRoute>
                  <PromptManagement />
                </ProtectedRoute>
              } />

              <Route path="/analysis" element={
                <ProtectedRoute>
                  <div>分析页面（开发中）</div>
                </ProtectedRoute>
              } />

              <Route path="/templates" element={
                <ProtectedRoute>
                  <TemplateManagement />
                </ProtectedRoute>
              } />

              <Route path="/monitoring" element={
                <ProtectedRoute>
                  <MonitoringPage />
                </ProtectedRoute>
              } />

              <Route path="/settings" element={
                <ProtectedRoute>
                  <div>设置页面（开发中）</div>
                </ProtectedRoute>
              } />

              {/* 404页面 */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Content>
        </Layout>

        {/* PWA安装组件 */}
        <PWAInstall />
      </AppInitializer>
    </Router>
  )
}

export default App
