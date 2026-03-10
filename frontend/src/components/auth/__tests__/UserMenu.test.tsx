import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { renderWithProviders } from '../../../test/test-utils';
import { UserMenu } from '../UserMenu';
import { useAuthStore } from '../../../stores/authStore';

// Mock the auth store
vi.mock('../../../stores/authStore', () => ({
  useAuthStore: vi.fn(),
}));

describe('UserMenu', () => {
  const mockLogout = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing when user is not authenticated', () => {
    (useAuthStore as any).mockReturnValue({
      user: null,
      logout: mockLogout,
    });

    const { container } = renderWithProviders(<UserMenu />);
    expect(container.firstChild).toBeNull();
  });

  it('renders username when user is authenticated', () => {
    (useAuthStore as any).mockReturnValue({
      user: { username: 'testuser', id: '1' },
      logout: mockLogout,
    });

    renderWithProviders(<UserMenu />);

    expect(screen.getByText('testuser')).toBeInTheDocument();
  });

  it('displays avatar with first letter of username', () => {
    (useAuthStore as any).mockReturnValue({
      user: { username: 'john', id: '1' },
      logout: mockLogout,
    });

    const { container } = renderWithProviders(<UserMenu />);

    // Check for avatar with the letter 'J'
    const avatar = container.querySelector('.ant-avatar');
    expect(avatar).toBeInTheDocument();
    expect(avatar?.textContent).toBe('J');
  });

  it('capitalizes first letter for avatar', () => {
    (useAuthStore as any).mockReturnValue({
      user: { username: 'alice', id: '1' },
      logout: mockLogout,
    });

    const { container } = renderWithProviders(<UserMenu />);

    const avatar = container.querySelector('.ant-avatar');
    expect(avatar?.textContent).toBe('A');
  });

  it('opens dropdown menu on click', async () => {
    (useAuthStore as any).mockReturnValue({
      user: { username: 'testuser', id: '1' },
      logout: mockLogout,
    });

    renderWithProviders(<UserMenu />);

    // Click the user menu to open dropdown
    const userMenu = screen.getByText('testuser').closest('.cursor-pointer');
    fireEvent.click(userMenu!);

    // Wait for dropdown to appear
    await waitFor(() => {
      expect(screen.getByText('退出登录')).toBeInTheDocument();
    });
  });

  it('calls logout when logout button is clicked', async () => {
    (useAuthStore as any).mockReturnValue({
      user: { username: 'testuser', id: '1' },
      logout: mockLogout,
    });

    renderWithProviders(<UserMenu />);

    // Open the dropdown
    const userMenu = screen.getByText('testuser').closest('.cursor-pointer');
    fireEvent.click(userMenu!);

    // Wait for logout button and click it
    await waitFor(() => {
      const logoutButton = screen.getByTestId('logout-button');
      fireEvent.click(logoutButton);
    });

    expect(mockLogout).toHaveBeenCalledTimes(1);
  });

  it('displays avatar with correct styling', () => {
    (useAuthStore as any).mockReturnValue({
      user: { username: 'testuser', id: '1' },
      logout: mockLogout,
    });

    const { container } = renderWithProviders(<UserMenu />);

    const avatar = container.querySelector('.ant-avatar');
    expect(avatar).toBeInTheDocument();
    expect(avatar).toHaveStyle({ backgroundColor: '#1890ff' });
  });

  it('applies hover effect to user menu', () => {
    (useAuthStore as any).mockReturnValue({
      user: { username: 'testuser', id: '1' },
      logout: mockLogout,
    });

    const { container } = renderWithProviders(<UserMenu />);

    const userMenu = container.querySelector('.cursor-pointer');
    expect(userMenu).toHaveClass('hover:bg-gray-100');
  });

  it('handles single character username', () => {
    (useAuthStore as any).mockReturnValue({
      user: { username: 'a', id: '1' },
      logout: mockLogout,
    });

    const { container } = renderWithProviders(<UserMenu />);

    const avatar = container.querySelector('.ant-avatar');
    expect(avatar?.textContent).toBe('A');
    expect(screen.getByText('a')).toBeInTheDocument();
  });

  it('handles numeric username', () => {
    (useAuthStore as any).mockReturnValue({
      user: { username: '123user', id: '1' },
      logout: mockLogout,
    });

    renderWithProviders(<UserMenu />);

    expect(screen.getByText('123user')).toBeInTheDocument();
  });
});
