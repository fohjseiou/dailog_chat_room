import { useState } from 'react';
import { Send } from 'lucide-react';
import { useChatStore } from '../../stores/chatStore';

export function MessageInput() {
  const [message, setMessage] = useState('');
  const { sendMessageStream, isLoading, thinking } = useChatStore();

  const isDisabled = isLoading || thinking.stage !== 'idle' && thinking.stage !== 'done' && thinking.stage !== 'error';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isDisabled) return;

    const currentMessage = message;
    setMessage('');
    await sendMessageStream(currentMessage);
  };

  const getButtonText = () => {
    if (thinking.stage === 'routing') return '🔍';
    if (thinking.stage === 'retrieving') return '📚';
    if (thinking.stage === 'generating') return '✍️';
    return <Send className="w-5 h-5" />;
  };

  const getPlaceholder = () => {
    if (thinking.stage === 'routing') return '理解问题中...';
    if (thinking.stage === 'retrieving') return '检索知识库中...';
    if (thinking.stage === 'generating') return '生成回复中...';
    return '输入您的法律问题...';
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 p-4 border-t border-gray-200 bg-white">
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder={getPlaceholder()}
        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        disabled={isDisabled}
      />
      <button
        type="submit"
        disabled={!message.trim() || isDisabled}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
      >
        {getButtonText()}
      </button>
    </form>
  );
}
