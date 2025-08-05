/**
 * 模板库组件
 */

import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Input,
  Select,
  Button,
  Space,
  Typography,
  Tag,
  Rate,
  Avatar,
  Pagination,
  Empty,
  Spin,
  Modal,
  message,
  Tooltip,
  Badge
} from 'antd'
import {
  SearchOutlined,
  EyeOutlined,
  HeartOutlined,
  HeartFilled,
  DownloadOutlined,
  StarOutlined,
  UserOutlined,
  CalendarOutlined,
  TagsOutlined,
  FilterOutlined,
  AppstoreOutlined,
  UnorderedListOutlined
} from '@ant-design/icons'
import { templateApi } from '../../services/api'
import './TemplateLibrary.css'

const { Search } = Input
const { Option } = Select
const { Title, Text, Paragraph } = Typography

interface Template {
  id: string
  name: string
  description: string
  content: string
  category: string
  tags: string[]
  industry: string
  use_case: string
  difficulty_level: string
  rating: number
  rating_count: number
  usage_count: number
  is_featured: boolean
  is_verified: boolean
  creator_id: string
  created_at: string
  updated_at: string
}

interface TemplateLibraryProps {
  onSelectTemplate?: (template: Template) => void
  onUseTemplate?: (template: Template) => void
  showActions?: boolean
  embedded?: boolean
}

