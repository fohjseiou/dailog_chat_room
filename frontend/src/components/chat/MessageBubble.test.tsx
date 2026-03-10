import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '../../test/test-utils';
import { MessageBubble } from './MessageBubble';
import { Message } from '../../stores/chatStore';

const createMockMessage = (overrides: Partial<Message> = {}): Message => ({
  id: '1',
  role: 'user',
  content: 'Test message',
  timestamp: new Date('2024-01-01T00:00:00Z'),
  ...overrides,
});

describe('MessageBubble', () => {
  it('renders user message correctly', () => {
    const message = createMockMessage({ role: 'user', content: 'Hello' });
    renderWithProviders(<MessageBubble message={message} />);

    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('renders assistant message correctly', () => {
    const message = createMockMessage({ role: 'assistant', content: 'Hi there!' });
    renderWithProviders(<MessageBubble message={message} />);

    expect(screen.getByText('Hi there!')).toBeInTheDocument();
  });

  it('displays streaming indicator when streaming without content', () => {
    const message = createMockMessage({
      role: 'assistant',
      content: '',
      streaming: true,
    });
    const { container } = renderWithProviders(<MessageBubble message={message} />);

    expect(screen.getByText('▊')).toBeInTheDocument();
  });

  it('displays timestamp', () => {
    const message = createMockMessage({
      role: 'user',
      content: 'Test',
      timestamp: new Date('2024-03-09T14:30:00Z'),
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
        { title: 'Source 1', score: 0.95 },
        { title: 'Source 2', score: 0.87 },
      ],
    });
    renderWithProviders(<MessageBubble message={message} />);

    expect(screen.getByText('Source 1')).toBeInTheDocument();
    expect(screen.getByText('Source 2')).toBeInTheDocument();
  });

  it('does not display sources when not provided', () => {
    const message = createMockMessage({
      role: 'assistant',
      content: 'Answer',
    });
    renderWithProviders(<MessageBubble message={message} />);

    // No sources means no tags
    const tags = screen.queryAllByRole('generic').filter(
      el => el.textContent?.includes('📖')
    );
    expect(tags.length).toBe(0);
  });

  it('handles empty message content gracefully', () => {
    const message = createMockMessage({ role: 'user', content: '' });
    renderWithProviders(<MessageBubble message={message} />);

    // Should not throw error
    const timeText = new Date('2024-01-01T00:00:00Z').toLocaleTimeString();
    const bubble = screen.getByText(timeText).closest('.ant-card');
    expect(bubble).toBeInTheDocument();
  });
});
