import { useState } from 'react';
import type { Conversation } from '../types';

interface Props {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
  onRename: (id: string, title: string) => void;
}

export function Sidebar({ conversations, activeId, onSelect, onCreate, onDelete, onRename }: Props) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [contextMenu, setContextMenu] = useState<{ id: string; x: number; y: number } | null>(null);

  const handleContextMenu = (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    setContextMenu({ id, x: e.clientX, y: e.clientY });
  };

  const handleRenameStart = (conv: Conversation) => {
    setEditingId(conv.id);
    setEditTitle(conv.title);
    setContextMenu(null);
  };

  const handleRenameSubmit = (id: string) => {
    if (editTitle.trim()) {
      onRename(id, editTitle.trim());
    }
    setEditingId(null);
  };

  return (
    <div className="w-64 bg-gray-900 text-white flex flex-col h-full">
      <div className="p-3">
        <button
          onClick={onCreate}
          className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
        >
          + New Conversation
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {conversations.map((conv) => (
          <div
            key={conv.id}
            className={`px-3 py-2 mx-2 rounded-lg cursor-pointer text-sm truncate mb-0.5 ${
              activeId === conv.id ? 'bg-gray-700' : 'hover:bg-gray-800'
            }`}
            onClick={() => onSelect(conv.id)}
            onContextMenu={(e) => handleContextMenu(e, conv.id)}
          >
            {editingId === conv.id ? (
              <input
                autoFocus
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                onBlur={() => handleRenameSubmit(conv.id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleRenameSubmit(conv.id);
                  if (e.key === 'Escape') setEditingId(null);
                }}
                className="w-full bg-gray-600 text-white px-1 rounded outline-none text-sm"
                onClick={(e) => e.stopPropagation()}
              />
            ) : (
              conv.title
            )}
          </div>
        ))}
      </div>

      {/* Context menu */}
      {contextMenu && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setContextMenu(null)} />
          <div
            className="fixed z-50 bg-gray-800 border border-gray-600 rounded-lg shadow-lg py-1 min-w-[120px]"
            style={{ left: contextMenu.x, top: contextMenu.y }}
          >
            <button
              className="w-full text-left px-3 py-1.5 text-sm hover:bg-gray-700"
              onClick={() => {
                const conv = conversations.find((c) => c.id === contextMenu.id);
                if (conv) handleRenameStart(conv);
              }}
            >
              Rename
            </button>
            <button
              className="w-full text-left px-3 py-1.5 text-sm hover:bg-gray-700 text-red-400"
              onClick={() => {
                onDelete(contextMenu.id);
                setContextMenu(null);
              }}
            >
              Delete
            </button>
          </div>
        </>
      )}
    </div>
  );
}
