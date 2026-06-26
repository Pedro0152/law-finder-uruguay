"use client";

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import styles from './page.module.css';
import globalStyles from '../page.module.css';

interface Source {
  documento: string;
  version: string;
  jerarquia: string;
  articulo: string;
  estado_vigencia: string;
  texto: string;
}

interface Message {
  role: 'user' | 'ai';
  content: string;
  sources?: Source[];
}

function ChatContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get('q');
  
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'ai',
      content: 'Hola. Soy el asistente jurídico de Law Finder Uruguay. Puedes hacerme preguntas sobre la legislación nacional vigente y te responderé citando las normas aplicables. ¿En qué te puedo ayudar hoy?'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [hasInitialized, setHasInitialized] = useState(false);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);

  const executeQuery = async (queryText: string) => {
    if (!queryText.trim()) return;

    setMessages(prev => [...prev, { role: 'user', content: queryText }]);
    setLoading(true);

    try {
      const res = await fetch('/api/internal/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: queryText })
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
      setMessages(prev => [...prev, {
        role: 'ai',
        content: 'Ocurrió un error al procesar tu solicitud. Por favor intenta de nuevo.'
      }]);
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialQuery && !hasInitialized) {
      setHasInitialized(true);
      executeQuery(initialQuery);
    }
  }, [initialQuery, hasInitialized]);

  const handleSend = () => {
    if (input.trim()) {
      const query = input.trim();
      setInput('');
      executeQuery(query);
    }
  };

  const openSourceModal = (sourceIndex: number, sources: Source[]) => {
    if (sources && sources[sourceIndex]) {
      setSelectedSource(sources[sourceIndex]);
      setIsModalOpen(true);
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
                  <ReactMarkdown
                    components={{
                      a: ({ node, ...props }) => {
                        const href = props.href || '';
                        if (href.startsWith('source:')) {
                          const index = parseInt(href.replace('source:', ''), 10);
                          return (
                            <a
                              href="#"
                              onClick={(e) => {
                                e.preventDefault();
                                openSourceModal(index, msg.sources || []);
                              }}
                              style={{ color: '#60a5fa', textDecoration: 'none', fontWeight: 'bold' }}
                              onMouseEnter={(e) => e.currentTarget.style.textDecoration = 'underline'}
                              onMouseLeave={(e) => e.currentTarget.style.textDecoration = 'none'}
                            >
                              {props.children}
                            </a>
                          );
                        }
                        return <a {...props} target="_blank" rel="noopener noreferrer" style={{ color: '#60a5fa' }} />;
                      }
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
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

      {/* Source Modal */}
      {isModalOpen && selectedSource && (
        <div className={styles.modalOverlay} onClick={() => setIsModalOpen(false)}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <button className={styles.closeBtn} onClick={() => setIsModalOpen(false)}>✕</button>
            <h2 className={styles.modalTitle}>{selectedSource.documento}</h2>
            <h3 className={styles.modalSubtitle}>{selectedSource.jerarquia} - {selectedSource.articulo}</h3>
            <div className={styles.modalText}>
              {selectedSource.texto}
            </div>
            <div className={styles.modalMeta}>
              <span>Vigencia: {selectedSource.estado_vigencia}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div style={{color: 'white', padding: '2rem'}}>Cargando chat...</div>}>
      <ChatContent />
    </Suspense>
  );
}
