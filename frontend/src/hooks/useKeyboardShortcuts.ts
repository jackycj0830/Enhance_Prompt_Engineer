/**
 * 键盘快捷键Hook
 */

import { useEffect, useCallback, useRef } from 'react'

interface KeyboardShortcut {
  key: string
  ctrl?: boolean
  alt?: boolean
  shift?: boolean
  meta?: boolean
  callback: (event: KeyboardEvent) => void
  description?: string
  preventDefault?: boolean
  stopPropagation?: boolean
}

interface UseKeyboardShortcutsOptions {
  enabled?: boolean
  target?: HTMLElement | Document
}

export function useKeyboardShortcuts(
  shortcuts: KeyboardShortcut[],
  options: UseKeyboardShortcutsOptions = {}
) {
  const { enabled = true, target = document } = options
  const shortcutsRef = useRef<KeyboardShortcut[]>(shortcuts)
  const enabledRef = useRef(enabled)

  // 更新引用
  useEffect(() => {
    shortcutsRef.current = shortcuts
  }, [shortcuts])

  useEffect(() => {
    enabledRef.current = enabled
  }, [enabled])

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!enabledRef.current) return

    // 检查是否在输入元素中
    const activeElement = document.activeElement
    const isInputElement = activeElement && (
      activeElement.tagName === 'INPUT' ||
      activeElement.tagName === 'TEXTAREA' ||
      activeElement.tagName === 'SELECT' ||
      activeElement.getAttribute('contenteditable') === 'true'
    )

    // 在输入元素中时，只处理特定的快捷键
    if (isInputElement && !event.ctrlKey && !event.metaKey && !event.altKey) {
      return
    }

    for (const shortcut of shortcutsRef.current) {
      if (isShortcutMatch(event, shortcut)) {
        if (shortcut.preventDefault !== false) {
          event.preventDefault()
        }
        if (shortcut.stopPropagation) {
          event.stopPropagation()
        }
        shortcut.callback(event)
        break
      }
    }
  }, [])

  useEffect(() => {
    if (!enabled) return

    const targetElement = target as EventTarget
    targetElement.addEventListener('keydown', handleKeyDown)

    return () => {
      targetElement.removeEventListener('keydown', handleKeyDown)
    }
  }, [enabled, target, handleKeyDown])

  return {
    shortcuts: shortcutsRef.current,
    enabled: enabledRef.current
  }
}

function isShortcutMatch(event: KeyboardEvent, shortcut: KeyboardShortcut): boolean {
  const key = event.key.toLowerCase()
  const shortcutKey = shortcut.key.toLowerCase()

  // 检查主键
  if (key !== shortcutKey) return false

  // 检查修饰键
  if (!!shortcut.ctrl !== event.ctrlKey) return false
  if (!!shortcut.alt !== event.altKey) return false
  if (!!shortcut.shift !== event.shiftKey) return false
  if (!!shortcut.meta !== event.metaKey) return false

  return true
}

// 预定义的快捷键组合
export const commonShortcuts = {
  // 通用快捷键
  save: { key: 's', ctrl: true, description: '保存' },
  copy: { key: 'c', ctrl: true, description: '复制' },
  paste: { key: 'v', ctrl: true, description: '粘贴' },
  cut: { key: 'x', ctrl: true, description: '剪切' },
  undo: { key: 'z', ctrl: true, description: '撤销' },
  redo: { key: 'y', ctrl: true, description: '重做' },
  selectAll: { key: 'a', ctrl: true, description: '全选' },
  find: { key: 'f', ctrl: true, description: '查找' },
  
  // 导航快捷键
  escape: { key: 'Escape', description: '取消/关闭' },
  enter: { key: 'Enter', description: '确认' },
  tab: { key: 'Tab', description: '下一个' },
  shiftTab: { key: 'Tab', shift: true, description: '上一个' },
  
  // 应用特定快捷键
  newPrompt: { key: 'n', ctrl: true, description: '新建提示词' },
  newTemplate: { key: 't', ctrl: true, description: '新建模板' },
  analyze: { key: 'Enter', ctrl: true, description: '开始分析' },
  search: { key: 'k', ctrl: true, description: '搜索' },
  
  // 功能键
  help: { key: 'F1', description: '帮助' },
  refresh: { key: 'F5', description: '刷新' },
  fullscreen: { key: 'F11', description: '全屏' },
  
  // 数字键
  number1: { key: '1', ctrl: true, description: '切换到第1个标签' },
  number2: { key: '2', ctrl: true, description: '切换到第2个标签' },
  number3: { key: '3', ctrl: true, description: '切换到第3个标签' },
  number4: { key: '4', ctrl: true, description: '切换到第4个标签' },
  number5: { key: '5', ctrl: true, description: '切换到第5个标签' },
}

