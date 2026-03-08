import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

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

export interface Session {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

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
