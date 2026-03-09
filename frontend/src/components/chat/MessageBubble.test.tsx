import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '../../test/test-utils';
import { MessageBubble } from './MessageBubble';
import { Message } from '../../stores/chatStore';

const createMockMessage = (overrides: Partial<Message> = {}): Message => ({
  id: '1',
  role: 'user',
  content: 'Test message',
  timestamp: '2024-01-01T00:00:00Z',
  ...overrides,
});

describe('MessageBubble', () => {
  it('renders user message correctly', () => {
    const message = createMockMessage({ role: 'user', content: 'Hello' });
    renderWithProviders(<MessageBubble message={message} />);

    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hello')).toHaveClass('bg-blue-500', 'text-white');
  });

  it('renders assistant message correctly', () => {
    const message = createMockMessage({ role: 'assistant', content: 'Hi there!' });
    renderWithProviders(<MessageBubble message={message} />);

    expect(screen.getByText('Hi there!')).toBeInTheDocument();
    expect(screen.getByText('Hi there!')).toHaveClass('bg-gray-200', 'text-gray-800');
  });

  it('displays intent badge for assistant messages', () => {
    const message = createMockMessage({
      role: 'assistant',
      content: 'Legal advice',
      intent: 'legal_consultation',
    });
    renderWithProviders(<MessageBubble message={message} />);

    expect(screen.getByText('⚖️ 法律咨询')).toBeInTheDocument();
  });

  it('displays greeting intent badge', () => {
    const message = createMockMessage({
      role: 'assistant',
      content: 'Hello!',
      intent: 'greeting',
    });
    renderWithProviders(<MessageBubble message={message} />);

    expect(screen.getByText('👋 问候')).toBeInTheDocument();
  });

  it('displays general chat intent badge', () => {
    const message = createMockMessage({
      role: 'assistant',
      content: 'Nice day',
      intent: 'general_chat',
    });
    renderWithProviders(<MessageBubble message={message} />);

    expect(screen.getByText('💬 一般对话')).toBeInTheDocument();
  });

  it('does not display intent badge for user messages', () => {
    const message = createMockMessage({
      role: 'user',
      content: 'Hello',
      intent: 'greeting',
    });
    renderWithProviders(<MessageBubble message={message} />);

    expect(screen.queryByText('👋 问候')).not.toBeInTheDocument();
  });

  it('displays retrieved docs for assistant messages', () => {
    const message = createMockMessage({
      role: 'assistant',
      content: 'Based on documents...',
      retrievedDocs: [
        { title: 'Contract Law 101', score: 0.95 },
        { title: 'Civil Code', score: 0.87 },
      ],
    });
    renderWithProviders(<MessageBubble message={message} />);

    expect(screen.getByText('📚 参考文档：')).toBeInTheDocument();
    expect(screen.getByText('Contract Law 101')).toBeInTheDocument();
    expect(screen.getByText('Civil Code')).toBeInTheDocument();
    expect(screen.getByText('95%')).toBeInTheDocument();
    expect(screen.getByText('87%')).toBeInTheDocument();
  });

  it('displays streaming indicator when streaming', () => {
    const message = createMockMessage({
      role: 'assistant',
      content: 'Thinking',
      streaming: true,
    });
    const { container } = renderWithProviders(<MessageBubble message={message} />);

    const indicators = container.querySelectorAll('.animate-bounce');
    expect(indicators).toHaveLength(3);
  });

  it('displays pulse cursor when streaming without content', () => {
    const message = createMockMessage({
      role: 'assistant',
      content: '',
      streaming: true,
    });
    const { container } = renderWithProviders(<MessageBubble message={message} />);

    const pulse = container.querySelector('.animate-pulse');
    expect(pulse).toBeInTheDocument();
    expect(pulse).toHaveTextContent('▊');
  });

  it('displays timestamp', () => {
    const message = createMockMessage({
      role: 'user',
      content: 'Test',
      timestamp: '2024-03-09T14:30:00Z',
    });
    renderWithProviders(<MessageBubble message={message} />);

    // Check for timestamp (exact format depends on locale)
    const timeText = new Date('2024-03-09T14:30:00Z').toLocaleTimeString();
    expect(screen.getByText(timeText)).toBeInTheDocument();
  });

  it('displays sources when provided', () => {
    const message = createMockMessage({
      role: 'assistant',
      content: 'Answer',
      sources: [
        { title: 'Source 1', url: 'http://example.com/1' },
        { title: 'Source 2', url: 'http://example.com/2' },
      ],
    });
    renderWithProviders(<MessageBubble message={message} />);

    expect(screen.getByText('📖 Source 1')).toBeInTheDocument();
    expect(screen.getByText('📖 Source 2')).toBeInTheDocument();
  });

  it('aligns user message to the right', () => {
    const message = createMockMessage({ role: 'user', content: 'User message' });
    const { container } = renderWithProviders(<MessageBubble message={message} />);

    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass('justify-end');
  });

  it('aligns assistant message to the left', () => {
    const message = createMockMessage({ role: 'assistant', content: 'Assistant message' });
    const { container } = renderWithProviders(<MessageBubble message={message} />);

    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass('justify-start');
  });

  it('handles empty message content gracefully', () => {
    const message = createMockMessage({ role: 'user', content: '' });
    renderWithProviders(<MessageBubble message={message} />);

    // Should not throw error
    const bubble = screen.getByText('12:00:00 AM').closest('.flex');
    expect(bubble).toBeInTheDocument();
  });

  it('does not display retrieved docs section when no docs', () => {
    const message = createMockMessage({
      role: 'assistant',
      content: 'Answer',
      retrievedDocs: [],
    });
    renderWithProviders(<MessageBubble message={message} />);

    expect(screen.queryByText('📚 参考文档：')).not.toBeInTheDocument();
  });

  it('handles long content with whitespace preservation', () => {
    const longContent = 'Line 1\nLine 2\nLine 3';
    const message = createMockMessage({ role: 'user', content: longContent });
    renderWithProviders(<MessageBubble message={message} />);

    const contentDiv = screen.getByText('Line 1').closest('.whitespace-pre-wrap');
    expect(contentDiv).toHaveClass('whitespace-pre-wrap');
  });
});
