import { useEffect } from 'react';
import { Trash2, MessageSquare, Plus } from 'lucide-react';
import { useSessionStore } from '../../stores/sessionStore';
import { useChatStore } from '../../stores/chatStore';

export function SessionList() {
  const { sessions, isLoading, loadSessions, deleteSession } = useSessionStore();
  const { sessionId, setSessionId, clearMessages } = useChatStore();

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const handleSelectSession = (id: string) => {
    setSessionId(id);
    clearMessages();
  };

  const handleNewChat = () => {
    setSessionId(null);
    clearMessages();
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

  return (
    <div className="w-64 border-r flex flex-col bg-gray-50">
      <div className="p-4 border-b">
        <button
          onClick={handleNewChat}
          className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
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
              className={`p-4 border-b cursor-pointer hover:bg-gray-100 flex justify-between items-center ${
                sessionId === session.id ? 'bg-blue-100' : ''
              }`}
            >
              <div className="flex-1 min-w-0">
                <div className="font-medium truncate">
                  {session.title || '新对话'}
                </div>
                <div className="text-xs text-gray-500 flex items-center gap-1">
                  <MessageSquare className="w-3 h-3" />
                  {session.message_count} 条消息
                </div>
              </div>
              <button
                onClick={(e) => handleDelete(e, session.id)}
                className="p-1 hover:text-red-500"
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
