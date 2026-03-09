import { describe, it, expect, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { renderWithProviders } from '../../test/test-utils';
import { FadeIn, SlideIn, ScaleIn, Stagger, Typewriter } from './Transition';

describe('FadeIn', () => {
  it('renders children correctly', () => {
    renderWithProviders(<FadeIn>Fade content</FadeIn>);
    expect(screen.getByText('Fade content')).toBeInTheDocument();
  });

  it('applies default delay', () => {
    const { container } = renderWithProviders(<FadeIn>Test</FadeIn>);
    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('animate-fade-in');
    expect(div).toHaveStyle({ animationDelay: '0ms' });
  });

  it('applies custom delay', () => {
    const { container } = renderWithProviders(<FadeIn delay={300}>Test</FadeIn>);
    const div = container.firstChild as HTMLElement;
    expect(div).toHaveStyle({ animationDelay: '300ms' });
  });

  it('applies custom duration', () => {
    const { container } = renderWithProviders(<FadeIn duration={500}>Test</FadeIn>);
    const div = container.firstChild as HTMLElement;
    expect(div).toHaveStyle({ animationDuration: '500ms' });
  });

  it('applies custom className', () => {
    const { container } = renderWithProviders(<FadeIn className="custom-class">Test</FadeIn>);
    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('custom-class');
  });
});

describe('SlideIn', () => {
  it('renders children correctly', () => {
    renderWithProviders(<SlideIn>Slide content</SlideIn>);
    expect(screen.getByText('Slide content')).toBeInTheDocument();
  });

  it('applies direction classes', () => {
    const { container: c1 } = renderWithProviders(<SlideIn direction="up">Test</SlideIn>);
    expect(c1.firstChild).toHaveClass('slide-in-up');

    const { container: c2 } = renderWithProviders(<SlideIn direction="down">Test</SlideIn>);
    expect(c2.firstChild).toHaveClass('slide-in-down');

    const { container: c3 } = renderWithProviders(<SlideIn direction="left">Test</SlideIn>);
    expect(c3.firstChild).toHaveClass('slide-in-left');

    const { container: c4 } = renderWithProviders(<SlideIn direction="right">Test</SlideIn>);
    expect(c4.firstChild).toHaveClass('slide-in-right');
  });

  it('applies custom delay', () => {
    const { container } = renderWithProviders(<SlideIn delay={200}>Test</SlideIn>);
    const div = container.firstChild as HTMLElement;
    expect(div).toHaveStyle({ animationDelay: '200ms' });
  });

  it('applies custom duration', () => {
    const { container } = renderWithProviders(<SlideIn duration={400}>Test</SlideIn>);
    const div = container.firstChild as HTMLElement;
    expect(div).toHaveStyle({ animationDuration: '400ms' });
  });
});

describe('ScaleIn', () => {
  it('renders children correctly', () => {
    renderWithProviders(<ScaleIn>Scale content</ScaleIn>);
    expect(screen.getByText('Scale content')).toBeInTheDocument();
  });

  it('applies default animation class', () => {
    const { container } = renderWithProviders(<ScaleIn>Test</ScaleIn>);
    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('animate-scale-in');
  });

  it('applies custom delay', () => {
    const { container } = renderWithProviders(<ScaleIn delay={150}>Test</ScaleIn>);
    const div = container.firstChild as HTMLElement;
    expect(div).toHaveStyle({ animationDelay: '150ms' });
  });

  it('applies custom duration', () => {
    const { container } = renderWithProviders(<ScaleIn duration={300}>Test</ScaleIn>);
    const div = container.firstChild as HTMLElement;
    expect(div).toHaveStyle({ animationDuration: '300ms' });
  });
});

describe('Stagger', () => {
  it('renders all children', () => {
    renderWithProviders(
      <Stagger>
        <div>Item 1</div>
        <div>Item 2</div>
        <div>Item 3</div>
      </Stagger>
    );

    expect(screen.getByText('Item 1')).toBeInTheDocument();
    expect(screen.getByText('Item 2')).toBeInTheDocument();
    expect(screen.getByText('Item 3')).toBeInTheDocument();
  });

  it('applies stagger delay to children', () => {
    const staggerDelay = 100;

    const { container } = renderWithProviders(
      <Stagger staggerDelay={staggerDelay}>
        <div>Item 1</div>
        <div>Item 2</div>
        <div>Item 3</div>
      </Stagger>
    );

    const children = container.children;
    expect(children[0]).toHaveStyle({ animationDelay: '0ms' });
    expect(children[1]).toHaveStyle({ animationDelay: `${staggerDelay}ms` });
    expect(children[2]).toHaveStyle({ animationDelay: `${staggerDelay * 2}ms` });
  });

  it('applies custom className to wrapper', () => {
    const { container } = renderWithProviders(
      <Stagger className="custom-wrapper">
        <div>Item</div>
      </Stagger>
    );

    expect(container.firstChild).toHaveClass('custom-wrapper');
  });

  it('handles single child', () => {
    const { container } = renderWithProviders(
      <Stagger staggerDelay={50}>
        <div>Single Item</div>
      </Stagger>
    );

    const child = container.firstChild as HTMLElement;
    expect(child).toHaveStyle({ animationDelay: '0ms' });
  });
});

describe('Typewriter', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it('renders text gradually with typewriter effect', async () => {
    renderWithProviders(<Typewriter text="Hello" speed={50} />);

    // Initially empty
    expect(screen.queryByText('Hello')).not.toBeInTheDocument();

    // After first character
    vi.advanceTimersByTime(50);
    expect(screen.getByText('H')).toBeInTheDocument();

    // After all characters
    vi.advanceTimersByTime(200);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('handles empty text', () => {
    const { container } = renderWithProviders(<Typewriter text="" speed={50} />);
    expect(container.textContent).toBe('');
  });

  it('applies cursor when showCursor is true', () => {
    renderWithProviders(<Typewriter text="Hi" speed={10} showCursor />);

    vi.advanceTimersByTime(30);

    const cursor = screen.getByText('▊');
    expect(cursor).toBeInTheDocument();
    expect(cursor).toHaveClass('animate-pulse');
  });

  it('does not show cursor when showCursor is false', () => {
    renderWithProviders(<Typewriter text="Hi" speed={10} showCursor={false} />);

    vi.advanceTimersByTime(30);

    expect(screen.queryByText('▊')).not.toBeInTheDocument();
  });

  it('calls onComplete when typing finishes', async () => {
    const onComplete = vi.fn();
    renderWithProviders(<Typewriter text="Done" speed={50} onComplete={onComplete} />);

    vi.advanceTimersByTime(200);

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalledTimes(1);
    });
  });

  it('respects custom typing speed', () => {
    renderWithProviders(<Typewriter text="ABC" speed={100} />);

    vi.advanceTimersByTime(50);
    expect(screen.queryByText('A')).not.toBeInTheDocument();

    vi.advanceTimersByTime(100);
    expect(screen.getByText('A')).toBeInTheDocument();
  });
});
