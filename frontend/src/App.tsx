import { useState, useRef, useEffect, type FormEvent } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import './App.css'

interface Message {
  id: string
  rol: 'user' | 'assistant'
  contenido: string
  fecha_creacion: string
}

function App() {
  const [conversacionId, setConversacionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isInitializing, setIsInitializing] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  // 1. Al cargar la app, iniciamos una nueva conversación en el backend (POST /conversaciones)
  useEffect(() => {
    const iniciarSesion = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/conversaciones', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })

        if (!response.ok) throw new Error('No se pudo iniciar la sesión de chat')

        const data = await response.json()
        setConversacionId(data.conversacion_id)

        // Mensaje inicial de bienvenida en la interfaz
        setMessages([
          {
            id: 'welcome-msg',
            rol: 'assistant',
            contenido: '¡Hola! Soy el agente de IA de CyberGuard conectado mediante FastAPI. ¿En qué puedo ayudarte?',
            fecha_creacion: new Date().toISOString()
          }
        ])
      } catch (error) {
        console.warn('Backend no disponible, usando modo simulación local:', error)
        // Fallback local si el backend no está encendido
        setConversacionId('chat_simulado_local')
        setMessages([
          {
            id: 'welcome-msg',
            rol: 'assistant',
            contenido: '[Modo Simulación] Hola, no se pudo conectar con FastAPI en el puerto 8000. Revisa que esté activo.',
            fecha_creacion: new Date().toISOString()
          }
        ])
      } finally {
        setIsInitializing(false)
      }
    }

    iniciarSesion()
  }, [])

  // 2. Enviar mensaje usando la ruta POST /conversaciones/{conversacion_id}
  const handleSendMessage = async (e: FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading || !conversacionId) return

    const contenidoTexto = input.trim()
    setInput('')
    setIsLoading(true)

    // Si estamos en modo simulación local (sin backend real respondiendo)
    if (conversacionId === 'chat_simulado_local') {
      const ahora = new Date().toISOString()
      setTimeout(() => {
        const userMsg: Message = {
          id: Date.now().toString(),
          rol: 'user',
          contenido: contenidoTexto,
          fecha_creacion: ahora
        }
        const botMsg: Message = {
          id: (Date.now() + 1).toString(),
          rol: 'assistant',
          contenido: `Respuesta simulada a: "${contenidoTexto}"`,
          fecha_creacion: ahora
        }
        setMessages((prev) => [...prev, userMsg, botMsg])
        setIsLoading(false)
      }, 1000)
      return
    }

    try {
      // Petición ajustada al esquema exacto de tu API REST (`contenido` en el body)
      const response = await fetch(`http://localhost:8000/api/conversaciones/${conversacionId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ contenido: contenidoTexto }),
      })

      if (!response.ok) {
        throw new Error('Error al enviar el mensaje al servidor')
      }

      // La API devuelve un ConversacionResponse con { conversacion_id, mensaje_usuario, respuesta_bot }
      const data = await response.json()

      setMessages((prev) => [
        ...prev,
        data.mensaje_usuario,
        data.respuesta_bot
      ])
    } catch (error) {
      console.error('Error de red:', error)
      const errorMsg: Message = {
        id: Date.now().toString(),
        rol: 'assistant',
        contenido: '⚠️ Ocurrió un error al comunicarse con el servidor de FastAPI.',
        fecha_creacion: new Date().toISOString()
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="farm-chat-container">
      {/* Cabecera */}
      <header className="chat-header">
        <div className="header-info">
          <div className="logos-stack">
            <img src={viteLogo} className="logo-sm" alt="Vite" />
            <img src={reactLogo} className="logo-sm" alt="React" />
            <span className="badge-fastapi">CyberGuard AI</span>
          </div>
          <h2>Chat Bot (FARM Stack)</h2>
        </div>
        <div className="session-meta">
          {conversacionId && <span className="session-id">ID: {conversacionId}</span>}
          <span className="status-indicator">
            <span className="dot"></span> En línea
          </span>
        </div>
      </header>

      {/* Cuerpo de mensajes */}
      <div className="chat-messages">
        {isInitializing ? (
          <div className="loading-session">Conectando con el servidor de FastAPI...</div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`message-wrapper ${msg.rol === 'user' ? 'user-side' : 'ai-side'}`}
            >
              <div className={`message-bubble ${msg.rol === 'user' ? 'user' : 'ai'}`}>
                <p>{msg.contenido}</p>
                <span className="message-time">
                  {new Date(msg.fecha_creacion).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </div>
          ))
        )}

        {isLoading && (
          <div className="message-wrapper ai-side">
            <div className="message-bubble ai typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Formulario de entrada */}
      <form onSubmit={handleSendMessage} className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Escribe tu consulta de seguridad..."
          disabled={isLoading || isInitializing}
        />
        <button type="submit" disabled={isLoading || isInitializing || !input.trim()}>
          Enviar
        </button>
      </form>
    </div>
  )
}

export default App