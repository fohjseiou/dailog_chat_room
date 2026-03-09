import { create } from 'zustand';
import { knowledgeApi, KnowledgeDocument, DocumentListResponse, KnowledgeStats } from '../api/client';

interface KnowledgeState {
  documents: KnowledgeDocument[];
  stats: KnowledgeStats | null;
  loading: boolean;
  error: string | null;
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
  filters: {
    search: string;
    category: string;
  };

  fetchDocuments: (page?: number) => Promise<void>;
  uploadDocument: (file: File, title: string, category?: string, source?: string) => Promise<void>;
  deleteDocument: (id: string) => Promise<void>;
  updateDocument: (id: string, data: Partial<KnowledgeDocument>) => Promise<void>;
  fetchStats: () => Promise<void>;
  setSearch: (search: string) => void;
  setCategory: (category: string) => void;
  clearError: () => void;
}

export const useKnowledgeStore = create<KnowledgeState>((set, get) => ({
  documents: [],
  stats: null,
  loading: false,
  error: null,
  pagination: {
    page: 1,
    pageSize: 20,
    total: 0,
    totalPages: 0,
  },
  filters: {
    search: '',
    category: '',
  },

  fetchDocuments: async (page = 1) => {
    set({ loading: true, error: null });
    try {
      const { search, category } = get().filters;
      const response = await knowledgeApi.getDocuments({
        page,
        page_size: get().pagination.pageSize,
        search: search || undefined,
        category: category || undefined,
      });

      set({
        documents: response.documents,
        pagination: {
          page: response.page,
          pageSize: response.page_size,
          total: response.total,
          totalPages: response.total_pages,
        },
        loading: false,
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '获取文档列表失败',
        loading: false,
      });
    }
  },

  uploadDocument: async (file: File, title: string, category?: string, source?: string) => {
    set({ loading: true, error: null });
    try {
      await knowledgeApi.uploadDocument({ file, title, category, source });
      // Refresh documents
      await get().fetchDocuments(get().pagination.page);
      // Refresh stats
      await get().fetchStats();
      set({ loading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '上传文档失败',
        loading: false,
      });
      throw error;
    }
  },

  deleteDocument: async (id: string) => {
    set({ loading: true, error: null });
    try {
      await knowledgeApi.deleteDocument(id);
      // Refresh documents
      await get().fetchDocuments(get().pagination.page);
      // Refresh stats
      await get().fetchStats();
      set({ loading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '删除文档失败',
        loading: false,
      });
      throw error;
    }
  },

  updateDocument: async (id: string, data: Partial<KnowledgeDocument>) => {
    set({ loading: true, error: null });
    try {
      await knowledgeApi.updateDocument(id, data);
      // Refresh documents
      await get().fetchDocuments(get().pagination.page);
      set({ loading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '更新文档失败',
        loading: false,
      });
      throw error;
    }
  },

  fetchStats: async () => {
    try {
      const stats = await knowledgeApi.getStats();
      set({ stats });
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  },

  setSearch: (search: string) => {
    set({ filters: { ...get().filters, search }, pagination: { ...get().pagination, page: 1 } });
    get().fetchDocuments(1);
  },

  setCategory: (category: string) => {
    set({ filters: { ...get().filters, category }, pagination: { ...get().pagination, page: 1 } });
    get().fetchDocuments(1);
  },

  clearError: () => set({ error: null }),
}));
