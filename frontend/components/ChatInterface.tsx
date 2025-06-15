import React, { useState, useRef, useEffect } from 'react';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  sources?: any[];
}

interface ChatInterfaceProps {
  documentId?: string;
}

export default function ChatInterface({ documentId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now() + '-user',
      type: 'user',
      content: input,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
      const res = await fetch(`${backendUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: input,
          document_id: documentId,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const assistantMessage: Message = {
          id: Date.now() + '-assistant',
          type: 'assistant',
          content: data.answer || 'No response.',
          sources: data.sources || [],
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + '-assistant',
            type: 'assistant',
            content: 'Sorry, there was an error processing your request.',
          },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + '-assistant',
          type: 'assistant',
          content: 'Network error. Please try again.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    // Send message on Enter key
    if (e.key === 'Enter' && !e.shiftKey && !isLoading) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="chat-interface">
      <div className="messages">
        {messages.length === 0 && (
          <div style={{ color: '#888', textAlign: 'center', marginTop: '2rem' }}>
            Start chatting about your document!
          </div>
        )}
        {messages.map((msg) => (
          <div className="message-item-container"
            key={msg.id}
            style={{
              alignItems: msg.type === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <div className="message-item"
              style={{
                maxWidth: msg.type === 'user' ? '80%' : '100%',
                background: msg.type === 'user' ? '#0070f3' : 'none',
                color: msg.type === 'user' ? '#fff' : '#222',
                boxShadow: msg.type === 'user' ? '0 2px 8px #0070f322' : 'none',
              }}
            >
              {msg.content}
            </div>
    
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyPress}
          disabled={isLoading}
          placeholder="Type your question..."
          style={{
            background: isLoading ? '#f3f3f3' : '#fff',
          }}
        />
        <button
          onClick={handleSendMessage}
          disabled={!input.trim() || isLoading}
          style={{
            cursor: isLoading ? 'not-allowed' : 'pointer',
            opacity: !input.trim() || isLoading ? 0.6 : 1,
          }}
        >
          {isLoading ? '...' : 'Send'}
        </button>
      </div>
    </div>
  );
}