/**
 * 前端性能优化工具
 */

// 性能监控
export class PerformanceMonitor {
  private static instance: PerformanceMonitor
  private metrics: Map<string, number[]> = new Map()
  private observers: PerformanceObserver[] = []

  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor()
    }
    return PerformanceMonitor.instance
  }

  constructor() {
    this.initObservers()
  }

  private initObservers() {
    if (typeof window === 'undefined') return

    // 监控导航性能
    if ('PerformanceObserver' in window) {
      const navObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'navigation') {
            this.recordMetric('navigation', entry.duration)
          }
        }
      })
      navObserver.observe({ entryTypes: ['navigation'] })
      this.observers.push(navObserver)

      // 监控资源加载性能
      const resourceObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'resource') {
            this.recordMetric(`resource_${entry.name}`, entry.duration)
          }
        }
      })
      resourceObserver.observe({ entryTypes: ['resource'] })
      this.observers.push(resourceObserver)

      // 监控用户交互性能
      const measureObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'measure') {
            this.recordMetric(entry.name, entry.duration)
          }
        }
      })
      measureObserver.observe({ entryTypes: ['measure'] })
      this.observers.push(measureObserver)
    }
  }

  recordMetric(name: string, value: number) {
    if (!this.metrics.has(name)) {
      this.metrics.set(name, [])
    }
    this.metrics.get(name)!.push(value)
  }

  getMetrics(name: string) {
    return this.metrics.get(name) || []
  }

  getAverageMetric(name: string): number {
    const values = this.getMetrics(name)
    return values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0
  }

  getAllMetrics() {
    const result: Record<string, { average: number; count: number; values: number[] }> = {}
    for (const [name, values] of this.metrics.entries()) {
      result[name] = {
        average: this.getAverageMetric(name),
        count: values.length,
        values: [...values]
      }
    }
    return result
  }

  clearMetrics() {
    this.metrics.clear()
  }

  destroy() {
    this.observers.forEach(observer => observer.disconnect())
    this.observers = []
    this.metrics.clear()
  }
}

// 性能测量装饰器
export function measurePerformance(name: string) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value

    descriptor.value = async function (...args: any[]) {
      const startTime = performance.now()
      
      try {
        const result = await originalMethod.apply(this, args)
        const endTime = performance.now()
        
        PerformanceMonitor.getInstance().recordMetric(
          `${name}_${propertyKey}`,
          endTime - startTime
        )
        
        return result
      } catch (error) {
        const endTime = performance.now()
        PerformanceMonitor.getInstance().recordMetric(
          `${name}_${propertyKey}_error`,
          endTime - startTime
        )
        throw error
      }
    }

    return descriptor
  }
}

// 资源预加载
export class ResourcePreloader {
  private static preloadedResources = new Set<string>()

  static preloadImage(src: string): Promise<void> {
    if (this.preloadedResources.has(src)) {
      return Promise.resolve()
    }

    return new Promise((resolve, reject) => {
      const img = new Image()
      img.onload = () => {
        this.preloadedResources.add(src)
        resolve()
      }
      img.onerror = reject
      img.src = src
    })
  }

  static preloadScript(src: string): Promise<void> {
    if (this.preloadedResources.has(src)) {
      return Promise.resolve()
    }

    return new Promise((resolve, reject) => {
      const script = document.createElement('script')
      script.onload = () => {
        this.preloadedResources.add(src)
        resolve()
      }
      script.onerror = reject
      script.src = src
      document.head.appendChild(script)
    })
  }

  static preloadCSS(href: string): Promise<void> {
    if (this.preloadedResources.has(href)) {
      return Promise.resolve()
    }

    return new Promise((resolve, reject) => {
      const link = document.createElement('link')
      link.rel = 'stylesheet'
      link.onload = () => {
        this.preloadedResources.add(href)
        resolve()
      }
      link.onerror = reject
      link.href = href
      document.head.appendChild(link)
    })
  }
}

// 防抖和节流
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number,
  immediate = false
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null

  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null
      if (!immediate) func(...args)
    }

    const callNow = immediate && !timeout

    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(later, wait)

    if (callNow) func(...args)
  }
}

