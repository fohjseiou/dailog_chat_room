import { useKnowledgeStore } from '../../stores/knowledgeStore';
import { DocumentCard } from './DocumentCard';
import { DocumentPagination } from './DocumentPagination';
import { Stagger } from '../ui/Transition';

const CATEGORY_LABELS: Record<string, string> = {
  law: '法律法规',
  case: '案例分析',
  contract: '合同范本',
  interpretation: '司法解释',
};

const CATEGORY_COLORS: Record<string, string> = {
  law: 'bg-blue-100 text-blue-800',
  case: 'bg-green-100 text-green-800',
  contract: 'bg-yellow-100 text-yellow-800',
  interpretation: 'bg-purple-100 text-purple-800',
};

export function DocumentList() {
  const { documents, loading, pagination } = useKnowledgeStore();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full p-6">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">加载中...</p>
        </div>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="flex items-center justify-center h-full p-6">
        <div className="text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">暂无文档</h3>
          <p className="mt-1 text-sm text-gray-500">开始上传文档到知识库</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-4">
        <p className="text-sm text-gray-500">
          共 {pagination.total} 个文档，第 {pagination.page} / {pagination.totalPages} 页
        </p>
      </div>

      <Stagger staggerDelay={50}>
        {documents.map((doc) => (
          <DocumentCard
            key={doc.id}
            document={doc}
            categoryLabel={doc.category ? CATEGORY_LABELS[doc.category] : '未分类'}
            categoryColor={doc.category ? CATEGORY_COLORS[doc.category] : 'bg-gray-100 text-gray-800'}
          />
        ))}
      </Stagger>

      <DocumentPagination />
    </div>
  );
}
