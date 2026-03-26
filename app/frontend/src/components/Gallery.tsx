import { useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, ZoomIn, X, CheckCircle, Search, Sparkles, Image, Layers, AlertTriangle, Clock, Trash2, Copy, Loader2 } from 'lucide-react';
import type {
    GenerationStatus,
    MediaHistoryItem,
    JobEntry,
} from '../types';
import { imageUrl } from '../lib/api';
import {
    humanizeMode,
    humanizeFidelityMode,
    humanizeMarketplaceChannel,
    humanizeMarketplaceOperation,
    humanizePoseFlexMode,
    humanizePreset,
    humanizeScenePreference,
    humanizeSlotId,
    humanizeJobMessage,
} from '../lib/humanize';
import { useDialogA11y } from '../hooks/useDialogA11y';
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
    { id: 'preparing_references', label: 'Analisando peça', icon: <Search size={16} /> },
    { id: 'stabilizing_garment', label: 'Preparando modelo', icon: <Layers size={16} /> },
    { id: 'creating_listing', label: 'Gerando fotos', icon: <Image size={16} /> },
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
    queued: 'Aguardando…',
    preparing_references: 'Analisando peça…',
    stabilizing_garment: 'Preparando modelo…',
    creating_listing: 'Gerando fotos do anúncio…',
    marketplace_started: 'Iniciando…',
    done_partial: 'Concluído parcialmente',
    editing: 'Aplicando edição…',
    generating: 'Gerando imagem…',
};
function resolveStageLabel(stage: string | null, type: JobEntry['type']): string {
    if (!stage) return type === 'edit' ? 'Preparando edição…' : 'Na fila…';
    return STAGE_LABELS[stage] ?? stage;
}

