import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, 
  Menu, 
  MoreVertical, 
  Sparkles,
  User,
  Loader2
} from 'lucide-react';

interface Message {
  id: string;
  role: string;
  timetag: string;
  content: string;
}

interface Conversation {
  id: string;
  name: string;
  owner: string;
  creation_date: string;
  content: Message[];
}

interface ChatWindowProps {
  conversation: Conversation;
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
  onSendMessage: (text: string) => void;
  isLoading?: boolean;
}

export default function ChatWindow({
  conversation,
  isSidebarOpen,
  onToggleSidebar,
  onSendMessage,
  isLoading = false
}: ChatWindowProps) {
  const [inputText, setInputText] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;
    
    onSendMessage(inputText);
    setInputText('');
  };

  return (
  <main className="flex-1 flex flex-col bg-[var(--color-surface-bg)] relative overflow-hidden text-[var(--color-text-main)]">
    
    {/* -------------------- CABECERA DEL CHAT -------------------- */}
    <header className="h-16 border-b border-[var(--color-border-subtle)] bg-[var(--color-surface-card)]/50 backdrop-blur-md flex items-center justify-between px-6 z-10 shrink-0">
      <div className="flex items-center gap-4">
        {!isSidebarOpen && (
          <button 
            onClick={onToggleSidebar}
            className="p-2 rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-main)] hover:bg-[var(--color-border-subtle)]/40 transition-colors"
            title="Mostrar barra lateral"
          >
            <Menu className="h-5 w-5" />
          </button>
        )}
        <div>
          <h2 className="text-sm font-semibold text-[var(--color-text-main)]">
            {conversation?.name || 'Selecciona un chat'}
          </h2>
          <span className="text-xs text-[var(--color-success)] flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-success)] animate-pulse" />
            Dueño: {conversation?.owner || 'N/A'} | FastAPI Conectado
          </span>
        </div>
      </div>
      
      <div className="flex items-center gap-2">
        <button className="p-2 rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-main)] hover:bg-[var(--color-border-subtle)]/40 transition-colors">
          <MoreVertical className="h-5 w-5" />
        </button>
      </div>
    </header>

    {/* -------------------- LISTA DE MENSAJES (De arriba a abajo) -------------------- */}
    <div className="flex-1 overflow-y-auto p-6 space-y-6 flex flex-col custom-scrollbar">
      <AnimatePresence mode="popLayout">
        {conversation?.content?.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <motion.div 
              key={msg.id}
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.2, type: 'spring', stiffness: 400, damping: 25 }}
              className={`flex items-end gap-3 max-w-[75%] ${isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}
            >
              {/* Icono de Avatar */}
              <div className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 shadow-md ${
                isUser 
                  ? 'bg-[var(--color-primary-500)] text-white shadow-[var(--color-primary-500)]/20' 
                  : 'bg-[var(--color-surface-card)] text-[var(--color-text-muted)] border border-[var(--color-border-subtle)]'
              }`}>
                {isUser ? <User className="h-4 w-4" /> : <Sparkles className="h-4 w-4 text-[var(--color-primary-500)]" />}
              </div>

              {/* Burbuja de Contenido */}
              <div className={`p-4 rounded-2xl text-sm leading-relaxed shadow-sm ${
                isUser 
                  ? 'bg-[var(--color-primary-500)] text-white rounded-br-none shadow-[var(--color-primary-500)]/10' 
                  : 'bg-[var(--color-surface-card)] border border-[var(--color-border-subtle)] text-[var(--color-text-main)] rounded-bl-none backdrop-blur-md'
              }`}>
                <p className="whitespace-pre-wrap">{msg.content}</p>
                <span className={`text-[10px] block mt-1.5 text-right ${isUser ? 'text-[var(--color-primary-100)]' : 'text-[var(--color-text-muted)]'}`}>
                  {msg.timetag}
                </span>
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>

      {/* Indicador de carga si el bot está respondiendo */}
      {isLoading && (
        <motion.div 
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-3 mr-auto"
        >
          <div className="h-8 w-8 rounded-full bg-[var(--color-surface-card)] text-[var(--color-primary-500)] border border-[var(--color-border-subtle)] flex items-center justify-center shadow-md">
            <Sparkles className="h-4 w-4" />
          </div>
          <div className="p-4 rounded-2xl bg-[var(--color-surface-card)] border border-[var(--color-border-subtle)] text-[var(--color-text-muted)] text-sm flex items-center gap-2 rounded-bl-none backdrop-blur-md">
            <Loader2 className="h-4 w-4 animate-spin text-[var(--color-primary-500)]" />
            <span>Pensando respuesta...</span>
          </div>
        </motion.div>
      )}
    </div>

    {/* -------------------- FORMULARIO DE ENVÍO (Bottom Viewport) -------------------- */}
    <div className="p-4 bg-[var(--color-surface-bg)] border-t border-[var(--color-border-subtle)] shrink-0">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative flex items-center">
        <input 
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Escribe un mensaje orgánico e interactivo..."
          disabled={isLoading}
          className="w-full bg-[var(--color-surface-card)] border border-[var(--color-border-subtle)] rounded-2xl py-3.5 pl-4 pr-14 text-sm text-[var(--color-text-main)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-primary-500)] focus:ring-1 focus:ring-[var(--color-primary-500)] transition-all shadow-inner disabled:opacity-50"
        />
        <button 
          type="submit"
          disabled={isLoading || !inputText.trim()}
          className="absolute right-2 p-2.5 rounded-xl bg-[var(--color-primary-500)] hover:bg-[var(--color-primary-600)] text-white transition-all shadow-md shadow-[var(--color-primary-500)]/20 active:scale-95 flex items-center justify-center disabled:opacity-40 disabled:pointer-events-none"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>

  </main>
);
}