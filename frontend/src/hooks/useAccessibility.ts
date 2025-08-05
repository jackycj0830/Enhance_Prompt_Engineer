/**
 * 无障碍功能Hook
 */

import { useEffect, useRef, useCallback, useState } from 'react'

// 焦点管理Hook
export function useFocusManagement() {
  const focusableElementsRef = useRef<HTMLElement[]>([])
  const currentFocusIndexRef = useRef(-1)

  const updateFocusableElements = useCallback((container?: HTMLElement) => {
    const root = container || document.body
    const focusableSelectors = [
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      'a[href]',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable="true"]'
    ].join(', ')

    focusableElementsRef.current = Array.from(
      root.querySelectorAll(focusableSelectors)
    ) as HTMLElement[]
  }, [])

  const focusFirst = useCallback(() => {
    if (focusableElementsRef.current.length > 0) {
      focusableElementsRef.current[0].focus()
      currentFocusIndexRef.current = 0
    }
  }, [])

  const focusLast = useCallback(() => {
    const elements = focusableElementsRef.current
    if (elements.length > 0) {
      elements[elements.length - 1].focus()
      currentFocusIndexRef.current = elements.length - 1
    }
  }, [])

  const focusNext = useCallback(() => {
    const elements = focusableElementsRef.current
    if (elements.length === 0) return

    const currentIndex = currentFocusIndexRef.current
    const nextIndex = (currentIndex + 1) % elements.length
    elements[nextIndex].focus()
    currentFocusIndexRef.current = nextIndex
  }, [])

  const focusPrevious = useCallback(() => {
    const elements = focusableElementsRef.current
    if (elements.length === 0) return

    const currentIndex = currentFocusIndexRef.current
    const prevIndex = currentIndex <= 0 ? elements.length - 1 : currentIndex - 1
    elements[prevIndex].focus()
    currentFocusIndexRef.current = prevIndex
  }, [])

  const trapFocus = useCallback((container: HTMLElement) => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return

      updateFocusableElements(container)
      const elements = focusableElementsRef.current

      if (elements.length === 0) {
        event.preventDefault()
        return
      }

      const firstElement = elements[0]
      const lastElement = elements[elements.length - 1]

      if (event.shiftKey) {
        if (document.activeElement === firstElement) {
          event.preventDefault()
          lastElement.focus()
        }
      } else {
        if (document.activeElement === lastElement) {
          event.preventDefault()
          firstElement.focus()
        }
      }
    }

    container.addEventListener('keydown', handleKeyDown)
    return () => container.removeEventListener('keydown', handleKeyDown)
  }, [updateFocusableElements])

  return {
    updateFocusableElements,
    focusFirst,
    focusLast,
    focusNext,
    focusPrevious,
    trapFocus
  }
}

// 屏幕阅读器支持Hook
export function useScreenReader() {
  const [isScreenReaderActive, setIsScreenReaderActive] = useState(false)

  useEffect(() => {
    // 检测屏幕阅读器
    const checkScreenReader = () => {
      // 检查是否有屏幕阅读器相关的媒体查询
      const hasScreenReader = window.matchMedia('(prefers-reduced-motion: reduce)').matches ||
                             window.navigator.userAgent.includes('NVDA') ||
                             window.navigator.userAgent.includes('JAWS') ||
                             window.speechSynthesis?.getVoices().length > 0

      setIsScreenReaderActive(hasScreenReader)
    }

    checkScreenReader()
    
    // 监听语音合成变化
    if (window.speechSynthesis) {
      window.speechSynthesis.addEventListener('voiceschanged', checkScreenReader)
      return () => window.speechSynthesis.removeEventListener('voiceschanged', checkScreenReader)
    }
  }, [])

  const announce = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    const announcement = document.createElement('div')
    announcement.setAttribute('aria-live', priority)
    announcement.setAttribute('aria-atomic', 'true')
    announcement.className = 'sr-only'
    announcement.textContent = message

    document.body.appendChild(announcement)

    // 清理
    setTimeout(() => {
      document.body.removeChild(announcement)
    }, 1000)
  }, [])

  const speak = useCallback((text: string, options?: SpeechSynthesisUtteranceOptions) => {
    if (!window.speechSynthesis) return

    const utterance = new SpeechSynthesisUtterance(text)
    
    if (options) {
      Object.assign(utterance, options)
    }

    window.speechSynthesis.speak(utterance)
  }, [])

  const stopSpeaking = useCallback(() => {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel()
    }
  }, [])

  return {
    isScreenReaderActive,
    announce,
    speak,
    stopSpeaking
  }
}

