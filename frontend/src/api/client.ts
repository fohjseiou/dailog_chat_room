import axios from 'axios';
import { useAuthStore } from '../stores/authStore';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add auth token to headers
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor: Handle 401 errors by logging out
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token is invalid or expired - log out the user
      useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  }
);

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

// Auth Types
export interface User {
  id: string;
  username: string;
  created_at: string;
  last_login: string | null;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
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

  getMessages: async (sessionId: string): Promise<any[]> => {
    const response = await api.get<any[]>(`/sessions/${sessionId}/messages`);
    return response.data;
  },

  deleteMessage: async (sessionId: string, messageId: string): Promise<void> => {
    await api.delete(`/sessions/${sessionId}/messages/${messageId}`);
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

// Auth API
export const authApi = {
  login: async (credentials: LoginRequest): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/login', credentials);
    return response.data;
  },

  register: async (userData: RegisterRequest): Promise<User> => {
    const response = await api.post<User>('/auth/register', userData);
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },
};
