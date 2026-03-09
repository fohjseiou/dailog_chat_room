import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { renderWithProviders } from '../../test/test-utils';
import { Alert, AlertProvider, useAlert } from './Alert';

// Test component to use the alert context
function TestComponent() {
  const { showToast, showSuccess, showError, showInfo, showWarning } = useAlert();

  return (
    <div>
      <button onClick={() => showToast('Test toast')}>Toast</button>
      <button onClick={() => showSuccess('Test success')}>Success</button>
      <button onClick={() => showError('Test error')}>Error</button>
      <button onClick={() => showInfo('Test info')}>Info</button>
      <button onClick={() => showWarning('Test warning')}>Warning</button>
      <button onClick={() => showToast('Auto dismiss', { duration: 100 })}>
        Auto Dismiss
      </button>
    </div>
  );
}

describe('Alert Component', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders alert with default variant', () => {
    renderWithProviders(<Alert>Alert message</Alert>);
    expect(screen.getByText('Alert message')).toBeInTheDocument();
  });

  it('applies variant classes correctly', () => {
    const { rerender } = renderWithProviders(<Alert variant="info">Info</Alert>);
    expect(screen.getByText('Info')).toHaveClass('bg-blue-50', 'border-blue-200');

    rerender(<Alert variant="success">Success</Alert>);
    expect(screen.getByText('Success')).toHaveClass('bg-green-50', 'border-green-200');

    rerender(<Alert variant="warning">Warning</Alert>);
    expect(screen.getByText('Warning')).toHaveClass('bg-yellow-50', 'border-yellow-200');

    rerender(<Alert variant="error">Error</Alert>);
    expect(screen.getByText('Error')).toHaveClass('bg-red-50', 'border-red-200');
  });

  it('renders with icon when showIcon is true', () => {
    renderWithProviders(<Alert showIcon>With icon</Alert>);
    const alert = screen.getByText('With icon').closest('div');
    const icon = alert?.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });

  it('renders with close button when closable is true', () => {
    renderWithProviders(<Alert closable>Closable</Alert>);
    const closeButton = screen.getByRole('button', { name: /close/i });
    expect(closeButton).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    const handleClose = vi.fn();
    renderWithProviders(<Alert closable onClose={handleClose}>Close me</Alert>);

    const closeButton = screen.getByRole('button', { name: /close/i });
    closeButton.click();

    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('renders with title when provided', () => {
    renderWithProviders(
      <Alert title="Alert Title">
        Alert content
      </Alert>
    );
    expect(screen.getByText('Alert Title')).toBeInTheDocument();
    expect(screen.getByText('Alert content')).toBeInTheDocument();
  });
});

describe('AlertProvider', () => {
  it('provides alert context to children', () => {
    renderWithProviders(
      <AlertProvider>
        <TestComponent />
      </AlertProvider>
    );
    expect(screen.getByText('Toast')).toBeInTheDocument();
  });

  it('shows toast alert when showToast is called', () => {
    renderWithProviders(
      <AlertProvider>
        <TestComponent />
      </AlertProvider>
    );

    const button = screen.getByText('Toast');
    button.click();

    expect(screen.getByText('Test toast')).toBeInTheDocument();
  });

  it('shows success alert when showSuccess is called', () => {
    renderWithProviders(
      <AlertProvider>
        <TestComponent />
      </AlertProvider>
    );

    const button = screen.getByText('Success');
    button.click();

    expect(screen.getByText('Test success')).toBeInTheDocument();
  });

  it('shows error alert when showError is called', () => {
    renderWithProviders(
      <AlertProvider>
        <TestComponent />
      </AlertProvider>
    );

    const button = screen.getByText('Error');
    button.click();

    expect(screen.getByText('Test error')).toBeInTheDocument();
  });

  it('shows info alert when showInfo is called', () => {
    renderWithProviders(
      <AlertProvider>
        <TestComponent />
      </AlertProvider>
    );

    const button = screen.getByText('Info');
    button.click();

    expect(screen.getByText('Test info')).toBeInTheDocument();
  });

  it('shows warning alert when showWarning is called', () => {
    renderWithProviders(
      <AlertProvider>
        <TestComponent />
      </AlertProvider>
    );

    const button = screen.getByText('Warning');
    button.click();

    expect(screen.getByText('Test warning')).toBeInTheDocument();
  });

  it('auto-dismisses alert after duration', async () => {
    renderWithProviders(
      <AlertProvider>
        <TestComponent />
      </AlertProvider>
    );

    const button = screen.getByText('Auto Dismiss');
    button.click();

    expect(screen.getByText('Auto dismiss')).toBeInTheDocument();

    // Fast-forward time
    vi.advanceTimersByTime(150);

    await waitFor(() => {
      expect(screen.queryByText('Auto dismiss')).not.toBeInTheDocument();
    });
  });

  it('displays multiple alerts simultaneously', () => {
    renderWithProviders(
      <AlertProvider>
        <TestComponent />
      </AlertProvider>
    );

    screen.getByText('Success').click();
    screen.getByText('Error').click();
    screen.getByText('Info').click();

    expect(screen.getByText('Test success')).toBeInTheDocument();
    expect(screen.getByText('Test error')).toBeInTheDocument();
    expect(screen.getByText('Test info')).toBeInTheDocument();
  });

  it('closes alert when close button is clicked', () => {
    renderWithProviders(
      <AlertProvider>
        <TestComponent />
      </AlertProvider>
    );

    const button = screen.getByText('Toast');
    button.click();

    const closeButton = screen.getByRole('button', { name: /close/i });
    closeButton.click();

    expect(screen.queryByText('Test toast')).not.toBeInTheDocument();
  });

  it('respects custom duration', async () => {
    renderWithProviders(
      <AlertProvider defaultDuration={5000}>
        <TestComponent />
      </AlertProvider>
    );

    const button = screen.getByText('Toast');
    button.click();

    // Should still be visible after 1 second
    vi.advanceTimersByTime(1000);
    expect(screen.getByText('Test toast')).toBeInTheDocument();

    // Should be dismissed after 5 seconds
    vi.advanceTimersByTime(4000);
    await waitFor(() => {
      expect(screen.queryByText('Test toast')).not.toBeInTheDocument();
    });
  });

  it('respects custom position', () => {
    const { container } = renderWithProviders(
      <AlertProvider position="top-center">
        <TestComponent />
      </AlertProvider>
    );

    screen.getByText('Toast').click();

    const containerDiv = container.querySelector('.fixed.top-4.left-1\\/2');
    expect(containerDiv).toBeInTheDocument();
  });
});
