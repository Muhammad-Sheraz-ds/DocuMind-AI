import axios from 'axios';

// Configurable API URL: set VITE_API_URL in .env for deployment
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const API_ROOT = API_BASE.replace('/api/v1', '');

const api = axios.create({
    baseURL: API_BASE,
    timeout: 120000,
});

// ─── Documents ──────────────────────────────────

export async function uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
}

export async function getDocuments() {
    const { data } = await api.get('/documents');
    return data;
}

export async function deleteDocument(id) {
    const { data } = await api.delete(`/documents/${id}`);
    return data;
}

// ─── Chat ───────────────────────────────────────

export async function askQuestion(question, documentId = null, topK = 5) {
    const { data } = await api.post('/ask', {
        question,
        document_id: documentId,
        top_k: topK,
    });
    return data;
}

// ─── Analytics ──────────────────────────────────

export async function getAnalytics() {
    const { data } = await api.get('/analytics');
    return data;
}

// ─── Evaluation ─────────────────────────────────

export async function runEvaluation(testName, questions) {
    const { data } = await api.post('/evaluate', {
        test_name: testName,
        questions,
    });
    return data;
}

export async function getEvalHistory() {
    const { data } = await api.get('/evaluate/history');
    return data;
}

// ─── Feedback ───────────────────────────────────

export async function submitFeedback(queryId, feedback) {
    const { data } = await api.post('/feedback', {
        query_id: queryId,
        feedback,
    });
    return data;
}

// ─── Health ─────────────────────────────────────

export async function getHealth() {
    try {
        const { data } = await axios.get(`${API_ROOT}/health`, { timeout: 5000 });
        return data;
    } catch {
        return null;
    }
}
