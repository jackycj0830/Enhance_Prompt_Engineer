/**
 * 触摸手势Hook
 */

import { useRef, useEffect, useCallback } from 'react'

interface TouchPoint {
  x: number
  y: number
  timestamp: number
}

interface SwipeGesture {
  direction: 'left' | 'right' | 'up' | 'down'
  distance: number
  duration: number
  velocity: number
}

interface PinchGesture {
  scale: number
  center: { x: number; y: number }
}

interface TouchGestureOptions {
  onSwipe?: (gesture: SwipeGesture) => void
  onPinch?: (gesture: PinchGesture) => void
  onTap?: (point: TouchPoint) => void
  onDoubleTap?: (point: TouchPoint) => void
  onLongPress?: (point: TouchPoint) => void
  swipeThreshold?: number
  longPressDelay?: number
  doubleTapDelay?: number
}

export const useTouchGestures = (
  elementRef: React.RefObject<HTMLElement>,
  options: TouchGestureOptions = {}
) => {
  const {
    onSwipe,
    onPinch,
    onTap,
    onDoubleTap,
    onLongPress,
    swipeThreshold = 50,
    longPressDelay = 500,
    doubleTapDelay = 300
  } = options

  const touchStartRef = useRef<TouchPoint | null>(null)
  const touchEndRef = useRef<TouchPoint | null>(null)
  const lastTapRef = useRef<TouchPoint | null>(null)
  const longPressTimerRef = useRef<NodeJS.Timeout | null>(null)
  const initialDistanceRef = useRef<number>(0)
  const initialCenterRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 })

  // 获取触摸点坐标
  const getTouchPoint = useCallback((touch: Touch): TouchPoint => ({
    x: touch.clientX,
    y: touch.clientY,
    timestamp: Date.now()
  }), [])

  // 计算两点距离
  const getDistance = useCallback((point1: TouchPoint, point2: TouchPoint): number => {
    const dx = point2.x - point1.x
    const dy = point2.y - point1.y
    return Math.sqrt(dx * dx + dy * dy)
  }, [])

  // 计算两个触摸点之间的距离
  const getTouchDistance = useCallback((touch1: Touch, touch2: Touch): number => {
    const dx = touch2.clientX - touch1.clientX
    const dy = touch2.clientY - touch1.clientY
    return Math.sqrt(dx * dx + dy * dy)
  }, [])

  // 计算两个触摸点的中心点
  const getTouchCenter = useCallback((touch1: Touch, touch2: Touch) => ({
    x: (touch1.clientX + touch2.clientX) / 2,
    y: (touch1.clientY + touch2.clientY) / 2
  }), [])

  // 判断滑动方向
  const getSwipeDirection = useCallback((start: TouchPoint, end: TouchPoint): 'left' | 'right' | 'up' | 'down' => {
    const dx = end.x - start.x
    const dy = end.y - start.y
    
    if (Math.abs(dx) > Math.abs(dy)) {
      return dx > 0 ? 'right' : 'left'
    } else {
      return dy > 0 ? 'down' : 'up'
    }
  }, [])

  // 处理触摸开始
  const handleTouchStart = useCallback((event: TouchEvent) => {
    const touches = event.touches
    
    if (touches.length === 1) {
      // 单点触摸
      const touchPoint = getTouchPoint(touches[0])
      touchStartRef.current = touchPoint
      
      // 设置长按定时器
      if (onLongPress) {
        longPressTimerRef.current = setTimeout(() => {
          onLongPress(touchPoint)
        }, longPressDelay)
      }
    } else if (touches.length === 2) {
      // 双点触摸（缩放手势）
      if (longPressTimerRef.current) {
        clearTimeout(longPressTimerRef.current)
        longPressTimerRef.current = null
      }
      
      initialDistanceRef.current = getTouchDistance(touches[0], touches[1])
      initialCenterRef.current = getTouchCenter(touches[0], touches[1])
    }
  }, [getTouchPoint, onLongPress, longPressDelay, getTouchDistance, getTouchCenter])

  // 处理触摸移动
  const handleTouchMove = useCallback((event: TouchEvent) => {
    const touches = event.touches
    
    if (touches.length === 1) {
      // 单点移动，清除长按定时器
      if (longPressTimerRef.current) {
        clearTimeout(longPressTimerRef.current)
        longPressTimerRef.current = null
      }
    } else if (touches.length === 2 && onPinch) {
      // 双点移动（缩放手势）
      const currentDistance = getTouchDistance(touches[0], touches[1])
      const currentCenter = getTouchCenter(touches[0], touches[1])
      
      if (initialDistanceRef.current > 0) {
        const scale = currentDistance / initialDistanceRef.current
        onPinch({
          scale,
          center: currentCenter
        })
      }
    }
  }, [onPinch, getTouchDistance, getTouchCenter])

  // 处理触摸结束
  const handleTouchEnd = useCallback((event: TouchEvent) => {
    // 清除长按定时器
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current)
      longPressTimerRef.current = null
    }

    const changedTouches = event.changedTouches
    if (changedTouches.length === 1 && touchStartRef.current) {
      const touchEnd = getTouchPoint(changedTouches[0])
      touchEndRef.current = touchEnd
      
      const distance = getDistance(touchStartRef.current, touchEnd)
      const duration = touchEnd.timestamp - touchStartRef.current.timestamp
      
      if (distance < swipeThreshold) {
        // 点击事件
        const now = Date.now()
        
        if (lastTapRef.current && 
            now - lastTapRef.current.timestamp < doubleTapDelay &&
            getDistance(lastTapRef.current, touchEnd) < 50) {
          // 双击
          if (onDoubleTap) {
            onDoubleTap(touchEnd)
          }
          lastTapRef.current = null
        } else {
          // 单击
          if (onTap) {
            onTap(touchEnd)
          }
          lastTapRef.current = touchEnd
        }
      } else if (onSwipe && duration < 1000) {
        // 滑动事件
        const direction = getSwipeDirection(touchStartRef.current, touchEnd)
        const velocity = distance / duration
        
        onSwipe({
          direction,
          distance,
          duration,
          velocity
        })
      }
    }

    // 重置状态
    touchStartRef.current = null
    touchEndRef.current = null
    initialDistanceRef.current = 0
  }, [
    getTouchPoint,
    getDistance,
    swipeThreshold,
    doubleTapDelay,
    onDoubleTap,
    onTap,
    onSwipe,
    getSwipeDirection
  ])

  // 绑定事件监听器
  useEffect(() => {
    const element = elementRef.current
    if (!element) return

    // 阻止默认的触摸行为
    const preventDefault = (e: TouchEvent) => {
      if (e.touches.length > 1) {
        e.preventDefault()
      }
    }

    element.addEventListener('touchstart', handleTouchStart, { passive: false })
    element.addEventListener('touchmove', handleTouchMove, { passive: false })
    element.addEventListener('touchend', handleTouchEnd, { passive: false })
    element.addEventListener('touchstart', preventDefault, { passive: false })

    return () => {
      element.removeEventListener('touchstart', handleTouchStart)
      element.removeEventListener('touchmove', handleTouchMove)
      element.removeEventListener('touchend', handleTouchEnd)
      element.removeEventListener('touchstart', preventDefault)
      
      if (longPressTimerRef.current) {
        clearTimeout(longPressTimerRef.current)
      }
    }
  }, [elementRef, handleTouchStart, handleTouchMove, handleTouchEnd])

  return {
    touchStart: touchStartRef.current,
    touchEnd: touchEndRef.current
  }
}

// 移动端检测Hook
export const useIsMobile = () => {
  const checkIsMobile = useCallback(() => {
    return window.innerWidth <= 768 || 
           /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
  }, [])

  const [isMobile, setIsMobile] = React.useState(checkIsMobile)

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(checkIsMobile())
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [checkIsMobile])

  return isMobile
}

// 设备方向Hook
export const useDeviceOrientation = () => {
  const [orientation, setOrientation] = React.useState<'portrait' | 'landscape'>('portrait')

  useEffect(() => {
    const handleOrientationChange = () => {
      setOrientation(window.innerHeight > window.innerWidth ? 'portrait' : 'landscape')
    }

    handleOrientationChange()
    window.addEventListener('resize', handleOrientationChange)
    window.addEventListener('orientationchange', handleOrientationChange)

    return () => {
      window.removeEventListener('resize', handleOrientationChange)
      window.removeEventListener('orientationchange', handleOrientationChange)
    }
  }, [])

  return orientation
}

export default useTouchGestures
