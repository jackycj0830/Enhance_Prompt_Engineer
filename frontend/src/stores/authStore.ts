/**
 * 认证状态管理
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authApi, User, LoginRequest, RegisterRequest } from '../services/api'
import { message } from 'antd'

interface AuthState {
  // 状态
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean

  // 操作
  login: (credentials: LoginRequest) => Promise<boolean>
  register: (userData: RegisterRequest) => Promise<boolean>
  logout: () => void
  refreshToken: () => Promise<boolean>
  getCurrentUser: () => Promise<void>
  setLoading: (loading: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // 初始状态
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      // 登录
      login: async (credentials: LoginRequest) => {
        set({ isLoading: true })
        
        try {
          const response = await authApi.login(credentials)
          const { access_token, user } = response
          
          // 保存token到localStorage
          localStorage.setItem('access_token', access_token)
          localStorage.setItem('user_info', JSON.stringify(user))
          
          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false
          })
          
          message.success('登录成功')
          return true
        } catch (error) {
          set({ isLoading: false })
          console.error('登录失败:', error)
          return false
        }
      },

      // 注册
      register: async (userData: RegisterRequest) => {
        set({ isLoading: true })
        
        try {
          await authApi.register(userData)
          set({ isLoading: false })
          message.success('注册成功，请登录')
          return true
        } catch (error) {
          set({ isLoading: false })
          console.error('注册失败:', error)
          return false
        }
      },

      // 登出
      logout: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user_info')
        
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false
        })
        
        message.success('已退出登录')
      },

      // 刷新token
      refreshToken: async () => {
        try {
          const response = await authApi.refreshToken()
          const { access_token, user } = response
          
          localStorage.setItem('access_token', access_token)
          localStorage.setItem('user_info', JSON.stringify(user))
          
          set({
            user,
            token: access_token,
            isAuthenticated: true
          })
          
          return true
        } catch (error) {
          console.error('刷新token失败:', error)
          get().logout()
          return false
        }
      },

      // 获取当前用户信息
      getCurrentUser: async () => {
        const token = localStorage.getItem('access_token')
        if (!token) {
          return
        }

        try {
          const user = await authApi.getCurrentUser()
          set({
            user,
            token,
            isAuthenticated: true
          })
        } catch (error) {
          console.error('获取用户信息失败:', error)
          get().logout()
        }
      },

      // 设置加载状态
      setLoading: (loading: boolean) => {
        set({ isLoading: loading })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

// 初始化认证状态
export const initializeAuth = async () => {
  const token = localStorage.getItem('access_token')
  const userInfo = localStorage.getItem('user_info')
  
  if (token && userInfo) {
    try {
      const user = JSON.parse(userInfo)
      useAuthStore.setState({
        user,
        token,
        isAuthenticated: true
      })
      
      // 验证token是否仍然有效
      await useAuthStore.getState().getCurrentUser()
    } catch (error) {
      console.error('初始化认证状态失败:', error)
      useAuthStore.getState().logout()
    }
  }
}
