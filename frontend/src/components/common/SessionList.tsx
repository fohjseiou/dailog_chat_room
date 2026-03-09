import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Trash2, MessageSquare, Plus, Clock } from 'lucide-react';
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

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirm('确定删除此会话吗？')) {
      await deleteSession(id);
      if (sessionId === id) {
        handleNewChat();
      }
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
        <button
          onClick={handleNewChat}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4 inline mr-2" />
          新对话
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-gray-500">加载中...</div>
        ) : sessions.length === 0 ? (
          <div className="p-4 text-center text-gray-500">暂无会话</div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              onClick={() => handleSelectSession(session.id)}
              className={`p-4 border-b border-gray-200 cursor-pointer hover:bg-gray-100 flex justify-between items-center group transition-colors ${
                sessionId === session.id ? 'bg-blue-100' : ''
              }`}
            >
              <div className="flex-1 min-w-0">
                <div className="font-medium text-gray-900 truncate">
                  {session.title || '新对话'}
                </div>
                <div className="text-xs text-gray-500 flex items-center gap-2 mt-1">
                  <span className="flex items-center gap-1">
                    <MessageSquare className="w-3 h-3" />
                    {session.message_count} 条消息
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatDate(session.updated_at)}
                  </span>
                </div>
              </div>
              <button
                onClick={(e) => handleDelete(e, session.id)}
                className="p-1 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