const TemplateLibrary: React.FC<TemplateLibraryProps> = ({
  onSelectTemplate,
  onUseTemplate,
  showActions = true,
  embedded = false
}) => {
  const [loading, setLoading] = useState(false)
  const [templates, setTemplates] = useState<Template[]>([])
  const [total, setTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(12)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  
  // 搜索和筛选状态
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>()
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [selectedIndustry, setSelectedIndustry] = useState<string>()
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>()
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState('desc')
  
  // 模板详情模态框
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  
  // 分类和标签选项
  const [categories, setCategories] = useState<string[]>([])
  const [tags, setTags] = useState<any[]>([])

  // 加载模板列表
  const loadTemplates = async () => {
    setLoading(true)
    try {
      const params = {
        query: searchQuery || undefined,
        category: selectedCategory,
        tags: selectedTags.length > 0 ? selectedTags.join(',') : undefined,
        industry: selectedIndustry,
        difficulty_level: selectedDifficulty,
        sort_by: sortBy,
        sort_order: sortOrder,
        page: currentPage,
        page_size: pageSize
      }
      
      const response = await templateApi.getTemplates(params)
      setTemplates(response.templates)
      setTotal(response.total)
    } catch (error) {
      console.error('加载模板失败:', error)
      message.error('加载模板失败')
    } finally {
      setLoading(false)
    }
  }

  // 加载分类和标签
  const loadMetadata = async () => {
    try {
      const [categoriesRes, tagsRes] = await Promise.all([
        templateApi.getCategories(),
        templateApi.getTags({ featured_only: false, limit: 100 })
      ])
      setCategories(categoriesRes.categories.map((c: any) => c.name))
      setTags(tagsRes.tags)
    } catch (error) {
      console.error('加载元数据失败:', error)
    }
  }

  useEffect(() => {
    loadTemplates()
  }, [currentPage, searchQuery, selectedCategory, selectedTags, selectedIndustry, selectedDifficulty, sortBy, sortOrder])

  useEffect(() => {
    loadMetadata()
  }, [])

  // 搜索处理
  const handleSearch = (value: string) => {
    setSearchQuery(value)
    setCurrentPage(1)
  }

  // 筛选处理
  const handleFilterChange = (type: string, value: any) => {
    setCurrentPage(1)
    switch (type) {
      case 'category':
        setSelectedCategory(value)
        break
      case 'tags':
        setSelectedTags(value)
        break
      case 'industry':
        setSelectedIndustry(value)
        break
      case 'difficulty':
        setSelectedDifficulty(value)
        break
      case 'sort':
        const [field, order] = value.split('_')
        setSortBy(field)
        setSortOrder(order)
        break
    }
  }

  // 使用模板
  const handleUseTemplate = async (template: Template) => {
    try {
      await templateApi.useTemplate(template.id)
      message.success('模板使用记录已保存')
      onUseTemplate?.(template)
    } catch (error) {
      console.error('使用模板失败:', error)
      message.error('使用模板失败')
    }
  }

  // 查看模板详情
  const handleViewDetail = (template: Template) => {
    setSelectedTemplate(template)
    setDetailModalVisible(true)
  }

  // 获取难度标签颜色
  const getDifficultyColor = (level: string) => {
    switch (level) {
      case 'beginner': return 'green'
      case 'intermediate': return 'orange'
      case 'advanced': return 'red'
      default: return 'default'
    }
  }

  // 获取难度标签文本
  const getDifficultyText = (level: string) => {
    switch (level) {
      case 'beginner': return '初级'
      case 'intermediate': return '中级'
      case 'advanced': return '高级'
      default: return level
    }
  }

  // 渲染模板卡片
  const renderTemplateCard = (template: Template) => (
    <Card
      key={template.id}
      className="template-card"
      hoverable
      actions={showActions ? [
        <Tooltip title="查看详情">
          <EyeOutlined onClick={() => handleViewDetail(template)} />
        </Tooltip>,
        <Tooltip title="使用模板">
          <DownloadOutlined onClick={() => handleUseTemplate(template)} />
        </Tooltip>,
        <Tooltip title="收藏">
          <HeartOutlined />
        </Tooltip>
      ] : undefined}
    >
      <div className="template-card-header">
        <div className="template-title">
          <Title level={5} ellipsis={{ rows: 1 }}>
            {template.name}
            {template.is_verified && (
              <Badge
                count={<StarOutlined style={{ color: '#faad14' }} />}
                style={{ marginLeft: 8 }}
              />
            )}
          </Title>
        </div>
        <div className="template-meta">
          <Space>
            <Tag color={getDifficultyColor(template.difficulty_level)}>
              {getDifficultyText(template.difficulty_level)}
            </Tag>
            {template.is_featured && (
              <Tag color="red">推荐</Tag>
            )}
          </Space>
        </div>
      </div>
      
      <Paragraph
        ellipsis={{ rows: 2 }}
        style={{ marginBottom: 16, minHeight: 44 }}
      >
        {template.description}
      </Paragraph>
      
      <div className="template-tags">
        {template.tags.slice(0, 3).map(tag => (
          <Tag key={tag} size="small">{tag}</Tag>
        ))}
        {template.tags.length > 3 && (
          <Tag size="small">+{template.tags.length - 3}</Tag>
        )}
      </div>
      
      <div className="template-stats">
        <Space split={<span style={{ color: '#d9d9d9' }}>|</span>}>
          <Space>
            <Rate disabled value={template.rating} allowHalf />
            <Text type="secondary">({template.rating_count})</Text>
          </Space>
          <Text type="secondary">{template.usage_count} 次使用</Text>
        </Space>
      </div>
      
      <div className="template-footer">
        <Space>
          <Avatar size="small" icon={<UserOutlined />} />
          <Text type="secondary" style={{ fontSize: 12 }}>
            {new Date(template.created_at).toLocaleDateString()}
          </Text>
        </Space>
      </div>
    </Card>
  )

  // 渲染列表项
  const renderTemplateListItem = (template: Template) => (
    <Card key={template.id} className="template-list-item" hoverable>
      <Row gutter={16} align="middle">
        <Col span={16}>
          <div className="template-info">
            <Title level={5} style={{ margin: 0 }}>
              {template.name}
              {template.is_verified && (
                <StarOutlined style={{ color: '#faad14', marginLeft: 8 }} />
              )}
            </Title>
            <Paragraph ellipsis={{ rows: 1 }} style={{ margin: '4px 0' }}>
              {template.description}
            </Paragraph>
            <Space>
              <Tag color={getDifficultyColor(template.difficulty_level)}>
                {getDifficultyText(template.difficulty_level)}
              </Tag>
              {template.category && <Tag>{template.category}</Tag>}
              {template.is_featured && <Tag color="red">推荐</Tag>}
            </Space>
          </div>
        </Col>
        <Col span={4}>
          <div className="template-stats">
            <Space direction="vertical" size="small">
              <Space>
                <Rate disabled value={template.rating} allowHalf size="small" />
                <Text type="secondary">({template.rating_count})</Text>
              </Space>
              <Text type="secondary">{template.usage_count} 次使用</Text>
            </Space>
          </div>
        </Col>
        <Col span={4}>
          <Space>
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(template)}
            >
              查看
            </Button>
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              onClick={() => handleUseTemplate(template)}
            >
              使用
            </Button>
          </Space>
        </Col>
      </Row>
    </Card>
  )

  return (
    <div className={`template-library ${embedded ? 'embedded' : ''}`}>
      {/* 搜索和筛选栏 */}
      <Card className="search-filter-card">
        <Row gutter={16} align="middle">
          <Col span={8}>
            <Search
              placeholder="搜索模板..."
              allowClear
              onSearch={handleSearch}
              style={{ width: '100%' }}
            />
          </Col>
          <Col span={4}>
            <Select
              placeholder="分类"
              allowClear
              style={{ width: '100%' }}
              value={selectedCategory}
              onChange={(value) => handleFilterChange('category', value)}
            >
              {categories.map(category => (
                <Option key={category} value={category}>{category}</Option>
              ))}
            </Select>
          </Col>
          <Col span={4}>
            <Select
              placeholder="难度"
              allowClear
              style={{ width: '100%' }}
              value={selectedDifficulty}
              onChange={(value) => handleFilterChange('difficulty', value)}
            >
              <Option value="beginner">初级</Option>
              <Option value="intermediate">中级</Option>
              <Option value="advanced">高级</Option>
            </Select>
          </Col>
          <Col span={4}>
            <Select
              placeholder="排序"
              style={{ width: '100%' }}
              value={`${sortBy}_${sortOrder}`}
              onChange={(value) => handleFilterChange('sort', value)}
            >
              <Option value="created_at_desc">最新</Option>
              <Option value="rating_desc">评分最高</Option>
              <Option value="usage_count_desc">最热门</Option>
              <Option value="name_asc">名称A-Z</Option>
            </Select>
          </Col>
          <Col span={4}>
            <Space>
              <Button
                type={viewMode === 'grid' ? 'primary' : 'default'}
                icon={<AppstoreOutlined />}
                onClick={() => setViewMode('grid')}
              />
              <Button
                type={viewMode === 'list' ? 'primary' : 'default'}
                icon={<UnorderedListOutlined />}
                onClick={() => setViewMode('list')}
              />
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 模板列表 */}
      <Spin spinning={loading}>
        {templates.length > 0 ? (
          <>
            {viewMode === 'grid' ? (
              <Row gutter={[16, 16]}>
                {templates.map(template => (
                  <Col key={template.id} xs={24} sm={12} md={8} lg={6}>
                    {renderTemplateCard(template)}
                  </Col>
                ))}
              </Row>
            ) : (
              <Space direction="vertical" style={{ width: '100%' }}>
                {templates.map(renderTemplateListItem)}
              </Space>
            )}
            
            {/* 分页 */}
            <div style={{ textAlign: 'center', marginTop: 24 }}>
              <Pagination
                current={currentPage}
                total={total}
                pageSize={pageSize}
                showSizeChanger={false}
                showQuickJumper
                showTotal={(total, range) => 
                  `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
                }
                onChange={setCurrentPage}
              />
            </div>
          </>
        ) : (
          <Empty
            description="暂无模板"
            style={{ margin: '40px 0' }}
          />
        )}
      </Spin>

      {/* 模板详情模态框 */}
      <Modal
        title={selectedTemplate?.name}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        width={800}
        footer={[
          <Button key="cancel" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
          <Button
            key="use"
            type="primary"
            icon={<DownloadOutlined />}
            onClick={() => {
              if (selectedTemplate) {
                handleUseTemplate(selectedTemplate)
                setDetailModalVisible(false)
              }
            }}
          >
            使用模板
          </Button>
        ]}
      >
        {selectedTemplate && (
          <div className="template-detail">
            <Paragraph>{selectedTemplate.description}</Paragraph>
            
            <div className="template-content">
              <Title level={5}>模板内容</Title>
              <div className="content-preview">
                <pre>{selectedTemplate.content}</pre>
              </div>
            </div>
            
            <div className="template-metadata">
              <Row gutter={16}>
                <Col span={12}>
                  <Space direction="vertical">
                    <Text strong>分类：</Text>
                    <Text>{selectedTemplate.category || '未分类'}</Text>
                  </Space>
                </Col>
                <Col span={12}>
                  <Space direction="vertical">
                    <Text strong>难度：</Text>
                    <Tag color={getDifficultyColor(selectedTemplate.difficulty_level)}>
                      {getDifficultyText(selectedTemplate.difficulty_level)}
                    </Tag>
                  </Space>
                </Col>
              </Row>
              
              <div style={{ marginTop: 16 }}>
                <Text strong>标签：</Text>
                <div style={{ marginTop: 8 }}>
                  {selectedTemplate.tags.map(tag => (
                    <Tag key={tag}>{tag}</Tag>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default TemplateLibrary
