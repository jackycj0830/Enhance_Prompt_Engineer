// Service Worker for PWA functionality

const CACHE_NAME = 'ai-prompt-engineer-v1.0.0'
const STATIC_CACHE = 'static-v1.0.0'
const DYNAMIC_CACHE = 'dynamic-v1.0.0'

// 需要缓存的静态资源
const STATIC_ASSETS = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png'
]

// 需要缓存的API路径
const API_CACHE_PATTERNS = [
  /^\/api\/v1\/templates/,
  /^\/api\/v1\/prompts/,
  /^\/api\/v1\/analysis/
]

// 安装事件 - 缓存静态资源
self.addEventListener('install', event => {
  console.log('Service Worker: Installing...')
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('Service Worker: Caching static assets')
        return cache.addAll(STATIC_ASSETS)
      })
      .then(() => {
        console.log('Service Worker: Static assets cached')
        return self.skipWaiting()
      })
      .catch(error => {
        console.error('Service Worker: Failed to cache static assets', error)
      })
  )
})

// 激活事件 - 清理旧缓存
self.addEventListener('activate', event => {
  console.log('Service Worker: Activating...')
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              console.log('Service Worker: Deleting old cache', cacheName)
              return caches.delete(cacheName)
            }
          })
        )
      })
      .then(() => {
        console.log('Service Worker: Activated')
        return self.clients.claim()
      })
  )
})

// 获取事件 - 处理网络请求
self.addEventListener('fetch', event => {
  const { request } = event
  const url = new URL(request.url)
  
  // 只处理同源请求
  if (url.origin !== location.origin) {
    return
  }
  
  // 处理导航请求
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .catch(() => {
          return caches.match('/')
        })
    )
    return
  }
  
  // 处理静态资源请求
  if (request.destination === 'script' || 
      request.destination === 'style' || 
      request.destination === 'image' ||
      request.destination === 'font') {
    event.respondWith(
      caches.match(request)
        .then(response => {
          if (response) {
            return response
          }
          
          return fetch(request)
            .then(fetchResponse => {
              const responseClone = fetchResponse.clone()
              caches.open(STATIC_CACHE)
                .then(cache => {
                  cache.put(request, responseClone)
                })
              return fetchResponse
            })
        })
    )
    return
  }
  
  // 处理API请求
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      handleApiRequest(request)
    )
    return
  }
  
  // 其他请求使用网络优先策略
  event.respondWith(
    fetch(request)
      .catch(() => {
        return caches.match(request)
      })
  )
})

// 处理API请求
async function handleApiRequest(request) {
  const url = new URL(request.url)
  
  // 对于GET请求，使用缓存优先策略
  if (request.method === 'GET') {
    // 检查是否是可缓存的API
    const isCacheable = API_CACHE_PATTERNS.some(pattern => 
      pattern.test(url.pathname)
    )
    
    if (isCacheable) {
      try {
        const cache = await caches.open(DYNAMIC_CACHE)
        const cachedResponse = await cache.match(request)
        
        // 如果有缓存且网络不可用，返回缓存
        if (cachedResponse && !navigator.onLine) {
          return cachedResponse
        }
        
        // 尝试从网络获取
        const networkResponse = await fetch(request)
        
        if (networkResponse.ok) {
          // 缓存成功的响应
          const responseClone = networkResponse.clone()
          cache.put(request, responseClone)
        }
        
        return networkResponse
      } catch (error) {
        // 网络失败，返回缓存
        const cache = await caches.open(DYNAMIC_CACHE)
        const cachedResponse = await cache.match(request)
        
        if (cachedResponse) {
          return cachedResponse
        }
        
        // 返回离线页面或错误响应
        return new Response(
          JSON.stringify({ 
            error: '网络连接失败，请检查网络设置',
            offline: true 
          }),
          {
            status: 503,
            statusText: 'Service Unavailable',
            headers: { 'Content-Type': 'application/json' }
          }
        )
      }
    }
  }
  
  // 对于POST/PUT/DELETE等请求，直接使用网络
  try {
    return await fetch(request)
  } catch (error) {
    return new Response(
      JSON.stringify({ 
        error: '网络连接失败，请检查网络设置',
        offline: true 
      }),
      {
        status: 503,
        statusText: 'Service Unavailable',
        headers: { 'Content-Type': 'application/json' }
      }
    )
  }
}

// 后台同步事件
self.addEventListener('sync', event => {
  console.log('Service Worker: Background sync', event.tag)
  
  if (event.tag === 'background-sync') {
    event.waitUntil(
      handleBackgroundSync()
    )
  }
})

// 处理后台同步
async function handleBackgroundSync() {
  try {
    // 这里可以处理离线时的数据同步
    console.log('Service Worker: Performing background sync')
    
    // 示例：同步离线时保存的数据
    const offlineData = await getOfflineData()
    if (offlineData.length > 0) {
      for (const data of offlineData) {
        try {
          await syncDataToServer(data)
          await removeOfflineData(data.id)
        } catch (error) {
          console.error('Service Worker: Failed to sync data', error)
        }
      }
    }
  } catch (error) {
    console.error('Service Worker: Background sync failed', error)
  }
}

// 推送通知事件
self.addEventListener('push', event => {
  console.log('Service Worker: Push received', event)
  
  const options = {
    body: event.data ? event.data.text() : '您有新的消息',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: '查看详情',
        icon: '/icons/checkmark.png'
      },
      {
        action: 'close',
        title: '关闭',
        icon: '/icons/xmark.png'
      }
    ]
  }
  
  event.waitUntil(
    self.registration.showNotification('AI提示词工程师', options)
  )
})

// 通知点击事件
self.addEventListener('notificationclick', event => {
  console.log('Service Worker: Notification clicked', event)
  
  event.notification.close()
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    )
  }
})

// 消息事件 - 与主线程通信
self.addEventListener('message', event => {
  console.log('Service Worker: Message received', event.data)
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting()
  }
  
  if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: CACHE_NAME })
  }
})

// 辅助函数
async function getOfflineData() {
  // 从IndexedDB或其他存储获取离线数据
  return []
}

async function syncDataToServer(data) {
  // 将数据同步到服务器
  return fetch('/api/v1/sync', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  })
}

async function removeOfflineData(id) {
  // 从离线存储中删除已同步的数据
  console.log('Removing offline data:', id)
}
