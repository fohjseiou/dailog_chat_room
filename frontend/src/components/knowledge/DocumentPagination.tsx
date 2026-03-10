import { useKnowledgeStore } from '../../stores/knowledgeStore';
import { Pagination } from 'antd';

export function DocumentPagination() {
  const { pagination, fetchDocuments } = useKnowledgeStore();

  const { page, total_pages: totalPages, page_size: pageSize } = pagination;

  if (totalPages <= 1) return null;

  return (
    <div className="flex justify-center mt-6">
      <Pagination
        current={page}
        total={pagination.total}
        pageSize={pageSize}
        onChange={(newPage) => fetchDocuments(newPage)}
        showSizeChanger={false}
        showQuickJumper
        showTotal={(total) => `共 ${total} 条`}
      />
    </div>
  );
}