// 键盘导航Hook
export function useKeyboardNavigation(options: {
  onEscape?: () => void
  onEnter?: () => void
  onArrowUp?: () => void
  onArrowDown?: () => void
  onArrowLeft?: () => void
  onArrowRight?: () => void
  onHome?: () => void
  onEnd?: () => void
} = {}) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      switch (event.key) {
        case 'Escape':
          options.onEscape?.()
          break
        case 'Enter':
          options.onEnter?.()
          break
        case 'ArrowUp':
          event.preventDefault()
          options.onArrowUp?.()
          break
        case 'ArrowDown':
          event.preventDefault()
          options.onArrowDown?.()
          break
        case 'ArrowLeft':
          options.onArrowLeft?.()
          break
        case 'ArrowRight':
          options.onArrowRight?.()
          break
        case 'Home':
          event.preventDefault()
          options.onHome?.()
          break
        case 'End':
          event.preventDefault()
          options.onEnd?.()
          break
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [options])
}

// 颜色对比度检查Hook
export function useColorContrast() {
  const checkContrast = useCallback((foreground: string, background: string): number => {
    // 将颜色转换为RGB
    const getRGB = (color: string) => {
      const canvas = document.createElement('canvas')
      canvas.width = canvas.height = 1
      const ctx = canvas.getContext('2d')!
      ctx.fillStyle = color
      ctx.fillRect(0, 0, 1, 1)
      const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data
      return [r, g, b]
    }

    // 计算相对亮度
    const getLuminance = (rgb: number[]) => {
      const [r, g, b] = rgb.map(c => {
        c = c / 255
        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
      })
      return 0.2126 * r + 0.7152 * g + 0.0722 * b
    }

    const fgRGB = getRGB(foreground)
    const bgRGB = getRGB(background)
    
    const fgLuminance = getLuminance(fgRGB)
    const bgLuminance = getLuminance(bgRGB)
    
    const lighter = Math.max(fgLuminance, bgLuminance)
    const darker = Math.min(fgLuminance, bgLuminance)
    
    return (lighter + 0.05) / (darker + 0.05)
  }, [])

  const isAccessible = useCallback((foreground: string, background: string, level: 'AA' | 'AAA' = 'AA'): boolean => {
    const contrast = checkContrast(foreground, background)
    return level === 'AA' ? contrast >= 4.5 : contrast >= 7
  }, [checkContrast])

  return { checkContrast, isAccessible }
}

// ARIA属性管理Hook
export function useAriaAttributes() {
  const setAriaLabel = useCallback((element: HTMLElement, label: string) => {
    element.setAttribute('aria-label', label)
  }, [])

  const setAriaDescribedBy = useCallback((element: HTMLElement, id: string) => {
    element.setAttribute('aria-describedby', id)
  }, [])

  const setAriaExpanded = useCallback((element: HTMLElement, expanded: boolean) => {
    element.setAttribute('aria-expanded', expanded.toString())
  }, [])

  const setAriaSelected = useCallback((element: HTMLElement, selected: boolean) => {
    element.setAttribute('aria-selected', selected.toString())
  }, [])

  const setAriaChecked = useCallback((element: HTMLElement, checked: boolean | 'mixed') => {
    element.setAttribute('aria-checked', checked.toString())
  }, [])

  const setAriaDisabled = useCallback((element: HTMLElement, disabled: boolean) => {
    element.setAttribute('aria-disabled', disabled.toString())
  }, [])

  const setAriaHidden = useCallback((element: HTMLElement, hidden: boolean) => {
    element.setAttribute('aria-hidden', hidden.toString())
  }, [])

  const setRole = useCallback((element: HTMLElement, role: string) => {
    element.setAttribute('role', role)
  }, [])

  return {
    setAriaLabel,
    setAriaDescribedBy,
    setAriaExpanded,
    setAriaSelected,
    setAriaChecked,
    setAriaDisabled,
    setAriaHidden,
    setRole
  }
}

