/**
 * 受保护的路由组件
 */

import React, { useEffect } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { Spin } from 'antd'
import { useAuthStore } from '../stores/authStore'

interface ProtectedRouteProps {
  children: React.ReactNode
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading, getCurrentUser } = useAuthStore()
  const location = useLocation()

  useEffect(() => {
    // 如果有token但没有用户信息，尝试获取用户信息
    const token = localStorage.getItem('access_token')
    if (token && !isAuthenticated && !isLoading) {
      getCurrentUser()
    }
  }, [isAuthenticated, isLoading, getCurrentUser])

  // 显示加载状态
  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        <Spin size="large" tip="加载中..." />
      </div>
    )
  }

  // 如果未认证，重定向到登录页
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // 如果已认证，渲染子组件
  return <>{children}</>
}

export default ProtectedRoute
