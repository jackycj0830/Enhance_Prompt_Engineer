/**
 * 骨架屏加载组件
 */

import React from 'react'
import { Skeleton, Card, List, Space } from 'antd'
import './SkeletonLoader.css'

interface SkeletonLoaderProps {
  type?: 'card' | 'list' | 'form' | 'table' | 'profile' | 'article' | 'custom'
  rows?: number
  loading?: boolean
  children?: React.ReactNode
  animated?: boolean
  size?: 'small' | 'default' | 'large'
}

const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
  type = 'card',
  rows = 3,
  loading = true,
  children,
  animated = true,
  size = 'default'
}) => {
  if (!loading && children) {
    return <>{children}</>
  }

  const renderSkeleton = () => {
    switch (type) {
      case 'card':
        return <CardSkeleton animated={animated} size={size} />
      
      case 'list':
        return <ListSkeleton rows={rows} animated={animated} size={size} />
      
      case 'form':
        return <FormSkeleton rows={rows} animated={animated} size={size} />
      
      case 'table':
        return <TableSkeleton rows={rows} animated={animated} size={size} />
      
      case 'profile':
        return <ProfileSkeleton animated={animated} size={size} />
      
      case 'article':
        return <ArticleSkeleton animated={animated} size={size} />
      
      default:
        return (
          <Skeleton
            active={animated}
            paragraph={{ rows }}
            size={size}
          />
        )
    }
  }

  return <div className="skeleton-loader">{renderSkeleton()}</div>
}

// 卡片骨架屏
const CardSkeleton: React.FC<{ animated: boolean; size: string }> = ({ animated, size }) => (
  <Card className={`skeleton-card skeleton-${size}`}>
    <Skeleton
      active={animated}
      avatar={{ size: size === 'large' ? 64 : size === 'small' ? 32 : 48 }}
      paragraph={{ rows: 3 }}
      title={{ width: '60%' }}
    />
  </Card>
)

// 列表骨架屏
const ListSkeleton: React.FC<{ rows: number; animated: boolean; size: string }> = ({ 
  rows, animated, size 
}) => (
  <div className={`skeleton-list skeleton-${size}`}>
    {Array.from({ length: rows }, (_, index) => (
      <div key={index} className="skeleton-list-item">
        <Skeleton
          active={animated}
          avatar={{ size: size === 'large' ? 48 : size === 'small' ? 24 : 32 }}
          paragraph={{ rows: 2, width: ['100%', '80%'] }}
          title={{ width: '40%' }}
        />
      </div>
    ))}
  </div>
)

// 表单骨架屏
const FormSkeleton: React.FC<{ rows: number; animated: boolean; size: string }> = ({ 
  rows, animated, size 
}) => (
  <div className={`skeleton-form skeleton-${size}`}>
    {Array.from({ length: rows }, (_, index) => (
      <div key={index} className="skeleton-form-item">
        <Skeleton.Input
          active={animated}
          size={size as any}
          style={{ width: '100%', marginBottom: 16 }}
        />
      </div>
    ))}
    <div className="skeleton-form-actions">
      <Skeleton.Button active={animated} size={size as any} />
      <Skeleton.Button active={animated} size={size as any} />
    </div>
  </div>
)

// 表格骨架屏
const TableSkeleton: React.FC<{ rows: number; animated: boolean; size: string }> = ({ 
  rows, animated, size 
}) => (
  <div className={`skeleton-table skeleton-${size}`}>
    {/* 表头 */}
    <div className="skeleton-table-header">
      {Array.from({ length: 4 }, (_, index) => (
        <Skeleton.Input
          key={index}
          active={animated}
          size={size as any}
          style={{ width: '100%' }}
        />
      ))}
    </div>
    
    {/* 表格行 */}
    {Array.from({ length: rows }, (_, rowIndex) => (
      <div key={rowIndex} className="skeleton-table-row">
        {Array.from({ length: 4 }, (_, colIndex) => (
          <Skeleton.Input
            key={colIndex}
            active={animated}
            size={size as any}
            style={{ width: '100%' }}
          />
        ))}
      </div>
    ))}
  </div>
)

// 个人资料骨架屏
const ProfileSkeleton: React.FC<{ animated: boolean; size: string }> = ({ animated, size }) => (
  <div className={`skeleton-profile skeleton-${size}`}>
    <div className="skeleton-profile-header">
      <Skeleton.Avatar
        active={animated}
        size={size === 'large' ? 120 : size === 'small' ? 60 : 80}
      />
      <div className="skeleton-profile-info">
        <Skeleton
          active={animated}
          paragraph={{ rows: 3, width: ['60%', '80%', '40%'] }}
          title={{ width: '40%' }}
        />
      </div>
    </div>
    
    <div className="skeleton-profile-content">
      <Skeleton
        active={animated}
        paragraph={{ rows: 4 }}
      />
    </div>
  </div>
)

