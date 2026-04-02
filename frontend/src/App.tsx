import { ChatArea } from './components/ChatArea';
import { Sidebar } from './components/Sidebar';
import { useChat } from './hooks/useChat';

function App() {
  const {
    conversations,
    activeId,
    messages,
    loading,
    selectConversation,
    createConversation,
    deleteConversation,
    renameConversation,
    sendMessage,
  } = useChat();

  return (
    <div className="flex h-screen bg-white">
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={selectConversation}
        onCreate={createConversation}
        onDelete={deleteConversation}
        onRename={renameConversation}
      />
      <ChatArea
        messages={messages}
        loading={loading}
        hasConversation={activeId !== null}
        onSend={sendMessage}
        onCreate={createConversation}
      />
    </div>
  );
}

export default App;