/* ── Job Card (grid-native) ───────────────────────────────── */
function JobCard({ job, onDismiss }: { job: JobEntry; onDismiss?: () => void }) {
    // done → imagens já aparecem no grid via histórico; card some silenciosamente
    if (job.status === 'done') return null;

    // error → card de erro no grid
    if (job.status === 'error') {
        const m = job.meta;
        const metaItems = m ? [
            m.mode && humanizeMode(String(m.mode)),
            m.marketplace_channel && humanizeMarketplaceChannel(String(m.marketplace_channel)),
            m.marketplace_operation && humanizeMarketplaceOperation(String(m.marketplace_operation)),
            m.preset && humanizePreset(String(m.preset)),
            m.fidelity_mode && humanizeFidelityMode(String(m.fidelity_mode)),
            m.aspect_ratio && `${m.aspect_ratio}`,
        ].filter(Boolean) as string[] : [];

        return (
            <motion.div
                className="image-card job-card-grid job-card-grid--error"
                role="listitem"
                initial={{ opacity: 0, scale: 0.92 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                layout
            >
                <div className="job-card-grid-body">
                    <AlertTriangle size={22} className="text-error" aria-hidden="true" />
                    <p className="t-xs text-error" style={{ textAlign: 'center', marginTop: 4 }}>
                        {job.error ?? 'Erro na geração'}
                    </p>
                    {metaItems.length > 0 && (
                        <div className="job-card-error-meta" aria-label="Parâmetros do job">
                            {metaItems.map(item => (
                                <span key={item} className="job-card-error-tag">{item}</span>
                            ))}
                        </div>
                    )}
                </div>
                {onDismiss && (
                    <button className="job-card-grid-dismiss" onClick={onDismiss} aria-label="Fechar">
                        <X size={12} />
                    </button>
                )}
            </motion.div>
        );
    }

    // queued | running → shimmer card nativo no grid
    const rawMessage = job.message;
    const stageLabel = humanizeJobMessage(rawMessage) || resolveStageLabel(job.stage, job.type);
    const isMarketplace = job.type === 'marketplace';
    const isHeroCard = !!onDismiss; // primeiro card do grupo

    // ── Marketplace Hero Card: card informativo com progresso detalhado ──
    if (isMarketplace && isHeroCard) {
        const pct = job.progress
            ? Math.round((job.progress.current / job.progress.total) * 100)
            : 0;
        const progressLabel = job.progress
            ? `${job.progress.current}/${job.progress.total}`
            : '';

        return (
            <motion.div
                className="image-card job-card-grid job-card-grid--loading job-card-grid--hero"
                role="listitem"
                aria-label={`Marketplace em andamento: ${stageLabel}`}
                initial={{ opacity: 0, scale: 0.94 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.94 }}
                layout
            >
                {/* Shimmer sweep */}
                <div className="job-card-grid-shimmer" aria-hidden="true" />

                {/* Conteúdo central informativo */}
                <div className="job-card-hero-body">
                    <motion.div
                        className="job-card-hero-spinner"
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1.6, repeat: Infinity, ease: 'linear' }}
                    >
                        <Loader2 size={24} />
                    </motion.div>

                    <span className="job-card-hero-label">{stageLabel}</span>

                    {job.progress && (
                        <div className="job-card-hero-progress-wrap">
                            <div className="job-card-hero-progress-bar">
                                <motion.div
                                    className="job-card-hero-progress-fill"
                                    initial={{ width: '0%' }}
                                    animate={{ width: `${pct}%` }}
                                    transition={{ ease: 'easeOut', duration: 0.4 }}
                                />
                            </div>
                            <span className="job-card-hero-progress-text">{progressLabel}</span>
                        </div>
                    )}

                    <span className="job-card-hero-stage">{resolveStageLabel(job.stage, job.type)}</span>
                </div>

                <button className="job-card-grid-dismiss" onClick={onDismiss} aria-label="Cancelar geração">
                    <X size={12} />
                </button>
            </motion.div>
        );
    }

    // ── Placeholder card (slots restantes de marketplace ou card padrão generate/edit) ──
    return (
        <motion.div
            className="image-card job-card-grid job-card-grid--loading"
            role="listitem"
            aria-label={`Geração em andamento: ${stageLabel}`}
            initial={{ opacity: 0, scale: 0.94 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.94 }}
            layout
        >
            {/* Shimmer sweep */}
            <div className="job-card-grid-shimmer" aria-hidden="true" />

            {/* Anel central pulsante */}
            <div className="job-card-grid-center" aria-hidden="true">
                <motion.div
                    className="job-card-grid-ring"
                    animate={{ scale: [1, 1.18, 1], opacity: [0.45, 0.9, 0.45] }}
                    transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut' }}
                />
                <Loader2 size={18} className="job-card-grid-icon" aria-hidden="true" />
            </div>

            {/* Label no rodapé — sempre visível */}
            <div className="job-card-grid-footer" role="status" aria-live="polite">
                <span className="job-card-grid-label">{isMarketplace ? '' : stageLabel}</span>
                {!isMarketplace && job.progress && (
                    <div className="job-card-grid-progress" aria-hidden="true">
                        <motion.div
                            className="job-card-grid-progress-fill"
                            initial={{ width: '0%' }}
                            animate={{ width: `${Math.round((job.progress.current / job.progress.total) * 100)}%` }}
                            transition={{ ease: 'easeOut' }}
                        />
                    </div>
                )}
            </div>

            {onDismiss && (
                <button className="job-card-grid-dismiss" onClick={onDismiss} aria-label="Cancelar geração">
                    <X size={12} />
                </button>
            )}
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

/* ── Session ID Chip (copiável) ───────────────────────────── */
function SessionIdChip({ sessionId, slotId }: { sessionId?: string; slotId?: string }) {
    const [copied, setCopied] = useState(false);
    if (!sessionId) return null;

    const shortId = sessionId.slice(0, 8);
    const slotLabel = slotId ? humanizeSlotId(slotId) : null;
    const displayText = slotLabel ? `#${shortId} · ${slotLabel}` : `#${shortId}`;

    const handleCopy = async (e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            await navigator.clipboard.writeText(`#${shortId}`);
            setCopied(true);
            setTimeout(() => setCopied(false), 1800);
        } catch { /* no-op */ }
    };

    return (
        <button
            className={`session-id-chip ${copied ? 'session-id-chip--copied' : ''}`}
            onClick={handleCopy}
            title={`ID da sessão: #${shortId}${slotId ? ` · slot: ${slotId}` : ''} — clique para copiar`}
            aria-label={`Copiar ID da sessão ${shortId}`}
            type="button"
        >
            {copied ? <CheckCircle size={9} /> : <Copy size={9} />}
            <span>{displayText}</span>
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

interface ImageCardMediaProps {
    src: string;
    alt: string;
    loading: 'lazy' | 'eager';
    onOpen?: () => void;
}

const ImageCardMedia = React.memo(({ src, alt, loading, onOpen }: ImageCardMediaProps) => {
    const [loaded, setLoaded] = useState(false);

    return (
        <>
            {!loaded && (
                <div className="image-card-load-mask" aria-hidden="true">
                    <div className="image-card-load-shimmer" />
                </div>
            )}
            <img
                src={src}
                alt={alt}
                className={`image-card-img ${loaded ? 'image-card-img--loaded' : 'image-card-img--loading'}`}
                loading={loading}
                onLoad={() => setLoaded(true)}
                onError={() => setLoaded(true)}
                onClick={onOpen}
            />
        </>
    );
});

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
            <ImageCardMedia
                src={src}
                alt={`Imagem gerada — ${item.aspect_ratio || '1:1'}`}
                loading="lazy"
            />

            {/* Overlay — seller-facing only */}
            <div className="image-card-overlay">
                <div className="image-card-badges">
                    {item.aspect_ratio && <span className="badge badge--sm">{item.aspect_ratio}</span>}
                </div>
                <SessionIdChip sessionId={item.session_id} slotId={item.slot_id} />
                <span className="image-card-time"><Clock size={9} /> {timeAgo(item.created_at)}</span>
            </div>

            {/* Actions */}
            <div className="image-card-actions" role="group" onClick={e => e.stopPropagation()}>
                <a
                    href={src}
                    download={item.filename}
                    className="img-action-btn"
                    title="Baixar"
                    aria-label={`Baixar ${item.filename}`}
                    onClick={e => e.stopPropagation()}
                >
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
                        aria-label="Remover imagem"
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

    /* ── Edição pontual ativa (SSE legado) ──────────────────── */
    if (isEditing) {
        const editingMsg = 'message' in status && status.message ? status.message : 'Editando imagem…';
        return (
            <>
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
        mode?: string;
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
            mode: resp.mode,
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

    const hasAnything = currentImages.length > 0 || filteredHistory.length > 0 || activeJobs.length > 0;

    if (!hasAnything) {
        return (
            <div className="gallery-state-wrap">
                <div className="gallery-empty" role="status" aria-live="polite">
                    <div className="empty-icon" aria-hidden="true">✦</div>
                    <p className="t-h4 text-secondary">Pronto para criar</p>
                    <p className="t-sm text-tertiary" style={{ maxWidth: 320, textAlign: 'center' }}>
                        Envie fotos da peça e escolha o estilo para gerar imagens profissionais.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <>
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
                    {(promptInfo.mode || promptInfo.preset || promptInfo.scene_preference || promptInfo.fidelity_mode || promptInfo.pose_flex_mode) && (
                        <div className="prompt-meta-badges">
                            {promptInfo.mode && <span className="badge badge--sm badge--accent" title={promptInfo.mode}>{humanizeMode(promptInfo.mode)}</span>}
                            {promptInfo.preset && <span className="badge badge--sm" title={promptInfo.preset}>{humanizePreset(promptInfo.preset)}</span>}
                            {promptInfo.scene_preference && <span className="badge badge--sm" title={promptInfo.scene_preference}>{humanizeScenePreference(promptInfo.scene_preference)}</span>}
                            {promptInfo.fidelity_mode && <span className="badge badge--sm" title={promptInfo.fidelity_mode}>{humanizeFidelityMode(promptInfo.fidelity_mode)}</span>}
                            {promptInfo.pose_flex_mode && <span className="badge badge--sm" title={promptInfo.pose_flex_mode}>{humanizePoseFlexMode(promptInfo.pose_flex_mode)}</span>}
                            {promptInfo.repair_applied && <span className="badge badge--sm">recovery: on</span>}
                        </div>
                    )}
                    <p className="t-sm text-secondary prompt-text" style={{ paddingRight: 10 }}>{promptInfo.optimized_prompt}</p>
                </motion.div>
            )}

            {/* Grid unificado: jobs ativos + geração recente + histórico */}
            <div className="unified-grid" role="list" aria-label="Imagens geradas">
                <AnimatePresence>
                    {/* Jobs em andamento — N cards por job (1 por imagem esperada) */}
                    {activeJobs.flatMap(job => {
                        // Oculta cards redundantes se a operação inteira falhou ou foi abortada
                        const isErrorState = job.status === 'error';
                        const displayCount = isErrorState ? 1 : Math.max(1, job.count);

                        return Array.from({ length: displayCount }, (_, i) => (
                            <JobCard
                                key={`${job.id}-${i}`}
                                job={job}
                                // dismiss só no primeiro card do grupo
                                onDismiss={i === 0 ? () => onDismissJob?.(job.id) : undefined}
                            />
                        ));
                    })}

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
                            <ImageCardMedia
                                src={imageUrl(img.url)}
                                alt={`Geração ${i + 1}`}
                                loading="eager"
                                onOpen={() => openLightbox(imageUrl(img.url))}
                            />
                            <div className="image-card-actions" role="group" onClick={e => e.stopPropagation()}>
                                <button
                                    className="img-action-btn"
                                    onClick={(e) => { e.stopPropagation(); openLightbox(imageUrl(img.url)); }}
                                    title="Ampliar"
                                    aria-label={`Ampliar ${img.filename}`}
                                >
                                    <ZoomIn size={15} />
                                </button>
                                <a
                                    href={imageUrl(img.url)}
                                    download={img.filename}
                                    className="img-action-btn"
                                    onClick={e => e.stopPropagation()}
                                    title="Baixar"
                                    aria-label={`Baixar ${img.filename}`}
                                >
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
    const dialogRef = useRef<HTMLDivElement>(null);
    useDialogA11y(true, dialogRef, onClose);

    return (
        <AnimatePresence>
            <motion.div
                className="lightbox"
                ref={dialogRef}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={onClose}
                role="dialog"
                aria-modal="true"
                aria-label="Imagem ampliada"
                tabIndex={-1}
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
