import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '../../test/test-utils';
import { ThinkingIndicator } from './ThinkingIndicator';

describe('ThinkingIndicator', () => {
  it('does not render when stage is idle', () => {
    const { container } = renderWithProviders(
      <ThinkingIndicator stage="idle" />
    );
    expect(container.firstChild).toBeNull();
  });

  it('does not render when stage is done', () => {
    const { container } = renderWithProviders(
      <ThinkingIndicator stage="done" />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders processing stage correctly', () => {
    renderWithProviders(<ThinkingIndicator stage="processing" />);

    expect(screen.getByText('AI 正在处理...')).toBeInTheDocument();
  });

  it('renders error stage correctly', () => {
    renderWithProviders(<ThinkingIndicator stage="error" />);

    expect(screen.getByText('AI 正在处理...')).toBeInTheDocument();
  });
});
