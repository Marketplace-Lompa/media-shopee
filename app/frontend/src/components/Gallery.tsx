import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, ZoomIn, X, CheckCircle, Search, Sparkles, Image, Globe, Layers, AlertTriangle, Clock, Trash2 } from 'lucide-react';
import type { GenerationStatus, MediaHistoryItem } from '../types';
import { imageUrl } from '../lib/api';
import './Gallery.css';

interface Props {
    status: GenerationStatus;
    hadResearch: boolean;
    mediaHistory: MediaHistoryItem[];
    onHistoryDelete?: (id: string) => void;
    onLightbox?: (url: string) => void;
    onLightboxItem?: (item: MediaHistoryItem) => void;
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

function setDragPayload(e: any, url: string, filename: string) {
    if (!e?.dataTransfer) return;
    e.dataTransfer.setData('text/plain', url);
    e.dataTransfer.setData('application/x-studio-image', JSON.stringify({ url, filename }));
    e.dataTransfer.effectAllowed = 'copy';
}

/* ── Stepper helpers ──────────────────────────────────────── */
type StepId = 'mode_selected' | 'researching' | 'analyzing' | 'triage_done' | 'prompt_ready' | 'generating';

interface StepDef {
    id: StepId;
    label: string;
    icon: React.ReactNode;
}

const STEPS_BASE: StepDef[] = [
    { id: 'mode_selected', label: 'Selecionando modo', icon: <Layers size={16} /> },
    { id: 'analyzing', label: 'Analisando imagens', icon: <Search size={16} /> },
    { id: 'triage_done', label: 'Triage grounding', icon: <Sparkles size={16} /> },
    { id: 'prompt_ready', label: 'Prompt criado', icon: <Sparkles size={16} /> },
    { id: 'generating', label: 'Gerando imagem', icon: <Image size={16} /> },
];

const STEP_RESEARCH: StepDef = { id: 'researching', label: 'Pesquisando referências', icon: <Globe size={16} /> };

function getSteps(hasResearch: boolean): StepDef[] {
    return hasResearch ? [STEP_RESEARCH, ...STEPS_BASE] : STEPS_BASE;
}

function stepIndex(type: string, hasResearch: boolean): number {
    const steps = getSteps(hasResearch);
    return steps.findIndex(s => s.id === type);
}

/* ── Pipeline Stepper ─────────────────────────────────────── */
function PipelineStepper({ status, hasResearch }: { status: GenerationStatus; hasResearch: boolean }) {
    const steps = getSteps(hasResearch);
    const current = stepIndex(status.type, hasResearch);

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

                            {state === 'active' && (
                                <motion.div
                                    className="step-detail"
                                    initial={{ opacity: 0, y: -4 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.25 }}
                                >
                                    {status.type === 'analyzing' && (
                                        <p className="step-detail-text">{status.message}</p>
                                    )}

                                    {status.type === 'mode_selected' && (
                                        <p className="step-detail-text">
                                            {status.message} · {status.pipeline_mode === 'reference_mode' ? 'Com referência' : 'Sem referência'}
                                        </p>
                                    )}

                                    {status.type === 'triage_done' && (
                                        <>
                                            <p className="step-detail-text">{status.message}</p>
                                            <p className="step-detail-text">
                                                Modo: <strong>{status.grounding_mode}</strong>
                                                {typeof status.grounding_score === 'number' ? ` · Score: ${status.grounding_score.toFixed(2)}` : ''}
                                            </p>
                                            {typeof status.complexity_score === 'number' && (
                                                <p className="step-detail-text">Complexidade: {status.complexity_score.toFixed(2)}</p>
                                            )}
                                            {typeof status.hint_confidence === 'number' && (
                                                <p className="step-detail-text">Confiança: {status.hint_confidence.toFixed(2)}</p>
                                            )}
                                            {status.trigger_reason && (
                                                <p className="step-detail-text">Motivo: {status.trigger_reason}</p>
                                            )}
                                            {status.classifier_summary?.garment_category && (
                                                <p className="step-detail-text">
                                                    Categoria: {status.classifier_summary.garment_category}
                                                    {status.classifier_summary?.atypical ? ' · Atípica' : ''}
                                                </p>
                                            )}
                                            {status.reason_codes?.length ? (
                                                <p className="step-detail-text">
                                                    Códigos: {status.reason_codes.slice(0, 3).join(', ')}
                                                </p>
                                            ) : null}
                                            {status.garment_hypothesis && (
                                                <p className="step-detail-text">{status.garment_hypothesis}</p>
                                            )}
                                        </>
                                    )}

                                    {status.type === 'prompt_ready' && (
                                        <>
                                            {status.image_analysis && (
                                                <div className="step-analysis-card">
                                                    <p className="step-analysis-title">🔍 Análise visual</p>
                                                    <p className="step-analysis-body">{status.image_analysis}</p>
                                                </div>
                                            )}
                                            <p className="step-detail-prompt">{status.prompt}</p>
                                        </>
                                    )}

                                    {status.type === 'generating' && (
                                        <>
                                            <p className="step-detail-text">{status.message}</p>
                                            <div className="step-progress-wrap">
                                                <motion.div
                                                    className="step-progress-fill"
                                                    initial={{ width: 0 }}
                                                    animate={{ width: `${Math.round((status.current / status.total) * 100)}%` }}
                                                    transition={{ ease: 'easeOut' }}
                                                />
                                            </div>
                                        </>
                                    )}
                                </motion.div>
                            )}

                            {state === 'done' && status.type === 'prompt_ready' && i === 0 && status.image_analysis && (
                                <p className="step-done-summary">{status.image_analysis}</p>
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

/* ── History Grid Card ────────────────────────────────────── */
function HistoryCard({
    item,
    index,
    onLightboxItem,
    onDelete,
}: {
    item: MediaHistoryItem;
    index: number;
    onLightboxItem?: (item: MediaHistoryItem) => void;
    onDelete?: (id: string) => void;
}) {
    const src = imageUrl(item.url);

    return (
        <motion.div
            className="image-card image-card--history"
            role="listitem"
            draggable
            onDragStart={e => setDragPayload(e, src, item.filename)}
            onClick={() => onLightboxItem?.(item)}
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.92 }}
            transition={{ duration: 0.2, delay: index < 12 ? index * 0.03 : 0 }}
        >
            <img src={src} alt={item.filename} className="image-card-img" loading="lazy" />

            {/* Overlay com badges compactos */}
            <div className="image-card-overlay">
                <div className="image-card-badges">
                    {item.aspect_ratio && <span className="badge badge--sm">{item.aspect_ratio}</span>}
                    {item.thinking_level && <span className="badge badge--sm badge--accent">{item.thinking_level}</span>}
                    {item.grounding_effective != null && (
                        <span className={`badge badge--sm ${item.grounding_effective ? 'badge--success' : ''}`}>
                            {item.grounding_effective ? '🌐 Pesquisa web' : 'Sem pesquisa'}
                        </span>
                    )}
                </div>
                <span className="image-card-time"><Clock size={9} /> {timeAgo(item.created_at)}</span>
            </div>

            {/* Actions */}
            <div className="image-card-actions" role="group" onClick={e => e.stopPropagation()}>
                <a href={src} download={item.filename} className="img-action-btn" title="Baixar" onClick={e => e.stopPropagation()}>
                    <Download size={14} />
                </a>
                {onDelete && (
                    <button className="img-action-btn img-action-btn--danger" onClick={() => onDelete(item.id)} title="Remover">
                        <Trash2 size={14} />
                    </button>
                )}
            </div>
        </motion.div>
    );
}

/* ── Main Gallery (grid unificado) ───────────────────────── */
export function Gallery({ status, hadResearch, mediaHistory, onHistoryDelete, onLightbox, onLightboxItem }: Props) {
    const [localLightbox, setLocalLightbox] = useState<string | null>(null);
    const openLightbox = onLightbox ?? ((url: string) => setLocalLightbox(url));
    const openLightboxWithItem = onLightboxItem ?? ((item: MediaHistoryItem) => setLocalLightbox(imageUrl(item.url)));

    const isPipeline =
        status.type === 'mode_selected' ||
        status.type === 'analyzing' ||
        status.type === 'triage_done' ||
        status.type === 'prompt_ready' ||
        status.type === 'generating' ||
        status.type === 'researching';

    const isDone = status.type === 'done' || status.type === 'done_partial';

    /* ── Pipeline ativo ────────────────────────────────────── */
    if (isPipeline) {
        return (
            <>
                <div className="gallery-state-wrap">
                    <div className="gallery-loading">
                        <PipelineStepper status={status} hasResearch={hadResearch || status.type === 'researching'} />
                    </div>
                </div>
                {/* Grid de histórico visível mesmo durante pipeline */}
                {mediaHistory.length > 0 && (
                    <div className="unified-grid" role="list" aria-label="Histórico de gerações">
                        <AnimatePresence initial={false}>
                            {mediaHistory.map((item, i) => (
                                <HistoryCard key={item.id} item={item} index={i} onLightboxItem={openLightboxWithItem} onDelete={onHistoryDelete} />
                            ))}
                        </AnimatePresence>
                    </div>
                )}
                {!onLightbox && localLightbox && <LightboxOverlay src={localLightbox} onClose={() => setLocalLightbox(null)} />}
            </>
        );
    }

    /* ── Erro ───────────────────────────────────────────────── */
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
                                <HistoryCard key={item.id} item={item} index={i} onLightboxItem={openLightboxWithItem} onDelete={onHistoryDelete} />
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
        optimized_prompt: string;
        thinking_level?: string;
        generation_time?: number;
        grounding?: any;
        pipeline_mode?: string;
        failed_indices?: number[] | null;
        quality_contract?: any;
        fidelity_score?: number;
        commercial_score?: number;
        diversity_score?: number;
        grounding_reliability?: number;
        reason_codes?: string[];
        repair_applied?: boolean;
        classifier_summary?: any;
        reference_pack_stats?: Record<string, number>;
    } | null = null;

    if (isDone) {
        const resp = status.response;
        currentImages = resp.images;
        promptInfo = {
            optimized_prompt: resp.optimized_prompt,
            thinking_level: resp.thinking_level,
            generation_time: resp.generation_time,
            grounding: resp.grounding,
            pipeline_mode: resp.pipeline_mode,
            failed_indices: resp.failed_indices,
            quality_contract: resp.quality_contract,
            fidelity_score: resp.fidelity_score,
            commercial_score: resp.commercial_score,
            diversity_score: resp.diversity_score,
            grounding_reliability: resp.grounding_reliability,
            reason_codes: resp.reason_codes,
            repair_applied: resp.repair_applied,
            classifier_summary: resp.classifier_summary,
            reference_pack_stats: resp.reference_pack_stats,
        };
    }

    // Filtrar do histórico os itens que já estão na geração atual (evita duplicatas no grid)
    const currentFilenames = new Set(currentImages.map(img => img.filename));
    const filteredHistory = mediaHistory.filter(h => !currentFilenames.has(h.filename));

    const hasAnything = currentImages.length > 0 || filteredHistory.length > 0;


    if (!hasAnything) {
        return (
            <div className="gallery-state-wrap">
                <div className="gallery-empty" role="status" aria-live="polite">
                    <div className="empty-icon" aria-hidden="true">✦</div>
                    <p className="t-h4 text-secondary">Pronto para gerar</p>
                    <p className="t-sm text-tertiary" style={{ maxWidth: 320, textAlign: 'center' }}>
                        Escreva um prompt ou deixe em branco para o agente criar autonomamente.
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
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                >
                    <div className="flex items-center gap-2" style={{ marginBottom: 6 }}>
                        <CheckCircle size={14} className="text-success" aria-hidden="true" />
                        <span className="t-label text-success">Prompt otimizado pelo Agente</span>
                        {promptInfo.pipeline_mode && (
                            <span className="badge">
                                {promptInfo.pipeline_mode === 'reference_mode' ? 'Com referência' : 'Sem referência'}
                            </span>
                        )}
                        {promptInfo.thinking_level && <span className="badge">{promptInfo.thinking_level}</span>}
                        {promptInfo.grounding && (
                            <span className="badge" title={`engine: ${promptInfo.grounding.source_engine || promptInfo.grounding.engine}`}>
                                {promptInfo.grounding.effective ? 'Grounding ativo' : 'Grounding inativo'}
                            </span>
                        )}
                        {promptInfo.generation_time && (
                            <span className="t-xs text-tertiary" style={{ marginLeft: 'auto' }}>
                                {promptInfo.generation_time.toFixed(1)}s
                            </span>
                        )}
                    </div>
                    {promptInfo.grounding?.trigger_reason && (
                        <p className="t-xs text-tertiary" style={{ marginBottom: 6 }}>
                            Motivo grounding: {promptInfo.grounding.trigger_reason}
                        </p>
                    )}
                    {promptInfo.quality_contract && (
                        <p className="t-xs text-tertiary" style={{ marginBottom: 6 }}>
                            Efetividade: G {Number(promptInfo.quality_contract.global_score || 0).toFixed(2)}
                            {' · '}F {Number(promptInfo.fidelity_score || 0).toFixed(2)}
                            {' · '}C {Number(promptInfo.commercial_score || 0).toFixed(2)}
                            {' · '}D {Number(promptInfo.diversity_score || 0).toFixed(2)}
                            {' · '}GR {Number(promptInfo.grounding_reliability || 0).toFixed(2)}
                        </p>
                    )}
                    {promptInfo.repair_applied && (
                        <p className="t-xs text-warning" style={{ marginBottom: 6 }}>
                            Repair pass aplicado automaticamente.
                        </p>
                    )}
                    {promptInfo.reason_codes?.length ? (
                        <p className="t-xs text-tertiary" style={{ marginBottom: 6 }}>
                            Códigos: {promptInfo.reason_codes.slice(0, 4).join(', ')}
                        </p>
                    ) : null}
                    {status.type === 'done_partial' && promptInfo.failed_indices?.length ? (
                        <div className="step-analysis-card" style={{ marginBottom: 8 }}>
                            <p className="step-analysis-title">
                                <AlertTriangle size={12} style={{ marginRight: 6 }} />
                                Geração parcial
                            </p>
                            <p className="step-analysis-body">
                                Falharam os índices: {promptInfo.failed_indices.join(', ')}.
                            </p>
                        </div>
                    ) : null}
                    <p className="t-sm text-secondary prompt-text">{promptInfo.optimized_prompt}</p>
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
                            onDragStart={e => setDragPayload(e, imageUrl(img.url), img.filename)}
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
                        <HistoryCard key={item.id} item={item} index={i} onLightboxItem={openLightboxWithItem} onDelete={onHistoryDelete} />
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
