import { create } from 'zustand';
import { chatApi, ChatRequest } from '../api/client';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Array<{
    title: string;
    score: number;
  }>;
}

interface ChatState {
  sessionId: string | null;
  messages: Message[];
  isLoading: boolean;
  error: string | null;

  sendMessage: (message: string) => Promise<void>;
  setSessionId: (id: string) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessionId: null,
  messages: [],
  isLoading: false,
  error: null,

  setSessionId: (id) => set({ sessionId: id }),

  clearMessages: () => set({ messages: [], error: null }),

  sendMessage: async (content: string) => {
    set({ isLoading: true, error: null });

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    set((state) => ({ messages: [...state.messages, userMessage] }));

    try {
      const currentSessionId = get().sessionId;
      const response = await chatApi.sendMessage({
        session_id: currentSessionId || undefined,
        message: content,
      });

      if (!currentSessionId && response.session_id) {
        set({ sessionId: response.session_id });
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        sources: response.sources.map(s => ({ title: s.title, score: s.score })),
      };
      set((state) => ({
        messages: [...state.messages, assistantMessage],
        isLoading: false,
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '发送消息失败',
        isLoading: false,
      });
    }
  },
}));
