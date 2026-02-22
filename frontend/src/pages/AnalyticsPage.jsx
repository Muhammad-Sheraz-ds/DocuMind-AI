import { useState, useEffect } from 'react';
import { getAnalytics } from '../services/api';

export default function AnalyticsPage() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadAnalytics();
        const interval = setInterval(loadAnalytics, 30000);
        return () => clearInterval(interval);
    }, []);

    const loadAnalytics = async () => {
        try {
            const result = await getAnalytics();
            setData(result);
        } catch { /* offline */ }
        setLoading(false);
    };

    if (loading) {
        return (
            <div className="empty-state">
                <div className="spinner" style={{ margin: '0 auto', width: 32, height: 32 }} />
            </div>
        );
    }

    if (!data) {
        return (
            <div className="empty-state">
                <div className="empty-state-icon">📊</div>
                <p>Cannot connect to the API server.</p>
            </div>
        );
    }

    const maxQueries = Math.max(...(data.queries_over_time?.map(d => d.count) || [1]), 1);

    return (
        <>
            <div className="page-header">
                <h2>📊 Analytics Dashboard</h2>
                <p>Real-time usage statistics, query trends, and performance metrics.</p>
            </div>

            {/* Top Metrics */}
            <div className="metrics-grid">
                <div className="metric-card">
                    <div className="metric-label">📄 Documents</div>
                    <div className="metric-value accent">{data.total_documents}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">💬 Total Queries</div>
                    <div className="metric-value accent">{data.total_queries}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">🧩 Total Chunks</div>
                    <div className="metric-value accent">{data.total_chunks}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">📅 Queries Today</div>
                    <div className="metric-value accent">{data.queries_today}</div>
                </div>
            </div>

            {/* Performance Metrics */}
            <div className="metrics-grid">
                <div className="metric-card">
                    <div className="metric-label">⚡ Avg Latency</div>
                    <div className="metric-value">{data.avg_latency_ms?.toFixed(0) || 0}ms</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">🎯 Avg Retrieval Score</div>
                    <div className="metric-value">{((data.avg_retrieval_score || 0) * 100).toFixed(1)}%</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">👍 Thumbs Up</div>
                    <div className="metric-value" style={{ color: 'var(--success)' }}>{data.thumbs_up}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">👎 Thumbs Down</div>
                    <div className="metric-value" style={{ color: 'var(--error)' }}>{data.thumbs_down}</div>
                </div>
            </div>

            {/* Query Trends Chart */}
            <div className="card" style={{ marginBottom: 24 }}>
                <div className="card-header">
                    <span className="card-title">📈 Queries Over Time (Last 7 Days)</span>
                </div>
                {data.queries_over_time && data.queries_over_time.length > 0 ? (
                    <div className="chart-bars">
                        {data.queries_over_time.map((day, i) => (
                            <div key={i} className="chart-bar-wrapper">
                                <span className="chart-bar-value">{day.count}</span>
                                <div
                                    className="chart-bar"
                                    style={{ height: `${Math.max(4, (day.count / maxQueries) * 160)}px` }}
                                />
                                <span className="chart-bar-label">
                                    {new Date(day.date).toLocaleDateString('en', { weekday: 'short' })}
                                </span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 32 }}>
                        No query data yet. Start asking questions!
                    </p>
                )}
            </div>

            {/* Top Questions */}
            <div className="card">
                <div className="card-header">
                    <span className="card-title">🔥 Most Asked Questions</span>
                </div>
                {data.top_questions && data.top_questions.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {data.top_questions.map((q, i) => (
                            <div key={i} className="doc-item" style={{ padding: '12px 16px' }}>
                                <span style={{ opacity: 0.5, marginRight: 12, fontWeight: 700 }}>#{i + 1}</span>
                                <div className="doc-item-info">
                                    <div className="doc-item-name">{q.question}</div>
                                </div>
                                <span style={{
                                    background: 'var(--accent-gradient)',
                                    WebkitBackgroundClip: 'text',
                                    WebkitTextFillColor: 'transparent',
                                    fontWeight: 700,
                                }}>
                                    {q.count}×
                                </span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 32 }}>
                        No questions asked yet.
                    </p>
                )}
            </div>
        </>
    );
}
