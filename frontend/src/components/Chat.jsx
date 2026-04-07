import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Bot, Loader2 } from 'lucide-react';
import { sendChat } from '../api/client';

export default function Chat({ userId = 'demo_user' }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Hi! I am AutoRoutine. How can I help you manage your day?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async () => {
    if (!input.trim() || loading) return;
    
    const userMsg = input.trim();
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setInput('');
    setLoading(true);
    
    try {
      const { data } = await sendChat(userMsg, userId);
      setMessages(prev => [...prev, { role: 'assistant', text: data.response }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'error', text: 'Network Error: ' + e.message }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel chat-window">
      <div className="panel-header">
        <h2 className="panel-title">
          <div className="panel-icon-wrapper">
            <Bot size={22} color="var(--accent-primary)" strokeWidth={2.5} />
          </div>
          <span>Agent <span className="gradient-text">Orchestrator</span></span>
        </h2>
      </div>
      
      <div className="panel-content">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.role === 'assistant' ? (
              <ReactMarkdown>{m.text}</ReactMarkdown>
            ) : (
              m.text
            )}
          </div>
        ))}
        {loading && (
          <div className="msg assistant flex-row" style={{ alignSelf: 'flex-start' }}>
            <Loader2 className="animate-spin-slow" size={16} color="var(--accent-primary)" />
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Working...</span>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="chat-input-wrapper">
        <input 
          className="chat-input-field"
          value={input} 
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          placeholder="Ask AutoRoutine to schedule, take notes, or show insights..." 
          disabled={loading}
          autoFocus
        />
        <button 
          className="btn-primary" 
          onClick={send} 
          disabled={loading || !input.trim()}
          style={{ width: '50px', height: '50px', borderRadius: '50%', padding: 0 }}
        >
          {loading ? <Loader2 className="animate-spin-slow" size={20} /> : <Send size={20} style={{ marginLeft: '2px' }} />}
        </button>
      </div>
    </div>
  );
}