// 快捷键帮助Hook
export function useShortcutHelp() {
  const shortcuts = useRef<Map<string, KeyboardShortcut>>(new Map())

  const registerShortcut = useCallback((id: string, shortcut: KeyboardShortcut) => {
    shortcuts.current.set(id, shortcut)
  }, [])

  const unregisterShortcut = useCallback((id: string) => {
    shortcuts.current.delete(id)
  }, [])

  const getShortcutList = useCallback(() => {
    return Array.from(shortcuts.current.entries()).map(([id, shortcut]) => ({
      id,
      ...shortcut
    }))
  }, [])

  const formatShortcut = useCallback((shortcut: KeyboardShortcut) => {
    const parts: string[] = []
    
    if (shortcut.ctrl) parts.push('Ctrl')
    if (shortcut.alt) parts.push('Alt')
    if (shortcut.shift) parts.push('Shift')
    if (shortcut.meta) parts.push('Cmd')
    
    parts.push(shortcut.key.toUpperCase())
    
    return parts.join(' + ')
  }, [])

  return {
    registerShortcut,
    unregisterShortcut,
    getShortcutList,
    formatShortcut
  }
}

// 全局快捷键管理器
class GlobalShortcutManager {
  private shortcuts = new Map<string, KeyboardShortcut>()
  private listeners = new Set<(shortcuts: KeyboardShortcut[]) => void>()

  register(id: string, shortcut: KeyboardShortcut) {
    this.shortcuts.set(id, shortcut)
    this.notifyListeners()
  }

  unregister(id: string) {
    this.shortcuts.delete(id)
    this.notifyListeners()
  }

  getAll() {
    return Array.from(this.shortcuts.values())
  }

  subscribe(listener: (shortcuts: KeyboardShortcut[]) => void) {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  private notifyListeners() {
    const shortcuts = this.getAll()
    this.listeners.forEach(listener => listener(shortcuts))
  }
}

export const globalShortcutManager = new GlobalShortcutManager()

// 快捷键上下文Hook
export function useShortcutContext(contextShortcuts: Record<string, KeyboardShortcut>) {
  useEffect(() => {
    // 注册上下文快捷键
    Object.entries(contextShortcuts).forEach(([id, shortcut]) => {
      globalShortcutManager.register(id, shortcut)
    })

    return () => {
      // 清理上下文快捷键
      Object.keys(contextShortcuts).forEach(id => {
        globalShortcutManager.unregister(id)
      })
    }
  }, [contextShortcuts])
}

// 快捷键冲突检测
export function detectShortcutConflicts(shortcuts: KeyboardShortcut[]): string[] {
  const conflicts: string[] = []
  const shortcutMap = new Map<string, number>()

  shortcuts.forEach((shortcut, index) => {
    const key = getShortcutKey(shortcut)
    if (shortcutMap.has(key)) {
      conflicts.push(`快捷键冲突: ${formatShortcutKey(shortcut)} (索引 ${shortcutMap.get(key)} 和 ${index})`)
    } else {
      shortcutMap.set(key, index)
    }
  })

  return conflicts
}

function getShortcutKey(shortcut: KeyboardShortcut): string {
  return `${shortcut.ctrl ? 'ctrl+' : ''}${shortcut.alt ? 'alt+' : ''}${shortcut.shift ? 'shift+' : ''}${shortcut.meta ? 'meta+' : ''}${shortcut.key.toLowerCase()}`
}

function formatShortcutKey(shortcut: KeyboardShortcut): string {
  const parts: string[] = []
  if (shortcut.ctrl) parts.push('Ctrl')
  if (shortcut.alt) parts.push('Alt')
  if (shortcut.shift) parts.push('Shift')
  if (shortcut.meta) parts.push('Cmd')
  parts.push(shortcut.key.toUpperCase())
  return parts.join('+')
}