export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean

  return function executedFunction(...args: Parameters<T>) {
    if (!inThrottle) {
      func.apply(this, args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

// 虚拟滚动
export class VirtualScroller {
  private container: HTMLElement
  private itemHeight: number
  private visibleCount: number
  private totalCount: number
  private scrollTop = 0
  private renderCallback: (startIndex: number, endIndex: number) => void

  constructor(
    container: HTMLElement,
    itemHeight: number,
    visibleCount: number,
    totalCount: number,
    renderCallback: (startIndex: number, endIndex: number) => void
  ) {
    this.container = container
    this.itemHeight = itemHeight
    this.visibleCount = visibleCount
    this.totalCount = totalCount
    this.renderCallback = renderCallback

    this.init()
  }

  private init() {
    this.container.style.height = `${this.visibleCount * this.itemHeight}px`
    this.container.style.overflow = 'auto'

    this.container.addEventListener('scroll', this.handleScroll.bind(this))
    this.render()
  }

  private handleScroll() {
    this.scrollTop = this.container.scrollTop
    this.render()
  }

  private render() {
    const startIndex = Math.floor(this.scrollTop / this.itemHeight)
    const endIndex = Math.min(startIndex + this.visibleCount, this.totalCount)

    this.renderCallback(startIndex, endIndex)
  }

  updateTotalCount(count: number) {
    this.totalCount = count
    this.render()
  }

  scrollToIndex(index: number) {
    this.scrollTop = index * this.itemHeight
    this.container.scrollTop = this.scrollTop
    this.render()
  }

  destroy() {
    this.container.removeEventListener('scroll', this.handleScroll.bind(this))
  }
}

// 图片懒加载
export class LazyImageLoader {
  private observer: IntersectionObserver | null = null
  private images = new Set<HTMLImageElement>()

  constructor(options: IntersectionObserverInit = {}) {
    if ('IntersectionObserver' in window) {
      this.observer = new IntersectionObserver(this.handleIntersection.bind(this), {
        rootMargin: '50px',
        threshold: 0.1,
        ...options
      })
    }
  }

  private handleIntersection(entries: IntersectionObserverEntry[]) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target as HTMLImageElement
        this.loadImage(img)
        this.observer?.unobserve(img)
        this.images.delete(img)
      }
    })
  }

  private loadImage(img: HTMLImageElement) {
    const src = img.dataset.src
    if (src) {
      img.src = src
      img.removeAttribute('data-src')
    }
  }

  observe(img: HTMLImageElement) {
    if (this.observer) {
      this.observer.observe(img)
      this.images.add(img)
    } else {
      // 降级处理
      this.loadImage(img)
    }
  }

  unobserve(img: HTMLImageElement) {
    if (this.observer) {
      this.observer.unobserve(img)
      this.images.delete(img)
    }
  }

  destroy() {
    if (this.observer) {
      this.observer.disconnect()
      this.images.clear()
    }
  }
}

// Web Workers 工具
export class WebWorkerManager {
  private workers = new Map<string, Worker>()

  createWorker(name: string, script: string): Worker {
    if (this.workers.has(name)) {
      return this.workers.get(name)!
    }

    const blob = new Blob([script], { type: 'application/javascript' })
    const worker = new Worker(URL.createObjectURL(blob))
    
    this.workers.set(name, worker)
    return worker
  }

  getWorker(name: string): Worker | undefined {
    return this.workers.get(name)
  }

  terminateWorker(name: string) {
    const worker = this.workers.get(name)
    if (worker) {
      worker.terminate()
      this.workers.delete(name)
    }
  }

  terminateAll() {
    this.workers.forEach(worker => worker.terminate())
    this.workers.clear()
  }
}

// 内存管理
export class MemoryManager {
  private static cache = new Map<string, any>()
  private static maxCacheSize = 100

  static set(key: string, value: any) {
    if (this.cache.size >= this.maxCacheSize) {
      const firstKey = this.cache.keys().next().value
      this.cache.delete(firstKey)
    }
    this.cache.set(key, value)
  }

  static get(key: string) {
    return this.cache.get(key)
  }

  static has(key: string): boolean {
    return this.cache.has(key)
  }

  static delete(key: string) {
    return this.cache.delete(key)
  }

  static clear() {
    this.cache.clear()
  }

  static getSize(): number {
    return this.cache.size
  }

  static setMaxSize(size: number) {
    this.maxCacheSize = size
    while (this.cache.size > size) {
      const firstKey = this.cache.keys().next().value
      this.cache.delete(firstKey)
    }
  }
}

// 导出单例实例
export const performanceMonitor = PerformanceMonitor.getInstance()
export const webWorkerManager = new WebWorkerManager()
