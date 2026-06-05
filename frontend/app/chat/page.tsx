"use client";

import { useState } from 'react';
import styles from './page.module.css';
import globalStyles from '../page.module.css';

interface Message {
  role: 'user' | 'ai';
  content: string;
  sources?: { norma: string; articulo: string }[];
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'ai',
      content: 'Hola. Soy el asistente jurídico de Law Finder Uruguay. Puedes hacerme preguntas sobre la legislación nacional vigente y te responderé citando las normas aplicables. ¿En qué te puedo ayudar hoy?'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userQuery = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userQuery }]);
    setLoading(true);

    try {
      const res = await fetch('/api/internal/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: userQuery })
      });

      if (!res.ok) {
        throw new Error('Error al conectar con la API.');
      }

      const data = await res.json();
      
      setMessages(prev => [...prev, {
        role: 'ai',
        content: data.answer,
        sources: data.sources || []
      }]);
      setLoading(false);
      
    } catch (error) {
      console.error(error);
      setLoading(false);
    }
  };

  return (
    <div className={styles.main}>
      {/* Navbar Minimalista */}
      <nav className={globalStyles.nav}>
        <div className={globalStyles.navContainer}>
          <a href="/" className={globalStyles.logoArea}>
            <div className={globalStyles.logoIcon}>L</div>
            <span className={globalStyles.logoText}>Law Finder <span>Chat</span></span>
          </a>
        </div>
      </nav>

      <div className={styles.chatContainer}>
        <div className={styles.messagesArea}>
          {messages.map((msg, idx) => (
            <div key={idx} className={msg.role === 'user' ? styles.userMsgWrapper : styles.aiMsgWrapper}>
              {msg.role === 'user' ? (
                <div className={styles.userMsg}>{msg.content}</div>
              ) : (
                <div className={styles.aiMsg}>
                  {msg.content}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className={styles.sourcesArea}>
                      {msg.sources.map((src, i) => (
                        <div key={i} className={styles.sourceTag}>
                          {src.norma} - {src.articulo}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className={styles.aiMsgWrapper}>
              <div className={styles.aiMsg}>
                <span className={globalStyles.pulseDot} style={{ display: 'inline-block', marginRight: '8px' }}></span>
                Buscando normativa y redactando respuesta...
              </div>
            </div>
          )}
        </div>

        <div className={styles.inputWrapper}>
          <textarea 
            className={styles.chatInput}
            placeholder="Pregunta sobre normativa uruguaya..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            rows={1}
          />
          <button 
            className={styles.sendBtn}
            onClick={handleSend}
            disabled={loading || !input.trim()}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
