import { useEffect, useRef } from 'react';
import { useChatStore } from '../../stores/chatStore';
import { MessageBubble } from './MessageBubble';
import { MessageInput } from './MessageInput';
import { ThinkingIndicator } from './ThinkingIndicator';
import { ResponsiveLayout } from '../layout/ResponsiveLayout';
import { SessionList } from '../common/SessionList';

export function ChatView() {
  const { messages, sessionId, loadMessages, isLoading, error, thinking, clearError } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Load messages if session exists and messages are empty
  useEffect(() => {
    if (sessionId && messages.length === 0) {
      loadMessages(sessionId);
    }
  }, [sessionId, loadMessages, messages.length]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, thinking.stage]);

  return (
    <ResponsiveLayout sidebarContent={<SessionList />}>
      <div className="flex flex-col h-full">
        <div className="flex-1 overflow-y-auto p-4" ref={messagesContainerRef}>
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <div className="text-6xl mb-4">⚖️</div>
                <h2 className="text-xl font-semibold mb-2">法律咨询助手</h2>
                <p>请输入您的问题，我将为您提供法律信息参考</p>
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))
          )}

          {/* Thinking Indicator */}
          <ThinkingIndicator
            stage={thinking.stage}
            intent={thinking.intent}
            retrievedDocs={thinking.retrievedDocs}
          />

          {/* Legacy Loading State */}
          {isLoading && thinking.stage === 'idle' && (
            <div className="flex justify-start mb-4">
              <div className="bg-gray-200 rounded-lg px-4 py-2">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-100" />
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-200" />
                </div>
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
              <div className="flex items-center justify-between">
                <p>{error}</p>
                <button
                  onClick={clearError}
                  className="text-red-800 hover:text-red-900 font-medium text-sm"
                >
                  ✕
                </button>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <MessageInput />
      </div>
    </ResponsiveLayout>
  );
}
