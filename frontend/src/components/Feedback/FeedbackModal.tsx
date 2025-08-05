/**
 * 用户反馈模态框组件
 */

import React, { useState } from 'react'
import {
  Modal,
  Form,
  Input,
  Select,
  Rate,
  Upload,
  Button,
  message,
  Space,
  Typography,
  Divider,
  Row,
  Col,
  Card
} from 'antd'
import {
  BugOutlined,
  BulbOutlined,
  HeartOutlined,
  QuestionCircleOutlined,
  UploadOutlined,
  StarOutlined
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'

const { TextArea } = Input
const { Option } = Select
const { Title, Text } = Typography

interface FeedbackModalProps {
  visible: boolean
  onCancel: () => void
  onSubmit: (feedback: FeedbackData) => Promise<void>
}

interface FeedbackData {
  type: 'bug' | 'feature' | 'general' | 'question'
  title: string
  description: string
  rating?: number
  email?: string
  attachments?: File[]
  metadata?: {
    url: string
    userAgent: string
    timestamp: string
    userId?: string
  }
}

const FeedbackModal: React.FC<FeedbackModalProps> = ({
  visible,
  onCancel,
  onSubmit
}) => {
  const { t } = useTranslation()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [feedbackType, setFeedbackType] = useState<string>('general')

  const feedbackTypes = [
    {
      key: 'bug',
      label: '错误报告',
      icon: <BugOutlined />,
      color: '#ff4d4f',
      description: '报告系统错误或异常行为'
    },
    {
      key: 'feature',
      label: '功能建议',
      icon: <BulbOutlined />,
      color: '#1890ff',
      description: '建议新功能或改进现有功能'
    },
    {
      key: 'general',
      label: '一般反馈',
      icon: <HeartOutlined />,
      color: '#52c41a',
      description: '分享您的使用体验和想法'
    },
    {
      key: 'question',
      label: '问题咨询',
      icon: <QuestionCircleOutlined />,
      color: '#faad14',
      description: '询问使用方法或寻求帮助'
    }
  ]

  const handleSubmit = async (values: any) => {
    setLoading(true)
    
    try {
      const feedbackData: FeedbackData = {
        type: values.type,
        title: values.title,
        description: values.description,
        rating: values.rating,
        email: values.email,
        attachments: values.attachments?.fileList?.map((file: any) => file.originFileObj),
        metadata: {
          url: window.location.href,
          userAgent: navigator.userAgent,
          timestamp: new Date().toISOString(),
          userId: localStorage.getItem('userId') || undefined
        }
      }

      await onSubmit(feedbackData)
      
      message.success('反馈提交成功，感谢您的宝贵意见！')
      form.resetFields()
      onCancel()
    } catch (error) {
      message.error('反馈提交失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  const handleTypeSelect = (type: string) => {
    setFeedbackType(type)
    form.setFieldsValue({ type })
  }

  const uploadProps = {
    beforeUpload: (file: File) => {
      const isValidType = ['image/jpeg', 'image/png', 'image/gif', 'text/plain', 'application/pdf'].includes(file.type)
      if (!isValidType) {
        message.error('只支持上传图片、文本或PDF文件')
        return false
      }
      
      const isLt5M = file.size / 1024 / 1024 < 5
      if (!isLt5M) {
        message.error('文件大小不能超过5MB')
        return false
      }
      
      return false // 阻止自动上传
    },
    multiple: true,
    maxCount: 3
  }

  return (
    <Modal
      title={
        <Space>
          <HeartOutlined style={{ color: '#1890ff' }} />
          <span>用户反馈</span>
        </Space>
      }
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={800}
      destroyOnClose
    >
      <div style={{ marginBottom: 24 }}>
        <Text type="secondary">
          您的反馈对我们非常重要，帮助我们不断改进产品体验。
        </Text>
      </div>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{ type: 'general' }}
      >
        {/* 反馈类型选择 */}
        <Form.Item
          label="反馈类型"
          name="type"
          rules={[{ required: true, message: '请选择反馈类型' }]}
        >
          <div>
            <Row gutter={[16, 16]}>
              {feedbackTypes.map(type => (
                <Col span={12} key={type.key}>
                  <Card
                    hoverable
                    size="small"
                    style={{
                      borderColor: feedbackType === type.key ? type.color : undefined,
                      backgroundColor: feedbackType === type.key ? `${type.color}10` : undefined
                    }}
                    onClick={() => handleTypeSelect(type.key)}
                  >
                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                      <Space>
                        <span style={{ color: type.color, fontSize: 18 }}>
                          {type.icon}
                        </span>
                        <Text strong>{type.label}</Text>
                      </Space>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {type.description}
                      </Text>
                    </Space>
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        </Form.Item>

        {/* 标题 */}
        <Form.Item
          label="标题"
          name="title"
          rules={[
            { required: true, message: '请输入反馈标题' },
            { max: 100, message: '标题长度不能超过100字符' }
          ]}
        >
          <Input placeholder="简要描述您的反馈内容" />
        </Form.Item>

        {/* 详细描述 */}
        <Form.Item
          label="详细描述"
          name="description"
          rules={[
            { required: true, message: '请输入详细描述' },
            { min: 10, message: '描述至少需要10个字符' },
            { max: 2000, message: '描述长度不能超过2000字符' }
          ]}
        >
          <TextArea
            rows={6}
            placeholder={
              feedbackType === 'bug'
                ? '请详细描述遇到的问题，包括操作步骤、预期结果和实际结果...'
                : feedbackType === 'feature'
                ? '请详细描述您希望添加的功能，包括使用场景和预期效果...'
                : feedbackType === 'question'
                ? '请详细描述您的问题，我们会尽快为您解答...'
                : '请详细描述您的反馈内容...'
            }
            showCount
            maxLength={2000}
          />
        </Form.Item>

        {/* 评分（仅一般反馈显示） */}
        {feedbackType === 'general' && (
          <Form.Item
            label="整体评分"
            name="rating"
          >
            <Rate
              character={<StarOutlined />}
              tooltips={['很差', '较差', '一般', '良好', '优秀']}
            />
          </Form.Item>
        )}

        {/* 联系邮箱 */}
        <Form.Item
          label="联系邮箱（可选）"
          name="email"
          rules={[
            { type: 'email', message: '请输入有效的邮箱地址' }
          ]}
        >
          <Input placeholder="如需回复，请留下您的邮箱地址" />
        </Form.Item>

        {/* 附件上传 */}
        <Form.Item
          label="附件（可选）"
          name="attachments"
          extra="支持上传图片、文本或PDF文件，单个文件不超过5MB，最多3个文件"
        >
          <Upload {...uploadProps} listType="text">
            <Button icon={<UploadOutlined />}>
              上传附件
            </Button>
          </Upload>
        </Form.Item>

        <Divider />

        {/* 提交按钮 */}
        <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
          <Space>
            <Button onClick={onCancel}>
              取消
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              icon={<HeartOutlined />}
            >
              提交反馈
            </Button>
          </Space>
        </Form.Item>
      </Form>

      {/* 隐私说明 */}
      <div style={{ marginTop: 16, padding: 16, backgroundColor: '#f6f8fa', borderRadius: 6 }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          <strong>隐私说明：</strong>
          我们会妥善保护您的个人信息，反馈内容仅用于产品改进，不会用于其他商业用途。
          如果您提供了邮箱地址，我们可能会就您的反馈进行回复。
        </Text>
      </div>
    </Modal>
  )
}

export default FeedbackModal
