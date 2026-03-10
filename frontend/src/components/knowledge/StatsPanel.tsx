import { KnowledgeStats } from '../../api/client';
import { Card, Col, Row, Statistic, Space, Tag } from 'antd';
import {
  FileTextOutlined,
  AppstoreOutlined,
  DatabaseOutlined,
  TagsOutlined,
} from '@ant-design/icons';

interface StatsPanelProps {
  stats: KnowledgeStats;
}

const CATEGORY_LABELS: Record<string, string> = {
  law: '法律法规',
  case: '案例分析',
  contract: '合同范本',
  interpretation: '司法解释',
};

const CATEGORY_COLORS: Record<string, string> = {
  law: 'blue',
  case: 'green',
  contract: 'orange',
  interpretation: 'purple',
};

export function StatsPanel({ stats }: StatsPanelProps) {
  return (
    <div className="bg-white border-b border-gray-200 px-6 py-4">
      <Row gutter={16}>
        <Col xs={12} sm={6}>
          <Card className="!bg-blue-50">
            <Statistic
              title="文档总数"
              value={stats.total_documents}
              prefix={<FileTextOutlined className="text-blue-600" />}
              valueStyle={{ color: '#1f2937' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card className="!bg-green-50">
            <Statistic
              title="知识块总数"
              value={stats.total_chunks}
              prefix={<AppstoreOutlined className="text-green-600" />}
              valueStyle={{ color: '#1f2937' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card className="!bg-purple-50">
            <Statistic
              title="向量存储"
              value={stats.chroma_collection_count}
              prefix={<DatabaseOutlined className="text-purple-600" />}
              valueStyle={{ color: '#1f2937' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card className="!bg-orange-50">
            <Statistic
              title="分类数量"
              value={Object.keys(stats.categories).length}
              prefix={<TagsOutlined className="text-orange-600" />}
              valueStyle={{ color: '#1f2937' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Category Distribution */}
      {Object.keys(stats.categories).length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <Space wrap size="small">
            {Object.entries(stats.categories).map(([category, count]) => (
              <Tag
                key={category}
                color={CATEGORY_COLORS[category] || 'default'}
                className="text-sm px-3 py-1"
              >
                {CATEGORY_LABELS[category] || category}: {count}
              </Tag>
            ))}
          </Space>
        </div>
      )}
    </div>
  );
}
