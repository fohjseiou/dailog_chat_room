import { Message } from '../../stores/chatStore';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[70%] rounded-lg px-4 py-2 ${
        isUser
          ? 'bg-blue-500 text-white'
          : 'bg-gray-200 text-gray-800'
      }`}>
        {/* Intent Badge for Assistant */}
        {!isUser && message.intent && (
          <div className="mb-2">
            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
              {message.intent === 'legal_consultation' && '⚖️ 法律咨询'}
              {message.intent === 'greeting' && '👋 问候'}
              {message.intent === 'general_chat' && '💬 一般对话'}
            </span>
          </div>
        )}

        {/* Retrieved Docs for Assistant */}
        {!isUser && message.retrievedDocs && message.retrievedDocs.length > 0 && (
          <div className="mb-2 p-2 bg-green-50 rounded border border-green-200">
            <p className="text-xs text-green-700 mb-1">📚 参考文档：</p>
            <div className="space-y-1">
              {message.retrievedDocs.map((doc, idx) => (
                <div key={idx} className="flex items-center gap-2 text-xs">
                  <span className="text-green-600">📄</span>
                  <span className="text-green-800 truncate flex-1">{doc.title}</span>
                  <span className="text-green-600">
                    {Math.round(doc.score * 100)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Message Content */}
        <div className="text-sm whitespace-pre-wrap">
          {message.content || (message.streaming && <span className="animate-pulse">▊</span>)}
        </div>

        {/* Streaming Indicator */}
        {message.streaming && (
          <div className="flex gap-1 mt-2">
            <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" />
            <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce delay-100" />
            <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce delay-200" />
          </div>
        )}

        {/* Timestamp */}
        <div className={`text-xs mt-1 ${isUser ? 'text-blue-100' : 'text-gray-500'}`}>
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {message.sources.map((source, idx) => (
              <span
                key={idx}
                className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded"
              >
                📖 {source.title}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
