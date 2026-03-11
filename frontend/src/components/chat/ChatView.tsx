import { useEffect, useRef, useState } from 'react';
import { useChatStore } from '../../stores/chatStore';
import { MessageBubble } from './MessageBubble';
import { MessageInput } from './MessageInput';
import { ThinkingIndicator } from './ThinkingIndicator';
import { ResponsiveLayout } from '../layout/ResponsiveLayout';
import { SessionList } from '../common/SessionList';
import { Empty, Alert, Space, Typography } from 'antd';
import { SafetyCertificateOutlined } from '@ant-design/icons';

const { Title, Paragraph } = Typography;

export function ChatView() {
  const { messages, sessionId, loadMessages, isLoading, error, thinking, clearError } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [isNearBottom, setIsNearBottom] = useState(true);
  const [lastUserMessage, setLastUserMessage] = useState<string | undefined>(undefined);

  // Load messages if session exists and messages are empty
  useEffect(() => {
    if (sessionId && messages.length === 0) {
      loadMessages(sessionId);
    }
  }, [sessionId, loadMessages, messages.length]);

  // Track last user message for case search
  useEffect(() => {
    const userMessages = messages.filter(m => m.role === 'user');
    if (userMessages.length > 0) {
      setLastUserMessage(userMessages[userMessages.length - 1].content);
    } else {
      setLastUserMessage(undefined);
    }
  }, [messages]);

  // Check if user is near bottom (within 100px)
  const checkIfNearBottom = () => {
    const container = messagesContainerRef.current;
    if (container) {
      const { scrollTop, scrollHeight, clientHeight } = container;
      const distanceToBottom = scrollHeight - scrollTop - clientHeight;
      setIsNearBottom(distanceToBottom < 100);
    }
  };

  // Auto-scroll to bottom when messages change, only if user is near bottom
  // FIXED: Use requestAnimationFrame for better timing
  useEffect(() => {
    if (isNearBottom) {
      requestAnimationFrame(() => {
        messagesEndRef.current?.scrollIntoView({
          behavior: 'smooth',
          block: 'end'
        });
      });
    }
  }, [messages, thinking.stage, isNearBottom]);

  // Track scroll position to detect if user is near bottom
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (container) {
      container.addEventListener('scroll', checkIfNearBottom);
      return () => container.removeEventListener('scroll', checkIfNearBottom);
    }
  }, []);

  return (
    <ResponsiveLayout sidebarContent={<SessionList />}>
      <div className="flex flex-col flex-1 h-full">
        <div className="flex-1 overflow-y-auto p-4" ref={messagesContainerRef}>
          {messages.length === 0 ? (
            <Empty
              image={<SafetyCertificateOutlined className="text-6xl text-blue-200" />}
              description={
                <Space direction="vertical" size={4}>
                  <Title level={4} className="!mb-0">法律咨询助手</Title>
                  <Paragraph className="text-gray-500">请输入您的问题，我将为您提供法律信息参考</Paragraph>
                </Space>
              }
              className="flex items-center justify-center h-full"
            />
          ) : (
            messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                lastUserMessage={message.role === 'assistant' ? lastUserMessage : undefined}
              />
            ))
          )}

          {/* Thinking Indicator */}
          <ThinkingIndicator stage={thinking.stage} />

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
            <Alert
              message={error}
              type="error"
              closable
              onClose={clearError}
              showIcon
              className="mb-4"
            />
          )}

          <div ref={messagesEndRef} />
        </div>

        <MessageInput />
      </div>
    </ResponsiveLayout>
  );
}
