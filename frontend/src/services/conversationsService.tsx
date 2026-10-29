// Definimos las estructuras de datos basadas en tu backend y frontend
export interface Message {
  id: string;
  role: string; // 'user' o 'assistant'
  timetag: string;
  content: string;
}

export interface Conversation {
  id: string;
  name: string;
  owner: string;
  creation_date: string;
  content: Message[];
}

// URL base de tu backend FastAPI
const API_BASE_URL = 'http://localhost:8000/api';

/**
 * Crea una nueva conversación en el backend.
 * POST /api/conversaciones
 */
export async function createConversation(ownerId: string = 'user_123', name: string = 'Nueva Conversación'): Promise<{ conversacion_id: string; mensaje: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/conversaciones/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name,
        owner: ownerId,
        creation_date: new Date().toISOString().split('T')[0],
        content: []
      }),
    });

    if (response.status !== 201) {
      throw new Error(`Error al crear la conversación. Código HTTP: ${response.status}`);
    }

    const data = await response.json();
    return data; // Espera { conversacion_id: string, mensaje: string }
  } catch (error) {
    console.error('Error en createConversation:', error);
    // Modo simulación de respaldo (Fallback) por si FastAPI no está levantado aún
    return {
      conversacion_id: Date.now().toString(),
      mensaje: "Sesión de chat iniciada (Simulado)"
    };
  }
}

/**
 * Envia un mensaje a una conversación específica y recibe la respuesta del bot.
 * POST /api/conversaciones/{conversacion_id}
 */
export async function sendMessage(msg: string, conversation_id: string): Promise<Message> {
  try {
    const response = await fetch(`${API_BASE_URL}/conversaciones/${conversation_id}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content: msg,
        timetag: new Date().toISOString()
      }),
    });

    if (!response.ok) {
      throw new Error(`Error al enviar mensaje. Código HTTP: ${response.status}`);
    }

    const data = await response.json();
    
    // Mapeamos la respuesta del backend al formato que consume tu frontend
    // El backend devuelve: { "respuesta_bot": { id, rol, contenido, fecha_creacion } }
    const botMsg = data.respuesta_bot || data;

    return {
      id: botMsg.id || Date.now().toString(),
      role: botMsg.rol || 'assistant',
      timetag: new Date(botMsg.fecha_creacion || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      content: botMsg.contenido || botMsg.content || 'Respuesta vacía del bot'
    };

  } catch (error) {
    console.error('Error en sendMessage:', error);
    
    // Modo simulación inteligente de respaldo para desarrollo local fluido
    return {
      id: 'msg_bot_' + Date.now(),
      role: 'assistant',
      timetag: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      content: `[Simulación FastAPI] Recibí tu mensaje: "${msg}". Todo funciona correctamente en el frontend.`
    };
  }
}