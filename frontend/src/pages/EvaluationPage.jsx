import { useState, useEffect } from 'react';
import { FiPlus, FiTrash2, FiPlay } from 'react-icons/fi';
import { runEvaluation, getEvalHistory } from '../services/api';

export default function EvaluationPage() {
    const [testName, setTestName] = useState('manual_test');
    const [pairs, setPairs] = useState([{ question: '', expected_answer: '' }]);
    const [running, setRunning] = useState(false);
    const [result, setResult] = useState(null);
    const [history, setHistory] = useState([]);
    const [alert, setAlert] = useState(null);

    useEffect(() => { loadHistory(); }, []);

    const loadHistory = async () => {
        try {
            setHistory(await getEvalHistory());
        } catch { /* offline */ }
    };

    const addPair = () => {
        setPairs(prev => [...prev, { question: '', expected_answer: '' }]);
    };

    const removePair = (index) => {
        setPairs(prev => prev.filter((_, i) => i !== index));
    };

    const updatePair = (index, field, value) => {
        setPairs(prev => prev.map((p, i) => i === index ? { ...p, [field]: value } : p));
    };

    const handleRun = async () => {
        const valid = pairs.filter(p => p.question.trim() && p.expected_answer.trim());
        if (valid.length === 0) {
            setAlert({ type: 'error', message: 'Add at least one Q&A pair.' });
            return;
        }

        setRunning(true);
        setAlert(null);
        setResult(null);

        try {
            const res = await runEvaluation(testName, valid);
            setResult(res);
            setAlert({ type: 'success', message: `✅ Evaluation complete: ${valid.length} questions tested.` });
            loadHistory();
        } catch (err) {
            setAlert({ type: 'error', message: `❌ ${err.response?.data?.detail || err.message}` });
        } finally {
            setRunning(false);
        }
    };

    return (
        <>
            <div className="page-header">
                <h2>🧪 Evaluation Harness</h2>
                <p>Measure RAG pipeline accuracy with golden Q&A test sets.</p>
            </div>

            {alert && <div className={`alert alert-${alert.type}`}>{alert.message}</div>}

            {/* New Evaluation */}
            <div className="card" style={{ marginBottom: 24 }}>
                <div className="card-header">
                    <span className="card-title">Run New Evaluation</span>
                </div>

                <div style={{ marginBottom: 16 }}>
                    <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                        Test Name
                    </label>
                    <input
                        className="input"
                        value={testName}
                        onChange={(e) => setTestName(e.target.value)}
                        placeholder="e.g., accuracy_test_v1"
                        style={{ maxWidth: 300 }}
                    />
                </div>

                <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 12 }}>
                    Q&A Pairs (Question → Expected Answer)
                </label>

                {pairs.map((pair, i) => (
                    <div key={i} className="eval-pair">
                        <input
                            className="input"
                            placeholder={`Question ${i + 1}`}
                            value={pair.question}
                            onChange={(e) => updatePair(i, 'question', e.target.value)}
                        />
                        <input
                            className="input"
                            placeholder={`Expected answer ${i + 1}`}
                            value={pair.expected_answer}
                            onChange={(e) => updatePair(i, 'expected_answer', e.target.value)}
                        />
                        <button className="btn btn-danger" onClick={() => removePair(i)}>
                            <FiTrash2 />
                        </button>
                    </div>
                ))}

                <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
                    <button className="btn btn-ghost" onClick={addPair}>
                        <FiPlus /> Add Pair
                    </button>
                    <button className="btn btn-primary" onClick={handleRun} disabled={running}>
                        {running ? <><span className="spinner" /> Running...</> : <><FiPlay /> Run Evaluation</>}
                    </button>
                </div>
            </div>

            {/* Results */}
            {result && (
                <div className="card" style={{ marginBottom: 24 }}>
                    <div className="card-header">
                        <span className="card-title">Results: {result.test_name}</span>
                    </div>

                    <div className="metrics-grid" style={{ marginBottom: 20 }}>
                        <div className="metric-card">
                            <div className="metric-label">🎯 Retrieval Accuracy</div>
                            <div className="metric-value accent">{(result.retrieval_accuracy * 100).toFixed(1)}%</div>
                        </div>
                        <div className="metric-card">
                            <div className="metric-label">📝 Avg Faithfulness</div>
                            <div className="metric-value accent">{result.avg_faithfulness?.toFixed(2)}</div>
                        </div>
                        <div className="metric-card">
                            <div className="metric-label">⚡ Avg Latency</div>
                            <div className="metric-value">{result.avg_latency_ms?.toFixed(0)}ms</div>
                        </div>
                    </div>

                    {result.results?.map((r, i) => (
                        <div key={i} className={`eval-result ${r.retrieval_hit ? 'pass' : 'fail'}`}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                                <strong>{r.retrieval_hit ? '✅' : '❌'} {r.question}</strong>
                                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                    {r.latency_ms?.toFixed(0)}ms
                                </span>
                            </div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                <p><strong>Expected:</strong> {r.expected_answer}</p>
                                <p style={{ marginTop: 4 }}><strong>Actual:</strong> {r.actual_answer?.slice(0, 300)}</p>
                                <p style={{ marginTop: 4 }}>
                                    <strong>Faithfulness:</strong> {r.faithfulness_score?.toFixed(2)} |
                                    <strong> Retrieval Hit:</strong> {r.retrieval_hit ? 'Yes' : 'No'}
                                </p>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* History */}
            <div className="card">
                <div className="card-header">
                    <span className="card-title">📜 Evaluation History</span>
                </div>
                {history.length === 0 ? (
                    <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 32 }}>
                        No evaluations run yet.
                    </p>
                ) : (
                    <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                                    {['Test Name', 'Questions', 'Retrieval Acc.', 'Faithfulness', 'Latency', 'Date'].map(h => (
                                        <th key={h} style={{
                                            padding: '10px 12px', textAlign: 'left',
                                            fontSize: '0.78rem', color: 'var(--text-muted)',
                                            textTransform: 'uppercase', letterSpacing: '0.5px',
                                        }}>{h}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {history.map((row, i) => (
                                    <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                                        <td style={{ padding: '10px 12px', fontSize: '0.85rem' }}>{row.test_name}</td>
                                        <td style={{ padding: '10px 12px', fontSize: '0.85rem' }}>{row.total_questions}</td>
                                        <td style={{ padding: '10px 12px', fontSize: '0.85rem' }}>
                                            {(row.retrieval_accuracy * 100).toFixed(1)}%
                                        </td>
                                        <td style={{ padding: '10px 12px', fontSize: '0.85rem' }}>
                                            {row.answer_faithfulness?.toFixed(2)}
                                        </td>
                                        <td style={{ padding: '10px 12px', fontSize: '0.85rem' }}>
                                            {row.avg_latency_ms?.toFixed(0)}ms
                                        </td>
                                        <td style={{ padding: '10px 12px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                                            {new Date(row.run_time).toLocaleDateString()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </>
    );
}
