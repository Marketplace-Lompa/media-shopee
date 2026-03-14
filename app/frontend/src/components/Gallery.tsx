import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, ZoomIn, X, CheckCircle, Search, Sparkles, Image, Layers, AlertTriangle, Clock, Trash2, Copy, Loader2 } from 'lucide-react';
import type {
    GenerationStatus,
    MediaHistoryItem,
    JobEntry,
} from '../types';
import { imageUrl } from '../lib/api';
import './Gallery.css';
import React from 'react'; // Added React import for React.memo

interface Props {
    status?: GenerationStatus;
    mediaHistory: MediaHistoryItem[];
    onDelete: (id: string) => void;
    onReuse?: (item: MediaHistoryItem) => void;
    onLightbox: (url: string) => void;
    onLightboxItem: (item: MediaHistoryItem) => void;
    activeJobs?: JobEntry[];
    onDismissJob?: (id: string) => void;
}

/* ── Helpers ───────────────────────────────────────────────── */
function timeAgo(ts: number): string {
    const diff = Date.now() - ts;
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'agora';
    if (mins < 60) return `${mins}m`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h`;
    const days = Math.floor(hours / 24);
    return `${days}d`;
}

function setDragPayload(e: React.DragEvent, url: string, filename: string, prompt?: string) {
    if (!e?.dataTransfer) return;
    const payload = JSON.stringify({ url, filename, prompt });
    e.dataTransfer.setData('text/plain', url);
    e.dataTransfer.setData('application/x-media-history', payload);
    e.dataTransfer.setData('application/x-studio-image', payload);
    e.dataTransfer.effectAllowed = 'copy';
}

/* ── Stepper helpers ──────────────────────────────────────── */
type StepId = string;

interface StepDef {
    id: StepId;
    label: string;
    icon: React.ReactNode;
}

// V2 pipeline steps — seller-facing
const STEPS_V2: StepDef[] = [
    { id: 'preparing_references', label: 'Preparando referências', icon: <Search size={16} /> },
    { id: 'stabilizing_garment', label: 'Estabilizando a peça', icon: <Layers size={16} /> },
    { id: 'creating_listing', label: 'Criando o anúncio', icon: <Image size={16} /> },
];

// Legacy steps (kept for old pipeline compat)
const STEPS_LEGACY: StepDef[] = [
    { id: 'mode_selected', label: 'Iniciando', icon: <Layers size={16} /> },
    { id: 'analyzing', label: 'Analisando', icon: <Search size={16} /> },
    { id: 'triage_done', label: 'Avaliando', icon: <Sparkles size={16} /> },
    { id: 'prompt_ready', label: 'Preparando', icon: <Sparkles size={16} /> },
    { id: 'generating', label: 'Gerando imagem', icon: <Image size={16} /> },
];

const V2_IDS = new Set(STEPS_V2.map(s => s.id));

function getSteps(statusType: string): StepDef[] {
    return V2_IDS.has(statusType) ? STEPS_V2 : STEPS_LEGACY;
}

function stepIndex(type: string, steps: StepDef[]): number {
    return steps.findIndex(s => s.id === type);
}

/* ── Pipeline Stepper ─────────────────────────────────────── */
function PipelineStepper({ status }: { status: GenerationStatus }) {
    const steps = getSteps(status.type);
    const current = stepIndex(status.type, steps);

    return (
        <div className="pipeline-stepper" role="status" aria-live="polite">
            {steps.map((step, i) => {
                const state = i < current ? 'done' : i === current ? 'active' : 'pending';
                return (
                    <div key={step.id} className={`pipeline-step pipeline-step--${state}`}>
                        <div className="step-indicator">
                            {state === 'done' ? (
                                <motion.div
                                    className="step-icon step-icon--done"
                                    initial={{ scale: 0 }}
                                    animate={{ scale: 1 }}
                                    transition={{ type: 'spring', stiffness: 500, damping: 25 }}
                                >
                                    <CheckCircle size={16} />
                                </motion.div>
                            ) : state === 'active' ? (
                                <motion.div
                                    className="step-icon step-icon--active"
                                    animate={{ boxShadow: ['0 0 0px rgba(139,92,246,0.3)', '0 0 16px rgba(139,92,246,0.6)', '0 0 0px rgba(139,92,246,0.3)'] }}
                                    transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
                                >
                                    {step.icon}
                                </motion.div>
                            ) : (
                                <div className="step-icon step-icon--pending">
                                    {step.icon}
                                </div>
                            )}
                            {i < steps.length - 1 && (
                                <div className={`step-connector ${i < current ? 'step-connector--done' : ''}`}>
                                    {i === current && (
                                        <motion.div
                                            className="step-connector-fill"
                                            initial={{ height: '0%' }}
                                            animate={{ height: '100%' }}
                                            transition={{ duration: 8, ease: 'linear' }}
                                        />
                                    )}
                                    {i < current && <div className="step-connector-fill" style={{ height: '100%' }} />}
                                </div>
                            )}
                        </div>

                        <div className="step-content">
                            <span className={`step-label ${state === 'active' ? 'step-label--active' : ''}`}>
                                {step.label}
                            </span>

                            {state === 'active' && 'message' in status && (
                                <motion.div
                                    className="step-detail"
                                    initial={{ opacity: 0, y: -4 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.25 }}
                                >
                                    <p className="step-detail-text">{status.message}</p>

                                    {(status.type === 'generating' || status.type === 'creating_listing') && status.current && status.total && (
                                        <div className="step-progress-wrap">
                                            <motion.div
                                                className="step-progress-fill"
                                                initial={{ width: 0 }}
                                                animate={{ width: `${Math.round((status.current / status.total) * 100)}%` }}
                                                transition={{ ease: 'easeOut' }}
                                            />
                                        </div>
                                    )}
                                </motion.div>
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

/* ── Stage label map ─────────────────────────────────────── */
const STAGE_LABELS: Record<string, string> = {
    queued: 'Na fila…',
    preparing_references: 'Preparando referências',
    stabilizing_garment: 'Estabilizando a peça',
    creating_listing: 'Criando o anúncio',
    editing: 'Analisando instrução',
    generating: 'Gerando…',
};
function resolveStageLabel(stage: string | null, type: JobEntry['type']): string {
    if (!stage) return type === 'edit' ? 'Preparando edição…' : 'Na fila…';
    return STAGE_LABELS[stage] ?? stage;
}

/* ── Job Card ─────────────────────────────────────────────── */
function JobCard({ job, onDismiss }: { job: JobEntry; onDismiss?: () => void }) {
    if (job.status === 'done') {
        const images = job.type === 'generate'
            ? (job.result?.images ?? [])
            : (job.editResult?.images ?? []);
        return (
            <motion.div
                className="job-card job-card--done"
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                layout
            >
                <div className="job-card-header">
                    <CheckCircle size={13} className="text-success" />
                    <span className="t-xs text-success">{job.type === 'edit' ? 'Edição concluída' : 'Geração concluída'}</span>
                    {onDismiss && (
                        <button className="job-card-dismiss" onClick={onDismiss} aria-label="Fechar" title="Fechar">
                            <X size={12} />
                        </button>
                    )}
                </div>
                {images.length > 0 && (
                    <div className="job-card-images">
                        {images.slice(0, 4).map(img => (
                            <img key={img.filename} src={imageUrl(img.url)} alt="Resultado" className="job-card-result-thumb" />
                        ))}
                    </div>
                )}
            </motion.div>
        );
    }

    if (job.status === 'error') {
        return (
            <motion.div
                className="job-card job-card--error"
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                layout
            >
                <div className="job-card-header">
                    <AlertTriangle size={13} className="text-error" />
                    <span className="t-xs text-error">Erro</span>
                    {onDismiss && (
                        <button className="job-card-dismiss" onClick={onDismiss} aria-label="Fechar">
                            <X size={12} />
                        </button>
                    )}
                </div>
                <p className="t-xs text-tertiary job-card-error-msg">{job.error}</p>
            </motion.div>
        );
    }

    // queued | running → loading card
    return (
        <motion.div
            className="job-card job-card--loading"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            layout
        >
            <div className="job-card-header">
                <Loader2 size={13} className="job-card-spinner" />
                <span className="t-xs text-secondary">{resolveStageLabel(job.stage, job.type)}</span>
                {job.message && job.message !== resolveStageLabel(job.stage, job.type) && (
                    <span className="t-xs text-tertiary job-card-msg" title={job.message}>{job.message}</span>
                )}
            </div>

            {/* Thumbnails das imagens enviadas */}
            {job.inputThumbnails.length > 0 && (
                <div className="job-card-thumbs">
                    {job.inputThumbnails.slice(0, 3).map((url, i) => (
                        <img key={i} src={url} alt="" className="job-card-thumb" />
                    ))}
                    {job.inputThumbnails.length > 3 && (
                        <span className="job-card-thumb-more t-xs text-tertiary">+{job.inputThumbnails.length - 3}</span>
                    )}
                </div>
            )}

            {/* Mini progress bar */}
            {job.progress && (
                <div className="job-card-progress">
                    <motion.div
                        className="job-card-progress-fill"
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.round((job.progress.current / job.progress.total) * 100)}%` }}
                        transition={{ ease: 'easeOut' }}
                    />
                </div>
            )}

            {/* Skeleton */}
            <div className="job-card-skeleton" />
        </motion.div>
    );
}

