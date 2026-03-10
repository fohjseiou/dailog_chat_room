import { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeftOutlined, DownloadOutlined, ShareAltOutlined, CalendarOutlined, FileTextOutlined } from '@ant-design/icons';
import { useChatStore } from '../../stores/chatStore';
import { MessageBubble } from '../chat/MessageBubble';
import { MessageInput } from '../chat/MessageInput';
import { ThinkingIndicator } from '../chat/ThinkingIndicator';
import { chatApi } from '../../api/client';
import { Button, Typography, Descriptions, Spin, Empty, Space, Alert, message } from 'antd';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;

interface SessionDetail {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
  summary?: string;
}

export function SessionDetailPage() {
  const { sessionId: currentSessionId, messages, loadMessages, setSessionId, clearMessages, thinking } = useChatStore();
  const { sessionId } = useParams<{ sessionId: string }>();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [session, setSession] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<string | null>(null);

  // Sync session with chat store and load messages
  useEffect(() => {
    if (sessionId) {
      if (sessionId !== currentSessionId) {
        setSessionId(sessionId);
        loadMessages(sessionId);
      } else if (messages.length === 0) {
        loadMessages(sessionId);
      }
    }
  }, [sessionId, currentSessionId, loadMessages, setSessionId, messages.length]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    const fetchSession = async () => {
      if (!sessionId) return;

      try {
        setLoading(true);
        const sessionData = await chatApi.getSession(sessionId);
        setSession(sessionData);

        // Try to fetch summary
        try {
          const summaryResponse = await fetch(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/api/v1/chat/sessions/${sessionId}/summary`);
          if (summaryResponse.ok) {
            const summaryData = await summaryResponse.json();
            setSummary(summaryData.summary);
          }
        } catch (e) {
          // Summary not available
        }
      } catch (error) {
        console.error('Failed to fetch session:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSession();
  }, [sessionId]);

  const handleExport = async () => {
    if (!session || messages.length === 0) return;

    try {
      let content = `对话记录\n`;
      content += `标题: ${session.title || '新对话'}\n`;
      content += `创建时间: ${new Date(session.created_at).toLocaleString('zh-CN')}\n`;
      content += `消息数量: ${messages.length}\n`;
      if (summary) {
        content += `\n摘要:\n${summary}\n`;
      }
      content += `\n${'='.repeat(50)}\n\n`;

      messages.forEach((msg) => {
        const roleName = msg.role === 'user' ? '用户' : '助手';
        const time = new Date(msg.timestamp).toLocaleTimeString();
        content += `[${time}] ${roleName}:\n${msg.content}\n\n`;
        if (msg.sources && msg.sources.length > 0) {
          content += `参考资料: ${msg.sources.map(s => s.title).join(', ')}\n\n`;
        }
      });

      // Create blob and download
      const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `对话_${session.title || session.id}_${new Date().toISOString().slice(0, 10)}.txt`;
      a.click();
      URL.revokeObjectURL(url);
      message.success('导出成功');
    } catch (error) {
      message.error('导出失败，请重试');
    }
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: session?.title || '法律咨询对话',
          text: summary || '查看我的法律咨询对话记录',
          url: window.location.href,
        });
      } catch (error) {
        console.log('Share cancelled');
      }
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(window.location.href);
      message.success('链接已复制到剪贴板');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spin tip="加载中..." size="large" />
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex items-center justify-center h-full">
        <Empty
          image={<FileTextOutlined className="text-5xl text-gray-400" />}
          description={
            <div>
              <Text className="text-sm font-medium text-gray-900">会话不存在</Text>
              <br />
              <Text className="text-sm text-gray-500">该会话可能已被删除</Text>
            </div>
          }
        >
          <Link to="/">
            <Button type="primary">返回首页</Button>
          </Link>
        </Empty>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-64px)]">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <Space size="large">
            <Link to="/">
              <Button type="text" icon={<ArrowLeftOutlined />} />
            </Link>
            <div>
              <Title level={4} className="!mb-1">
                {session.title || '新对话'}
              </Title>
              <Space>
                <Text type="secondary">
                  <CalendarOutlined className="mr-1" />
                  {dayjs(session.created_at).format('YYYY-MM-DD HH:mm')}
                </Text>
                <Text type="secondary">{session.message_count} 条消息</Text>
              </Space>
            </div>
          </Space>
          <Space>
            <Button
              icon={<ShareAltOutlined />}
              onClick={handleShare}
            >
              分享
            </Button>
            <Button
              icon={<DownloadOutlined />}
              onClick={handleExport}
            >
              导出
            </Button>
          </Space>
        </div>

        {/* Summary */}
        {summary && (
          <Alert
            message="对话摘要"
            description={summary}
            type="info"
            showIcon
            className="mt-4"
          />
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-3xl mx-auto">
          {messages.length === 0 ? (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="暂无消息记录"
            />
          ) : (
            messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))
          )}

          {/* Thinking Indicator */}
          <ThinkingIndicator stage={thinking.stage} />
        </div>
        <div ref={messagesEndRef} />
      </div>

      {/* Input for continuing the conversation */}
      <div className="border-t border-gray-200 bg-white">
        <div className="max-w-3xl mx-auto">
          <MessageInput />
        </div>
      </div>
    </div>
  );
}
