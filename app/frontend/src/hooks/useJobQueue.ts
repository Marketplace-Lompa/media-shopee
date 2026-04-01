/**
 * useJobQueue — fila de jobs assíncronos de geração e edição.
 *
 * Permite submeter múltiplos jobs sem bloquear o input.
 * Cada job tem polling independente e auto-dismiss após conclusão.
 *
 * Persistência: job_ids ativos são salvos em localStorage.
 * Ao recarregar a página, jobs ainda em execução no servidor são retomados
 * automaticamente — sem perder o andamento.
 */
import { useEffect, useRef, useState } from 'react';
import { submitGenerateAsync, submitEditAsync, submitMarketplaceAsync } from '../lib/api';
import type { JobEntry, JobType, JobStatus, EditTarget, EditCommandCenterOptions, AspectRatio, Resolution, Mode, MarketplaceChannel, MarketplaceOperation, CreateCategory } from '../types';

// Adaptive polling: ajusta taxa baseado no estágio atual do job
const POLL_DEFAULT_MS = 1200;       // queued / desconhecido
const POLL_ANALYSIS_MS = 2000;      // stages de análise/preparação
const POLL_GENERATION_MS = 4500;    // stages de GPU (geração/edição — sabidamente 15-30s)
const MAX_POLL_FAILURES = 5;
const STORAGE_KEY = 'mshopee:active_jobs';

const _SLOW_STAGES = new Set([
    'generating', 'editing', 'creating_listing',
    'stage1_generate', 'stage2_edit', 'marketplace_started',
]);
const _MEDIUM_STAGES = new Set([
    'analyzing', 'researching',
]);

function _adaptiveInterval(stage: string | null | undefined): number {
    if (!stage) return POLL_DEFAULT_MS;
    if (_SLOW_STAGES.has(stage)) return POLL_GENERATION_MS;
    if (_MEDIUM_STAGES.has(stage)) return POLL_ANALYSIS_MS;
    return POLL_DEFAULT_MS;
}

// ── Persistência ─────────────────────────────────────────────────────────────

interface PersistedJob {
    id: string;
    type: JobType;
    prompt: string | null;
    createdAt: number;
    count: number;
}

function loadPersistedJobs(): PersistedJob[] {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) return [];
        const parsed = JSON.parse(raw) as unknown;
        if (!Array.isArray(parsed)) return [];
        return parsed.filter(
            (j): j is PersistedJob =>
                typeof j === 'object' && j !== null &&
                typeof (j as PersistedJob).id === 'string' &&
                typeof (j as PersistedJob).type === 'string',
        );
    } catch {
        return [];
    }
}

function persistJobs(jobs: JobEntry[]) {
    // Salvar apenas jobs com ID real (não pending-*) ainda em execução
    const toSave: PersistedJob[] = jobs
        .filter(j => (j.status === 'queued' || j.status === 'running') && !j.id.startsWith('pending-'))
        .map(j => ({ id: j.id, type: j.type, prompt: j.prompt, createdAt: j.createdAt, count: j.count }));

    try {
        if (toSave.length === 0) {
            localStorage.removeItem(STORAGE_KEY);
        } else {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
        }
    } catch { /* quota exceeded — ignorar */ }
}

function removePersistedJob(id: string) {
    const current = loadPersistedJobs().filter(j => j.id !== id);
    try {
        if (current.length === 0) localStorage.removeItem(STORAGE_KEY);
        else localStorage.setItem(STORAGE_KEY, JSON.stringify(current));
    } catch { /* no-op */ }
}

// ── Payload types ─────────────────────────────────────────────────────────────

export interface GeneratePayload {
    category: CreateCategory;
    prompt: string;
    files: File[];
    n_images: number;
    aspect_ratio: AspectRatio;
    resolution: Resolution;
    mode: Mode;
}

export interface FreeformEditPayload {
    editInstruction: string;
    target: EditTarget;
    files?: File[];
}

export interface GuidedAnglePayload {
    editInstruction: string;
    target: EditTarget;
    commandCenter: EditCommandCenterOptions;
    files?: File[];
}

export interface MarketplacePayload {
    category: CreateCategory;
    channel: MarketplaceChannel;
    operation: MarketplaceOperation;
    baseFiles: File[];
    colorFiles?: File[];
    prompt?: string;
}

