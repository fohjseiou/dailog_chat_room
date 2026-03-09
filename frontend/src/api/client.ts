import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Chat Types
export interface ChatRequest {
  session_id?: string;
  message: string;
}

export interface ChatResponse {
  session_id: string;
  response: string;
  sources: Array<{
    title: string;
    score: number;
  }>;
}

// Session Types
export interface Session {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

// Knowledge Types
export interface KnowledgeDocument {
  id: string;
  title: string;
  category: 'law' | 'case' | 'contract' | 'interpretation' | null;
  source: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  documents: KnowledgeDocument[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface KnowledgeStats {
  total_documents: number;
  total_chunks: number;
  categories: Record<string, number>;
  chroma_collection_count: number;
  valid_categories: string[];
}

export interface DocumentUploadParams {
  title: string;
  category?: string;
  source?: string;
  file: File;
}

// Chat API
export const chatApi = {
  sendMessage: async (data: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/chat', data);
    return response.data;
  },

  getSessions: async (): Promise<Session[]> => {
    const response = await api.get<Session[]>('/sessions');
    return response.data;
  },

  getSession: async (id: string): Promise<Session> => {
    const response = await api.get<Session>(`/sessions/${id}`);
    return response.data;
  },

  deleteSession: async (id: string) => {
    await api.delete(`/sessions/${id}`);
  },
};

// Knowledge API
export const knowledgeApi = {
  getDocuments: async (params?: {
    page?: number;
    page_size?: number;
    search?: string;
    category?: string;
  }): Promise<DocumentListResponse> => {
    const response = await api.get<DocumentListResponse>('/knowledge/documents', { params });
    return response.data;
  },

  uploadDocument: async (params: DocumentUploadParams): Promise<KnowledgeDocument> => {
    const formData = new FormData();
    formData.append('file', params.file);
    formData.append('title', params.title);
    if (params.category) formData.append('category', params.category);
    if (params.source) formData.append('source', params.source);

    const response = await api.post<KnowledgeDocument>('/knowledge/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  getDocument: async (id: string): Promise<KnowledgeDocument> => {
    const response = await api.get<KnowledgeDocument>(`/knowledge/documents/${id}`);
    return response.data;
  },

  updateDocument: async (id: string, data: Partial<Pick<KnowledgeDocument, 'title' | 'category' | 'source'>>): Promise<KnowledgeDocument> => {
    const response = await api.put<KnowledgeDocument>(`/knowledge/documents/${id}`, data);
    return response.data;
  },

  deleteDocument: async (id: string): Promise<void> => {
    await api.delete(`/knowledge/documents/${id}`);
  },

  getStats: async (): Promise<KnowledgeStats> => {
    const response = await api.get<KnowledgeStats>('/knowledge/stats');
    return response.data;
  },
};
