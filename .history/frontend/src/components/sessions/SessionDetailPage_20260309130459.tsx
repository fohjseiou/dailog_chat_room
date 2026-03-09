import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Download, Share2, Calendar, FileText } from 'lucide-react';
import { useChatStore } from '../../stores/chatStore';
import { MessageBubble } from '../chat/MessageBubble';
import { MessageInput } from '../chat/MessageInput';
import { chatApi } from '../../api/client';

interface SessionDetail {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
  summary?: string;
}

export function SessionDetailPage() {
  const { sessionId: currentSessionId, messages, loadMessages, setSessionId, clearMessages } = useChatStore();
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
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
    if (!session) return;

    try {
      // Get session messages (in real app, you'd have an API for this)
      const messages = []; // You'd need to implement getMessages endpoint

      let content = `对话记录\n`;
      content += `标题: ${session.title || '新对话'}\n`;
      content += `创建时间: ${new Date(session.created_at).toLocaleString('zh-CN')}\n`;
      content += `消息数量: ${session.message_count}\n`;
      if (summary) {
        content += `\n摘要:\n${summary}\n`;
      }
      content += `\n{'='.repeat(50)}\n\n`;

      // Create blob and download
      const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `对话_${session.title || session.id}_${new Date().toISOString().slice(0, 10)}.txt`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      alert('导出失败，请重试');
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
      alert('链接已复制到剪贴板');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">加载中...</p>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <FileText className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">会话不存在</h3>
          <p className="mt-1 text-sm text-gray-500">该会话可能已被删除</p>
          <Link
            to="/"
            className="mt-4 inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            返回首页
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-64px)]">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              to="/"
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="h-5 w-5 text-gray-600" />
            </Link>
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                {session.title || '新对话'}
              </h1>
              <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                <span className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  {new Date(session.created_at).toLocaleString('zh-CN')}
                </span>
                <span>{session.message_count} 条消息</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleShare}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="分享"
            >
              <Share2 className="h-5 w-5 text-gray-600" />
            </button>
            <button
              onClick={handleExport}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="导出"
            >
              <Download className="h-5 w-5 text-gray-600" />
            </button>
          </div>
        </div>

        {/* Summary */}
        {summary && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h3 className="text-sm font-medium text-blue-900 mb-1">对话摘要</h3>
            <p className="text-sm text-blue-800">{summary}</p>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-3xl mx-auto">
          {/* Message list would go here - for now showing placeholder */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
            <p className="text-sm text-yellow-800">
              消息记录加载中... <br />
              <span className="text-xs">(完整消息历史功能即将推出)</span>
            </p>
          </div>
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
