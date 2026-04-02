import { useEffect, useRef } from 'react';
import type { Message } from '../types';
import { InputArea } from './InputArea';
import { MessageBubble } from './MessageBubble';

interface Props {
  messages: Message[];
  loading: boolean;
  hasConversation: boolean;
  onSend: (content: string) => void;
  onCreate: () => void;
}

export function ChatArea({ messages, loading, hasConversation, onSend, onCreate }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (!hasConversation) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-gray-50 text-gray-400">
        <div className="text-4xl mb-4">📧</div>
        <h2 className="text-xl font-medium text-gray-600 mb-2">Email Search Assistant</h2>
        <p className="text-sm mb-6">Ask questions about your email history</p>
        <button
          onClick={onCreate}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition-colors"
        >
          Start a conversation
        </button>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-gray-50">
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-3xl mx-auto">
          {messages.length === 0 && (
            <div className="text-center text-gray-400 mt-20">
              <p className="text-sm">Send a message to start searching emails</p>
            </div>
          )}
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {loading && (
            <div className="flex justify-start mb-4">
              <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
                <div className="flex items-center gap-1">
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>
      <InputArea onSend={onSend} disabled={loading} />
    </div>
  );
}
