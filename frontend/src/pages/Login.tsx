/**
 * 登录页面
 */

import React, { useState } from 'react'
import { Form, Input, Button, Card, Typography, Divider, Space, message } from 'antd'
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { LoginRequest, RegisterRequest } from '../services/api'

const { Title, Text } = Typography

const Login: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { login, register } = useAuthStore()

  const from = (location.state as any)?.from?.pathname || '/'

  const handleLogin = async (values: LoginRequest) => {
    setLoading(true)
    try {
      const success = await login(values)
      if (success) {
        navigate(from, { replace: true })
      }
    } catch (error) {
      console.error('登录失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (values: RegisterRequest & { confirmPassword: string }) => {
    if (values.password !== values.confirmPassword) {
      message.error('两次输入的密码不一致')
      return
    }

    setLoading(true)
    try {
      const success = await register({
        username: values.username,
        email: values.email,
        password: values.password,
      })
      if (success) {
        setIsLogin(true)
      }
    } catch (error) {
      console.error('注册失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const testApiConnection = async () => {
    try {
      const response = await fetch('/api/health')
      const data = await response.json()
      message.success(`API连接成功！状态: ${data.status}`)
    } catch (error) {
      message.error('API连接失败，请检查后端服务')
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '20px'
    }}>
      <Card
        style={{
          width: '100%',
          maxWidth: '400px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          borderRadius: '12px'
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <Title level={2} style={{ color: '#1890ff', marginBottom: '8px' }}>
            Enhance Prompt Engineer
          </Title>
          <Text type="secondary">
            {isLogin ? '登录您的账户' : '创建新账户'}
          </Text>
        </div>

        {isLogin ? (
          <Form
            name="login"
            onFinish={handleLogin}
            autoComplete="off"
            size="large"
          >
            <Form.Item
              name="email"
              rules={[
                { required: true, message: '请输入邮箱地址' },
                { type: 'email', message: '请输入有效的邮箱地址' }
              ]}
            >
              <Input
                prefix={<MailOutlined />}
                placeholder="邮箱地址"
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="密码"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                style={{ height: '44px' }}
              >
                登录
              </Button>
            </Form.Item>
          </Form>
        ) : (
          <Form
            name="register"
            onFinish={handleRegister}
            autoComplete="off"
            size="large"
          >
            <Form.Item
              name="username"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, message: '用户名至少需要3个字符' }
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="用户名"
              />
            </Form.Item>

            <Form.Item
              name="email"
              rules={[
                { required: true, message: '请输入邮箱地址' },
                { type: 'email', message: '请输入有效的邮箱地址' }
              ]}
            >
              <Input
                prefix={<MailOutlined />}
                placeholder="邮箱地址"
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 6, message: '密码至少需要6个字符' }
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="密码"
              />
            </Form.Item>

            <Form.Item
              name="confirmPassword"
              rules={[{ required: true, message: '请确认密码' }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="确认密码"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                style={{ height: '44px' }}
              >
                注册
              </Button>
            </Form.Item>
          </Form>
        )}

        <Divider />

        <div style={{ textAlign: 'center' }}>
          <Space direction="vertical" size="middle">
            <Text>
              {isLogin ? '还没有账户？' : '已有账户？'}
              <Button
                type="link"
                onClick={() => setIsLogin(!isLogin)}
                style={{ padding: 0, marginLeft: '8px' }}
              >
                {isLogin ? '立即注册' : '立即登录'}
              </Button>
            </Text>

            <Button
              type="link"
              onClick={testApiConnection}
              size="small"
            >
              测试API连接
            </Button>
          </Space>
        </div>
      </Card>
    </div>
  )
}

export default Login
