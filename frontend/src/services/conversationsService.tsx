import type { Conversation, ConversationSummary, Message } from '../model/datamodel';

const API_BASE_URL = 'http://localhost:8000/api';
const CONVERSATIONS_URL = `${API_BASE_URL}/conversaciones`;

// ---- DTOs: forma exacta de las respuestas del backend ----
interface MessageAnswerDTO {
  id: string;
  role: string;
  content: string;
  timetag: string; // ISO 8601
}

interface ListConversationsDTO {
  conversations: ConversationSummary[];
}

interface CreateConversationDTO {
  id: string;
  mensaje: string;
}

interface SendMessageDTO {
  conversacion_id: string;
  respuesta_agente: MessageAnswerDTO;
}

interface HistorialDTO {
  conversacion_id: string;
  historial: MessageAnswerDTO[];
}

// ---- Utilidades ----
async function request<T>(url: string, errorMsg: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: options.body
      ? { 'Content-Type': 'application/json', ...options.headers }
      : options.headers,
  });

  if (!response.ok) {
    throw new Error(`${errorMsg}. Código HTTP: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

// Mongo suele devolver datetimes sin zona horaria; se asume UTC para que JS no los interprete como hora local.
function formatTime(timetag: string): string {
  const hasTimezone = /(Z|[+-]\d{2}:?\d{2})$/.test(timetag);
  const date = new Date(hasTimezone ? timetag : `${timetag}Z`);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function toMessage(dto: MessageAnswerDTO): Message {
  return {
    id: dto.id,
    role: dto.role as Message['role'],
    timetag: formatTime(dto.timetag),
    content: dto.content,
  };
}

// ---- API ----

/** GET /api/conversaciones/ */
export async function getConversations(): Promise<ConversationSummary[]> {
  const data = await request<ListConversationsDTO>(
    `${CONVERSATIONS_URL}/`,
    'Error al recuperar conversaciones'
  );
  return data.conversations;
}

/** POST /api/conversaciones/ (el backend genera el ID; no recibe body) */
export async function createConversation(): Promise<{ conversacion_id: string; mensaje: string }> {
  const data = await request<CreateConversationDTO>(
    `${CONVERSATIONS_URL}/`,
    'Error al crear la conversación',
    { method: 'POST' }
  );
  return { conversacion_id: data.id, mensaje: data.mensaje };
}

/** POST /api/conversaciones/{conversacion_id} */
export async function sendMessage(msg: string, conversation_id: string): Promise<Message> {
  const data = await request<SendMessageDTO>(
    `${CONVERSATIONS_URL}/${encodeURIComponent(conversation_id)}`,
    'Error al enviar mensaje',
    {
      method: 'POST',
      body: JSON.stringify({ content: msg }),
    }
  );
  return toMessage(data.respuesta_agente);
}

/** GET /api/conversaciones/{conversacion_id}?limite=N */
export async function getConversation(conversation_id: string, limite: number = 20): Promise<Conversation> {
  const data = await request<HistorialDTO>(
    `${CONVERSATIONS_URL}/${encodeURIComponent(conversation_id)}?limite=${limite}`,
    'Error al recuperar conversación'
  );

  // El endpoint solo devuelve el historial; name/owner/creation_date
  // están en ConversationSummary (getConversations).
  return {
    id: data.conversacion_id,
    name: '',
    owner: '',
    creation_date: '',
    content: data.historial.map(toMessage),
  };
}