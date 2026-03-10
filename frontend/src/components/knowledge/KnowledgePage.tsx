import { useEffect } from 'react';
import { useKnowledgeStore } from '../../stores/knowledgeStore';
import { StatsPanel } from './StatsPanel';
import { DocumentList } from './DocumentList';
import { DocumentUploader } from './DocumentUploader';
import { DocumentFilters } from './DocumentFilters';
import { Layout, Typography, Alert, Button, Space } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';

const { Header, Content } = Layout;
const { Title, Paragraph } = Typography;

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
    <Layout className="h-screen bg-gray-50">
      {/* Header */}
      <Header className="bg-white border-b border-gray-200 px-6 h-auto py-4">
        <div className="flex items-center justify-between">
          <Space direction="vertical" size={0}>
            <Title level={3} className="!mb-0">知识库管理</Title>
            <Paragraph className="!mb-0 text-gray-500">管理法律文档、案例和参考资料</Paragraph>
          </Space>
          <DocumentUploader />
        </div>
      </Header>

      {/* Error Display */}
      {error && (
        <Alert
          message={error}
          type="error"
          action={
            <Button size="small" icon={<ReloadOutlined />} onClick={handleRetry}>
              重试
            </Button>
          }
          closable
          onClose={clearError}
        />
      )}

      <Content className="flex flex-col overflow-hidden">
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
      </Content>
    </Layout>
  );
}
