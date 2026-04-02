import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Sidebar } from '../Sidebar';
import { MessageBubble } from '../MessageBubble';
import { SourceCard } from '../SourceCard';
import { InputArea } from '../InputArea';
import { ChatArea } from '../ChatArea';
import type { Conversation, Message, MessageSource } from '../../types';

const mockConversations: Conversation[] = [
  { id: '1', title: 'Test Conv 1', created_at: '2024-01-01', updated_at: '2024-01-01' },
  { id: '2', title: 'Test Conv 2', created_at: '2024-01-02', updated_at: '2024-01-02' },
];

const mockSource: MessageSource = {
  email_id: 'e1',
  subject: 'Q3 Sales Report',
  from_: 'Zhang San',
  from_email: 'zhang@test.com',
  date: '2024-10-15',
  attachments: ['report.xlsx', 'summary.pdf'],
  snippet: 'Please find attached...',
};

const mockUserMessage: Message = {
  id: 'm1',
  conversation_id: '1',
  role: 'user',
  content: 'Who sent the Q3 report?',
  sources: [],
  created_at: '2024-01-01T12:00:00Z',
};

const mockAssistantMessage: Message = {
  id: 'm2',
  conversation_id: '1',
  role: 'assistant',
  content: 'Zhang San sent the Q3 report.',
  sources: [mockSource],
  created_at: '2024-01-01T12:00:01Z',
};

// ---- F-01: 对话列表渲染 ----
describe('Sidebar', () => {
  it('renders conversation list', () => {
    render(
      <Sidebar
        conversations={mockConversations}
        activeId="1"
        onSelect={vi.fn()}
        onCreate={vi.fn()}
        onDelete={vi.fn()}
        onRename={vi.fn()}
      />,
    );
    expect(screen.getByText('Test Conv 1')).toBeInTheDocument();
    expect(screen.getByText('Test Conv 2')).toBeInTheDocument();
  });

  // ---- F-02: 新建对话按钮 ----
  it('calls onCreate when button clicked', () => {
    const onCreate = vi.fn();
    render(
      <Sidebar
        conversations={[]}
        activeId={null}
        onSelect={vi.fn()}
        onCreate={onCreate}
        onDelete={vi.fn()}
        onRename={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByText('+ New Conversation'));
    expect(onCreate).toHaveBeenCalledTimes(1);
  });

  // ---- F-05: 对话切换 ----
  it('calls onSelect when conversation clicked', () => {
    const onSelect = vi.fn();
    render(
      <Sidebar
        conversations={mockConversations}
        activeId={null}
        onSelect={onSelect}
        onCreate={vi.fn()}
        onDelete={vi.fn()}
        onRename={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByText('Test Conv 1'));
    expect(onSelect).toHaveBeenCalledWith('1');
  });
});

// ---- F-03: 发送消息 ----
describe('InputArea', () => {
  it('sends message on button click', () => {
    const onSend = vi.fn();
    render(<InputArea onSend={onSend} disabled={false} />);
    const textarea = screen.getByPlaceholderText('Ask about emails...');
    fireEvent.change(textarea, { target: { value: 'test message' } });
    fireEvent.click(screen.getByText('Send'));
    expect(onSend).toHaveBeenCalledWith('test message');
  });

  it('does not send empty message', () => {
    const onSend = vi.fn();
    render(<InputArea onSend={onSend} disabled={false} />);
    fireEvent.click(screen.getByText('Send'));
    expect(onSend).not.toHaveBeenCalled();
  });
});

// ---- F-04: 来源卡片 ----
describe('SourceCard', () => {
  it('renders source information', () => {
    render(<SourceCard source={mockSource} />);
    expect(screen.getByText('Q3 Sales Report')).toBeInTheDocument();
    expect(screen.getByText(/Zhang San/)).toBeInTheDocument();
    expect(screen.getByText(/2024-10-15/)).toBeInTheDocument();
  });

  it('renders attachment links', () => {
    render(<SourceCard source={mockSource} />);
    expect(screen.getByText('report.xlsx')).toBeInTheDocument();
    expect(screen.getByText('summary.pdf')).toBeInTheDocument();
  });
});

describe('MessageBubble', () => {
  it('renders user message', () => {
    render(<MessageBubble message={mockUserMessage} />);
    expect(screen.getByText('Who sent the Q3 report?')).toBeInTheDocument();
  });

  it('renders assistant message with sources', () => {
    render(<MessageBubble message={mockAssistantMessage} />);
    expect(screen.getByText('Zhang San sent the Q3 report.')).toBeInTheDocument();
    expect(screen.getByText('Q3 Sales Report')).toBeInTheDocument();
  });
});

// ---- F-06: 响应式 (ChatArea renders correctly) ----
describe('ChatArea', () => {
  it('shows empty state when no conversation selected', () => {
    render(
      <ChatArea
        messages={[]}
        loading={false}
        hasConversation={false}
        onSend={vi.fn()}
        onCreate={vi.fn()}
      />,
    );
    expect(screen.getByText('Email Search Assistant')).toBeInTheDocument();
    expect(screen.getByText('Start a conversation')).toBeInTheDocument();
  });

  it('renders messages', () => {
    render(
      <ChatArea
        messages={[mockUserMessage, mockAssistantMessage]}
        loading={false}
        hasConversation={true}
        onSend={vi.fn()}
        onCreate={vi.fn()}
      />,
    );
    expect(screen.getByText('Who sent the Q3 report?')).toBeInTheDocument();
    expect(screen.getByText('Zhang San sent the Q3 report.')).toBeInTheDocument();
  });
});
