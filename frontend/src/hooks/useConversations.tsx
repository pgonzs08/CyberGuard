import { useState } from 'react';
import { createConversation, sendMessage} from '../services/conversationsService';
import type {Conversation} from '../services/conversationsService';

export function useConversations(initialConversations: Conversation[]) {
  const [conversations, setConversations] = useState<Conversation[]>(initialConversations);
  const [activeId, setActiveId] = useState<string>(initialConversations[0]?.id || '');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const activeConversation = conversations.find(c => c.id === activeId) || conversations[0];

  // Enviar mensaje utilizando el servicio
  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;

    const userMsgId = Date.now().toString();
    const userMessage = {
      id: userMsgId,
      role: 'user',
      timetag: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      content: text
    };

    // 1. Actualización optimista en el cliente
    setConversations(prev => prev.map(conv => 
      conv.id === activeId ? { ...conv, content: [...conv.content, userMessage] } : conv
    ));

    setIsLoading(true);

    try {
      // 2. Llamada al servicio de FastAPI
      const botResponse = await sendMessage(text, activeId);

      // 3. Añadir la respuesta del bot
      setConversations(prev => prev.map(conv => 
        conv.id === activeId ? { ...conv, content: [...conv.content, botResponse] } : conv
      ));
    } catch (error) {
      console.error("Error al comunicarse con el backend:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Crear nueva conversación usando el servicio
  const handleNewConversation = async () => {
    const res = await createConversation('user_123', 'Nueva Conversación');
    
    const newConv: Conversation = {
      id: res.conversacion_id,
      name: 'Nueva Conversación',
      owner: 'user_123',
      creation_date: new Date().toISOString().split('T')[0],
      content: []
    };

    setConversations(prev => [newConv, ...prev]);
    setActiveId(res.conversacion_id);
  };

  return {
    conversations,
    activeId,
    setActiveId,
    activeConversation,
    handleSendMessage,
    handleNewConversation,
    isLoading
  };
}