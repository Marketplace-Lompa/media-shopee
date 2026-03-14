// Com Vite proxy configurado, BASE fica vazio — caminhos relativos passam pelo proxy
const BASE = '';

export async function listPool() {
    const r = await fetch(`${BASE}/pool`);
    if (!r.ok) throw new Error('Falha ao carregar pool');
    return r.json();
}

export async function addToPool(formData: FormData) {
    const r = await fetch(`${BASE}/pool/add`, { method: 'POST', body: formData });
    if (!r.ok) throw new Error(`Falha ao adicionar ao pool: ${r.statusText}`);
    return r.json();
}

export async function removeFromPool(id: string) {
    const r = await fetch(`${BASE}/pool/${id}`, { method: 'DELETE' });
    if (!r.ok) throw new Error(`Falha ao remover: ${r.statusText}`);
    return r.json();
}

export async function listHistory(limit = 200, offset = 0) {
    const r = await fetch(`${BASE}/history?limit=${limit}&offset=${offset}`);
    if (!r.ok) throw new Error('Falha ao carregar histórico');
    return r.json();
}

export async function getLatestReview(refresh = false) {
    const suffix = refresh ? '?refresh=true' : '';
    const r = await fetch(`${BASE}/review/latest${suffix}`);
    if (!r.ok) throw new Error('Falha ao carregar revisão');
    return r.json();
}

export async function getReviewBySession(sessionId: string, refresh = false) {
    const suffix = refresh ? '?refresh=true' : '';
    const r = await fetch(`${BASE}/review/session/${encodeURIComponent(sessionId)}${suffix}`);
    if (!r.ok) throw new Error('Falha ao carregar revisão da sessão');
    return r.json();
}

export async function deleteHistoryEntry(id: string) {
    const r = await fetch(`${BASE}/history/${encodeURIComponent(id)}`, { method: 'DELETE' });
    if (!r.ok) throw new Error(`Falha ao remover entry: ${r.statusText}`);
    return r.json();
}

export async function submitGenerateAsync(formData: FormData): Promise<{ job_id: string }> {
    const r = await fetch(`${BASE}/generate/async`, { method: 'POST', body: formData });
    if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error((err as { detail?: string }).detail ?? `HTTP ${r.status}`);
    }
    return r.json();
}

export async function pollGenerateJob(jobId: string) {
    const r = await fetch(`${BASE}/generate/jobs/${jobId}`);
    if (!r.ok) throw new Error(`Falha ao consultar job (${r.status})`);
    return r.json();
}

export async function submitEditAsync(formData: FormData): Promise<{ job_id: string }> {
    const r = await fetch(`${BASE}/edit/async`, { method: 'POST', body: formData });
    if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error((err as { detail?: string }).detail ?? `HTTP ${r.status}`);
    }
    return r.json();
}

export async function pollEditJob(jobId: string) {
    const r = await fetch(`${BASE}/edit/jobs/${jobId}`);
    if (!r.ok) throw new Error(`Falha ao consultar job de edição (${r.status})`);
    return r.json();
}

export function imageUrl(url: string) {
    // URLs absolutas passam direto; relativas usam o origin atual
    if (url.startsWith('http')) return url;
    return url;
}
