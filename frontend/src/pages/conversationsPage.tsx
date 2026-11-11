import { useState } from 'react';
import Sidebar from '../components/sidebar';
import ChatWindow from '../components/chatWindow';
import { useConversations } from '../hooks/useConversations';

export default function ConversationsPage() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Toda la lógica de negocio y las llamadas a servicios viven en el hook
  const {
    conversations,
    activeId,
    setActiveId,
    activeConversation,
    handleSendMessage,
    handleNewConversation,
    isSending,
    error
  } = useConversations();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[var(--color-surface-bg)] text-[var(--color-text-main)] font-sans">

      {/* Barra lateral de navegación */}
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen((prev) => !prev)}
        conversations={conversations}
        activeId={activeId}
        onSelectConversation={setActiveId}
        onNewConversation={handleNewConversation}
      />

      {/* Ventana de chat principal (el contenedor permite superponer el aviso de error) */}
      <div className="relative flex flex-1 min-w-0">
        {error && (
          <div
            role="alert"
            className="absolute top-20 left-1/2 -translate-x-1/2 z-50 max-w-md px-4 py-2.5 rounded-xl border border-red-500/30 bg-red-500/10 text-red-400 text-sm shadow-lg backdrop-blur-md"
          >
            {error}
          </div>
        )}

        <ChatWindow
          conversation={activeConversation}
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={() => setIsSidebarOpen(true)}
          onSendMessage={handleSendMessage}
          isLoading={isSending}
        />
      </div>

    </div>
  );
}