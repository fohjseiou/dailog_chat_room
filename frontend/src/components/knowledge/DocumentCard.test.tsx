import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { renderWithProviders } from '../../test/test-utils';
import { DocumentCard } from './DocumentCard';
import { KnowledgeDocument } from '../../api/client';
import * as knowledgeStore from '../../stores/knowledgeStore';

// Mock the knowledge store
const mockDeleteDocument = vi.fn();
vi.mock('../../stores/knowledgeStore', () => ({
  useKnowledgeStore: () => ({
    deleteDocument: mockDeleteDocument,
  }),
}));

// Mock DocumentEditModal
vi.mock('./DocumentEditModal', () => ({
  DocumentEditModal: ({ document, onClose }: any) => (
    <div data-testid="edit-modal">
      <span>Editing: {document.title}</span>
      <button onClick={onClose}>Close</button>
    </div>
  ),
}));

const createMockDocument = (overrides: Partial<KnowledgeDocument> = {}): KnowledgeDocument => ({
  id: '1',
  title: 'Test Document',
  category: 'law',
  chunk_count: 10,
  created_at: '2024-03-09T00:00:00Z',
  ...overrides,
});

describe('DocumentCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock confirm to return true by default
    global.confirm = vi.fn(() => true);
    // Mock alert
    global.alert = vi.fn();
  });

  it('renders document title', () => {
    const doc = createMockDocument({ title: 'Contract Law Guide' });
    renderWithProviders(
      <DocumentCard document={doc} categoryLabel="法律法规" categoryColor="bg-blue-100 text-blue-800" />
    );

    expect(screen.getByText('Contract Law Guide')).toBeInTheDocument();
  });

  it('renders category badge when category exists', () => {
    const doc = createMockDocument({ category: 'law' });
    renderWithProviders(
      <DocumentCard document={doc} categoryLabel="法律法规" categoryColor="bg-blue-100 text-blue-800" />
    );

    expect(screen.getByText('法律法规')).toBeInTheDocument();
  });

  it('renders source when provided', () => {
    const doc = createMockDocument({ source: 'Supreme Court' });
    renderWithProviders(
      <DocumentCard document={doc} categoryLabel="法律法规" categoryColor="bg-blue-100 text-blue-800" />
    );

    expect(screen.getByText(/来源:/i)).toBeInTheDocument();
    expect(screen.getByText('Supreme Court')).toBeInTheDocument();
  });

  it('does not render source when not provided', () => {
    const doc = createMockDocument({ source: undefined });
    renderWithProviders(
      <DocumentCard document={doc} categoryLabel="法律法规" categoryColor="bg-blue-100 text-blue-800" />
    );

    expect(screen.queryByText(/来源:/i)).not.toBeInTheDocument();
  });

  it('renders chunk count', () => {
    const doc = createMockDocument({ chunk_count: 25 });
    renderWithProviders(
      <DocumentCard document={doc} categoryLabel="法律法规" categoryColor="bg-blue-100 text-blue-800" />
    );

    expect(screen.getByText('25 个知识块')).toBeInTheDocument();
  });

  it('renders formatted creation date', () => {
    const doc = createMockDocument({ created_at: '2024-03-09T14:30:00Z' });
    renderWithProviders(
      <DocumentCard document={doc} categoryLabel="法律法规" categoryColor="bg-blue-100 text-blue-800" />
    );

    expect(screen.getByText(/创建于/)).toBeInTheDocument();
    // Should contain date info
    const dateText = screen.getByText(/创建于/).textContent || '';
    expect(dateText).toContain('2024');
  });

  it('opens edit modal when edit button is clicked', () => {
    const doc = createMockDocument();
    renderWithProviders(
      <DocumentCard document={doc} categoryLabel="法律法规" categoryColor="bg-blue-100 text-blue-800" />
    );

    const editButton = screen.getByTitle('编辑');
    editButton.click();

    expect(screen.getByTestId('edit-modal')).toBeInTheDocument();
    expect(screen.getByText('Editing: Test Document')).toBeInTheDocument();
  });

  it('closes edit modal when close button is clicked', () => {
    const doc = createMockDocument();
    renderWithProviders(
      <DocumentCard document={doc} categoryLabel="法律法规" categoryColor="bg-blue-100 text-blue-800" />
    );

    const editButton = screen.getByTitle('编辑');
    editButton.click();

    const closeButton = screen.getByText('Close');
    closeButton.click();

    expect(screen.queryByTestId('edit-modal')).not.toBeInTheDocument();
  });

  it('shows confirm dialog before deleting', () => {
    const doc = createMockDocument({ title: 'Important Document' });
    renderWithProviders(
      <DocumentCard document={doc} categoryLabel="法律法规" categoryColor="bg-blue-100 text-blue-800" />
    );

    const deleteButton = screen.getByTitle('删除');
    deleteButton.click();

    expect(global.confirm).toHaveBeenCalledWith('确定要删除文档"Important Document"吗？此操作不可撤销。');
  });

  it('does not delete when confirm is cancelled', () => {
    global.confirm = vi.fn(() => false);
    const doc = createMockDocument();
    renderWithProviders(
      <DocumentCard document={doc} categoryLabel="法律法规" categoryColor="bg-blue-100 text-blue-800" />
    );

    const deleteButton = screen.getByTitle('删除');
    deleteButton.click();

    expect(mockDeleteDocument).not.toHaveBeenCalled();
  });

  it('deletes document when confirm is accepted', async () => {
    mockDeleteDocument.mockResolvedValue(undefined);
    const doc = createMockDocument();
    renderWithProviders(
      <DocumentCard document={doc} categoryLabel="法律法规" categoryColor="bg-blue-100 text-blue-800" />
    );

    const deleteButton = screen.getByTitle('删除');
    deleteButton.click();

    await waitFor(() => {
      expect(mockDeleteDocument).toHaveBeenCalledWith('1');
    });
  });

  it('shows alert when delete fails', async () => {
    mockDeleteDocument.mockRejectedValue(new Error('Delete failed'));
    const doc = createMockDocument();
    renderWithProviders(
      <DocumentCard document={doc} categoryLabel="法律法规" categoryColor="bg-blue-100 text-blue-800" />
    );

    const deleteButton = screen.getByTitle('删除');
    deleteButton.click();

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith('删除失败，请重试');
    });
  });

  it('disables delete button while deleting', async () => {
    mockDeleteDocument.mockImplementation(() => new Promise(() => {})); // Never resolves
    const doc = createMockDocument();
    renderWithProviders(
      <DocumentCard document={doc} categoryLabel="法律法规" categoryColor="bg-blue-100 text-blue-800" />
    );

    const deleteButton = screen.getByTitle('删除') as HTMLButtonElement;
    deleteButton.click();

    await waitFor(() => {
      expect(deleteButton).toBeDisabled();
    });
  });

  it('applies category color class to badge', () => {
    const doc = createMockDocument({ category: 'case' });
    renderWithProviders(
      <DocumentCard document={doc} categoryLabel="案例分析" categoryColor="bg-green-100 text-green-800" />
    );

    const badge = screen.getByText('案例分析');
    expect(badge).toHaveClass('bg-green-100', 'text-green-800');
  });

  it('handles documents without category', () => {
    const doc = createMockDocument({ category: undefined });
    renderWithProviders(
      <DocumentCard document={doc} categoryLabel="未分类" categoryColor="bg-gray-100 text-gray-800" />
    );

    expect(screen.getByText('未分类')).toBeInTheDocument();
  });

  it('renders action buttons with correct titles', () => {
    const doc = createMockDocument();
    renderWithProviders(
      <DocumentCard document={doc} categoryLabel="法律法规" categoryColor="bg-blue-100 text-blue-800" />
    );

    expect(screen.getByTitle('编辑')).toBeInTheDocument();
    expect(screen.getByTitle('删除')).toBeInTheDocument();
  });

  it('handles zero chunk count', () => {
    const doc = createMockDocument({ chunk_count: 0 });
    renderWithProviders(
      <DocumentCard document={doc} categoryLabel="法律法规" categoryColor="bg-blue-100 text-blue-800" />
    );

    expect(screen.getByText('0 个知识块')).toBeInTheDocument();
  });
});
