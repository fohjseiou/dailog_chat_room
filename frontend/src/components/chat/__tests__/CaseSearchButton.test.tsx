import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { CaseSearchButton } from '../CaseSearchButton';

// Mock the chatApi
vi.mock('@/api/client', () => ({
  chatApi: {
    sendMessage: vi.fn(),
  },
}));

describe('CaseSearchButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders button with search icon and text', () => {
    render(<CaseSearchButton query="test query" />);
    expect(screen.getByText('🔍 搜索相关案例')).toBeInTheDocument();
  });

  it('is disabled when disabled prop is true', () => {
    render(<CaseSearchButton query="test" disabled={true} />);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('is not disabled when disabled prop is false or omitted', () => {
    render(<CaseSearchButton query="test" disabled={false} />);
    expect(screen.getByRole('button')).not.toBeDisabled();
  });

  it('calls sendMessage on click with correct command', async () => {
    const { chatApi } = await import('@/api/client');
    vi.mocked(chatApi.sendMessage).mockResolvedValue({} as any);

    render(<CaseSearchButton query="劳动合同纠纷" />);
    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(chatApi.sendMessage).toHaveBeenCalledWith({ message: 'search_cases:劳动合同纠纷' });
  });
});
