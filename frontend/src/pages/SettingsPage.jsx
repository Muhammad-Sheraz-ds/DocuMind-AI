import { useState, useEffect } from 'react';
import { getHealth } from '../services/api';

export default function SettingsPage() {
    const [health, setHealth] = useState(null);

    useEffect(() => {
        getHealth().then(setHealth);
    }, []);

    return (
        <>
            <div className="page-header">
                <h2>⚙️ System Settings</h2>
                <p>Configuration, service status, and system information.</p>
            </div>

            {/* Service Status */}
            <div className="card" style={{ marginBottom: 24 }}>
                <div className="card-header">
                    <span className="card-title">Service Status</span>
                </div>
                {health ? (
                    <div className="metrics-grid">
                        {Object.entries(health.services || {}).map(([service, status]) => (
                            <div key={service} className="metric-card">
                                <div className="metric-label">
                                    <span className={`status-dot ${status === 'connected' ? '' : 'offline'}`} />
                                    {service.replace('_', ' ').toUpperCase()}
                                </div>
                                <div className="metric-value" style={{
                                    fontSize: '1rem',
                                    color: status === 'connected' ? 'var(--success)' : 'var(--error)',
                                }}>
                                    {status}
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="alert alert-error">
                        Cannot connect to the API server. Make sure the backend is running.
                    </div>
                )}
            </div>

            {/* Configuration */}
            <div className="card" style={{ marginBottom: 24 }}>
                <div className="card-header">
                    <span className="card-title">Configuration</span>
                </div>
                {health?.config ? (
                    <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px 24px' }}>
                        {Object.entries(health.config).map(([key, value]) => (
                            <div key={key} style={{ display: 'contents' }}>
                                <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                                    {key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                                </span>
                                <span style={{
                                    fontFamily: 'var(--font-mono)',
                                    fontSize: '0.85rem',
                                    color: 'var(--text-accent)',
                                    background: 'var(--bg-glass)',
                                    padding: '4px 10px',
                                    borderRadius: '4px',
                                }}>
                                    {String(value)}
                                </span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p style={{ color: 'var(--text-muted)' }}>No configuration available.</p>
                )}
            </div>

            {/* About */}
            <div className="card">
                <div className="card-header">
                    <span className="card-title">About DocuMind AI</span>
                </div>
                <p style={{ color: 'var(--text-secondary)', lineHeight: 1.8, fontSize: '0.9rem' }}>
                    <strong style={{ color: 'var(--text-primary)' }}>DocuMind AI</strong> v1.0.0 — Enterprise RAG Platform
                </p>
                <div style={{ marginTop: 16, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    {[
                        { icon: '🧠', label: 'LLM', value: 'Groq (Llama 3.3 70B)' },
                        { icon: '📐', label: 'Embeddings', value: 'HuggingFace MiniLM' },
                        { icon: '🗄️', label: 'Vector Store', value: 'ChromaDB' },
                        { icon: '🔍', label: 'Search', value: 'Hybrid (Semantic + BM25 + RRF)' },
                        { icon: '🛡️', label: 'Security', value: 'Injection Detection + PII' },
                        { icon: '🖥️', label: 'Frontend', value: 'React + Vite' },
                    ].map(item => (
                        <div key={item.label} style={{
                            display: 'flex', alignItems: 'center', gap: 10,
                            padding: '10px 14px', background: 'var(--bg-glass)',
                            borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)',
                        }}>
                            <span style={{ fontSize: '1.2rem' }}>{item.icon}</span>
                            <div>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{item.label}</div>
                                <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>{item.value}</div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </>
    );
}
