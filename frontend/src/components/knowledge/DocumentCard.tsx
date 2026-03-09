import { useState } from 'react';
import { KnowledgeDocument } from '../../api/client';
import { useKnowledgeStore } from '../../stores/knowledgeStore';
import { DocumentEditModal } from './DocumentEditModal';

interface DocumentCardProps {
  document: KnowledgeDocument;
  categoryLabel: string;
  categoryColor: string;
}

export function DocumentCard({ document, categoryLabel, categoryColor }: DocumentCardProps) {
  const { deleteDocument } = useKnowledgeStore();
  const [showEditModal, setShowEditModal] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (!confirm(`确定要删除文档"${document.title}"吗？此操作不可撤销。`)) {
      return;
    }

    setDeleting(true);
    try {
      await deleteDocument(document.id);
    } catch (error) {
      alert('删除失败，请重试');
    } finally {
      setDeleting(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <>
      <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
        <div className="flex items-start justify-between">
          {/* Main Content */}
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="text-lg font-medium text-gray-900">{document.title}</h3>
              {document.category && (
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${categoryColor}`}>
                  {categoryLabel}
                </span>
              )}
            </div>

            {document.source && (
              <p className="text-sm text-gray-600 mb-2">
                <span className="font-medium">来源:</span> {document.source}
              </p>
            )}

            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span>{document.chunk_count} 个知识块</span>
              <span>创建于 {formatDate(document.created_at)}</span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 ml-4">
            <button
              onClick={() => setShowEditModal(true)}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="编辑"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
            </button>
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="删除"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {showEditModal && (
        <DocumentEditModal
          document={document}
          onClose={() => setShowEditModal(false)}
        />
      )}
    </>
  );
}
