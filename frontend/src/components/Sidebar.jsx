import { useState, useEffect } from 'react';
import { FiMessageSquare, FiFileText, FiBarChart2, FiCheckCircle, FiSettings } from 'react-icons/fi';
import { getHealth } from '../services/api';

export default function Sidebar({ activePage, onPageChange }) {
    const [health, setHealth] = useState(null);

    useEffect(() => {
        getHealth().then(setHealth);
        const interval = setInterval(() => getHealth().then(setHealth), 30000);
        return () => clearInterval(interval);
    }, []);

    const navItems = [
        { id: 'chat', label: 'Chat', icon: <FiMessageSquare /> },
        { id: 'documents', label: 'Documents', icon: <FiFileText /> },
        { id: 'analytics', label: 'Analytics', icon: <FiBarChart2 /> },
        { id: 'evaluation', label: 'Evaluation', icon: <FiCheckCircle /> },
        { id: 'settings', label: 'Settings', icon: <FiSettings /> },
    ];

    const isOnline = health?.status === 'healthy';

    return (
        <aside className="sidebar">
            <div className="sidebar-brand">
                <span className="sidebar-brand-icon">📚</span>
                <h1>DocuMind AI</h1>
            </div>
            <p className="sidebar-subtitle">Enterprise RAG Platform</p>

            <nav className="sidebar-nav">
                {navItems.map(item => (
                    <button
                        key={item.id}
                        className={`nav-item ${activePage === item.id ? 'active' : ''}`}
                        onClick={() => onPageChange(item.id)}
                    >
                        <span className="nav-item-icon">{item.icon}</span>
                        {item.label}
                    </button>
                ))}
            </nav>

            <div className="sidebar-footer">
                <div className="status-indicator">
                    <span className={`status-dot ${isOnline ? '' : 'offline'}`} />
                    {isOnline ? 'API Connected' : 'API Offline'}
                </div>
                {health?.services && (
                    <>
                        <div className="status-indicator">
                            <span className={`status-dot ${health.services.llm === 'connected' ? '' : 'offline'}`} />
                            LLM: {health.services.llm}
                        </div>
                        <div className="status-indicator">
                            <span className="status-dot" />
                            Vector Store: {health.services.vector_store}
                        </div>
                    </>
                )}
            </div>
        </aside>
    );
}
