/**
 * PWA安装提示组件
 */

import React, { useState, useEffect } from 'react'
import {
  Modal,
  Button,
  Space,
  Typography,
  Card,
  Row,
  Col,
  Steps,
  Alert,
  Divider
} from 'antd'
import {
  DownloadOutlined,
  MobileOutlined,
  DesktopOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
  CloseOutlined
} from '@ant-design/icons'
import './PWAInstall.css'

const { Title, Text, Paragraph } = Typography
const { Step } = Steps

interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[]
  readonly userChoice: Promise<{
    outcome: 'accepted' | 'dismissed'
    platform: string
  }>
  prompt(): Promise<void>
}

const PWAInstall: React.FC = () => {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [showInstallModal, setShowInstallModal] = useState(false)
  const [isInstalled, setIsInstalled] = useState(false)
  const [isIOS, setIsIOS] = useState(false)
  const [isStandalone, setIsStandalone] = useState(false)
  const [installStep, setInstallStep] = useState(0)

  useEffect(() => {
    // 检测设备类型
    const userAgent = window.navigator.userAgent.toLowerCase()
    const isIOSDevice = /iphone|ipad|ipod/.test(userAgent)
    setIsIOS(isIOSDevice)

    // 检测是否已安装
    const isStandaloneMode = window.matchMedia('(display-mode: standalone)').matches ||
                            (window.navigator as any).standalone ||
                            document.referrer.includes('android-app://')
    setIsStandalone(isStandaloneMode)
    setIsInstalled(isStandaloneMode)

    // 监听安装提示事件
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e as BeforeInstallPromptEvent)
      
      // 延迟显示安装提示
      setTimeout(() => {
        if (!isStandaloneMode && !localStorage.getItem('pwa-install-dismissed')) {
          setShowInstallModal(true)
        }
      }, 3000)
    }

    // 监听应用安装事件
    const handleAppInstalled = () => {
      console.log('PWA was installed')
      setIsInstalled(true)
      setShowInstallModal(false)
      setDeferredPrompt(null)
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
    window.addEventListener('appinstalled', handleAppInstalled)

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
      window.removeEventListener('appinstalled', handleAppInstalled)
    }
  }, [])

  // 处理安装
  const handleInstall = async () => {
    if (!deferredPrompt) {
      if (isIOS) {
        setInstallStep(1)
      }
      return
    }

    try {
      await deferredPrompt.prompt()
      const { outcome } = await deferredPrompt.userChoice
      
      if (outcome === 'accepted') {
        console.log('User accepted the install prompt')
      } else {
        console.log('User dismissed the install prompt')
      }
      
      setDeferredPrompt(null)
    } catch (error) {
      console.error('Error during installation:', error)
    }
  }

  // 关闭安装提示
  const handleDismiss = () => {
    setShowInstallModal(false)
    localStorage.setItem('pwa-install-dismissed', 'true')
  }

  // 渲染iOS安装步骤
  const renderIOSSteps = () => (
    <div className="ios-install-steps">
      <Steps direction="vertical" current={installStep}>
        <Step
          title="点击分享按钮"
          description="在Safari浏览器底部找到分享按钮"
          icon={<InfoCircleOutlined />}
        />
        <Step
          title="添加到主屏幕"
          description="在分享菜单中选择"添加到主屏幕""
          icon={<MobileOutlined />}
        />
        <Step
          title="确认添加"
          description="点击"添加"按钮完成安装"
          icon={<CheckCircleOutlined />}
        />
      </Steps>
      
      <div className="ios-install-demo">
        <img 
          src="/images/ios-install-demo.png" 
          alt="iOS安装演示" 
          style={{ width: '100%', maxWidth: 300, margin: '16px auto', display: 'block' }}
        />
      </div>
    </div>
  )

  // 渲染Android安装步骤
  const renderAndroidSteps = () => (
    <div className="android-install-steps">
      <Alert
        message="一键安装应用"
        description="点击下方安装按钮，将应用添加到您的设备主屏幕"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />
      
      <div className="install-benefits">
        <Title level={5}>安装后您将享受：</Title>
        <ul>
          <li>🚀 更快的启动速度</li>
          <li>📱 原生应用体验</li>
          <li>🔄 离线功能支持</li>
          <li>🔔 消息推送通知</li>
          <li>💾 本地数据缓存</li>
        </ul>
      </div>
    </div>
  )

  // 如果已安装，不显示组件
  if (isInstalled) {
    return null
  }

  return (
    <>
      {/* 浮动安装按钮 */}
      {deferredPrompt && !showInstallModal && (
        <div className="pwa-install-fab">
          <Button
            type="primary"
            shape="round"
            icon={<DownloadOutlined />}
            onClick={() => setShowInstallModal(true)}
            size="large"
          >
            安装应用
          </Button>
        </div>
      )}

      {/* 安装模态框 */}
      <Modal
        title={
          <Space>
            <MobileOutlined />
            <span>安装 AI提示词工程师</span>
          </Space>
        }
        open={showInstallModal}
        onCancel={handleDismiss}
        footer={null}
        width={500}
        className="pwa-install-modal"
        closeIcon={<CloseOutlined />}
      >
        <div className="pwa-install-content">
          {/* 应用信息 */}
          <Card className="app-info-card">
            <Row gutter={16} align="middle">
              <Col span={6}>
                <div className="app-icon">
                  <img 
                    src="/icons/icon-192x192.png" 
                    alt="应用图标" 
                    width={64} 
                    height={64}
                  />
                </div>
              </Col>
              <Col span={18}>
                <Title level={4} style={{ margin: 0 }}>
                  AI提示词工程师
                </Title>
                <Text type="secondary">
                  专业的AI提示词优化和分析工具
                </Text>
                <div style={{ marginTop: 8 }}>
                  <Space>
                    <Text strong>版本:</Text>
                    <Text>1.0.0</Text>
                    <Text strong>大小:</Text>
                    <Text>~2MB</Text>
                  </Space>
                </div>
              </Col>
            </Row>
          </Card>

          <Divider />

          {/* 安装步骤 */}
          {isIOS ? renderIOSSteps() : renderAndroidSteps()}

          <Divider />

          {/* 操作按钮 */}
          <div className="install-actions">
            <Row gutter={16}>
              <Col span={12}>
                <Button 
                  block 
                  onClick={handleDismiss}
                  style={{ height: 44 }}
                >
                  稍后安装
                </Button>
              </Col>
              <Col span={12}>
                <Button
                  type="primary"
                  block
                  icon={<DownloadOutlined />}
                  onClick={handleInstall}
                  style={{ height: 44 }}
                  disabled={isIOS && installStep === 0}
                >
                  {isIOS ? '开始安装' : '立即安装'}
                </Button>
              </Col>
            </Row>
          </div>

          {/* 隐私说明 */}
          <div className="privacy-notice">
            <Text type="secondary" style={{ fontSize: 12 }}>
              安装此应用不会收集您的个人信息，所有数据均存储在本地设备上。
            </Text>
          </div>
        </div>
      </Modal>
    </>
  )
}

export default PWAInstall
