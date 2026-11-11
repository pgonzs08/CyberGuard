export interface Conversation {
  id: string;
  name: string;
  owner: string;
  creation_date: string;
  content: Message[];
}

// Definimos las estructuras de datos basadas en tu backend y frontend
export interface Message {
  id: string;
  role: string; // 'user' o 'assistant'
  timetag: string;
  content: string;
}

export interface ConversationSummary {
  id: string;
  name: string;
  creation_date: string;
  last_msg: Message | null;
}
