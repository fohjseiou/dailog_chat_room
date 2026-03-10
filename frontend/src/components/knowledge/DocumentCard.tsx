import { useState } from 'react';
import { KnowledgeDocument } from '../../api/client';
import { useKnowledgeStore } from '../../stores/knowledgeStore';
import { DocumentEditModal } from './DocumentEditModal';
import { Card, Tag, Space, Button, Popconfirm, Typography, message } from 'antd';
import { EditOutlined, DeleteOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

const { Text, Title } = Typography;

interface DocumentCardProps {
  document: KnowledgeDocument;
  categoryLabel: string;
  categoryColor: string;
}

const CATEGORY_COLORS: Record<string, string> = {
  law: 'blue',
  case: 'green',
  contract: 'orange',
  interpretation: 'purple',
};

export function DocumentCard({ document, categoryLabel, categoryColor }: DocumentCardProps) {
  const { deleteDocument } = useKnowledgeStore();
  const [showEditModal, setShowEditModal] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await deleteDocument(document.id);
      message.success('删除成功');
    } catch (error) {
      message.error('删除失败，请重试');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <>
      <Card
        hoverable
        className="shadow-sm"
        actions={[
          <Button
            key="edit"
            type="text"
            icon={<EditOutlined />}
            onClick={() => setShowEditModal(true)}
          >
            编辑
          </Button>,
          <Popconfirm
            key="delete"
            title="确定要删除此文档吗？"
            description="此操作不可撤销。"
            onConfirm={handleDelete}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              loading={deleting}
            >
              删除
            </Button>
          </Popconfirm>,
        ]}
      >
        <Space direction="vertical" size="small" className="w-full">
          <Space>
            <Title level={5} className="!mb-0">
              {document.title}
            </Title>
            {document.category && (
              <Tag color={CATEGORY_COLORS[document.category] || 'default'}>
                {categoryLabel}
              </Tag>
            )}
          </Space>

          {document.source && (
            <Text type="secondary">
              来源: {document.source}
            </Text>
          )}

          <Space>
            <Text type="secondary">{document.chunk_count} 个知识块</Text>
            <Text type="secondary">
              创建于 {dayjs(document.created_at).format('YYYY-MM-DD HH:mm')}
            </Text>
          </Space>
        </Space>
      </Card>

      {showEditModal && (
        <DocumentEditModal
          document={document}
          onClose={() => setShowEditModal(false)}
        />
      )}
    </>
  );
}
