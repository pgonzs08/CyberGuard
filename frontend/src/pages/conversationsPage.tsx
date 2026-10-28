import { useState } from 'react';
import Sidebar from '../components/sidebar';
import ChatWindow from '../components/chatWindow';
import { useConversations } from '../hooks/useConversations';

// Datos de prueba iniciales (Mock Data)
const INITIAL_DATA = [
  {
    id: '1',
    name: 'Diseño de Interfaz Orgánica',
    owner: 'user_123',
    creation_date: '2026-10-27',
    content: [
      { id: 'm1', role: 'assistant', timetag: '10:40 AM', content: '¡Hola! Estamos diseñando la nueva versión de la app.' },
      { id: 'm2', role: 'user', timetag: '10:41 AM', content: 'Genial, usaremos React, Tailwind y Motion.' },
      { id: 'm3', role: 'assistant', timetag: '10:42 AM', content: '¿Qué te parece este stack?' },
    ]
  }
];

export default function ConversationsPage() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Consumimos toda la lógica de negocio y llamadas a servicios desde el hook
  const {
    conversations,
    activeId,
    setActiveId,
    activeConversation,
    handleSendMessage,
    handleNewConversation,
    isLoading
  } = useConversations(INITIAL_DATA);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
      
      {/* Barra lateral de navegación */}
      <Sidebar 
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        conversations={conversations}
        activeId={activeId}
        onSelectConversation={setActiveId}
        onNewConversation={handleNewConversation}
      />

      {/* Ventana de Chat Principal */}
      <ChatWindow 
        conversation={activeConversation}
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen(true)}
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
      />

    </div>
  );
}