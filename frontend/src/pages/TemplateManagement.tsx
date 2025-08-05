/**
 * 模板管理页面
 */

import React, { useState, useEffect } from 'react'
import {
  Layout,
  Card,
  Button,
  Space,
  Typography,
  Tabs,
  Modal,
  Form,
  Input,
  Select,
  Tag,
  message,
  Row,
  Col,
  Statistic,
  Empty
} from 'antd'
import {
  PlusOutlined,
  AppstoreOutlined,
  HeartOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  EditOutlined
} from '@ant-design/icons'
import TemplateLibrary from '../components/TemplateLibrary'
import { templateApi } from '../services/api'
import { useAuthStore } from '../stores/authStore'

const { Content } = Layout
const { Title, Text } = Typography
const { TabPane } = Tabs
const { TextArea } = Input
const { Option } = Select

interface TemplateFormData {
  name: string
  description: string
  content: string
  category: string
  tags: string[]
  industry: string
  use_case: string
  difficulty_level: string
  is_public: boolean
}

const TemplateManagement: React.FC = () => {
  const { user } = useAuthStore()
  const [activeTab, setActiveTab] = useState('library')
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()
  
  // 统计数据
  const [stats, setStats] = useState({
    total: 0,
    myTemplates: 0,
    collections: 0,
    totalUsage: 0
  })
  
  // 推荐模板
  const [featuredTemplates, setFeaturedTemplates] = useState([])
  const [popularTemplates, setPopularTemplates] = useState([])
  const [recentTemplates, setRecentTemplates] = useState([])

  // 加载统计数据
  const loadStats = async () => {
    try {
      // 这里可以调用统计API，暂时使用模拟数据
      setStats({
        total: 1250,
        myTemplates: 8,
        collections: 15,
        totalUsage: 342
      })
    } catch (error) {
      console.error('加载统计数据失败:', error)
    }
  }

  // 加载推荐模板
  const loadRecommendedTemplates = async () => {
    try {
      const [featured, popular, recent] = await Promise.all([
        templateApi.getFeaturedTemplates({ limit: 6 }),
        templateApi.getPopularTemplates({ limit: 6 }),
        templateApi.getRecentTemplates({ limit: 6 })
      ])
      
      setFeaturedTemplates(featured.templates)
      setPopularTemplates(popular.templates)
      setRecentTemplates(recent.templates)
    } catch (error) {
      console.error('加载推荐模板失败:', error)
    }
  }

  useEffect(() => {
    loadStats()
    loadRecommendedTemplates()
  }, [])

  // 创建模板
  const handleCreateTemplate = async (values: TemplateFormData) => {
    setLoading(true)
    try {
      await templateApi.createTemplate(values)
      message.success('模板创建成功')
      setCreateModalVisible(false)
      form.resetFields()
      loadStats() // 刷新统计数据
    } catch (error) {
      console.error('创建模板失败:', error)
      message.error('创建模板失败')
    } finally {
      setLoading(false)
    }
  }

  // 使用模板
  const handleUseTemplate = (template: any) => {
    // 这里可以跳转到提示词编辑器并填入模板内容
    message.success(`已使用模板: ${template.name}`)
  }

  // 渲染推荐模板卡片
  const renderTemplateCard = (template: any) => (
    <Card
      key={template.id}
      size="small"
      hoverable
      style={{ marginBottom: 12 }}
      actions={[
        <Button
          type="link"
          size="small"
          onClick={() => handleUseTemplate(template)}
        >
          使用
        </Button>
      ]}
    >
      <Card.Meta
        title={
          <Text ellipsis style={{ fontSize: 14 }}>
            {template.name}
          </Text>
        }
        description={
          <Text type="secondary" ellipsis style={{ fontSize: 12 }}>
            {template.description}
          </Text>
        }
      />
      <div style={{ marginTop: 8 }}>
        <Space>
          <Text type="secondary" style={{ fontSize: 12 }}>
            ⭐ {template.rating}
          </Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {template.usage_count} 次使用
          </Text>
        </Space>
      </div>
    </Card>
  )

  return (
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 1400, margin: '0 auto' }}>
          {/* 页面标题 */}
          <div style={{ marginBottom: 24 }}>
            <Title level={2}>
              <AppstoreOutlined style={{ marginRight: 8, color: '#1890ff' }} />
              模板库
            </Title>
            <Text type="secondary">
              发现、使用和管理AI提示词模板，提升工作效率
            </Text>
          </div>

          {/* 统计卡片 */}
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="模板总数"
                  value={stats.total}
                  prefix={<AppstoreOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="我的模板"
                  value={stats.myTemplates}
                  prefix={<EditOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="收藏模板"
                  value={stats.collections}
                  prefix={<HeartOutlined />}
                  valueStyle={{ color: '#faad14' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="总使用次数"
                  value={stats.totalUsage}
                  prefix={<TrophyOutlined />}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
          </Row>

          {/* 主要内容 */}
          <Row gutter={24}>
            <Col span={18}>
              <Card>
                <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Tabs activeKey={activeTab} onChange={setActiveTab}>
                    <TabPane tab="模板库" key="library" />
                    <TabPane tab="我的模板" key="my-templates" />
                    <TabPane tab="收藏夹" key="favorites" />
                  </Tabs>
                  
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => setCreateModalVisible(true)}
                  >
                    创建模板
                  </Button>
                </div>

                {activeTab === 'library' && (
                  <TemplateLibrary
                    onUseTemplate={handleUseTemplate}
                    embedded={true}
                  />
                )}

                {activeTab === 'my-templates' && (
                  <TemplateLibrary
                    onUseTemplate={handleUseTemplate}
                    embedded={true}
                    // 这里可以传入creator_id参数来只显示用户自己的模板
                  />
                )}

                {activeTab === 'favorites' && (
                  <Empty
                    description="收藏夹功能开发中..."
                    style={{ margin: '40px 0' }}
                  />
                )}
              </Card>
            </Col>

            <Col span={6}>
              {/* 推荐模板侧边栏 */}
              <Space direction="vertical" style={{ width: '100%' }}>
                {/* 精选模板 */}
                <Card
                  title={
                    <Space>
                      <TrophyOutlined style={{ color: '#faad14' }} />
                      <span>精选模板</span>
                    </Space>
                  }
                  size="small"
                >
                  {featuredTemplates.length > 0 ? (
                    featuredTemplates.map(renderTemplateCard)
                  ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无精选模板" />
                  )}
                </Card>

                {/* 热门模板 */}
                <Card
                  title={
                    <Space>
                      <HeartOutlined style={{ color: '#ff4d4f' }} />
                      <span>热门模板</span>
                    </Space>
                  }
                  size="small"
                >
                  {popularTemplates.length > 0 ? (
                    popularTemplates.map(renderTemplateCard)
                  ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无热门模板" />
                  )}
                </Card>

                {/* 最新模板 */}
                <Card
                  title={
                    <Space>
                      <ClockCircleOutlined style={{ color: '#1890ff' }} />
                      <span>最新模板</span>
                    </Space>
                  }
                  size="small"
                >
                  {recentTemplates.length > 0 ? (
                    recentTemplates.map(renderTemplateCard)
                  ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无最新模板" />
                  )}
                </Card>
              </Space>
            </Col>
          </Row>
        </div>
      </Content>

      {/* 创建模板模态框 */}
      <Modal
        title="创建新模板"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        onOk={() => form.submit()}
        confirmLoading={loading}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateTemplate}
        >
          <Form.Item
            name="name"
            label="模板名称"
            rules={[{ required: true, message: '请输入模板名称' }]}
          >
            <Input placeholder="请输入模板名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="模板描述"
            rules={[{ required: true, message: '请输入模板描述' }]}
          >
            <TextArea rows={3} placeholder="请描述模板的用途和特点" />
          </Form.Item>

          <Form.Item
            name="content"
            label="模板内容"
            rules={[{ required: true, message: '请输入模板内容' }]}
          >
            <TextArea rows={6} placeholder="请输入提示词模板内容" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="category"
                label="分类"
              >
                <Select placeholder="选择分类">
                  <Option value="创作">创作</Option>
                  <Option value="编程">编程</Option>
                  <Option value="分析">分析</Option>
                  <Option value="翻译">翻译</Option>
                  <Option value="总结">总结</Option>
                  <Option value="其他">其他</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="difficulty_level"
                label="难度级别"
                initialValue="beginner"
              >
                <Select>
                  <Option value="beginner">初级</Option>
                  <Option value="intermediate">中级</Option>
                  <Option value="advanced">高级</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="industry"
                label="行业"
              >
                <Select placeholder="选择行业">
                  <Option value="科技">科技</Option>
                  <Option value="教育">教育</Option>
                  <Option value="医疗">医疗</Option>
                  <Option value="金融">金融</Option>
                  <Option value="电商">电商</Option>
                  <Option value="其他">其他</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="use_case"
                label="使用场景"
              >
                <Input placeholder="如：客服对话、内容创作等" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="tags"
            label="标签"
          >
            <Select
              mode="tags"
              placeholder="添加标签"
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Form.Item
            name="is_public"
            label="公开设置"
            initialValue={true}
          >
            <Select>
              <Option value={true}>公开 - 所有用户可见</Option>
              <Option value={false}>私有 - 仅自己可见</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </Layout>
  )
}

export default TemplateManagement
