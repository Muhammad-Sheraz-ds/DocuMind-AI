import { useState, useRef, useEffect } from 'react';
import { FiSend, FiFileText, FiThumbsUp, FiThumbsDown } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import { askQuestion } from '../services/api';

export default function ChatPage() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(scrollToBottom, [messages]);

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const question = input.trim();
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: question }]);
        setLoading(true);

        try {
            const result = await askQuestion(question);
            setMessages(prev => [
                ...prev,
                {
                    role: 'assistant',
                    content: result.answer,
                    sources: result.sources || [],
                    confidence: result.confidence,
                    latency: result.latency_ms,
                    tokens: result.tokens_used,
                    flags: result.guardrail_flags || [],
                },
            ]);
        } catch (err) {
            let errorMsg = 'Could not connect to the API server.';

            if (err.response?.data?.detail) {
                const detail = err.response.data.detail;
                if (Array.isArray(detail)) {
                    // Handle FastAPI validation error list
                    errorMsg = detail.map(e => `${e.loc[e.loc.length - 1]}: ${e.msg}`).join(', ');
                } else {
                    errorMsg = detail;
                }
            } else if (err.message) {
                errorMsg = err.message;
            }

            setMessages(prev => [
                ...prev,
                {
                    role: 'assistant',
                    content: `⚠️ Error: ${errorMsg}`,
                    sources: [],
                },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <>
            <div className="page-header">
                <h2>💬 Ask Your Documents</h2>
                <p>Upload documents and ask questions — get AI-powered answers with source citations.</p>
            </div>

            <div className="chat-container">
                <div className="chat-messages">
                    {messages.length === 0 && (
                        <div className="empty-state">
                            <div className="empty-state-icon">📚</div>
                            <p>Upload a document, then ask questions about it.</p>
                            <p style={{ marginTop: 8, fontSize: '0.8rem' }}>
                                Powered by Groq (Llama 3.3 70B) • Hybrid Search • Guardrails
                            </p>
                        </div>
                    )}

                    {messages.map((msg, i) => (
                        <div key={i} className={`chat-message ${msg.role}`}>
                            <div className={`chat-avatar ${msg.role}`}>
                                {msg.role === 'user' ? '👤' : '🤖'}
                            </div>
                            <div>
                                <div className={`chat-bubble`}>
                                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                                </div>

                                {/* Resources */}
                                {msg.sources && msg.sources.length > 0 && (
                                    <div className="chat-sources">
                                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                                            Resources
                                        </div>
                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                            {msg.sources.map((src, j) => (
                                                <div key={j} className="source-chip" title={src.content}>
                                                    <FiFileText className="source-chip-icon" />
                                                    <span>
                                                        {src.document} {src.page && `• P.${src.page}`}
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Metrics */}
                                {msg.role === 'assistant' && msg.confidence !== undefined && (
                                    <div className="chat-metrics">
                                        <span>🎯 {(msg.confidence * 100).toFixed(0)}% confidence</span>
                                        <span>⚡ {msg.latency?.toFixed(0)}ms</span>
                                        <span>📝 {msg.tokens} tokens</span>
                                    </div>
                                )}

                                {/* Guardrail Flags */}
                                {msg.flags && msg.flags.length > 0 && (
                                    <div className="alert alert-info" style={{ marginTop: 8 }}>
                                        ⚠️ Flags: {msg.flags.join(', ')}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}

                    {loading && (
                        <div className="chat-message assistant">
                            <div className="chat-avatar assistant">🤖</div>
                            <div className="chat-bubble">
                                <div className="loading-dots">
                                    <span /><span /><span />
                                </div>
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>

                <div className="chat-input-area">
                    <div className="chat-input-wrapper">
                        <input
                            className="chat-input"
                            type="text"
                            placeholder="Ask a question about your documents..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            disabled={loading}
                        />
                        <button
                            className="chat-send-btn"
                            onClick={handleSend}
                            disabled={!input.trim() || loading}
                        >
                            {loading ? <span className="spinner" /> : <FiSend />}
                        </button>
                    </div>
                </div>
            </div>
        </>
    );
}
