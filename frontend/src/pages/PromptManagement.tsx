/**
 * 提示词管理页面
 */

import React, { useState, useEffect } from 'react'
import {
  Layout,
  Card,
  Button,
  Space,
  Typography,
  Row,
  Col,
  Modal,
  message,
  Spin,
  Empty,
  Tabs
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  AnalyticsOutlined,
  BulbOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

import PromptEditor from '../components/PromptEditor'
import AnalysisResult from '../components/AnalysisResult'
import OptimizationSuggestions from '../components/OptimizationSuggestions'
import { promptApi, analysisApi, optimizationApi } from '../services/api'
import { useAuthStore } from '../stores/authStore'

const { Content } = Layout
const { Title } = Typography
const { TabPane } = Tabs

const PromptManagement: React.FC = () => {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  
  // 状态管理
  const [activeTab, setActiveTab] = useState('editor')
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [optimizing, setOptimizing] = useState(false)
  
  // 数据状态
  const [currentPrompt, setCurrentPrompt] = useState('')
  const [analysisResult, setAnalysisResult] = useState<any>(null)
  const [optimizationResult, setOptimizationResult] = useState<any>(null)
  const [savedPromptId, setSavedPromptId] = useState<string | null>(null)

  // 处理提示词内容变化
  const handlePromptChange = (content: string) => {
    setCurrentPrompt(content)
    // 清除之前的分析结果
    if (analysisResult) {
      setAnalysisResult(null)
      setOptimizationResult(null)
    }
  }

  // 保存提示词
  const handleSavePrompt = async (content: string, metadata: any) => {
    if (!content.trim()) {
      message.warning('请输入提示词内容')
      return
    }

    setLoading(true)
    try {
      const promptData = {
        title: metadata.title || `提示词_${new Date().toLocaleDateString()}`,
        content,
        category: metadata.category,
        tags: metadata.tags || [],
        is_template: false,
        is_public: false
      }

      let result
      if (savedPromptId) {
        // 更新现有提示词
        result = await promptApi.updatePrompt(savedPromptId, promptData)
        message.success('提示词更新成功')
      } else {
        // 创建新提示词
        result = await promptApi.createPrompt(promptData)
        setSavedPromptId(result.id)
        message.success('提示词保存成功')
      }
    } catch (error) {
      console.error('保存提示词失败:', error)
      message.error('保存失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  // 分析提示词
  const handleAnalyzePrompt = async (content: string) => {
    if (!content.trim()) {
      message.warning('请输入提示词内容')
      return
    }

    setAnalyzing(true)
    try {
      const analysisData = {
        content,
        prompt_id: savedPromptId,
        ai_model: 'gpt-3.5-turbo'
      }

      const result = await analysisApi.analyzePrompt(analysisData)
      setAnalysisResult(result)
      setActiveTab('analysis')
      message.success('分析完成')
    } catch (error) {
      console.error('分析失败:', error)
      message.error('分析失败，请重试')
    } finally {
      setAnalyzing(false)
    }
  }

  // 获取优化建议
  const handleOptimize = async (analysisId: string) => {
    setOptimizing(true)
    try {
      const result = await optimizationApi.generateSuggestions({
        analysis_id: analysisId,
        scenario: '通用',
        regenerate: false
      })
      
      setOptimizationResult(result)
      setActiveTab('optimization')
      message.success('优化建议生成完成')
    } catch (error) {
      console.error('生成优化建议失败:', error)
      message.error('生成优化建议失败，请重试')
    } finally {
      setOptimizing(false)
    }
  }

  // 重新分析
  const handleReanalyze = async (analysisId: string) => {
    await handleAnalyzePrompt(currentPrompt)
  }

  // 应用优化建议
  const handleApplySuggestions = async (suggestionIds: string[], originalPrompt: string) => {
    setLoading(true)
    try {
      const result = await optimizationApi.applySuggestion(suggestionIds[0]) // 简化处理
      
      if (result.optimized_prompt) {
        setCurrentPrompt(result.optimized_prompt)
        message.success('优化建议已应用')
        setActiveTab('editor')
      }
    } catch (error) {
      console.error('应用建议失败:', error)
      message.error('应用建议失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  // 应用单个建议
  const handleApplySingle = async (suggestionId: string) => {
    try {
      const result = await optimizationApi.applySuggestion(suggestionId)
      message.success('建议已应用')
    } catch (error) {
      console.error('应用建议失败:', error)
      message.error('应用建议失败，请重试')
    }
  }

  return (
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          {/* 页面标题 */}
          <div style={{ marginBottom: 24 }}>
            <Title level={2}>
              <EditOutlined style={{ marginRight: 8, color: '#1890ff' }} />
              提示词工作台
            </Title>
            <p style={{ color: '#666', fontSize: 16 }}>
              创建、分析和优化您的AI提示词，提升AI应用效果
            </p>
          </div>

          {/* 主要内容区域 */}
          <Card style={{ borderRadius: 12, boxShadow: '0 4px 16px rgba(0,0,0,0.1)' }}>
            <Tabs
              activeKey={activeTab}
              onChange={setActiveTab}
              size="large"
              tabBarStyle={{ marginBottom: 24 }}
            >
              {/* 编辑器标签页 */}
              <TabPane
                tab={
                  <Space>
                    <EditOutlined />
                    <span>编辑器</span>
                  </Space>
                }
                key="editor"
              >
                <PromptEditor
                  value={currentPrompt}
                  onChange={handlePromptChange}
                  onAnalyze={handleAnalyzePrompt}
                  onSave={handleSavePrompt}
                  loading={analyzing || loading}
                  placeholder="请输入您的提示词内容..."
                  maxLength={5000}
                  showAnalytics={true}
                  showTemplates={true}
                />
              </TabPane>

              {/* 分析结果标签页 */}
              <TabPane
                tab={
                  <Space>
                    <AnalyticsOutlined />
                    <span>分析结果</span>
                    {analysisResult && <span style={{ color: '#52c41a' }}>●</span>}
                  </Space>
                }
                key="analysis"
                disabled={!analysisResult}
              >
                {analysisResult ? (
                  <AnalysisResult
                    data={analysisResult}
                    loading={optimizing}
                    onOptimize={handleOptimize}
                    onReanalyze={handleReanalyze}
                    showDetails={true}
                  />
                ) : (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description="暂无分析结果，请先分析提示词"
                  >
                    <Button
                      type="primary"
                      icon={<AnalyticsOutlined />}
                      onClick={() => setActiveTab('editor')}
                    >
                      去分析
                    </Button>
                  </Empty>
                )}
              </TabPane>

              {/* 优化建议标签页 */}
              <TabPane
                tab={
                  <Space>
                    <BulbOutlined />
                    <span>优化建议</span>
                    {optimizationResult && <span style={{ color: '#faad14' }}>●</span>}
                  </Space>
                }
                key="optimization"
                disabled={!optimizationResult}
              >
                {optimizationResult ? (
                  <OptimizationSuggestions
                    data={optimizationResult}
                    loading={loading}
                    onApplySuggestions={handleApplySuggestions}
                    onApplySingle={handleApplySingle}
                    originalPrompt={currentPrompt}
                  />
                ) : (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description="暂无优化建议，请先完成提示词分析"
                  >
                    <Button
                      type="primary"
                      icon={<BulbOutlined />}
                      onClick={() => setActiveTab('analysis')}
                      disabled={!analysisResult}
                    >
                      获取建议
                    </Button>
                  </Empty>
                )}
              </TabPane>
            </Tabs>
          </Card>

          {/* 快速操作提示 */}
          <Card 
            style={{ 
              marginTop: 16, 
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              border: 'none',
              color: 'white'
            }}
          >
            <Row gutter={24} align="middle">
              <Col span={18}>
                <Title level={4} style={{ color: 'white', margin: 0 }}>
                  💡 使用提示
                </Title>
                <p style={{ color: 'rgba(255,255,255,0.9)', margin: '8px 0 0 0' }}>
                  1. 在编辑器中输入您的提示词 → 2. 点击"分析提示词"获得评分 → 3. 查看"优化建议"并应用改进
                </p>
              </Col>
              <Col span={6} style={{ textAlign: 'right' }}>
                <Button
                  type="primary"
                  size="large"
                  ghost
                  onClick={() => navigate('/templates')}
                >
                  浏览模板库
                </Button>
              </Col>
            </Row>
          </Card>
        </div>
      </Content>
    </Layout>
  )
}

export default PromptManagement