// 高对比度模式检测Hook
export function useHighContrast() {
  const [isHighContrast, setIsHighContrast] = useState(false)

  useEffect(() => {
    const checkHighContrast = () => {
      // 检查Windows高对比度模式
      const mediaQuery = window.matchMedia('(prefers-contrast: high)')
      setIsHighContrast(mediaQuery.matches)
    }

    checkHighContrast()

    const mediaQuery = window.matchMedia('(prefers-contrast: high)')
    mediaQuery.addEventListener('change', checkHighContrast)

    return () => mediaQuery.removeEventListener('change', checkHighContrast)
  }, [])

  return isHighContrast
}

// 减少动画偏好检测Hook
export function useReducedMotion() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false)

  useEffect(() => {
    const checkReducedMotion = () => {
      const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
      setPrefersReducedMotion(mediaQuery.matches)
    }

    checkReducedMotion()

    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    mediaQuery.addEventListener('change', checkReducedMotion)

    return () => mediaQuery.removeEventListener('change', checkReducedMotion)
  }, [])

  return prefersReducedMotion
}

// 跳转链接Hook
export function useSkipLinks() {
  const createSkipLink = useCallback((targetId: string, text: string) => {
    const skipLink = document.createElement('a')
    skipLink.href = `#${targetId}`
    skipLink.textContent = text
    skipLink.className = 'skip-link'
    skipLink.style.cssText = `
      position: absolute;
      top: -40px;
      left: 6px;
      background: #000;
      color: #fff;
      padding: 8px;
      text-decoration: none;
      z-index: 9999;
      border-radius: 4px;
    `

    skipLink.addEventListener('focus', () => {
      skipLink.style.top = '6px'
    })

    skipLink.addEventListener('blur', () => {
      skipLink.style.top = '-40px'
    })

    return skipLink
  }, [])

  const addSkipLinks = useCallback((links: Array<{ targetId: string; text: string }>) => {
    const container = document.createElement('div')
    container.className = 'skip-links'

    links.forEach(({ targetId, text }) => {
      const skipLink = createSkipLink(targetId, text)
      container.appendChild(skipLink)
    })

    document.body.insertBefore(container, document.body.firstChild)

    return () => {
      if (container.parentNode) {
        container.parentNode.removeChild(container)
      }
    }
  }, [createSkipLink])

  return { createSkipLink, addSkipLinks }
}

// 无障碍测试Hook
export function useAccessibilityTesting() {
  const checkAccessibility = useCallback((element: HTMLElement) => {
    const issues: string[] = []

    // 检查图片alt属性
    const images = element.querySelectorAll('img')
    images.forEach((img, index) => {
      if (!img.alt && !img.getAttribute('aria-label')) {
        issues.push(`图片 ${index + 1} 缺少alt属性或aria-label`)
      }
    })

    // 检查表单标签
    const inputs = element.querySelectorAll('input, select, textarea')
    inputs.forEach((input, index) => {
      const hasLabel = input.id && element.querySelector(`label[for="${input.id}"]`)
      const hasAriaLabel = input.getAttribute('aria-label')
      const hasAriaLabelledBy = input.getAttribute('aria-labelledby')

      if (!hasLabel && !hasAriaLabel && !hasAriaLabelledBy) {
        issues.push(`表单控件 ${index + 1} 缺少标签`)
      }
    })

    // 检查按钮文本
    const buttons = element.querySelectorAll('button')
    buttons.forEach((button, index) => {
      const hasText = button.textContent?.trim()
      const hasAriaLabel = button.getAttribute('aria-label')

      if (!hasText && !hasAriaLabel) {
        issues.push(`按钮 ${index + 1} 缺少文本或aria-label`)
      }
    })

    // 检查标题层级
    const headings = element.querySelectorAll('h1, h2, h3, h4, h5, h6')
    let lastLevel = 0
    headings.forEach((heading, index) => {
      const level = parseInt(heading.tagName.charAt(1))
      if (level > lastLevel + 1) {
        issues.push(`标题 ${index + 1} 层级跳跃过大`)
      }
      lastLevel = level
    })

    return issues
  }, [])

  return { checkAccessibility }
}
