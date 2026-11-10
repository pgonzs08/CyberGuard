import { useState } from 'react';
import { createConversation, sendMessage, getConversations, getConversation} from '../services/conversationsService';
import type {Conversation, ConversationSummary} from '../model/datamodel';

export function useConversations(initialConversations: ConversationSummary[]) {
  const [conversations, setConversations] = useState<ConversationSummary[]>(initialConversations);
  const [activeId, setActiveId] = useState<string>(initialConversations[0]?.id || '');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [activeConversation, setActiveConversation] = useState<Conversation|null>(null);
  getConversations().then((value) => setConversations(value))

  getConversation(activeId).then((value) => setActiveConversation(value));

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
    activeConversation?.content.push(userMessage);

    setIsLoading(true);

    try {
      // 2. Llamada al servicio de FastAPI
      const botResponse = await sendMessage(userMessage, activeId);

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
    
    const newConv: ConversationSummary = {
      id: res.conversacion_id,
      name: 'Nueva Conversación',
      creation_date: new Date().toISOString().split('T')[0],
      last_msg: null
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