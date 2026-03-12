import { render, RenderOptions } from '@testing-library/react';
import { ReactElement } from 'react';
import { AlertProvider, ToastContainer } from '../components/ui';

// Custom render function with providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  withToastContainer?: boolean;
}

export function renderWithProviders(
  ui: ReactElement,
  options?: CustomRenderOptions
) {
  const { withToastContainer = false, ...restOptions } = options || {};

  // If withToastContainer is true, wrap with AlertProvider and ToastContainer
  if (withToastContainer) {
    const Wrapper = ({ children }: { children: React.ReactNode }) => (
      <AlertProvider>
        {children}
        <ToastContainer />
      </AlertProvider>
    );

    return render(ui, { wrapper: Wrapper, ...restOptions });
  }

  // Default: just render without providers
  return render(ui, restOptions);
}

// Re-export everything from testing-library
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';
