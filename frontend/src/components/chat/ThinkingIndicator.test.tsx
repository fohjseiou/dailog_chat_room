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

  it('renders routing stage correctly', () => {
    renderWithProviders(<ThinkingIndicator stage="routing" />);

    expect(screen.getByText('🔍')).toBeInTheDocument();
    expect(screen.getByText('理解问题...')).toBeInTheDocument();
  });

  it('renders retrieving stage correctly', () => {
    renderWithProviders(<ThinkingIndicator stage="retrieving" />);

    expect(screen.getByText('📚')).toBeInTheDocument();
    expect(screen.getByText('检索知识库...')).toBeInTheDocument();
  });

  it('renders generating stage correctly', () => {
    renderWithProviders(<ThinkingIndicator stage="generating" />);

    expect(screen.getByText('✍️')).toBeInTheDocument();
    expect(screen.getByText('生成回复...')).toBeInTheDocument();
  });

  it('renders error stage correctly', () => {
    renderWithProviders(<ThinkingIndicator stage="error" />);

    expect(screen.getByText('❌')).toBeInTheDocument();
    expect(screen.getByText('出错了')).toBeInTheDocument();
  });

  it('displays intent badge when retrieving', () => {
    renderWithProviders(
      <ThinkingIndicator stage="retrieving" intent="legal_consultation" />
    );

    expect(screen.getByText('法律咨询')).toBeInTheDocument();
  });

  it('displays greeting intent label', () => {
    renderWithProviders(
      <ThinkingIndicator stage="retrieving" intent="greeting" />
    );

    expect(screen.getByText('问候')).toBeInTheDocument();
  });

  it('displays general_chat intent label', () => {
    renderWithProviders(
      <ThinkingIndicator stage="retrieving" intent="general_chat" />
    );

    expect(screen.getByText('一般对话')).toBeInTheDocument();
  });

  it('displays unknown intent as-is', () => {
    renderWithProviders(
      <ThinkingIndicator stage="retrieving" intent="unknown_intent" />
    );

    expect(screen.getByText('unknown_intent')).toBeInTheDocument();
  });

  it('does not display intent badge for other stages', () => {
    renderWithProviders(
      <ThinkingIndicator stage="routing" intent="legal_consultation" />
    );

    expect(screen.queryByText('法律咨询')).not.toBeInTheDocument();
  });

  it('displays retrieved documents when retrieving', () => {
    const docs = [
      { title: 'Contract Law', score: 0.95 },
      { title: 'Civil Code', score: 0.87 },
    ];

    renderWithProviders(
      <ThinkingIndicator stage="retrieving" retrievedDocs={docs} />
    );

    expect(screen.getByText('找到相关文档：')).toBeInTheDocument();
    expect(screen.getByText('Contract Law')).toBeInTheDocument();
    expect(screen.getByText('Civil Code')).toBeInTheDocument();
    expect(screen.getByText('95%')).toBeInTheDocument();
    expect(screen.getByText('87%')).toBeInTheDocument();
  });

  it('limits retrieved documents to 3', () => {
    const docs = [
      { title: 'Doc 1', score: 0.9 },
      { title: 'Doc 2', score: 0.8 },
      { title: 'Doc 3', score: 0.7 },
      { title: 'Doc 4', score: 0.6 },
      { title: 'Doc 5', score: 0.5 },
    ];

    renderWithProviders(
      <ThinkingIndicator stage="retrieving" retrievedDocs={docs} />
    );

    // Should only show first 3
    expect(screen.getByText('Doc 1')).toBeInTheDocument();
    expect(screen.getByText('Doc 2')).toBeInTheDocument();
    expect(screen.getByText('Doc 3')).toBeInTheDocument();
    expect(screen.queryByText('Doc 4')).not.toBeInTheDocument();
    expect(screen.queryByText('Doc 5')).not.toBeInTheDocument();
  });

  it('does not display retrieved docs section when no docs', () => {
    renderWithProviders(
      <ThinkingIndicator stage="retrieving" retrievedDocs={[]} />
    );

    expect(screen.queryByText('找到相关文档：')).not.toBeInTheDocument();
  });

  it('displays animated dots when generating', () => {
    const { container } = renderWithProviders(
      <ThinkingIndicator stage="generating" />
    );

    const dots = container.querySelectorAll('.animate-bounce');
    expect(dots).toHaveLength(3);
  });

  it('displays both intent and docs when retrieving', () => {
    const docs = [{ title: 'Legal Doc', score: 0.92 }];

    renderWithProviders(
      <ThinkingIndicator
        stage="retrieving"
        intent="legal_consultation"
        retrievedDocs={docs}
      />
    );

    expect(screen.getByText('法律咨询')).toBeInTheDocument();
    expect(screen.getByText('找到相关文档：')).toBeInTheDocument();
    expect(screen.getByText('Legal Doc')).toBeInTheDocument();
  });

  it('does not display docs for other stages', () => {
    const docs = [{ title: 'Some Doc', score: 0.9 }];

    renderWithProviders(
      <ThinkingIndicator stage="generating" retrievedDocs={docs} />
    );

    expect(screen.queryByText('找到相关文档：')).not.toBeInTheDocument();
    expect(screen.queryByText('Some Doc')).not.toBeInTheDocument();
  });
});
