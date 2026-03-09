import { create } from 'zustand';
import { chatApi, ChatRequest } from '../api/client';
import { ChatStreamManager, StreamChunk } from '../api/streamingClient';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Array<{
    title: string;
    score: number;
  }>;
  streaming?: boolean;
  intent?: string;
  retrievedDocs?: Array<{
    title: string;
    score: number;
  }>;
}

interface ThinkingState {
  stage: 'idle' | 'routing' | 'retrieving' | 'generating' | 'done' | 'error';
  intent?: string;
  retrievedDocs?: Array<{ title: string; score: number }>;
}

interface ChatState {
  sessionId: string | null;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  thinking: ThinkingState;
  useStreaming: boolean;

  sendMessage: (message: string) => Promise<void>;
  sendMessageStream: (message: string) => Promise<void>;
  loadMessages: (sessionId: string) => Promise<void>;
  setSessionId: (id: string | null) => void;
  clearMessages: () => void;
  setUseStreaming: (use: boolean) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessionId: null,
  messages: [],
  isLoading: false,
  error: null,
  thinking: {
    stage: 'idle',
  },
  useStreaming: true, // Default to streaming

  setSessionId: (id) => set({ sessionId: id }),

  clearMessages: () => set({ messages: [], error: null, thinking: { stage: 'idle' } }),

  setUseStreaming: (use) => set({ useStreaming: use }),

  loadMessages: async (sessionId: string) => {
    set({ isLoading: true, error: null });
    try {
      const messages = await chatApi.getMessages(sessionId);
      set({
        messages: messages.map((m: any) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          timestamp: new Date(m.created_at),
          sources: m.msg_metadata?.sources || [],
          intent: m.msg_metadata?.intent,
        })),
        isLoading: false,
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '加载消息失败',
        isLoading: false,
      });
    }
  },

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

  sendMessageStream: async (content: string) => {
    set({ isLoading: true, error: null, thinking: { stage: 'routing' } });

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    set((state) => ({ messages: [...state.messages, userMessage] }));

    // Create placeholder for streaming response
    const assistantMessageId = (Date.now() + 1).toString();
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      streaming: true,
    };
    set((state) => ({ messages: [...state.messages, assistantMessage] }));

    const streamManager = new ChatStreamManager();
    const currentSessionId = get().sessionId;

    try {
      let fullResponse = '';
      let sources: Array<{ title: string; score: number }> = [];

      for await (const chunk of streamManager.stream({
        session_id: currentSessionId || undefined,
        message: content,
      })) {
        switch (chunk.event) {
          case 'session_id':
            if (!currentSessionId && chunk.data.session_id) {
              set({ sessionId: chunk.data.session_id });
            }
            break;

          case 'intent':
            set({
              thinking: {
                stage: 'retrieving',
                intent: chunk.data.intent,
              }
            });
            // Update message with intent
            set((state) => ({
              messages: state.messages.map(msg =>
                msg.id === assistantMessageId
                  ? { ...msg, intent: chunk.data.intent }
                  : msg
              )
            }));
            break;

          case 'context':
            set({
              thinking: {
                stage: 'generating',
                intent: get().thinking.intent,
                retrievedDocs: chunk.data.sources,
              }
            });
            sources = chunk.data.sources.map((s: any) => ({
              title: s.title,
              score: s.score
            }));
            // Update message with retrieved docs
            set((state) => ({
              messages: state.messages.map(msg =>
                msg.id === assistantMessageId
                  ? { ...msg, retrievedDocs: sources }
                  : msg
              )
            }));
            break;

          case 'token':
            fullResponse = chunk.data.full_response;
            set((state) => ({
              messages: state.messages.map(msg =>
                msg.id === assistantMessageId
                  ? { ...msg, content: fullResponse }
                  : msg
              )
            }));
            break;

          case 'end':
            fullResponse = chunk.data.response;
            set((state) => ({
              messages: state.messages.map(msg =>
                msg.id === assistantMessageId
                  ? {
                      ...msg,
                      content: fullResponse,
                      streaming: false,
                      sources: sources,
                    }
                  : msg
              ),
              thinking: { stage: 'done' },
              isLoading: false,
            }));
            break;

          case 'error':
            set({
              error: chunk.data.error || '处理请求时出错',
              thinking: { stage: 'error' },
              isLoading: false,
            });
            set((state) => ({
              messages: state.messages.map(msg =>
                msg.id === assistantMessageId
                  ? { ...msg, streaming: false }
                  : msg
              )
            }));
            break;
        }
      }
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '发送消息失败',
        thinking: { stage: 'error' },
        isLoading: false,
      });
      set((state) => ({
        messages: state.messages.map(msg =>
          msg.id === assistantMessageId
            ? { ...msg, streaming: false }
            : msg
        )
      }));
    }
  },
}));
