import { ChatRequest } from './client';

export interface StreamChunk {
  event: string;
  data: any;
}

export interface ChatStreamEvents {
  session_id?: string;
  intent?: string;
  context?: { sources: Array<{ title: string; score: number }> };
  token?: { chunk: string; full_response: string };
  end?: { response: string };
  error?: { error: string };
}

export async function* streamChat(
  request: ChatRequest,
  apiBaseUrl: string = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
): AsyncGenerator<StreamChunk> {
  const url = `${apiBaseUrl}/api/v1/chat/stream`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('No response body');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process SSE events
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;

        if (line.startsWith('event:')) {
          const event = line.substring(6).trim();
          // Look for the next data line
          i++;
          if (i < lines.length && lines[i].startsWith('data:')) {
            const dataLine = lines[i].substring(5).trim();
            try {
              const data = JSON.parse(dataLine);
              yield { event, data };
            } catch (e) {
              console.error('Failed to parse SSE data:', dataLine, e);
            }
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export class ChatStreamManager {
  private abortController: AbortController | null = null;

  async *stream(request: ChatRequest): AsyncGenerator<StreamChunk> {
    this.abortController = new AbortController();

    try {
      const url = `${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/api/v1/chat/stream`;

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
        signal: this.abortController.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';
      let currentEvent = '';

      try {
        while (true) {
          const { done, value } = await reader.read();

          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            if (!line) continue;

            if (line.startsWith('event:')) {
              currentEvent = line.substring(6).trim();
            } else if (line.startsWith('data:')) {
              const dataLine = line.substring(5).trim();
              try {
                const data = JSON.parse(dataLine);
                yield { event: currentEvent, data };
              } catch (e) {
                console.error('Failed to parse SSE data:', dataLine, e);
              }
              currentEvent = '';
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Stream aborted');
      } else {
        throw error;
      }
    }
  }

  abort() {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }
}
