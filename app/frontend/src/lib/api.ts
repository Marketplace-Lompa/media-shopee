// Com Vite proxy configurado, BASE fica vazio — caminhos relativos passam pelo proxy
const BASE = '';

interface ApiErrorPayload {
    detail?: string;
    message?: string;
    error?: string;
}

async function toApiError(r: Response, fallback: string): Promise<Error> {
    const contentType = r.headers.get('content-type') ?? '';
    const endpoint = (() => {
        try { return new URL(r.url).pathname; } catch { return 'unknown-endpoint'; }
    })();

    let detail = '';
    if (contentType.includes('application/json')) {
        const payload = await r.json().catch(() => ({})) as ApiErrorPayload;
        detail = String(payload.detail || payload.message || payload.error || '').trim();
    } else {
        detail = (await r.text().catch(() => '')).trim();
    }

    let message = detail || `${fallback} (HTTP ${r.status})`;
    if (r.status === 404 && endpoint.startsWith('/marketplace')) {
        message = 'Endpoint de Marketplace não encontrado. Verifique proxy do Vite e backend com rotas /marketplace/* ativas.';
    }
    return new Error(`${message} [${r.status} ${endpoint}]`);
}

export async function listPool() {
    const r = await fetch(`${BASE}/pool`);
    if (!r.ok) throw await toApiError(r, 'Falha ao carregar pool');
    return r.json();
}

export async function addToPool(formData: FormData) {
    const r = await fetch(`${BASE}/pool/add`, { method: 'POST', body: formData });
    if (!r.ok) throw await toApiError(r, 'Falha ao adicionar ao pool');
    return r.json();
}

export async function removeFromPool(id: string) {
    const r = await fetch(`${BASE}/pool/${id}`, { method: 'DELETE' });
    if (!r.ok) throw await toApiError(r, 'Falha ao remover');
    return r.json();
}

export async function listHistory(limit = 200, offset = 0) {
    const r = await fetch(`${BASE}/history?limit=${limit}&offset=${offset}`);
    if (!r.ok) throw await toApiError(r, 'Falha ao carregar histórico');
    return r.json();
}

export async function getLatestReview(refresh = false) {
    const suffix = refresh ? '?refresh=true' : '';
    const r = await fetch(`${BASE}/review/latest${suffix}`);
    if (!r.ok) throw await toApiError(r, 'Falha ao carregar revisão');
    return r.json();
}

export async function getReviewBySession(sessionId: string, refresh = false) {
    const suffix = refresh ? '?refresh=true' : '';
    const r = await fetch(`${BASE}/review/session/${encodeURIComponent(sessionId)}${suffix}`);
    if (!r.ok) throw await toApiError(r, 'Falha ao carregar revisão da sessão');
    return r.json();
}

export async function deleteHistoryEntry(id: string) {
    const r = await fetch(`${BASE}/history/${encodeURIComponent(id)}`, { method: 'DELETE' });
    if (!r.ok) throw await toApiError(r, 'Falha ao remover entry');
    return r.json();
}

export async function submitGenerateAsync(formData: FormData): Promise<{ job_id: string }> {
    const r = await fetch(`${BASE}/generate/async`, { method: 'POST', body: formData });
    if (!r.ok) throw await toApiError(r, 'Falha ao enviar job de geração');
    return r.json();
}

export async function pollGenerateJob(jobId: string) {
    const r = await fetch(`${BASE}/generate/jobs/${jobId}`);
    if (!r.ok) throw await toApiError(r, 'Falha ao consultar job');
    return r.json();
}

export async function submitEditAsync(formData: FormData): Promise<{ job_id: string }> {
    const r = await fetch(`${BASE}/edit/async`, { method: 'POST', body: formData });
    if (!r.ok) throw await toApiError(r, 'Falha ao enviar job de edição');
    return r.json();
}

export async function pollEditJob(jobId: string) {
    const r = await fetch(`${BASE}/edit/jobs/${jobId}`);
    if (!r.ok) throw await toApiError(r, 'Falha ao consultar job de edição');
    return r.json();
}

export async function submitMarketplaceAsync(formData: FormData): Promise<{ job_id: string }> {
    const r = await fetch(`${BASE}/marketplace/async`, { method: 'POST', body: formData });
    if (!r.ok) throw await toApiError(r, 'Falha ao enviar job de marketplace');
    return r.json();
}

export async function pollMarketplaceJob(jobId: string) {
    const r = await fetch(`${BASE}/marketplace/jobs/${jobId}`);
    if (!r.ok) throw await toApiError(r, 'Falha ao consultar job de marketplace');
    return r.json();
}

export function imageUrl(url: string) {
    // URLs absolutas passam direto; relativas usam o origin atual
    if (url.startsWith('http')) return url;
    return url;
}
