import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '../../test/test-utils';
import { StatsPanel } from './StatsPanel';
import { KnowledgeStats } from '../../api/client';

const createMockStats = (overrides: Partial<KnowledgeStats> = {}): KnowledgeStats => ({
  total_documents: 10,
  total_chunks: 150,
  chroma_collection_count: 145,
  categories: {
    law: 5,
    case: 3,
    contract: 2,
  },
  ...overrides,
});

describe('StatsPanel', () => {
  it('renders total documents stat', () => {
    const stats = createMockStats({ total_documents: 25 });
    renderWithProviders(<StatsPanel stats={stats} />);

    expect(screen.getByText('文档总数')).toBeInTheDocument();
    expect(screen.getByText('25')).toBeInTheDocument();
  });

  it('renders total chunks stat', () => {
    const stats = createMockStats({ total_chunks: 500 });
    renderWithProviders(<StatsPanel stats={stats} />);

    expect(screen.getByText('知识块总数')).toBeInTheDocument();
    expect(screen.getByText('500')).toBeInTheDocument();
  });

  it('renders chroma collection count stat', () => {
    const stats = createMockStats({ chroma_collection_count: 480 });
    renderWithProviders(<StatsPanel stats={stats} />);

    expect(screen.getByText('向量存储')).toBeInTheDocument();
    expect(screen.getByText('480')).toBeInTheDocument();
  });

  it('renders categories count', () => {
    const stats = createMockStats({
      categories: { law: 5, case: 3, contract: 2, interpretation: 1 },
    });
    renderWithProviders(<StatsPanel stats={stats} />);

    expect(screen.getByText('分类数量')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
  });

  it('displays category distribution when categories exist', () => {
    const stats = createMockStats({
      categories: { law: 5, case: 3 },
    });
    renderWithProviders(<StatsPanel stats={stats} />);

    expect(screen.getByText('分类分布')).toBeInTheDocument();
    expect(screen.getByText('法律法规: 5')).toBeInTheDocument();
    expect(screen.getByText('案例分析: 3')).toBeInTheDocument();
  });

  it('does not display category distribution when no categories', () => {
    const stats = createMockStats({ categories: {} });
    renderWithProviders(<StatsPanel stats={stats} />);

    expect(screen.queryByText('分类分布')).not.toBeInTheDocument();
  });

  it('displays all category labels correctly', () => {
    const stats = createMockStats({
      categories: { law: 1, case: 1, contract: 1, interpretation: 1 },
    });
    renderWithProviders(<StatsPanel stats={stats} />);

    expect(screen.getByText('法律法规: 1')).toBeInTheDocument();
    expect(screen.getByText('案例分析: 1')).toBeInTheDocument();
    expect(screen.getByText('合同范本: 1')).toBeInTheDocument();
    expect(screen.getByText('司法解释: 1')).toBeInTheDocument();
  });

  it('displays unknown category as-is', () => {
    const stats = createMockStats({
      categories: { unknown_category: 5 },
    });
    renderWithProviders(<StatsPanel stats={stats} />);

    expect(screen.getByText('unknown_category: 5')).toBeInTheDocument();
  });

  it('applies correct styling to stat cards', () => {
    const stats = createMockStats();
    const { container } = renderWithProviders(<StatsPanel stats={stats} />);

    // Check for background colors
    const cards = container.querySelectorAll('.rounded-lg');
    expect(cards[0]).toHaveClass('bg-blue-50');
    expect(cards[1]).toHaveClass('bg-green-50');
    expect(cards[2]).toHaveClass('bg-purple-50');
    expect(cards[3]).toHaveClass('bg-orange-50');
  });

  it('handles zero values correctly', () => {
    const stats = createMockStats({
      total_documents: 0,
      total_chunks: 0,
      chroma_collection_count: 0,
    });
    renderWithProviders(<StatsPanel stats={stats} />);

    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('handles large numbers correctly', () => {
    const stats = createMockStats({
      total_documents: 9999,
      total_chunks: 99999,
    });
    renderWithProviders(<StatsPanel stats={stats} />);

    expect(screen.getByText('9999')).toBeInTheDocument();
    expect(screen.getByText('99999')).toBeInTheDocument();
  });

  it('displays icons for each stat', () => {
    const stats = createMockStats();
    const { container } = renderWithProviders(<StatsPanel stats={stats} />);

    // Should have 4 SVG icons
    const icons = container.querySelectorAll('svg');
    expect(icons.length).toBeGreaterThanOrEqual(4);
  });

  it('uses responsive grid layout', () => {
    const stats = createMockStats();
    const { container } = renderWithProviders(<StatsPanel stats={stats} />);

    const grid = container.querySelector('.grid');
    expect(grid).toHaveClass('grid-cols-1', 'md:grid-cols-4');
  });
});
