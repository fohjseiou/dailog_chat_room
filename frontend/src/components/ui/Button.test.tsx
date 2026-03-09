import { describe, it, expect, vi } from 'vitest';
import { screen, fireEvent } from '@testing-library/react';
import { renderWithProviders } from '../../test/test-utils';
import { TouchButton, RippleButton } from './Button';

describe('TouchButton', () => {
  it('renders children correctly', () => {
    renderWithProviders(<TouchButton>Click me</TouchButton>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    renderWithProviders(<TouchButton onClick={handleClick}>Click me</TouchButton>);

    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('does not call onClick when disabled', () => {
    const handleClick = vi.fn();
    renderWithProviders(
      <TouchButton onClick={handleClick} disabled>
        Click me
      </TouchButton>
    );

    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('applies variant classes correctly', () => {
    const { rerender } = renderWithProviders(<TouchButton variant="primary">Primary</TouchButton>);
    expect(screen.getByText('Primary')).toHaveClass('bg-blue-600');

    rerender(<TouchButton variant="secondary">Secondary</TouchButton>);
    expect(screen.getByText('Secondary')).toHaveClass('bg-gray-100');

    rerender(<TouchButton variant="ghost">Ghost</TouchButton>);
    expect(screen.getByText('Ghost')).toHaveClass('bg-transparent');
  });

  it('applies size classes correctly', () => {
    const { rerender } = renderWithProviders(<TouchButton size="sm">Small</TouchButton>);
    expect(screen.getByText('Small')).toHaveClass('px-3', 'py-1.5', 'text-sm');

    rerender(<TouchButton size="md">Medium</TouchButton>);
    expect(screen.getByText('Medium')).toHaveClass('px-4', 'py-2');

    rerender(<TouchButton size="lg">Large</TouchButton>);
    expect(screen.getByText('Large')).toHaveClass('px-6', 'py-3');
  });

  it('applies fullWidth class when fullWidth is true', () => {
    renderWithProviders(<TouchButton fullWidth>Full width</TouchButton>);
    expect(screen.getByText('Full width')).toHaveClass('w-full');
  });

  it('applies disabled styles when disabled', () => {
    renderWithProviders(<TouchButton disabled>Disabled</TouchButton>);
    expect(screen.getByText('Disabled')).toHaveClass('opacity-50', 'cursor-not-allowed');
  });

  it('handles touch events', () => {
    const handleClick = vi.fn();
    renderWithProviders(<TouchButton onClick={handleClick}>Touch me</TouchButton>);

    const button = screen.getByText('Touch me');
    fireEvent.touchStart(button);
    fireEvent.touchEnd(button);

    // Should trigger click after touch
    expect(handleClick).toHaveBeenCalled();
  });

  it('respects button type prop', () => {
    renderWithProviders(<TouchButton type="submit">Submit</TouchButton>);
    expect(screen.getByText('Submit')).toHaveAttribute('type', 'submit');
  });
});

describe('RippleButton', () => {
  it('renders children correctly', () => {
    renderWithProviders(<RippleButton>Click me</RippleButton>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('creates ripple effect on click', () => {
    renderWithProviders(<RippleButton>Click me</RippleButton>);

    const button = screen.getByText('Click me').closest('button');
    fireEvent.mouseDown(button!);

    // Check if ripple element is created
    const ripple = button?.querySelector('.animate-ping');
    expect(ripple).toBeInTheDocument();
  });

  it('creates ripple effect on touch', () => {
    renderWithProviders(<RippleButton>Touch me</RippleButton>);

    const button = screen.getByText('Touch me').closest('button');
    fireEvent.touchStart(button!);

    // Check if ripple element is created
    const ripple = button?.querySelector('.animate-ping');
    expect(ripple).toBeInTheDocument();
  });

  it('applies custom className', () => {
    renderWithProviders(<RippleButton className="custom-class">Custom</RippleButton>);

    const button = screen.getByText('Custom').closest('button');
    expect(button).toHaveClass('custom-class');
  });

  it('passes through other props', () => {
    renderWithProviders(<RippleButton disabled>Disabled</RippleButton>);

    const button = screen.getByText('Disabled').closest('button');
    expect(button).toBeDisabled();
  });
});
