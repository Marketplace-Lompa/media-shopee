/**
 * useJobQueue — fila de jobs assíncronos de geração e edição.
 *
 * Permite submeter múltiplos jobs sem bloquear o input.
 * Cada job tem polling independente e auto-dismiss após conclusão.
 */
import { useEffect, useRef, useState } from 'react';
import { submitGenerateAsync, submitEditAsync } from '../lib/api';
import type { JobEntry, JobType, EditTarget, AspectRatio, Resolution, Preset, ScenePreference, FidelityMode, PoseFlexMode } from '../types';

const POLL_INTERVAL_MS = 1200;
const MAX_POLL_FAILURES = 5;
const AUTO_DISMISS_MS = 30_000;

export interface GeneratePayload {
    prompt: string;
    files: File[];
    n_images: number;
    aspect_ratio: AspectRatio;
    resolution: Resolution;
    preset: Preset;
    scene_preference: ScenePreference;
    fidelity_mode: FidelityMode;
    pose_flex_mode: PoseFlexMode;
}

export interface EditPayload {
    editInstruction: string;
    target: EditTarget;
    files?: File[];
}

interface UseJobQueueOptions {
    onJobComplete: () => void;
}

export function useJobQueue({ onJobComplete }: UseJobQueueOptions) {
    const [jobs, setJobs] = useState<JobEntry[]>([]);
    const timers = useRef<Map<string, number>>(new Map());
    const failures = useRef<Map<string, number>>(new Map());

    // Cleanup ao desmontar
    useEffect(() => {
        return () => {
            timers.current.forEach((timerId) => window.clearInterval(timerId));
            timers.current.clear();
        };
    }, []);

    function updateJob(id: string, patch: Partial<JobEntry>) {
        setJobs(prev => prev.map(j => j.id === id ? { ...j, ...patch } : j));
    }

    function stopPolling(id: string) {
        const timerId = timers.current.get(id);
        if (timerId != null) window.clearInterval(timerId);
        timers.current.delete(id);
        failures.current.delete(id);
    }

    function dismissJob(id: string) {
        stopPolling(id);
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
            : `/edit/jobs/${jobId}`;

        let isPolling = false;
        const timerId = window.setInterval(async () => {
            if (isPolling) return;
            isPolling = true;
            try {
                const r = await fetch(endpoint);
                if (!r.ok) throw new Error(`HTTP ${r.status}`);
                const job = await r.json();

                // Resetar contador de falhas em sucesso
                failures.current.set(jobId, 0);

                if (job.status === 'queued') {
                    updateJob(jobId, { status: 'queued', message: 'Na fila…' });
                } else if (job.status === 'running') {
                    const event = (job.event || {}) as Record<string, unknown>;
                    const hasProg = typeof event.current === 'number' && typeof event.total === 'number';
                    updateJob(jobId, {
                        status: 'running',
                        stage: typeof job.stage === 'string' ? job.stage : null,
                        message: typeof event.message === 'string' ? event.message : null,
                        progress: hasProg
                            ? { current: event.current as number, total: event.total as number }
                            : null,
                    });
                } else if (job.status === 'done') {
                    stopPolling(jobId);
                    updateJob(jobId, {
                        status: 'done',
                        result: type === 'generate' ? job.response ?? null : null,
                        editResult: type === 'edit' ? job.response ?? null : null,
                        stage: null,
                        message: null,
                        progress: null,
                    });
                    onJobComplete();
                    window.setTimeout(() => dismissJob(jobId), AUTO_DISMISS_MS);
                } else if (job.status === 'error') {
                    stopPolling(jobId);
                    updateJob(jobId, {
                        status: 'error',
                        error: typeof job.error === 'string' ? job.error : 'Erro desconhecido',
                    });
                }
            } catch {
                const current = (failures.current.get(jobId) ?? 0) + 1;
                failures.current.set(jobId, current);
                if (current >= MAX_POLL_FAILURES) {
                    stopPolling(jobId);
                    updateJob(jobId, { status: 'error', error: 'Servidor inacessível' });
                }
            } finally {
                isPolling = false;
            }
        }, POLL_INTERVAL_MS);

        timers.current.set(jobId, timerId);
    }

    function makeTempEntry(type: JobType, thumbs: string[], prompt: string | null): JobEntry {
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
            createdAt: Date.now(),
            inputThumbnails: thumbs,
            prompt,
        };
    }

    async function submitGenerateJob(payload: GeneratePayload) {
        const thumbs = payload.files.map(f => URL.createObjectURL(f));
        const entry = makeTempEntry('generate', thumbs, payload.prompt || null);
        setJobs(prev => [entry, ...prev]);

        try {
            const fd = new FormData();
            if (payload.prompt) fd.append('prompt', payload.prompt);
            fd.append('n_images', String(payload.n_images));
            fd.append('aspect_ratio', payload.aspect_ratio);
            fd.append('resolution', payload.resolution);
            fd.append('preset', payload.preset);
            fd.append('scene_preference', payload.scene_preference);
            fd.append('fidelity_mode', payload.fidelity_mode);
            fd.append('pose_flex_mode', payload.pose_flex_mode);
            payload.files.forEach(f => fd.append('images', f));

            const { job_id } = await submitGenerateAsync(fd);

            // Trocar id temporário pelo real
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

    async function submitEditJob(payload: EditPayload) {
        const sourceThumbnail = payload.target.url.startsWith('http')
            ? payload.target.url
            : `${window.location.origin}${payload.target.url}`;
        const entry = makeTempEntry('edit', [sourceThumbnail], payload.editInstruction);
        setJobs(prev => [entry, ...prev]);

        try {
            const fd = new FormData();
            fd.append('source_url', payload.target.url);
            fd.append('edit_instruction', payload.editInstruction);
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

    return { jobs, submitGenerateJob, submitEditJob, dismissJob };
}
