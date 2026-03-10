import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, List, Empty, Popconfirm, Space, Spin } from 'antd';
import { MessageOutlined, PlusOutlined, ClockCircleOutlined, DeleteOutlined } from '@ant-design/icons';
import { useSessionStore } from '../../stores/sessionStore';
import { useChatStore } from '../../stores/chatStore';

export function SessionList() {
  const navigate = useNavigate();
  const { sessions, isLoading, loadSessions, deleteSession } = useSessionStore();
  const { sessionId, setSessionId, clearMessages } = useChatStore();

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const handleSelectSession = (id: string) => {
    setSessionId(id);
    clearMessages();
    navigate(`/chat/${id}`);
  };

  const handleNewChat = () => {
    setSessionId(null);
    clearMessages();
    navigate('/chat');
  };

  const handleDelete = async (id: string) => {
    await deleteSession(id);
    if (sessionId === id) {
      handleNewChat();
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return '今天';
    } else if (diffDays === 1) {
      return '昨天';
    } else if (diffDays < 7) {
      return `${diffDays} 天前`;
    } else {
      return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
    }
  };

  return (
    <div className="w-64 border-r border-gray-200 flex flex-col bg-gray-50">
      <div className="p-4 border-b border-gray-200">
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleNewChat}
          block
        >
          新对话
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center">
            <Spin tip="加载中..." />
          </div>
        ) : sessions.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无会话"
            className="mt-8"
          />
        ) : (
          <List
            dataSource={sessions}
            renderItem={(session) => (
              <List.Item
                key={session.id}
                onClick={() => handleSelectSession(session.id)}
                className={`cursor-pointer hover:bg-gray-100 transition-colors !border-x-0 ${
                  sessionId === session.id ? 'bg-blue-100' : ''
                }`}
                actions={[
                  <Popconfirm
                    title="确定删除此会话吗？"
                    onConfirm={(e) => {
                      e?.stopPropagation();
                      handleDelete(session.id);
                    }}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button
                      type="text"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </Popconfirm>,
                ]}
              >
                <List.Item.Meta
                  title={
                    <div className="font-medium text-gray-900 truncate">
                      {session.title || '新对话'}
                    </div>
                  }
                  description={
                    <Space size="small" className="text-xs text-gray-500">
                      <Space size={4}>
                        <MessageOutlined className="text-xs" />
                        <span>{session.message_count} 条消息</span>
                      </Space>
                      <Space size={4}>
                        <ClockCircleOutlined className="text-xs" />
                        <span>{formatDate(session.updated_at)}</span>
                      </Space>
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </div>
    </div>
  );
}
