import { useKnowledgeStore } from '../../stores/knowledgeStore';
import { DocumentCard } from './DocumentCard';
import { DocumentPagination } from './DocumentPagination';
import { List, Empty, Spin, Typography } from 'antd';

const { Text } = Typography;

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

export function DocumentList() {
  const { documents, loading, pagination } = useKnowledgeStore();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full p-6">
        <Spin tip="加载中..." size="large" />
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="flex items-center justify-center h-full p-6">
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <div>
              <p className="text-sm font-medium text-gray-900">暂无文档</p>
              <p className="text-sm text-gray-500">开始上传文档到知识库</p>
            </div>
          }
        />
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-4">
        <Text type="secondary">
          共 {pagination.total} 个文档，第 {pagination.page} / {pagination.totalPages} 页
        </Text>
      </div>

      <List
        grid={{ gutter: 16, xs: 1, sm: 1, md: 1, lg: 1, xl: 1, xxl: 1 }}
        dataSource={documents}
        renderItem={(doc) => (
          <List.Item>
            <DocumentCard
              document={doc}
              categoryLabel={doc.category ? CATEGORY_LABELS[doc.category] : '未分类'}
              categoryColor={doc.category ? CATEGORY_COLORS[doc.category] : 'default'}
            />
          </List.Item>
        )}
      />

      <DocumentPagination />
    </div>
  );
}
