import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  createConversation,
  sendMessage,
  getConversations,
  getConversation,
} from '../services/conversationsService';
import type { Conversation, ConversationSummary, Message } from '../model/datamodel';

const formatNow = () =>
  new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

export function useConversations() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeId, setActiveId] = useState<string>('');
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);

  const [isLoadingList, setIsLoadingList] = useState<boolean>(true);
  const [isLoadingConversation, setIsLoadingConversation] = useState<boolean>(false);
  const [isSending, setIsSending] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const refreshConversations = useCallback(async () => {
    try {
      setConversations(await getConversations());
    } catch (err) {
      console.error('Error al recuperar conversaciones:', err);
      setError('No se pudieron cargar las conversaciones.');
    }
  }, []);

  // Carga inicial de la lista (una sola vez)
  useEffect(() => {
    refreshConversations().finally(() => setIsLoadingList(false));
  }, [refreshConversations]);

  // Carga del historial cada vez que cambia la conversación activa
  useEffect(() => {
    if (!activeId) {
      setActiveConversation(null);
      return;
    }

    let cancelled = false; // evita que una respuesta antigua pise a la nueva
    setActiveConversation(null);
    setIsLoadingConversation(true);

    getConversation(activeId)
      .then((conv) => {
        if (cancelled) return;
        setActiveConversation(conv);
        setError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        console.error('Error al recuperar la conversación:', err);
        setError('No se pudo cargar la conversación.');
      })
      .finally(() => {
        if (!cancelled) setIsLoadingConversation(false);
      });

    return () => {
      cancelled = true;
    };
  }, [activeId]);

  // getConversation no devuelve name/creation_date: se toman del resumen
  const activeConversationView = useMemo<Conversation | null>(() => {
    if (!activeConversation) return null;
    const summary = conversations.find((c) => c.id === activeConversation.id);
    return summary
      ? { ...activeConversation, name: summary.name, creation_date: summary.creation_date }
      : activeConversation;
  }, [activeConversation, conversations]);

  const handleSendMessage = async (text: string) => {
    const content = text.trim();
    if (!content || !activeId || !activeConversation) return;

    const conversationId = activeId; // se fija por si el usuario cambia de conversación
    const userMessage: Message = {
      id: `tmp_${Date.now()}`,
      role: 'user',
      timetag: formatNow(),
      content,
    };

    // Solo modifica la conversación si sigue siendo la misma
    const updateIfSame = (fn: (msgs: Message[]) => Message[]) =>
      setActiveConversation((prev) =>
        prev && prev.id === conversationId ? { ...prev, content: fn(prev.content) } : prev
      );

    // 1. Actualización optimista (sin mutar el estado)
    updateIfSame((msgs) => [...msgs, userMessage]);
    setIsSending(true);
    setError(null);

    try {
      // 2. Llamada al backend
      const botResponse = await sendMessage(content, conversationId);

      // 3. Añadir la respuesta del bot
      updateIfSame((msgs) => [...msgs, botResponse]);

      // 4. Actualizar el resumen (último mensaje, etc.)
      refreshConversations();
    } catch (err) {
      console.error('Error al comunicarse con el backend:', err);
      // Revertir el mensaje optimista
      updateIfSame((msgs) => msgs.filter((m) => m.id !== userMessage.id));
      setError('No se pudo enviar el mensaje. Inténtalo de nuevo.');
    } finally {
      setIsSending(false);
    }
  };

  const handleNewConversation = async () => {
    try {
      const res = await createConversation();
      await refreshConversations(); // el backend es la fuente de verdad
      setActiveId(res.conversacion_id);
    } catch (err) {
      console.error('Error al crear la conversación:', err);
      setError('No se pudo crear la conversación.');
    }
  };

  return {
    conversations,
    activeId,
    setActiveId,
    activeConversation: activeConversationView,
    handleSendMessage,
    handleNewConversation,
    isLoading: isLoadingList || isLoadingConversation || isSending,
    isSending,
    error,
  };
}