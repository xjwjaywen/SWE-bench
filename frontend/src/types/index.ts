export interface MessageSource {
  email_id: string;
  subject: string;
  from_: string;
  from_email?: string;
  date: string;
  attachments: string[];
  snippet: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  sources: MessageSource[];
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages?: Message[];
}

export interface ChatResponse {
  user_message: Message;
  assistant_message: Message;
}

export interface Memory {
  id: string;
  content: string;
  source_conversation_id: string | null;
  created_at: string;
}
