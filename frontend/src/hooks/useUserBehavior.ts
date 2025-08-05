/**
 * 用户行为分析Hook
 */

import { useEffect, useRef, useCallback } from 'react'
import { throttle, debounce } from 'lodash-es'

interface UserAction {
  type: string
  target?: string
  data?: any
  timestamp: number
  sessionId: string
  userId?: string
  page: string
  userAgent: string
}

interface UserSession {
  sessionId: string
  startTime: number
  endTime?: number
  pageViews: number
  actions: UserAction[]
  duration?: number
}

interface BehaviorAnalytics {
  clickHeatmap: Map<string, number>
  scrollDepth: Map<string, number>
  timeOnPage: Map<string, number>
  errorEvents: UserAction[]
  conversionFunnels: Map<string, number>
}

export function useUserBehavior() {
  const sessionRef = useRef<UserSession | null>(null)
  const analyticsRef = useRef<BehaviorAnalytics>({
    clickHeatmap: new Map(),
    scrollDepth: new Map(),
    timeOnPage: new Map(),
    errorEvents: [],
    conversionFunnels: new Map()
  })
  const pageStartTimeRef = useRef<number>(Date.now())
  const maxScrollDepthRef = useRef<number>(0)

  // 初始化会话
  const initSession = useCallback(() => {
    const sessionId = generateSessionId()
    const userId = localStorage.getItem('userId') || undefined

    sessionRef.current = {
      sessionId,
      startTime: Date.now(),
      pageViews: 1,
      actions: [],
      userId
    }

    // 存储到localStorage
    localStorage.setItem('userSession', JSON.stringify(sessionRef.current))
  }, [])

  // 生成会话ID
  const generateSessionId = () => {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  // 记录用户行为
  const trackAction = useCallback((type: string, target?: string, data?: any) => {
    if (!sessionRef.current) return

    const action: UserAction = {
      type,
      target,
      data,
      timestamp: Date.now(),
      sessionId: sessionRef.current.sessionId,
      userId: sessionRef.current.userId,
      page: window.location.pathname,
      userAgent: navigator.userAgent
    }

    sessionRef.current.actions.push(action)

    // 更新分析数据
    updateAnalytics(action)

    // 发送到服务器（节流）
    sendActionToServer(action)
  }, [])

  // 更新分析数据
  const updateAnalytics = (action: UserAction) => {
    const analytics = analyticsRef.current

    switch (action.type) {
      case 'click':
        const clickKey = `${action.page}:${action.target}`
        analytics.clickHeatmap.set(clickKey, (analytics.clickHeatmap.get(clickKey) || 0) + 1)
        break

      case 'scroll':
        const scrollKey = action.page
        const currentDepth = action.data?.scrollDepth || 0
        const maxDepth = Math.max(analytics.scrollDepth.get(scrollKey) || 0, currentDepth)
        analytics.scrollDepth.set(scrollKey, maxDepth)
        break

      case 'error':
        analytics.errorEvents.push(action)
        break

      case 'conversion':
        const conversionKey = action.data?.funnelStep || 'unknown'
        analytics.conversionFunnels.set(conversionKey, (analytics.conversionFunnels.get(conversionKey) || 0) + 1)
        break
    }
  }

  // 发送行为数据到服务器（节流）
  const sendActionToServer = throttle(async (action: UserAction) => {
    try {
      await fetch('/api/v1/analytics/actions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(action)
      })
    } catch (error) {
      console.error('Failed to send user action:', error)
    }
  }, 1000)

  // 发送会话数据到服务器（防抖）
  const sendSessionToServer = debounce(async (session: UserSession) => {
    try {
      await fetch('/api/v1/analytics/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(session)
      })
    } catch (error) {
      console.error('Failed to send session data:', error)
    }
  }, 5000)

  // 页面访问跟踪
  const trackPageView = useCallback((page?: string) => {
    const currentPage = page || window.location.pathname
    
    // 记录上一页的停留时间
    if (pageStartTimeRef.current) {
      const timeOnPage = Date.now() - pageStartTimeRef.current
      analyticsRef.current.timeOnPage.set(currentPage, timeOnPage)
    }

    // 重置页面开始时间
    pageStartTimeRef.current = Date.now()
    maxScrollDepthRef.current = 0

    // 更新会话
    if (sessionRef.current) {
      sessionRef.current.pageViews += 1
    }

    trackAction('pageview', currentPage)
  }, [trackAction])

  // 点击跟踪
  const trackClick = useCallback((target: string, data?: any) => {
    trackAction('click', target, data)
  }, [trackAction])

  // 滚动跟踪
  const trackScroll = useCallback(() => {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop
    const windowHeight = window.innerHeight
    const documentHeight = document.documentElement.scrollHeight
    const scrollDepth = Math.round((scrollTop + windowHeight) / documentHeight * 100)

    if (scrollDepth > maxScrollDepthRef.current) {
      maxScrollDepthRef.current = scrollDepth
      trackAction('scroll', window.location.pathname, { scrollDepth })
    }
  }, [trackAction])

  // 错误跟踪
  const trackError = useCallback((error: Error, errorInfo?: any) => {
    trackAction('error', 'javascript', {
      message: error.message,
      stack: error.stack,
      errorInfo
    })
  }, [trackAction])

  // 转化跟踪
  const trackConversion = useCallback((funnelStep: string, data?: any) => {
    trackAction('conversion', funnelStep, { funnelStep, ...data })
  }, [trackAction])

  // 表单跟踪
  const trackFormInteraction = useCallback((formName: string, fieldName: string, action: 'focus' | 'blur' | 'change' | 'submit') => {
    trackAction('form', `${formName}.${fieldName}`, { action })
  }, [trackAction])

  // 搜索跟踪
  const trackSearch = useCallback((query: string, results?: number) => {
    trackAction('search', 'search_box', { query, results })
  }, [trackAction])

  // 下载跟踪
  const trackDownload = useCallback((fileName: string, fileType?: string) => {
    trackAction('download', fileName, { fileType })
  }, [trackAction])

  // 外部链接跟踪
  const trackExternalLink = useCallback((url: string) => {
    trackAction('external_link', url)
  }, [trackAction])

  // 获取分析数据
  const getAnalytics = useCallback(() => {
    return {
      session: sessionRef.current,
      analytics: {
        clickHeatmap: Object.fromEntries(analyticsRef.current.clickHeatmap),
        scrollDepth: Object.fromEntries(analyticsRef.current.scrollDepth),
        timeOnPage: Object.fromEntries(analyticsRef.current.timeOnPage),
        errorEvents: analyticsRef.current.errorEvents,
        conversionFunnels: Object.fromEntries(analyticsRef.current.conversionFunnels)
      }
    }
  }, [])

  // 清除分析数据
  const clearAnalytics = useCallback(() => {
    analyticsRef.current = {
      clickHeatmap: new Map(),
      scrollDepth: new Map(),
      timeOnPage: new Map(),
      errorEvents: [],
      conversionFunnels: new Map()
    }
  }, [])

  // 结束会话
  const endSession = useCallback(() => {
    if (sessionRef.current) {
      sessionRef.current.endTime = Date.now()
      sessionRef.current.duration = sessionRef.current.endTime - sessionRef.current.startTime

      // 发送最终会话数据
      sendSessionToServer(sessionRef.current)

      // 清理
      localStorage.removeItem('userSession')
      sessionRef.current = null
    }
  }, [])

  // 设置事件监听器
  useEffect(() => {
    // 初始化会话
    const existingSession = localStorage.getItem('userSession')
    if (existingSession) {
      try {
        sessionRef.current = JSON.parse(existingSession)
      } catch {
        initSession()
      }
    } else {
      initSession()
    }

    // 滚动事件监听
    const throttledScrollTrack = throttle(trackScroll, 1000)
    window.addEventListener('scroll', throttledScrollTrack)

    // 点击事件监听
    const handleClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement
      const tagName = target.tagName.toLowerCase()
      const className = target.className
      const id = target.id
      const text = target.textContent?.slice(0, 50) || ''

      const targetSelector = id ? `#${id}` : className ? `.${className.split(' ')[0]}` : tagName
      trackClick(targetSelector, { tagName, text })
    }
    document.addEventListener('click', handleClick)

    // 错误事件监听
    const handleError = (event: ErrorEvent) => {
      trackError(new Error(event.message), {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
      })
    }
    window.addEventListener('error', handleError)

    // 页面卸载时结束会话
    const handleBeforeUnload = () => {
      endSession()
    }
    window.addEventListener('beforeunload', handleBeforeUnload)

    // 页面可见性变化
    const handleVisibilityChange = () => {
      if (document.hidden) {
        trackAction('page_hidden')
      } else {
        trackAction('page_visible')
      }
    }
    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      window.removeEventListener('scroll', throttledScrollTrack)
      document.removeEventListener('click', handleClick)
      window.removeEventListener('error', handleError)
      window.removeEventListener('beforeunload', handleBeforeUnload)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [initSession, trackScroll, trackClick, trackError, endSession, trackAction])

  return {
    trackAction,
    trackPageView,
    trackClick,
    trackScroll,
    trackError,
    trackConversion,
    trackFormInteraction,
    trackSearch,
    trackDownload,
    trackExternalLink,
    getAnalytics,
    clearAnalytics,
    endSession
  }
}
