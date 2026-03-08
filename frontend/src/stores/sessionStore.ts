import { create } from 'zustand';
import { chatApi } from '../api/client';

interface Session {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

interface SessionState {
  sessions: Session[];
  isLoading: boolean;
  error: string | null;

  loadSessions: () => Promise<void>;
  deleteSession: (id: string) => Promise<void>;
}

export const useSessionStore = create<SessionState>((set) => ({
  sessions: [],
  isLoading: false,
  error: null,

  loadSessions: async () => {
    set({ isLoading: true, error: null });
    try {
      const sessions = await chatApi.getSessions();
      set({ sessions, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '加载会话失败',
        isLoading: false,
      });
    }
  },

  deleteSession: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      await chatApi.deleteSession(id);
      set((state) => ({
        sessions: state.sessions.filter((s) => s.id !== id),
        isLoading: false,
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '删除会话失败',
        isLoading: false,
      });
    }
  },
}));