/* ── Copy Action ─────────────────────────────────────────── */
function CopyAction({ text }: { text: string }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Falha ao copiar:', err);
        }
    };

    return (
        <button
            className="copy-action-btn"
            onClick={handleCopy}
            title="Copiar prompt"
            aria-label="Copiar prompt"
        >
            {copied ? <CheckCircle size={14} className="text-success" /> : <Copy size={14} />}
        </button>
    );
}

/* ── History Grid Card ────────────────────────────────────── */
interface HistoryCardProps {
    item: MediaHistoryItem;
    index: number;
    onLightboxItem?: (item: MediaHistoryItem) => void;
    onDelete?: () => void;
    onReuse?: () => void;
}

const HistoryCard = React.memo(({ item, index, onLightboxItem, onDelete, onReuse }: HistoryCardProps) => {
    const src = imageUrl(item.url);

    return (
        <motion.div
            className="image-card image-card--history"
            role="listitem"
            draggable
            onDragStart={(e: unknown) => setDragPayload(
                e as React.DragEvent<Element>,
                src,
                item.filename,
                item.edit_instruction || item.prompt || item.optimized_prompt,
            )}
            onClick={() => onLightboxItem?.(item)}
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.92 }}
            transition={{ duration: 0.2, delay: index < 12 ? index * 0.03 : 0 }}
        >
            <img src={src} alt={`Imagem gerada — ${item.aspect_ratio || '1:1'}`} className="image-card-img" loading="lazy" />

            {/* Overlay — seller-facing only */}
            <div className="image-card-overlay">
                <div className="image-card-badges">
                    {item.aspect_ratio && <span className="badge badge--sm">{item.aspect_ratio}</span>}
                </div>
                <span className="image-card-time"><Clock size={9} /> {timeAgo(item.created_at)}</span>
            </div>

            {/* Actions */}
            <div className="image-card-actions" role="group" onClick={e => e.stopPropagation()}>
                <a href={src} download={item.filename} className="img-action-btn" title="Baixar" onClick={e => e.stopPropagation()}>
                    <Download size={14} />
                </a>
                {onReuse && (
                    <button
                        className="history-action-btn"
                        onClick={(e) => { e.stopPropagation(); onReuse(); }}
                        title="Usar como base"
                        aria-label="Usar como base para nova geração"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 2v6h-6"></path><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
                    </button>
                )}
                {onDelete && (
                    <button
                        className="history-action-btn history-action-btn--danger"
                        onClick={(e) => { e.stopPropagation(); onDelete(); }}
                        title="Remover"
                    >
                        <Trash2 size={14} />
                    </button>
                )}
            </div>
        </motion.div>
    );
});

