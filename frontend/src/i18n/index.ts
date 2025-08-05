/**
 * 国际化配置
 */

import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import Backend from 'i18next-http-backend'

// 导入语言资源
import zhCN from './locales/zh-CN.json'
import enUS from './locales/en-US.json'
import jaJP from './locales/ja-JP.json'

// 支持的语言列表
export const supportedLanguages = [
  { code: 'zh-CN', name: '简体中文', nativeName: '简体中文' },
  { code: 'en-US', name: 'English', nativeName: 'English' },
  { code: 'ja-JP', name: 'Japanese', nativeName: '日本語' }
]

// 默认语言
export const defaultLanguage = 'zh-CN'

// 语言资源
const resources = {
  'zh-CN': { translation: zhCN },
  'en-US': { translation: enUS },
  'ja-JP': { translation: jaJP }
}

// 初始化i18n
i18n
  .use(Backend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: defaultLanguage,
    debug: process.env.NODE_ENV === 'development',
    
    // 语言检测配置
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
      lookupLocalStorage: 'i18nextLng',
      checkWhitelist: true
    },

    // 插值配置
    interpolation: {
      escapeValue: false, // React已经处理了XSS
      format: (value, format, lng) => {
        if (format === 'uppercase') return value.toUpperCase()
        if (format === 'lowercase') return value.toLowerCase()
        if (format === 'currency') {
          return new Intl.NumberFormat(lng, {
            style: 'currency',
            currency: lng === 'zh-CN' ? 'CNY' : lng === 'ja-JP' ? 'JPY' : 'USD'
          }).format(value)
        }
        if (format === 'date') {
          return new Intl.DateTimeFormat(lng).format(new Date(value))
        }
        if (format === 'datetime') {
          return new Intl.DateTimeFormat(lng, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          }).format(new Date(value))
        }
        return value
      }
    },

    // 命名空间
    defaultNS: 'translation',
    ns: ['translation'],

    // 键分隔符
    keySeparator: '.',
    nsSeparator: ':',

    // 复数规则
    pluralSeparator: '_',
    contextSeparator: '_',

    // 后端配置
    backend: {
      loadPath: '/locales/{{lng}}/{{ns}}.json',
      addPath: '/locales/add/{{lng}}/{{ns}}',
      allowMultiLoading: false,
      crossDomain: false,
      withCredentials: false,
      overrideMimeType: false,
      requestOptions: {
        mode: 'cors',
        credentials: 'same-origin',
        cache: 'default'
      }
    },

    // React配置
    react: {
      useSuspense: false,
      bindI18n: 'languageChanged',
      bindI18nStore: '',
      transEmptyNodeValue: '',
      transSupportBasicHtmlNodes: true,
      transKeepBasicHtmlNodesFor: ['br', 'strong', 'i', 'em', 'span']
    }
  })

// 语言切换函数
export const changeLanguage = (language: string) => {
  i18n.changeLanguage(language)
  
  // 更新HTML lang属性
  document.documentElement.lang = language
  
  // 更新页面方向（如果需要）
  const isRTL = ['ar', 'he', 'fa'].includes(language)
  document.documentElement.dir = isRTL ? 'rtl' : 'ltr'
  
  // 触发自定义事件
  window.dispatchEvent(new CustomEvent('languageChanged', { detail: language }))
}

// 获取当前语言
export const getCurrentLanguage = () => i18n.language || defaultLanguage

// 获取语言显示名称
export const getLanguageName = (code: string) => {
  const lang = supportedLanguages.find(l => l.code === code)
  return lang ? lang.name : code
}

// 获取语言本地名称
export const getLanguageNativeName = (code: string) => {
  const lang = supportedLanguages.find(l => l.code === code)
  return lang ? lang.nativeName : code
}

// 检查是否支持某种语言
export const isLanguageSupported = (code: string) => {
  return supportedLanguages.some(l => l.code === code)
}

// 格式化数字
export const formatNumber = (value: number, options?: Intl.NumberFormatOptions) => {
  const locale = getCurrentLanguage()
  return new Intl.NumberFormat(locale, options).format(value)
}

// 格式化货币
export const formatCurrency = (value: number, currency?: string) => {
  const locale = getCurrentLanguage()
  const defaultCurrency = locale === 'zh-CN' ? 'CNY' : locale === 'ja-JP' ? 'JPY' : 'USD'
  
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency || defaultCurrency
  }).format(value)
}

// 格式化日期
export const formatDate = (date: Date | string | number, options?: Intl.DateTimeFormatOptions) => {
  const locale = getCurrentLanguage()
  return new Intl.DateTimeFormat(locale, options).format(new Date(date))
}

// 格式化相对时间
export const formatRelativeTime = (date: Date | string | number) => {
  const locale = getCurrentLanguage()
  const now = new Date()
  const target = new Date(date)
  const diffInSeconds = Math.floor((target.getTime() - now.getTime()) / 1000)
  
  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' })
  
  const intervals = [
    { unit: 'year' as const, seconds: 31536000 },
    { unit: 'month' as const, seconds: 2592000 },
    { unit: 'day' as const, seconds: 86400 },
    { unit: 'hour' as const, seconds: 3600 },
    { unit: 'minute' as const, seconds: 60 },
    { unit: 'second' as const, seconds: 1 }
  ]
  
  for (const interval of intervals) {
    const count = Math.floor(Math.abs(diffInSeconds) / interval.seconds)
    if (count >= 1) {
      return rtf.format(diffInSeconds < 0 ? -count : count, interval.unit)
    }
  }
  
  return rtf.format(0, 'second')
}

// 复数处理
export const pluralize = (count: number, key: string, options?: any) => {
  return i18n.t(key, { count, ...options })
}

// 获取翻译函数
export const getTranslation = (key: string, options?: any) => {
  return i18n.t(key, options)
}

// 检查翻译是否存在
export const hasTranslation = (key: string, lng?: string) => {
  return i18n.exists(key, { lng })
}

// 添加翻译资源
export const addTranslationResource = (lng: string, ns: string, key: string, value: string) => {
  i18n.addResource(lng, ns, key, value)
}

// 批量添加翻译资源
export const addTranslationResources = (lng: string, ns: string, resources: Record<string, any>) => {
  i18n.addResourceBundle(lng, ns, resources, true, true)
}

// 移除翻译资源
export const removeTranslationResource = (lng: string, ns: string, key: string) => {
  i18n.removeResourceBundle(lng, ns)
}

// 获取所有翻译键
export const getAllTranslationKeys = (lng?: string, ns?: string) => {
  const language = lng || getCurrentLanguage()
  const namespace = ns || 'translation'
  
  const store = i18n.getResourceBundle(language, namespace)
  if (!store) return []
  
  const keys: string[] = []
  const extractKeys = (obj: any, prefix = '') => {
    Object.keys(obj).forEach(key => {
      const fullKey = prefix ? `${prefix}.${key}` : key
      if (typeof obj[key] === 'object' && obj[key] !== null) {
        extractKeys(obj[key], fullKey)
      } else {
        keys.push(fullKey)
      }
    })
  }
  
  extractKeys(store)
  return keys
}

// 导出i18n实例
export default i18n