// 文章骨架屏
const ArticleSkeleton: React.FC<{ animated: boolean; size: string }> = ({ animated, size }) => (
  <div className={`skeleton-article skeleton-${size}`}>
    {/* 文章标题 */}
    <Skeleton.Input
      active={animated}
      size={size as any}
      style={{ width: '80%', height: size === 'large' ? 40 : size === 'small' ? 24 : 32 }}
    />
    
    {/* 文章元信息 */}
    <div className="skeleton-article-meta">
      <Skeleton.Avatar active={animated} size={24} />
      <Skeleton.Input active={animated} size="small" style={{ width: 100 }} />
      <Skeleton.Input active={animated} size="small" style={{ width: 80 }} />
    </div>
    
    {/* 文章内容 */}
    <div className="skeleton-article-content">
      <Skeleton
        active={animated}
        paragraph={{ rows: 6, width: ['100%', '100%', '80%', '100%', '60%', '90%'] }}
        title={false}
      />
    </div>
    
    {/* 文章图片 */}
    <Skeleton.Image
      active={animated}
      style={{ width: '100%', height: 200 }}
    />
    
    {/* 更多内容 */}
    <Skeleton
      active={animated}
      paragraph={{ rows: 3 }}
      title={false}
    />
  </div>
)

// 特定组件的骨架屏
export const PromptCardSkeleton: React.FC<{ count?: number }> = ({ count = 1 }) => (
  <div className="prompt-skeleton-container">
    {Array.from({ length: count }, (_, index) => (
      <Card key={index} className="prompt-skeleton-card">
        <Skeleton
          active
          avatar={{ size: 40 }}
          paragraph={{ rows: 3, width: ['100%', '80%', '60%'] }}
          title={{ width: '70%' }}
        />
        <div className="prompt-skeleton-actions">
          <Skeleton.Button active size="small" />
          <Skeleton.Button active size="small" />
          <Skeleton.Button active size="small" />
        </div>
      </Card>
    ))}
  </div>
)

export const TemplateListSkeleton: React.FC<{ count?: number }> = ({ count = 5 }) => (
  <List
    dataSource={Array.from({ length: count }, (_, index) => index)}
    renderItem={(index) => (
      <List.Item key={index}>
        <List.Item.Meta
          avatar={<Skeleton.Avatar active size={48} />}
          title={<Skeleton.Input active style={{ width: 200 }} />}
          description={<Skeleton active paragraph={{ rows: 2, width: ['100%', '60%'] }} title={false} />}
        />
        <div>
          <Skeleton.Button active size="small" />
        </div>
      </List.Item>
    )}
  />
)

export const AnalysisResultSkeleton: React.FC = () => (
  <div className="analysis-skeleton">
    <Card title={<Skeleton.Input active style={{ width: 150 }} />}>
      {/* 评分圆环 */}
      <div className="analysis-skeleton-score">
        <Skeleton.Avatar active size={120} shape="circle" />
        <Skeleton active paragraph={{ rows: 2 }} title={false} />
      </div>
      
      {/* 详细评分 */}
      <div className="analysis-skeleton-details">
        {Array.from({ length: 4 }, (_, index) => (
          <div key={index} className="analysis-skeleton-item">
            <Skeleton.Input active style={{ width: 100 }} />
            <Skeleton.Input active style={{ width: 200 }} />
            <Skeleton.Input active style={{ width: 50 }} />
          </div>
        ))}
      </div>
      
      {/* 建议列表 */}
      <div className="analysis-skeleton-suggestions">
        <Skeleton.Input active style={{ width: 80 }} />
        <Skeleton active paragraph={{ rows: 3 }} title={false} />
      </div>
    </Card>
  </div>
)

export const DashboardSkeleton: React.FC = () => (
  <div className="dashboard-skeleton">
    {/* 统计卡片 */}
    <div className="dashboard-skeleton-stats">
      {Array.from({ length: 4 }, (_, index) => (
        <Card key={index} className="dashboard-skeleton-stat-card">
          <Skeleton
            active
            avatar={{ size: 48, shape: 'square' }}
            paragraph={{ rows: 2, width: ['60%', '80%'] }}
            title={{ width: '40%' }}
          />
        </Card>
      ))}
    </div>
    
    {/* 图表区域 */}
    <div className="dashboard-skeleton-charts">
      <Card>
        <Skeleton.Image active style={{ width: '100%', height: 300 }} />
      </Card>
      <Card>
        <Skeleton.Image active style={{ width: '100%', height: 300 }} />
      </Card>
    </div>
    
    {/* 最近活动 */}
    <Card title={<Skeleton.Input active style={{ width: 100 }} />}>
      <ListSkeleton rows={5} animated={true} size="default" />
    </Card>
  </div>
)

export default SkeletonLoader
