import { useState, useEffect, useRef } from 'react';
import { FiUpload, FiTrash2, FiFile, FiCheckCircle } from 'react-icons/fi';
import { uploadDocument, getDocuments, deleteDocument } from '../services/api';

export default function DocumentsPage() {
    const [docs, setDocs] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [alert, setAlert] = useState(null);
    const [dragOver, setDragOver] = useState(false);
    const fileInputRef = useRef(null);

    const loadDocs = async () => {
        try {
            const data = await getDocuments();
            setDocs(data);
        } catch { /* API offline */ }
    };

    useEffect(() => { loadDocs(); }, []);

    const handleUpload = async (file) => {
        if (!file) return;
        setUploading(true);
        setAlert(null);
        try {
            const result = await uploadDocument(file);
            setAlert({
                type: 'success',
                message: `✅ "${result.filename}" uploaded — ${result.num_chunks} chunks, ${result.num_pages} pages`,
            });
            loadDocs();
        } catch (err) {
            setAlert({
                type: 'error',
                message: `❌ Upload failed: ${err.response?.data?.detail || err.message}`,
            });
        } finally {
            setUploading(false);
        }
    };

    const handleDelete = async (id, filename) => {
        if (!window.confirm(`Delete "${filename}"?`)) return;
        try {
            await deleteDocument(id);
            setAlert({ type: 'success', message: `Deleted "${filename}"` });
            loadDocs();
        } catch (err) {
            setAlert({ type: 'error', message: `Failed to delete: ${err.message}` });
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer.files[0];
        if (file) handleUpload(file);
    };

    const formatSize = (bytes) => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    return (
        <>
            <div className="page-header">
                <h2>📄 Document Management</h2>
                <p>Upload, manage, and index your documents for AI-powered Q&A.</p>
            </div>

            {alert && (
                <div className={`alert alert-${alert.type}`}>
                    {alert.message}
                </div>
            )}

            {/* Upload Zone */}
            <div
                className={`upload-zone ${dragOver ? 'dragover' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.docx,.txt,.csv,.md"
                    style={{ display: 'none' }}
                    onChange={(e) => handleUpload(e.target.files[0])}
                />
                {uploading ? (
                    <>
                        <div className="spinner" style={{ margin: '0 auto 16px', width: 32, height: 32 }} />
                        <p>Processing document...</p>
                    </>
                ) : (
                    <>
                        <div className="upload-zone-icon">
                            <FiUpload />
                        </div>
                        <p>
                            <span className="highlight">Click to upload</span> or drag and drop
                        </p>
                        <p style={{ fontSize: '0.8rem', marginTop: 8 }}>
                            PDF, DOCX, TXT, CSV, MD — up to 50MB
                        </p>
                    </>
                )}
            </div>

            {/* Documents List */}
            <h3 style={{ margin: '32px 0 16px', color: 'var(--text-secondary)' }}>
                Uploaded Documents ({docs.length})
            </h3>

            {docs.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-state-icon">📁</div>
                    <p>No documents uploaded yet.</p>
                </div>
            ) : (
                <div className="doc-list">
                    {docs.map(doc => (
                        <div key={doc.id} className="doc-item">
                            <span className="doc-item-icon">
                                {doc.file_type === 'pdf' ? '📕' :
                                    doc.file_type === 'docx' ? '📘' :
                                        doc.file_type === 'csv' ? '📊' : '📄'}
                            </span>
                            <div className="doc-item-info">
                                <div className="doc-item-name">{doc.filename}</div>
                                <div className="doc-item-meta">
                                    <span>{formatSize(doc.file_size)}</span>
                                    <span>{doc.num_pages} pages</span>
                                    <span>{doc.num_chunks} chunks</span>
                                </div>
                            </div>
                            <span className={`doc-item-status ${doc.status}`}>{doc.status}</span>
                            <button
                                className="btn btn-danger"
                                style={{ marginLeft: 12 }}
                                onClick={() => handleDelete(doc.id, doc.filename)}
                            >
                                <FiTrash2 />
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </>
    );
}
