import { motion } from 'framer-motion';
import { 
  PanelLeftClose, 
  Plus, 
  Search, 
  Sparkles 
} from 'lucide-react';

// Reutilizamos la misma estructura de tipos basada en Pydantic
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

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  conversations: Conversation[];
  activeId: string;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
}

export default function Sidebar({
  isOpen,
  onToggle,
  conversations,
  activeId,
  onSelectConversation,
  onNewConversation
}: SidebarProps) {
  return (
  <motion.aside
    initial={false}
    animate={{ width: isOpen ? '320px' : '0px', opacity: isOpen ? 1 : 0 }}
    transition={{ type: 'spring', stiffness: 350, damping: 30 }}
    className="relative flex flex-col border-r border-[var(--color-border-subtle)] bg-[var(--color-surface-card)] backdrop-blur-xl overflow-hidden z-40 shrink-0 text-[var(--color-text-main)] shadow-2xl"
  >
    {/* Cabecera del Sidebar */}
    <div className="flex items-center justify-between p-4 border-b border-[var(--color-border-subtle)] min-w-[320px]">
      <div className="flex items-center gap-2">
        <div className="h-8 w-8 rounded-xl bg-gradient-to-tr from-[var(--color-primary-500)] to-[var(--color-primary-900)] flex items-center justify-center shadow-lg shadow-[var(--color-primary-500)]/20">
          <Sparkles className="h-4 w-4 text-white" />
        </div>
        <span className="font-semibold tracking-tight text-[var(--color-text-main)]">Espacio Creativo</span>
      </div>
      <button 
        onClick={onToggle}
        className="p-2 rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-main)] hover:bg-[var(--color-border-subtle)]/40 transition-colors"
        title="Cerrar barra lateral"
      >
        <PanelLeftClose className="h-5 w-5" />
      </button>
    </div>

    {/* Botón Nueva Conversación */}
    <div className="p-4 min-w-[320px]">
      <button 
        onClick={onNewConversation}
        className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-[var(--color-primary-500)] hover:bg-[var(--color-primary-600)] text-white font-medium text-sm transition-all shadow-lg shadow-[var(--color-primary-500)]/20 active:scale-[0.98]"
      >
        <Plus className="h-4 w-4" />
        <span>Nuevo Chat</span>
      </button>
    </div>

    {/* Buscador interno */}
    <div className="px-4 pb-2 min-w-[320px]">
      <div className="relative">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-[var(--color-text-muted)]" />
        <input 
          type="text" 
          placeholder="Buscar conversaciones..." 
          className="w-full bg-[var(--color-surface-bg)] border border-[var(--color-border-subtle)] rounded-xl pl-9 pr-4 py-2 text-sm text-[var(--color-text-main)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-primary-500)] transition-colors"
        />
      </div>
    </div>

    {/* Lista de Conversaciones */}
    <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1 min-w-[320px] custom-scrollbar">
      {conversations.map(conv => {
        const isActive = conv.id === activeId;
        const lastMsg = conv.content[conv.content.length - 1]?.content || 'Sin mensajes aún...';
        
        return (
          <button
            key={conv.id}
            onClick={() => onSelectConversation(conv.id)}
            className={`w-full text-left p-3 rounded-xl transition-all flex flex-col gap-1 relative group ${
              isActive 
                ? 'bg-[var(--color-primary-500)]/10 border border-[var(--color-primary-500)]/30 text-[var(--color-text-main)]' 
                : 'hover:bg-[var(--color-border-subtle)]/40 text-[var(--color-text-muted)] hover:text-[var(--color-text-main)] border border-transparent'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className={`text-sm font-medium truncate ${isActive ? 'text-[var(--color-primary-500)]' : 'text-[var(--color-text-main)]'}`}>
                {conv.name}
              </span>
              <span className="text-[10px] text-[var(--color-text-muted)]">{conv.creation_date}</span>
            </div>
            <p className="text-xs text-[var(--color-text-muted)] truncate pr-4">{lastMsg}</p>
          </button>
        );
      })}
    </div>
  </motion.aside>
)};