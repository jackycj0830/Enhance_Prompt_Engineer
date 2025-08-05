/**
 * 应用全局状态管理
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AppState {
  // UI状态
  sidebarCollapsed: boolean
  theme: 'light' | 'dark'
  language: 'zh-CN' | 'en-US'
  
  // 应用状态
  isLoading: boolean
  currentPage: string
  
  // 用户偏好
  preferences: {
    preferred_ai_model: string
    analysis_depth: 'standard' | 'deep'
    notification_settings: {
      email: boolean
      push: boolean
    }
    ui_preferences: {
      theme: 'light' | 'dark'
      language: 'zh-CN' | 'en-US'
    }
  }

  // 操作
  setSidebarCollapsed: (collapsed: boolean) => void
  setTheme: (theme: 'light' | 'dark') => void
  setLanguage: (language: 'zh-CN' | 'en-US') => void
  setLoading: (loading: boolean) => void
  setCurrentPage: (page: string) => void
  updatePreferences: (preferences: Partial<AppState['preferences']>) => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // 初始状态
      sidebarCollapsed: false,
      theme: 'light',
      language: 'zh-CN',
      isLoading: false,
      currentPage: '/',
      
      preferences: {
        preferred_ai_model: 'gpt-3.5-turbo',
        analysis_depth: 'standard',
        notification_settings: {
          email: true,
          push: false,
        },
        ui_preferences: {
          theme: 'light',
          language: 'zh-CN',
        },
      },

      // 设置侧边栏折叠状态
      setSidebarCollapsed: (collapsed: boolean) => {
        set({ sidebarCollapsed: collapsed })
      },

      // 设置主题
      setTheme: (theme: 'light' | 'dark') => {
        set({ 
          theme,
          preferences: {
            ...get().preferences,
            ui_preferences: {
              ...get().preferences.ui_preferences,
              theme,
            },
          },
        })
      },

      // 设置语言
      setLanguage: (language: 'zh-CN' | 'en-US') => {
        set({ 
          language,
          preferences: {
            ...get().preferences,
            ui_preferences: {
              ...get().preferences.ui_preferences,
              language,
            },
          },
        })
      },

      // 设置加载状态
      setLoading: (loading: boolean) => {
        set({ isLoading: loading })
      },

      // 设置当前页面
      setCurrentPage: (page: string) => {
        set({ currentPage: page })
      },

      // 更新用户偏好
      updatePreferences: (newPreferences: Partial<AppState['preferences']>) => {
        set({
          preferences: {
            ...get().preferences,
            ...newPreferences,
          },
        })
      },
    }),
    {
      name: 'app-storage',
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        theme: state.theme,
        language: state.language,
        preferences: state.preferences,
      }),
    }
  )
)

// 数据状态管理
interface DataState {
  // 提示词数据
  prompts: any[]
  currentPrompt: any | null
  
  // 分析数据
  analysisHistory: any[]
  currentAnalysis: any | null
  
  // 模板数据
  templates: any[]
  currentTemplate: any | null
  
  // 统计数据
  userStats: any | null

  // 操作
  setPrompts: (prompts: any[]) => void
  setCurrentPrompt: (prompt: any | null) => void
  addPrompt: (prompt: any) => void
  updatePrompt: (id: string, prompt: any) => void
  removePrompt: (id: string) => void
  
  setAnalysisHistory: (history: any[]) => void
  setCurrentAnalysis: (analysis: any | null) => void
  addAnalysis: (analysis: any) => void
  
  setTemplates: (templates: any[]) => void
  setCurrentTemplate: (template: any | null) => void
  addTemplate: (template: any) => void
  updateTemplate: (id: string, template: any) => void
  removeTemplate: (id: string) => void
  
  setUserStats: (stats: any) => void
}

export const useDataStore = create<DataState>((set, get) => ({
  // 初始状态
  prompts: [],
  currentPrompt: null,
  analysisHistory: [],
  currentAnalysis: null,
  templates: [],
  currentTemplate: null,
  userStats: null,

  // 提示词操作
  setPrompts: (prompts: any[]) => set({ prompts }),
  setCurrentPrompt: (prompt: any | null) => set({ currentPrompt: prompt }),
  addPrompt: (prompt: any) => set({ prompts: [...get().prompts, prompt] }),
  updatePrompt: (id: string, updatedPrompt: any) => {
    set({
      prompts: get().prompts.map(p => p.id === id ? { ...p, ...updatedPrompt } : p),
      currentPrompt: get().currentPrompt?.id === id ? { ...get().currentPrompt, ...updatedPrompt } : get().currentPrompt,
    })
  },
  removePrompt: (id: string) => {
    set({
      prompts: get().prompts.filter(p => p.id !== id),
      currentPrompt: get().currentPrompt?.id === id ? null : get().currentPrompt,
    })
  },

  // 分析操作
  setAnalysisHistory: (history: any[]) => set({ analysisHistory: history }),
  setCurrentAnalysis: (analysis: any | null) => set({ currentAnalysis: analysis }),
  addAnalysis: (analysis: any) => set({ analysisHistory: [analysis, ...get().analysisHistory] }),

  // 模板操作
  setTemplates: (templates: any[]) => set({ templates }),
  setCurrentTemplate: (template: any | null) => set({ currentTemplate: template }),
  addTemplate: (template: any) => set({ templates: [...get().templates, template] }),
  updateTemplate: (id: string, updatedTemplate: any) => {
    set({
      templates: get().templates.map(t => t.id === id ? { ...t, ...updatedTemplate } : t),
      currentTemplate: get().currentTemplate?.id === id ? { ...get().currentTemplate, ...updatedTemplate } : get().currentTemplate,
    })
  },
  removeTemplate: (id: string) => {
    set({
      templates: get().templates.filter(t => t.id !== id),
      currentTemplate: get().currentTemplate?.id === id ? null : get().currentTemplate,
    })
  },

  // 统计数据操作
  setUserStats: (stats: any) => set({ userStats: stats }),
}))
