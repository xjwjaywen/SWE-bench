import type { ChatResponse, Conversation, Memory } from '../types';

const BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Conversations
  createConversation: (title?: string) =>
    request<Conversation>('/conversations', {
      method: 'POST',
      body: JSON.stringify({ title: title || 'New Conversation' }),
    }),

  listConversations: () => request<Conversation[]>('/conversations'),

  getConversation: (id: string) =>
    request<Conversation & { messages: any[] }>(`/conversations/${id}`),

  updateConversation: (id: string, title: string) =>
    request<Conversation>(`/conversations/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ title }),
    }),

  deleteConversation: (id: string) =>
    request<{ detail: string }>(`/conversations/${id}`, { method: 'DELETE' }),

  // Chat
  sendMessage: (conversationId: string, content: string) =>
    request<ChatResponse>(`/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    }),

  // Memory
  listMemories: () => request<Memory[]>('/memory'),

  deleteMemory: (id: string) =>
    request<{ detail: string }>(`/memory/${id}`, { method: 'DELETE' }),
};