interface UseJobQueueOptions {
    onJobComplete: () => void;
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useJobQueue({ onJobComplete }: UseJobQueueOptions) {
    const [jobs, setJobs] = useState<JobEntry[]>([]);
    const timers = useRef<Map<string, number>>(new Map());
    const failures = useRef<Map<string, number>>(new Map());
    // Guard: só persistir após a restauração do localStorage ter ocorrido no mount.
    // Sem este guard, o efeito de persistência roda primeiro (jobs=[]) e apaga o
    // localStorage antes do efeito de restauração ter chance de lê-lo.
    const restoredRef = useRef(false);

    // Persistir sempre que a lista de jobs muda (mas nunca antes da restauração)
    useEffect(() => {
        if (!restoredRef.current) return;
        persistJobs(jobs);
    }, [jobs]);

    // Cleanup ao desmontar
    useEffect(() => {
        return () => {
            timers.current.forEach((timerId) => window.clearTimeout(timerId));
            timers.current.clear();
        };
    }, []);

    function updateJob(id: string, patch: Partial<JobEntry>) {
        setJobs(prev => prev.map(j => j.id === id ? { ...j, ...patch } : j));
    }

    function stopPolling(id: string) {
        const timerId = timers.current.get(id);
        if (timerId != null) window.clearTimeout(timerId);
        timers.current.delete(id);
        failures.current.delete(id);
    }

    function dismissJob(id: string) {
        stopPolling(id);
        removePersistedJob(id);
        setJobs(prev => {
            const job = prev.find(j => j.id === id);
            // Revogar object URLs para evitar memory leak
            job?.inputThumbnails.forEach(u => {
                try { URL.revokeObjectURL(u); } catch { /* no-op */ }
            });
            return prev.filter(j => j.id !== id);
        });
    }

    function startPolling(jobId: string, type: JobType) {
        const endpoint = type === 'generate'
            ? `/generate/jobs/${jobId}`
            : type === 'marketplace'
                ? `/marketplace/jobs/${jobId}`
                : `/edit/jobs/${jobId}`;

        let currentStage: string | null = null;

        function scheduleNext() {
            const delay = _adaptiveInterval(currentStage);
            const timerId = window.setTimeout(() => pollOnce(), delay);
            timers.current.set(jobId, timerId);
        }

        async function pollOnce() {
            try {
                const r = await fetch(endpoint);

                // ── 404 = job finalizado (backend faz GC de jobs concluídos) ──
                if (r.status === 404) {
                    stopPolling(jobId);
                    removePersistedJob(jobId);
                    dismissJob(jobId);
                    onJobComplete();
                    return;
                }

                if (!r.ok) throw new Error(`HTTP ${r.status}`);
                const job = await r.json();

                // Resetar contador de falhas em sucesso
                failures.current.set(jobId, 0);

                // Atualizar estágio para adaptar intervalo do próximo poll
                if (typeof job.stage === 'string') {
                    currentStage = job.stage;
                }

                if (job.status === 'queued') {
                    const event = (job.event || {}) as Record<string, unknown>;
                    updateJob(jobId, {
                        status: 'queued',
                        message: typeof event.message === 'string' ? event.message : 'Na fila…',
                    });
                    scheduleNext();
                } else if (job.status === 'running') {
                    const event = (job.event || {}) as Record<string, unknown>;
                    const hasProg = typeof event.current === 'number' && typeof event.total === 'number';
                    const hasTotalSlots = typeof event.total_slots === 'number';
                    
                    const patch: Partial<JobEntry> = {
                        status: 'running',
                        stage: typeof job.stage === 'string' ? job.stage : null,
                        message: typeof event.message === 'string' ? event.message : null,
                        progress: hasProg
                            ? { current: event.current as number, total: event.total as number }
                            : null,
                    };

                    // Sincroniza a contagem visual de cartões com a realidade do backend 
                    // (ex: após de-duplicação de cores)
                    if (hasTotalSlots) {
                        patch.count = Math.max(1, event.total_slots as number);
                    }
                    if (hasProg) {
                        patch.count = Math.max(1, event.total as number);
                    }

                    updateJob(jobId, patch);
                    scheduleNext();
                } else if (job.status === 'done') {
                    stopPolling(jobId);
                    removePersistedJob(jobId);
                    updateJob(jobId, {
                        status: 'done',
                        result: (type === 'generate' || type === 'marketplace') ? job.response ?? null : null,
                        editResult: type === 'edit' ? job.response ?? null : null,
                        stage: null,
                        message: null,
                        progress: null,
                    });
                    window.setTimeout(() => {
                        dismissJob(jobId);
                        onJobComplete();
                    }, 2_000);
                } else if (job.status === 'error') {
                    stopPolling(jobId);
                    removePersistedJob(jobId);
                    updateJob(jobId, {
                        status: 'error',
                        error: typeof job.error === 'string' ? job.error : 'Erro desconhecido',
                        meta: job.meta && typeof job.meta === 'object' ? job.meta as Record<string, unknown> : null,
                    });
                }
            } catch {
                const current = (failures.current.get(jobId) ?? 0) + 1;
                failures.current.set(jobId, current);
                if (current >= MAX_POLL_FAILURES) {
                    stopPolling(jobId);
                    removePersistedJob(jobId);
                    updateJob(jobId, { status: 'error', error: 'Conexão perdida com o servidor' });
                    return;
                }
                scheduleNext();
            }
        }

        // Kick-off: primeiro poll rápido
        const initialTimer = window.setTimeout(() => pollOnce(), POLL_DEFAULT_MS);
        timers.current.set(jobId, initialTimer);
    }

    // ── Restaurar jobs do localStorage ao montar ──────────────────────────────
    useEffect(() => {
        const persisted = loadPersistedJobs();
        if (persisted.length === 0) {
            restoredRef.current = true;
            return;
        }

        // Descartar jobs muito antigos (>2h) — backend in-memory também não os tem mais
        const TWO_HOURS = 2 * 60 * 60 * 1000;
        const fresh = persisted.filter(j => Date.now() - j.createdAt < TWO_HOURS);

        if (fresh.length === 0) {
            localStorage.removeItem(STORAGE_KEY);
            restoredRef.current = true;
            return;
        }

        const restored: JobEntry[] = fresh.map(p => ({
            id: p.id,
            type: p.type,
            status: 'running' as JobStatus,
            stage: null,
            message: 'Sincronizando…',
            progress: null,
            result: null,
            editResult: null,
            error: null,
            meta: null,
            createdAt: p.createdAt,
            inputThumbnails: [], // object URLs não sobrevivem ao reload
            prompt: p.prompt,
            count: p.count ?? 1,
        }));

        restoredRef.current = true;
        setJobs(restored);
        restored.forEach(j => startPolling(j.id, j.type));
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); // apenas no mount

    // ── Heartbeat: re-inicia polling se timers foram perdidos (ex: HMR) ──────
    useEffect(() => {
        const heartbeat = window.setInterval(() => {
            const activeJobs = jobs.filter(j => j.status === 'queued' || j.status === 'running');
            for (const j of activeJobs) {
                if (!timers.current.has(j.id)) {
                    console.info(`[JobQueue] Polling perdido para ${j.id}, reiniciando…`);
                    startPolling(j.id, j.type);
                }
            }
        }, 2000);
        return () => window.clearInterval(heartbeat);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [jobs]);

    // ── Helpers de entrada ────────────────────────────────────────────────────

    function makeTempEntry(type: JobType, thumbs: string[], prompt: string | null, count = 1): JobEntry {
        return {
            id: `pending-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
            type,
            status: 'queued',
            stage: null,
            message: 'Enviando…',
            progress: null,
            result: null,
            editResult: null,
            error: null,
            meta: null,
            createdAt: Date.now(),
            inputThumbnails: thumbs,
            prompt,
            count,
        };
    }

    async function submitGenerateJob(payload: GeneratePayload) {
        const thumbs = payload.files.map(f => URL.createObjectURL(f));
        const entry = makeTempEntry('generate', thumbs, payload.prompt || null, payload.n_images ?? 1);
        setJobs(prev => [entry, ...prev]);

        try {
            const fd = new FormData();
            fd.append('category', payload.category);
            if (payload.prompt) fd.append('prompt', payload.prompt);
            fd.append('n_images', String(payload.n_images));
            fd.append('aspect_ratio', payload.aspect_ratio);
            fd.append('resolution', payload.resolution);
            fd.append('mode', payload.mode);
            payload.files.forEach(f => fd.append('images', f));

            const { job_id } = await submitGenerateAsync(fd);

            // Trocar id temporário pelo real (agora persiste automaticamente via useEffect)
            setJobs(prev => prev.map(j =>
                j.id === entry.id ? { ...j, id: job_id, message: 'Aguardando fila…' } : j
            ));
            startPolling(job_id, 'generate');
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Erro ao enviar job';
            setJobs(prev => prev.map(j =>
                j.id === entry.id ? { ...j, status: 'error', error: msg } : j
            ));
        }
    }

    async function submitFreeformEditJob(payload: FreeformEditPayload) {
        const sourceThumbnail = payload.target.url.startsWith('http')
            ? payload.target.url
            : `${window.location.origin}${payload.target.url}`;
        const entry = makeTempEntry('edit', [sourceThumbnail], payload.editInstruction);
        setJobs(prev => [entry, ...prev]);

        try {
            const fd = new FormData();
            fd.append('source_url', payload.target.url);
            fd.append('edit_instruction', payload.editInstruction);
            fd.append('input_mode', 'freeform');
            if (payload.target.prompt) fd.append('source_prompt', payload.target.prompt);
            if (payload.target.session_id) fd.append('source_session_id', payload.target.session_id);
            if (payload.target.aspect_ratio) fd.append('aspect_ratio', payload.target.aspect_ratio);
            if (payload.target.resolution) fd.append('resolution', payload.target.resolution);
            payload.files?.forEach(f => fd.append('images', f));

            const { job_id } = await submitEditAsync(fd);

            setJobs(prev => prev.map(j =>
                j.id === entry.id ? { ...j, id: job_id, message: 'Aguardando fila…' } : j
            ));
            startPolling(job_id, 'edit');
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Erro ao enviar edição';
            setJobs(prev => prev.map(j =>
                j.id === entry.id ? { ...j, status: 'error', error: msg } : j
            ));
        }
    }

    async function submitGuidedAngleJob(payload: GuidedAnglePayload) {
        const sourceThumbnail = payload.target.url.startsWith('http')
            ? payload.target.url
            : `${window.location.origin}${payload.target.url}`;
        const entry = makeTempEntry('edit', [sourceThumbnail], payload.editInstruction);
        setJobs(prev => [entry, ...prev]);

        try {
            const fd = new FormData();
            fd.append('source_url', payload.target.url);
            fd.append('edit_instruction', payload.editInstruction);
            fd.append('input_mode', 'guided_angle');
            if (payload.target.session_id) fd.append('source_session_id', payload.target.session_id);
            if (payload.commandCenter.aspect_ratio) fd.append('aspect_ratio', payload.commandCenter.aspect_ratio);
            else if (payload.target.aspect_ratio) fd.append('aspect_ratio', payload.target.aspect_ratio);
            if (payload.commandCenter.resolution) fd.append('resolution', payload.commandCenter.resolution);
            else if (payload.target.resolution) fd.append('resolution', payload.target.resolution);
            if (payload.commandCenter.editSubmode) fd.append('edit_submode', payload.commandCenter.editSubmode);
            if (payload.commandCenter.viewIntent) fd.append('view_intent', payload.commandCenter.viewIntent);
            if (payload.commandCenter.distanceIntent) fd.append('distance_intent', payload.commandCenter.distanceIntent);
            if (payload.commandCenter.poseFreedom) fd.append('pose_freedom', payload.commandCenter.poseFreedom);
            if (payload.commandCenter.angleTarget) fd.append('angle_target', payload.commandCenter.angleTarget);
            if (payload.commandCenter.sourceShotType) fd.append('source_shot_type', payload.commandCenter.sourceShotType);
            if (typeof payload.commandCenter.preserveFraming === 'boolean') fd.append('preserve_framing', String(payload.commandCenter.preserveFraming));
            if (typeof payload.commandCenter.preserveCameraHeight === 'boolean') fd.append('preserve_camera_height', String(payload.commandCenter.preserveCameraHeight));
            if (typeof payload.commandCenter.preserveDistance === 'boolean') fd.append('preserve_distance', String(payload.commandCenter.preserveDistance));
            if (typeof payload.commandCenter.preservePose === 'boolean') fd.append('preserve_pose', String(payload.commandCenter.preservePose));
            payload.files?.forEach(f => fd.append('images', f));

            const { job_id } = await submitEditAsync(fd);

            setJobs(prev => prev.map(j =>
                j.id === entry.id ? { ...j, id: job_id, message: 'Aguardando fila…' } : j
            ));
            startPolling(job_id, 'edit');
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Erro ao enviar edição guiada';
            setJobs(prev => prev.map(j =>
                j.id === entry.id ? { ...j, status: 'error', error: msg } : j
            ));
        }
    }

    async function submitMarketplaceJob(payload: MarketplacePayload) {
        const allFiles = [...payload.baseFiles, ...(payload.colorFiles || [])];
        const thumbs = allFiles.map(f => URL.createObjectURL(f));
        // color_variations é estimativa inicial conservadora; backend ajusta via stage total_slots/total.
        const count = payload.operation === 'main_variation' ? 5 : 3;
        const entryLabel = payload.operation === 'main_variation' ? 'Marketplace: Variação principal' : 'Marketplace: Variações de cor';
        
        const entry = makeTempEntry('marketplace', thumbs, entryLabel, count);
        setJobs(prev => [entry, ...prev]);

        try {
            const fd = new FormData();
            fd.append('category', payload.category);
            fd.append('marketplace_channel', payload.channel);
            fd.append('operation', payload.operation);
            if (payload.prompt) {
                fd.append('prompt', payload.prompt);
            }
            payload.baseFiles.forEach(f => fd.append('base_images', f));
            payload.colorFiles?.forEach(f => fd.append('color_images', f));

            const { job_id } = await submitMarketplaceAsync(fd);

            setJobs(prev => prev.map(j =>
                j.id === entry.id ? { ...j, id: job_id, message: 'Aguardando fila…' } : j
            ));
            startPolling(job_id, 'marketplace');
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Erro ao enviar job de marketplace';
            setJobs(prev => prev.map(j =>
                j.id === entry.id ? { ...j, status: 'error', error: msg } : j
            ));
        }
    }

    return { jobs, submitGenerateJob, submitFreeformEditJob, submitGuidedAngleJob, submitMarketplaceJob, dismissJob };
}
