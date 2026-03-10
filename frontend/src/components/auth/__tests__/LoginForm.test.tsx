import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../../test/test-utils';
import { LoginForm } from '../LoginForm';
import { useAuthStore } from '../../../stores/authStore';

// Mock the auth store
vi.mock('../../../stores/authStore', () => ({
  useAuthStore: vi.fn(),
}));

describe('LoginForm', () => {
  const mockLogin = vi.fn();
  const mockRegister = vi.fn();
  const mockClearError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuthStore as any).mockReturnValue({
      login: mockLogin,
      register: mockRegister,
      isLoading: false,
      error: null,
      clearError: mockClearError,
    });
  });

  it('renders login form correctly', () => {
    renderWithProviders(<LoginForm />);

    expect(screen.getByText('登录')).toBeInTheDocument();
    expect(screen.getByText('欢迎回来')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('用户名')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('密码')).toBeInTheDocument();
    expect(screen.getByText('还没有账户？')).toBeInTheDocument();
    expect(screen.getByText('立即注册')).toBeInTheDocument();
    // Submit button should be present
    expect(screen.getByTestId('submit-button')).toBeInTheDocument();
    expect(screen.getByTestId('toggle-mode-button')).toBeInTheDocument();
  });

  it('renders register form when toggled', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginForm />);

    await user.click(screen.getByTestId('toggle-mode-button'));

    expect(screen.getByText('注册')).toBeInTheDocument();
    expect(screen.getByText('创建新账户')).toBeInTheDocument();
    expect(screen.getByText('已有账户？')).toBeInTheDocument();
    expect(screen.getByText('立即登录')).toBeInTheDocument();
    expect(screen.getByTestId('submit-button')).toBeInTheDocument();
  });

  it('shows validation errors for empty fields', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginForm />);

    await user.click(screen.getByTestId('submit-button'));

    await waitFor(() => {
      expect(screen.getByText('请输入用户名')).toBeInTheDocument();
      expect(screen.getByText('请输入密码')).toBeInTheDocument();
    });

    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('shows validation error for short username', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginForm />);

    await user.type(screen.getByPlaceholderText('用户名'), 'ab');
    await user.click(screen.getByTestId('submit-button'));

    await waitFor(() => {
      expect(screen.getByText('用户名至少3个字符')).toBeInTheDocument();
    });

    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('shows validation error for short password', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginForm />);

    await user.type(screen.getByPlaceholderText('用户名'), 'testuser');
    await user.type(screen.getByPlaceholderText('密码'), '12345');
    await user.click(screen.getByTestId('submit-button'));

    await waitFor(() => {
      expect(screen.getByText('密码至少6个字符')).toBeInTheDocument();
    });

    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('calls login with correct credentials', async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();
    mockLogin.mockImplementation(() => Promise.resolve(undefined));

    renderWithProviders(<LoginForm onSuccess={onSuccess} />);

    await user.type(screen.getByPlaceholderText('用户名'), 'testuser');
    await user.type(screen.getByPlaceholderText('密码'), 'password123');
    await user.click(screen.getByTestId('submit-button'));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('testuser', 'password123');
    }, { timeout: 3000 });
  });

  it('calls register with correct credentials in register mode', async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();
    mockRegister.mockImplementation(() => Promise.resolve(undefined));

    renderWithProviders(<LoginForm onSuccess={onSuccess} />);

    // Switch to register mode
    await user.click(screen.getByTestId('toggle-mode-button'));

    // Wait for the form to update
    await waitFor(() => {
      expect(screen.getByText('注册')).toBeInTheDocument();
    });

    await user.type(screen.getByPlaceholderText('用户名'), 'newuser');
    await user.type(screen.getByPlaceholderText('密码'), 'password123');
    await user.click(screen.getByTestId('submit-button'));

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith('newuser', 'password123');
    }, { timeout: 3000 });
  });

  it('displays error message from store', () => {
    (useAuthStore as any).mockReturnValue({
      login: mockLogin,
      register: mockRegister,
      isLoading: false,
      error: 'Invalid credentials',
      clearError: mockClearError,
    });

    renderWithProviders(<LoginForm />);

    expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
  });

  it('disables form inputs during loading', () => {
    (useAuthStore as any).mockReturnValue({
      login: mockLogin,
      register: mockRegister,
      isLoading: true,
      error: null,
      clearError: mockClearError,
    });

    renderWithProviders(<LoginForm />);

    expect(screen.getByPlaceholderText('用户名')).toBeDisabled();
    expect(screen.getByPlaceholderText('密码')).toBeDisabled();
  });

  it('clears error when toggling between login and register', async () => {
    const user = userEvent.setup();
    (useAuthStore as any).mockReturnValue({
      login: mockLogin,
      register: mockRegister,
      isLoading: false,
      error: 'Some error',
      clearError: mockClearError,
    });

    renderWithProviders(<LoginForm />);

    expect(screen.getByText('Some error')).toBeInTheDocument();

    await user.click(screen.getByText('立即注册'));

    expect(mockClearError).toHaveBeenCalled();
  });

  it('clears error when closing error alert', async () => {
    (useAuthStore as any).mockReturnValue({
      login: mockLogin,
      register: mockRegister,
      isLoading: false,
      error: 'Some error',
      clearError: mockClearError,
    });

    const user = userEvent.setup();
    renderWithProviders(<LoginForm />);

    const closeButton = screen.getByRole('button', { name: /close/i });
    await user.click(closeButton);

    expect(mockClearError).toHaveBeenCalled();
  });

  it('resets form when toggling between login and register', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginForm />);

    // Fill in login form
    await user.type(screen.getByPlaceholderText('用户名'), 'testuser');
    await user.type(screen.getByPlaceholderText('密码'), 'password123');

    // Toggle to register
    await user.click(screen.getByTestId('toggle-mode-button'));

    // Form should be reset
    expect(screen.getByPlaceholderText('用户名')).toHaveValue('');
    expect(screen.getByPlaceholderText('密码')).toHaveValue('');
  });

  it('does not call login when credentials are invalid', async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValueOnce(new Error('Login failed'));

    renderWithProviders(<LoginForm />);

    await user.type(screen.getByPlaceholderText('用户名'), 'testuser');
    await user.type(screen.getByPlaceholderText('密码'), 'wrong');
    await user.click(screen.getByTestId('submit-button'));

    // Should show validation error for short password
    await waitFor(() => {
      expect(screen.getByText('密码至少6个字符')).toBeInTheDocument();
    });

    expect(mockLogin).not.toHaveBeenCalled();
  });
});
