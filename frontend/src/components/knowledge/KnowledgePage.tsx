import { useEffect } from 'react';
import { useKnowledgeStore } from '../../stores/knowledgeStore';
import { StatsPanel } from './StatsPanel';
import { DocumentList } from './DocumentList';
import { DocumentUploader } from './DocumentUploader';
import { DocumentFilters } from './DocumentFilters';

export function KnowledgePage() {
  const { fetchDocuments, fetchStats, stats, loading, error, clearError } = useKnowledgeStore();

  useEffect(() => {
    fetchDocuments();
    fetchStats();
  }, []);

  const handleRetry = () => {
    clearError();
    fetchDocuments();
    fetchStats();
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">知识库管理</h1>
              <p className="text-sm text-gray-500 mt-1">管理法律文档、案例和参考资料</p>
            </div>
            <DocumentUploader />
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border-b border-red-200 px-6 py-3">
            <div className="flex items-center justify-between">
              <p className="text-sm text-red-600">{error}</p>
              <button
                onClick={handleRetry}
                className="text-sm text-red-700 hover:text-red-800 font-medium"
              >
                重试
              </button>
            </div>
          </div>
        )}

        {/* Stats Panel */}
        {stats && <StatsPanel stats={stats} />}

        {/* Filters */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <DocumentFilters />
        </div>

        {/* Document List */}
        <div className="flex-1 overflow-auto">
          <DocumentList />
        </div>
      </div>
    </div>
  );
}
