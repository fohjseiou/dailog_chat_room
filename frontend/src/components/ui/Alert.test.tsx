import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, act } from '@testing-library/react';
import { renderWithProviders } from '../../test/test-utils';
import { Alert, AlertProvider, useAlert, ToastContainer } from './Alert';

// Test component to use the alert context
function TestComponent() {
  const { showToast, showSuccess, showError, showInfo, showWarning } = useAlert();

  return (
    <>
      <button onClick={() => showToast('Test toast')}>Toast</button>
      <button onClick={() => showSuccess('Test success')}>Success</button>
      <button onClick={() => showError('Test error')}>Error</button>
      <button onClick={() => showInfo('Test info')}>Info</button>
      <button onClick={() => showWarning('Test warning')}>Warning</button>
      <button onClick={() => showToast('Auto dismiss', { duration: 100 })}>
        Auto Dismiss
      </button>
      <ToastContainer />
    </>
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
    const infoElement = screen.getByText('Info').closest('div.bg-blue-50');
    expect(infoElement).toBeInTheDocument();
    expect(infoElement).toHaveClass('bg-blue-50', 'border-blue-200');

    rerender(<Alert variant="success">Success</Alert>);
    const successElement = screen.getByText('Success').closest('div.bg-green-50');
    expect(successElement).toBeInTheDocument();
    expect(successElement).toHaveClass('bg-green-50', 'border-green-200');

    rerender(<Alert variant="warning">Warning</Alert>);
    const warningElement = screen.getByText('Warning').closest('div.bg-yellow-50');
    expect(warningElement).toBeInTheDocument();
    expect(warningElement).toHaveClass('bg-yellow-50', 'border-yellow-200');

    rerender(<Alert variant="error">Error</Alert>);
    const errorElement = screen.getByText('Error').closest('div.bg-red-50');
    expect(errorElement).toBeInTheDocument();
    expect(errorElement).toHaveClass('bg-red-50', 'border-red-200');
  });

  it('renders with icon when showIcon is true', () => {
    renderWithProviders(<Alert showIcon>With icon</Alert>);
    const icon = document.querySelector('svg'); // lucide-react icons render as SVG
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
    act(() => {
      closeButton.click();
    });

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
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

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
    act(() => {
      button.click();
    });

    expect(screen.getByText('Test toast')).toBeInTheDocument();
  });

  it('shows success alert when showSuccess is called', () => {
    renderWithProviders(
      <AlertProvider>
        <TestComponent />
      </AlertProvider>
    );

    const button = screen.getByText('Success');
    act(() => {
      button.click();
    });

    expect(screen.getByText('Test success')).toBeInTheDocument();
  });

  it('shows error alert when showError is called', () => {
    renderWithProviders(
      <AlertProvider>
        <TestComponent />
      </AlertProvider>
    );

    const button = screen.getByText('Error');
    act(() => {
      button.click();
    });

    expect(screen.getByText('Test error')).toBeInTheDocument();
  });

  it('shows info alert when showInfo is called', () => {
    renderWithProviders(
      <AlertProvider>
        <TestComponent />
      </AlertProvider>
    );

    const button = screen.getByText('Info');
    act(() => {
      button.click();
    });

    expect(screen.getByText('Test info')).toBeInTheDocument();
  });

  it('shows warning alert when showWarning is called', () => {
    renderWithProviders(
      <AlertProvider>
        <TestComponent />
      </AlertProvider>
    );

    const button = screen.getByText('Warning');
    act(() => {
      button.click();
    });

    expect(screen.getByText('Test warning')).toBeInTheDocument();
  });

  it('auto-dismisses alert after duration', () => {
    renderWithProviders(
      <AlertProvider>
        <TestComponent />
      </AlertProvider>
    );

    const button = screen.getByText('Auto Dismiss');
    act(() => {
      button.click();
    });

    expect(screen.getByText('Auto dismiss')).toBeInTheDocument();

    // Fast-forward time
    act(() => {
      vi.advanceTimersByTime(150);
      vi.runAllTimers();
    });

    expect(screen.queryByText('Auto dismiss')).not.toBeInTheDocument();
  });

  it('displays multiple alerts simultaneously', () => {
    renderWithProviders(
      <AlertProvider>
        <TestComponent />
      </AlertProvider>
    );

    act(() => {
      screen.getByText('Success').click();
    });
    act(() => {
      screen.getByText('Error').click();
    });
    act(() => {
      screen.getByText('Info').click();
    });

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
    act(() => {
      button.click();
    });

    const closeButton = screen.getByRole('button', { name: /close/i });
    act(() => {
      closeButton.click();
    });

    expect(screen.queryByText('Test toast')).not.toBeInTheDocument();
  });

  it('respects custom duration', () => {
    renderWithProviders(
      <AlertProvider defaultDuration={5000}>
        <TestComponent />
      </AlertProvider>
    );

    const button = screen.getByText('Toast');
    act(() => {
      button.click();
    });

    // Should still be visible after 1 second
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(screen.getByText('Test toast')).toBeInTheDocument();

    // Should be dismissed after 5 seconds
    act(() => {
      vi.advanceTimersByTime(4000);
      vi.runAllTimers();
    });
    expect(screen.queryByText('Test toast')).not.toBeInTheDocument();
  });

  it('respects custom position', () => {
    const { container } = renderWithProviders(
      <AlertProvider position="top-center">
        <TestComponent />
      </AlertProvider>
    );

    act(() => {
      screen.getByText('Toast').click();
    });

    const containerDiv = container.querySelector('.fixed.top-4.left-1\\/2');
    expect(containerDiv).toBeInTheDocument();
  });
});
