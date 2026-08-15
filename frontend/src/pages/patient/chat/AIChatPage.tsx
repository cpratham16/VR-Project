import { useState, useEffect, useRef } from 'react';
import { apiClient } from '../../../api/client';

interface Message {
  id: string;
  sender: 'user' | 'assistant' | 'system';
  content: string;
  risk_flag: boolean;
  rag_context_used: boolean;
  created_at: string;
}

export default function AIChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMsg, setInputMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const fetchHistory = async () => {
    try {
      const res = await apiClient.get('/patient/chat/history');
      setSessionId(res.data.id);
      setMessages(res.data.messages || []);
    } catch {
      // Fallback initial welcome
      setMessages([
        {
          id: 'welcome',
          sender: 'assistant',
          content: 'Hello! I am AURA, your campus AI wellness companion. I am here to listen and offer supportive guidance. (Note: I am an AI, not a therapist. If you feel in crisis, please use the Panic SOS button above.)',
          risk_flag: false,
          rag_context_used: false,
          created_at: new Date().toISOString()
        }
      ]);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMsg.trim() || loading) return;

    const userText = inputMsg.trim();
    setInputMsg('');
    
    // Optimistic user UI message
    const tempUserMsg: Message = {
      id: Date.now().toString(),
      sender: 'user',
      content: userText,
      risk_flag: false,
      rag_context_used: false,
      created_at: new Date().toISOString()
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setLoading(true);

    try {
      const res = await apiClient.post('/patient/chat', {
        message: userText,
        session_id: sessionId
      });
      setMessages((prev) => [...prev, res.data]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          sender: 'assistant',
          content: 'I am experiencing connection difficulties right now. Please know you are not alone. If you need immediate support, please press the Panic SOS button at the top of the screen.',
          risk_flag: false,
          rag_context_used: false,
          created_at: new Date().toISOString()
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-4 flex flex-col h-[calc(100vh-8rem)]">
      {/* Disclaimer Banner */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 mb-4 flex items-center gap-3">
        <span className="text-2xl">💡</span>
        <div className="text-xs text-amber-900">
          <strong>Non-Therapist Disclosure:</strong> AURA is an AI campus support companion. It is <em>not</em> a medical doctor or licensed therapist and cannot diagnose or prescribe treatment.
        </div>
      </div>

      {/* Chat Messages Box */}
      <div className="flex-1 bg-white rounded-2xl shadow border border-gray-100 p-4 overflow-y-auto space-y-4" role="log" aria-live="polite" aria-relevant="additions">
        {messages.length === 0 ? (
          <div className="text-center text-gray-600 py-12">
            Say hello to AURA to start your supportive conversation.
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div
                className={`max-w-xl rounded-2xl px-4 py-3 shadow-sm ${
                  msg.sender === 'user'
                    ? 'bg-blue-600 text-white rounded-br-none'
                    : 'bg-gray-100 text-gray-900 rounded-bl-none border border-gray-200'
                }`}
              >
                <div className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</div>
                {msg.rag_context_used && (
                  <div className="mt-1 text-[10px] opacity-75 italic flex items-center gap-1">
                    <span>✨ Clinical RAG dialogue exemplar merged</span>
                  </div>
                )}
              </div>
              <span className="text-[10px] text-gray-600 mt-1 px-1">
                {msg.sender === 'user' ? 'You' : 'AURA AI'}
              </span>
            </div>
          ))
        )}
        {loading && (
          <div className="flex items-center gap-2 text-sm text-gray-400 py-2">
            <span className="animate-spin">🌀</span> AURA is thinking...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <form onSubmit={handleSend} className="mt-4 flex gap-2">
        <label htmlFor="chat-input" className="sr-only">Message AURA</label>
        <input
          id="chat-input"
          type="text"
          value={inputMsg}
          onChange={(e) => setInputMsg(e.target.value)}
          placeholder="Type your message to AURA..."
          className="flex-1 bg-white border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm"
        />
        <button
          type="submit"
          disabled={loading || !inputMsg.trim()}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold px-6 py-3 rounded-xl shadow-md cursor-pointer flex items-center gap-2"
        >
          Send
        </button>
      </form>
    </div>
  );
}