/* ── Main Gallery (grid unificado) ───────────────────────── */
export function Gallery({ status = { type: 'idle' }, mediaHistory, onDelete, onReuse, onLightbox, onLightboxItem, activeJobs = [], onDismissJob }: Props) {
    const [localLightbox, setLocalLightbox] = useState<string | null>(null);
    const openLightbox = onLightbox ?? ((url: string) => setLocalLightbox(url));
    const openLightboxWithItem = onLightboxItem ?? ((item: MediaHistoryItem) => setLocalLightbox(imageUrl(item.url)));

    const isPipeline =
        status.type === 'preparing_references' ||
        status.type === 'stabilizing_garment' ||
        status.type === 'creating_listing' ||
        status.type === 'mode_selected' ||
        status.type === 'analyzing' ||
        status.type === 'triage_done' ||
        status.type === 'prompt_ready' ||
        status.type === 'generating' ||
        status.type === 'researching';

    const isDone = status.type === 'done' || status.type === 'done_partial';
    const isEditing = status.type === 'editing';

    /* ── Feed de jobs ativos (sempre renderizado acima do resto) ── */
    const jobFeed = activeJobs.length > 0 ? (
        <div className="active-jobs-feed">
            <AnimatePresence>
                {activeJobs.map(job => (
                    <JobCard key={job.id} job={job} onDismiss={() => onDismissJob?.(job.id)} />
                ))}
            </AnimatePresence>
        </div>
    ) : null;

    /* ── Edição pontual ativa (SSE legado) ──────────────────── */
    if (isEditing) {
        const editingMsg = 'message' in status && status.message ? status.message : 'Editando imagem…';
        return (
            <>
                {jobFeed}
                <div className="gallery-state-wrap">
                    <div className="gallery-loading">
                        <div className="editing-indicator" role="status" aria-live="polite">
                            <Loader2 size={22} className="editing-spinner" aria-hidden="true" />
                            <div>
                                <p className="t-sm text-secondary editing-indicator-title">Modificando imagem</p>
                                <p className="t-xs text-tertiary editing-indicator-msg">{editingMsg}</p>
                            </div>
                        </div>
                    </div>
                </div>
                {mediaHistory.length > 0 && (
                    <div className="unified-grid" role="list" aria-label="Histórico de gerações">
                        <AnimatePresence initial={false}>
                            {mediaHistory.map((item, i) => (
                                <HistoryCard key={item.id} item={item} index={i} onLightboxItem={openLightboxWithItem} onDelete={() => onDelete(item.id)} onReuse={() => onReuse?.(item)} />
                            ))}
                        </AnimatePresence>
                    </div>
                )}
            </>
        );
    }

    /* ── Pipeline ativo (SSE legado) ───────────────────────── */
    if (isPipeline) {
        return (
            <>
                {jobFeed}
                <div className="gallery-state-wrap">
                    <div className="gallery-loading">
                        <PipelineStepper status={status} />
                    </div>
                </div>
                {mediaHistory.length > 0 && (
                    <div className="unified-grid" role="list" aria-label="Histórico de gerações">
                        <AnimatePresence initial={false}>
                            {mediaHistory.map((item, i) => (
                                <HistoryCard key={item.id} item={item} index={i} onLightboxItem={openLightboxWithItem} onDelete={() => onDelete(item.id)} onReuse={() => onReuse?.(item)} />
                            ))}
                        </AnimatePresence>
                    </div>
                )}
                {!onLightbox && localLightbox && <LightboxOverlay src={localLightbox} onClose={() => setLocalLightbox(null)} />}
            </>
        );
    }

    /* ── Erro (SSE legado) ──────────────────────────────────── */
    if (status.type === 'error') {
        return (
            <>
                {jobFeed}
                <div className="gallery-state-wrap">
                    <div className="gallery-empty" role="alert">
                        <p className="t-h4 text-error">Erro na geração</p>
                        <p className="t-sm text-secondary" style={{ maxWidth: 360, textAlign: 'center' }}>{status.message}</p>
                    </div>
                </div>
                {mediaHistory.length > 0 && (
                    <div className="unified-grid" role="list">
                        <AnimatePresence initial={false}>
                            {mediaHistory.map((item, i) => (
                                <HistoryCard key={item.id} item={item} index={i} onLightboxItem={openLightboxWithItem} onDelete={() => onDelete(item.id)} onReuse={() => onReuse?.(item)} />
                            ))}
                        </AnimatePresence>
                    </div>
                )}
                {!onLightbox && localLightbox && <LightboxOverlay src={localLightbox} onClose={() => setLocalLightbox(null)} />}
            </>
        );
    }

    /* ── Done / Idle — grid unificado ──────────────────────── */
    let currentImages: Array<{ url: string; filename: string }> = [];
    let promptInfo: {
        session_id?: string;
        optimized_prompt: string;
        generation_time?: number;
        pipeline_version?: string;
        failed_indices?: number[] | null;
        preset?: string;
        scene_preference?: string;
        fidelity_mode?: string;
        pose_flex_mode?: string;
        repair_applied?: boolean;
    } | null = null;

    if (isDone && status.response) {
        const resp = status.response;
        currentImages = resp.images || [];
        promptInfo = {
            session_id: resp.session_id,
            optimized_prompt: resp.optimized_prompt,
            generation_time: resp.generation_time,
            pipeline_version: resp.pipeline_version,
            failed_indices: resp.failed_indices,
            preset: resp.preset,
            scene_preference: resp.scene_preference,
            fidelity_mode: resp.fidelity_mode,
            pose_flex_mode: resp.pose_flex_mode,
            repair_applied: resp.repair_applied,
        };
    }

    // Filtrar do histórico os itens que já estão na geração atual (evita duplicatas no grid)
    const currentFilenames = new Set(currentImages.map(img => img.filename));
    const filteredHistory = mediaHistory.filter(h => !currentFilenames.has(h.filename));

    const hasAnything = currentImages.length > 0 || filteredHistory.length > 0;


    if (!hasAnything) {
        return (
            <>
                {jobFeed}
                <div className="gallery-state-wrap">
                    <div className="gallery-empty" role="status" aria-live="polite">
                        <div className="empty-icon" aria-hidden="true">✦</div>
                        <p className="t-h4 text-secondary">Pronto para criar</p>
                        <p className="t-sm text-tertiary" style={{ maxWidth: 320, textAlign: 'center' }}>
                            Envie fotos da peça e escolha o estilo para gerar imagens profissionais.
                        </p>
                    </div>
                </div>
            </>
        );
    }

    return (
        <>
            {jobFeed}
            {/* Prompt result card */}
            {promptInfo && (
                <motion.div
                    className="prompt-result-card"
                    style={{ position: 'relative' }}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                >
                    <CopyAction text={promptInfo.optimized_prompt} />
                    <div className="flex items-center gap-2" style={{ marginBottom: 6, paddingRight: 32 }}>
                        <CheckCircle size={14} className="text-success" aria-hidden="true" />
                        <span className="t-label text-success">Gerado com sucesso</span>
                        {promptInfo.generation_time && (
                            <span className="t-xs text-tertiary" style={{ marginLeft: 'auto' }}>
                                {promptInfo.generation_time.toFixed(1)}s
                            </span>
                        )}
                    </div>
                    {status.type === 'done_partial' && promptInfo.failed_indices?.length ? (
                        <div className="step-analysis-card" style={{ marginBottom: 8 }}>
                            <p className="step-analysis-title">
                                <AlertTriangle size={12} style={{ marginRight: 6 }} />
                                Geração parcial
                            </p>
                            <p className="step-analysis-body">
                                Algumas variações não puderam ser geradas.
                            </p>
                        </div>
                    ) : null}
                    {(promptInfo.preset || promptInfo.scene_preference || promptInfo.fidelity_mode || promptInfo.pose_flex_mode) && (
                        <div className="prompt-meta-badges">
                            {promptInfo.preset && <span className="badge badge--sm">{promptInfo.preset}</span>}
                            {promptInfo.scene_preference && <span className="badge badge--sm">{promptInfo.scene_preference}</span>}
                            {promptInfo.fidelity_mode && <span className="badge badge--sm">fidelidade: {promptInfo.fidelity_mode}</span>}
                            {promptInfo.pose_flex_mode && <span className="badge badge--sm">pose: {promptInfo.pose_flex_mode}</span>}
                            {promptInfo.repair_applied && <span className="badge badge--sm">recovery: on</span>}
                        </div>
                    )}
                    <p className="t-sm text-secondary prompt-text" style={{ paddingRight: 10 }}>{promptInfo.optimized_prompt}</p>
                </motion.div>
            )}

            {/* Grid unificado: geração recente + histórico */}
            <div className="unified-grid" role="list" aria-label="Imagens geradas">
                <AnimatePresence>
                    {/* Geração atual — cards maiores com destaque */}
                    {currentImages.map((img, i) => (
                        <motion.div
                            key={`current-${img.filename}`}
                            className="image-card image-card--current"
                            role="listitem"
                            draggable
                            onDragStart={(e: unknown) => setDragPayload(e as React.DragEvent<Element>, imageUrl(img.url), img.filename)}
                            onClick={() => openLightbox(imageUrl(img.url))}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' || e.key === ' ') {
                                    e.preventDefault();
                                    openLightbox(imageUrl(img.url));
                                }
                            }}
                            tabIndex={0}
                            aria-label={`Abrir imagem gerada ${i + 1}`}
                            initial={{ opacity: 0, scale: 0.92 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ duration: 0.3, delay: i * 0.08 }}
                        >
                            <img
                                src={imageUrl(img.url)}
                                alt={`Geração ${i + 1}`}
                                className="image-card-img"
                                loading="lazy"
                                onClick={() => openLightbox(imageUrl(img.url))}
                            />
                            <div className="image-card-actions" role="group" onClick={e => e.stopPropagation()}>
                                <button className="img-action-btn" onClick={(e) => { e.stopPropagation(); openLightbox(imageUrl(img.url)); }} title="Ampliar">
                                    <ZoomIn size={15} />
                                </button>
                                <a href={imageUrl(img.url)} download={img.filename} className="img-action-btn" onClick={e => e.stopPropagation()} title="Baixar">
                                    <Download size={15} />
                                </a>
                            </div>
                            <div className="image-card-new-badge">NOVO</div>
                        </motion.div>
                    ))}

                    {/* Histórico — mesmos cards, mesma grid */}
                    {filteredHistory.map((item, i) => (
                        <HistoryCard key={item.id} item={item} index={i} onLightboxItem={openLightboxWithItem} onDelete={() => onDelete(item.id)} onReuse={() => onReuse?.(item)} />
                    ))}
                </AnimatePresence>
            </div>

            {/* Lightbox local (fallback se App não gerenciar) */}
            {!onLightbox && localLightbox && <LightboxOverlay src={localLightbox} onClose={() => setLocalLightbox(null)} />}
        </>
    );
}

/* ── Lightbox ─────────────────────────────────────────────── */
function LightboxOverlay({ src, onClose }: { src: string; onClose: () => void }) {
    return (
        <AnimatePresence>
            <motion.div
                className="lightbox"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={onClose}
                role="dialog"
                aria-modal="true"
                aria-label="Imagem ampliada"
            >
                <button className="lightbox-close" onClick={onClose} aria-label="Fechar">
                    <X size={20} />
                </button>
                <motion.img
                    src={src}
                    alt="Imagem ampliada"
                    className="lightbox-img"
                    initial={{ scale: 0.9 }}
                    animate={{ scale: 1 }}
                    exit={{ scale: 0.9 }}
                    onClick={e => e.stopPropagation()}
                />
            </motion.div>
        </AnimatePresence>
    );
}
