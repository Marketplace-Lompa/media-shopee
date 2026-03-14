import { useRef, useState, useEffect } from 'react';
import type { DragEvent, KeyboardEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Send, ImagePlus, X,
    SlidersHorizontal, ChevronDown, ChevronUp, Pencil
} from 'lucide-react';
import type {
    AspectRatio,
    Resolution,
    EditTarget,
    Preset,
    ScenePreference,
    FidelityMode,
    PoseFlexMode,
} from '../types';
import './ChatInput.css';

interface Props {
    onSubmit: (payload: {
        prompt: string;
        files: File[];
        n_images: number;
        aspect_ratio: AspectRatio;
        resolution: Resolution;
        preset: Preset;
        scene_preference: ScenePreference;
        fidelity_mode: FidelityMode;
        pose_flex_mode: PoseFlexMode;
    }) => void;
    externalData?: {
        prompt?: string;
        references?: string[];
    } | null;
    onClearExternalData?: () => void;
    editTarget?: EditTarget | null;
    onEditSubmit?: (editInstruction: string, files?: File[]) => void;
    onEditCancel?: () => void;
}

const AR_OPTIONS: AspectRatio[] = ['4:5', '1:1', '9:16', '16:9', '4:3', '3:4'];
const RES_OPTIONS: Resolution[] = ['1K', '2K', '4K'];
const N_OPTIONS = [1, 2, 3, 4];
const PRESET_OPTIONS: Array<{ value: Preset; label: string }> = [
    { value: 'catalog_clean', label: 'Catálogo clean' },
    { value: 'marketplace_lifestyle', label: 'Marketplace' },
    { value: 'premium_lifestyle', label: 'Premium' },
    { value: 'ugc_real_br', label: 'UGC real BR' },
];
const SCENE_PREF_OPTIONS: Array<{ value: ScenePreference; label: string }> = [
    { value: 'auto_br', label: 'Auto BR' },
    { value: 'indoor_br', label: 'Indoor BR' },
    { value: 'outdoor_br', label: 'Outdoor BR' },
];
const FIDELITY_OPTIONS: Array<{ value: FidelityMode; label: string }> = [
    { value: 'balanceada', label: 'Balanceada' },
    { value: 'estrita', label: 'Estrita' },
];
const POSE_FLEX_OPTIONS: Array<{ value: PoseFlexMode; label: string }> = [
    { value: 'auto', label: 'Auto' },
    { value: 'controlled', label: 'Controlada' },
    { value: 'balanced', label: 'Balanceada' },
    { value: 'dynamic', label: 'Dinâmica' },
];
interface HistoryDragPayload {
    url: string;
    filename?: string;
    prompt?: string;
}

export function ChatInput({ onSubmit, externalData, onClearExternalData, editTarget, onEditSubmit, onEditCancel }: Props) {
    const [prompt, setPrompt] = useState('');
    const [files, setFiles] = useState<File[]>([]);
    const [showParams, setShowParams] = useState(false);
    const [ar, setAr] = useState<AspectRatio>('4:5');
    const [res, setRes] = useState<Resolution>('1K');
    const [n, setN] = useState(1);
    const [preset, setPreset] = useState<Preset>('marketplace_lifestyle');
    const [scenePreference, setScenePreference] = useState<ScenePreference>('auto_br');
    const [fidelityMode, setFidelityMode] = useState<FidelityMode>('balanceada');
    const [poseFlexMode, setPoseFlexMode] = useState<PoseFlexMode>('auto');
    const [dragOver, setDragOver] = useState(false);
    const [dropMessage, setDropMessage] = useState<string | null>(null);
    const fileRef = useRef<HTMLInputElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    // Hook para carregar dados externos (botão Reuse do histórico)
    useEffect(() => {
        if (externalData) {
            if (externalData.prompt) {
                // eslint-disable-next-line react-hooks/set-state-in-effect
                setPrompt(externalData.prompt);
            }
            if (externalData.references && externalData.references.length > 0) {
                // Carregar todas as refs simultaneamente
                Promise.all(externalData.references.map(async (url) => {
                    try {
                        const response = await fetch(url);
                        if (!response.ok) return null;
                        const blob = await response.blob();
                        const filename = url.split('/').pop() || 'reference.jpg';
                        return new File([blob], filename, { type: blob.type || 'image/jpeg' });
                    } catch {
                        return null;
                    }
                })).then((newFiles) => {
                    const validFiles = newFiles.filter((f): f is File => f !== null);
                    if (validFiles.length > 0) {
                        setFiles(prev => [...prev, ...validFiles].slice(0, 14));
                    }
                });
            }
            onClearExternalData?.();
        }
    }, [externalData, onClearExternalData]);

    // Auto-resize textarea conforme conteúdo
    useEffect(() => {
        const el = textareaRef.current;
        if (!el) return;
        el.style.height = 'auto';
        el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
    }, [prompt]);

    function handleFiles(incoming: FileList | null) {
        if (!incoming) return;
        const valid = Array.from(incoming).filter(f => f.type.startsWith('image/'));
        setFiles(prev => [...prev, ...valid].slice(0, 14));
    }

    function removeFile(i: number) {
        setFiles(prev => prev.filter((_, idx) => idx !== i));
    }

    function handleSubmit() {
        if (!editTarget && !prompt.trim() && files.length === 0) return;
        onSubmit({
            prompt,
            files,
            n_images: n,
            aspect_ratio: ar,
            resolution: res,
            preset,
            scene_preference: scenePreference,
            fidelity_mode: fidelityMode,
            pose_flex_mode: poseFlexMode,
        });
        setPrompt('');
        setFiles([]);
    }

    function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (editTarget && onEditSubmit && prompt.trim()) {
                onEditSubmit(prompt.trim(), files.length ? files : undefined);
                setPrompt('');
            } else {
                handleSubmit();
            }
        }
        if (e.key === 'Escape' && editTarget && onEditCancel) {
            onEditCancel();
        }
    }

    function readHistoryPayload(event: DragEvent<HTMLDivElement>): HistoryDragPayload | null {
        const custom = event.dataTransfer.getData('application/x-media-history');
        if (custom) {
            try {
                const parsed = JSON.parse(custom) as HistoryDragPayload;
                if (parsed.url) return parsed;
            } catch {
                // no-op
            }
        }

        const text = event.dataTransfer.getData('text/plain')?.trim();
        if (!text) return null;

        if (text.startsWith('{')) {
            try {
                const parsed = JSON.parse(text) as HistoryDragPayload;
                if (parsed.url) return parsed;
            } catch {
                return null;
            }
        }

        if (text.startsWith('http://') || text.startsWith('https://') || text.startsWith('/')) {
            return { url: text };
        }

        return null;
    }

    async function attachFromHistory(payload: HistoryDragPayload) {
        const response = await fetch(payload.url);
        if (!response.ok) {
            throw new Error(`Falha ao baixar mídia (${response.status})`);
        }

        const blob = await response.blob();
        if (!blob.type.startsWith('image/')) {
            throw new Error('A mídia arrastada não é uma imagem');
        }

        const fallbackExt = blob.type.split('/')[1] || 'jpg';
        const fallbackName = `history_${Date.now()}.${fallbackExt}`;
        const filename = payload.filename || fallbackName;
        const file = new File([blob], filename, { type: blob.type || 'image/jpeg' });

        setFiles(prev => [...prev, file].slice(0, 14));
    }

    function clearDropMessageLater(message: string) {
        setDropMessage(message);
        window.setTimeout(() => setDropMessage(null), 2200);
    }

    function handleDragOver(event: DragEvent<HTMLDivElement>) {
        const hasPayload =
            event.dataTransfer.types.includes('application/x-media-history') ||
            event.dataTransfer.types.includes('text/plain');
        if (!hasPayload) return;
        event.preventDefault();
        event.dataTransfer.dropEffect = 'copy';
        setDragOver(true);
    }

    function handleDragLeave() {
        setDragOver(false);
    }

    async function handleDrop(event: DragEvent<HTMLDivElement>) {
        event.preventDefault();
        setDragOver(false);

        const payload = readHistoryPayload(event);
        if (!payload) return;

        try {
            await attachFromHistory(payload);
            if (payload.prompt && !prompt.trim()) {
                setPrompt(payload.prompt);
            }
            clearDropMessageLater('Referência adicionada ao input');
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Falha ao adicionar referência';
            clearDropMessageLater(message);
        }
    }

    return (
        <div
            className={`chat-input-wrapper ${dragOver ? 'chat-input-wrapper--drag' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
        >

            {/* Banner de edição — modo /alterar */}
            <AnimatePresence>
                {editTarget && (
                    <motion.div
                        className="edit-banner"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.2 }}
                    >
                        <div className="edit-banner-content">
                            <img
                                className="edit-banner-thumb"
                                src={editTarget.url.startsWith('http') ? editTarget.url : `${window.location.origin}${editTarget.url}`}
                                alt="Imagem a editar"
                            />
                            <div className="edit-banner-info">
                                <span className="t-xs edit-banner-label">
                                    <Pencil size={12} /> Modo edição
                                </span>
                                <span className="t-xs text-tertiary">{editTarget.filename}</span>
                            </div>
                            <button
                                className="edit-banner-close"
                                onClick={() => onEditCancel?.()}
                                type="button"
                                aria-label="Cancelar edição"
                            >
                                <X size={14} />
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Preset e Cena — sempre visível */}
            {!editTarget && (
                <div className="preset-row">
                    <fieldset className="param-group">
                        <legend className="t-label text-tertiary">Estilo</legend>
                        <div className="param-chips">
                            {PRESET_OPTIONS.map(option => (
                                <button
                                    key={option.value}
                                    className={`chip ${preset === option.value ? 'chip--active' : ''}`}
                                    onClick={() => setPreset(option.value)}
                                    type="button"
                                    aria-pressed={preset === option.value}
                                >{option.label}</button>
                            ))}
                        </div>
                    </fieldset>

                    <fieldset className="param-group">
                        <legend className="t-label text-tertiary">Cena</legend>
                        <div className="param-chips">
                            {SCENE_PREF_OPTIONS.map(option => (
                                <button
                                    key={option.value}
                                    className={`chip ${scenePreference === option.value ? 'chip--active' : ''}`}
                                    onClick={() => setScenePreference(option.value)}
                                    type="button"
                                    aria-pressed={scenePreference === option.value}
                                >{option.label}</button>
                            ))}
                        </div>
                    </fieldset>
                </div>
            )}

            {/* Painel avançado (recolhido por padrão) */}
            <AnimatePresence>
                {showParams && (
                    <motion.div
                        className="params-panel"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.2, ease: 'easeOut' }}
                    >
                        <div className="params-row">
                            <fieldset className="param-group">
                                <legend className="t-label text-tertiary">Fidelidade</legend>
                                <div className="param-chips">
                                    {FIDELITY_OPTIONS.map(option => (
                                        <button
                                            key={option.value}
                                            className={`chip ${fidelityMode === option.value ? 'chip--active' : ''}`}
                                            onClick={() => setFidelityMode(option.value)}
                                            type="button"
                                            aria-pressed={fidelityMode === option.value}
                                            disabled={busy}
                                        >{option.label}</button>
                                    ))}
                                </div>
                            </fieldset>

                            <fieldset className="param-group">
                                <legend className="t-label text-tertiary">Pose</legend>
                                <div className="param-chips">
                                    {POSE_FLEX_OPTIONS.map(option => (
                                        <button
                                            key={option.value}
                                            className={`chip ${poseFlexMode === option.value ? 'chip--active' : ''}`}
                                            onClick={() => setPoseFlexMode(option.value)}
                                            type="button"
                                            aria-pressed={poseFlexMode === option.value}
                                            disabled={busy}
                                        >{option.label}</button>
                                    ))}
                                </div>
                                <p className="t-xs text-tertiary param-help">
                                    Auto analisa as referências e decide a pose no momento do job.
                                </p>
                            </fieldset>

                            <fieldset className="param-group">
                                <legend className="t-label text-tertiary">Aspecto</legend>
                                <div className="param-chips">
                                    {AR_OPTIONS.map(v => (
                                        <button
                                            key={v}
                                            className={`chip ${ar === v ? 'chip--active' : ''}`}
                                            onClick={() => setAr(v)}
                                            type="button"
                                            aria-pressed={ar === v}
                                        >{v}</button>
                                    ))}
                                </div>
                            </fieldset>

                            <fieldset className="param-group">
                                <legend className="t-label text-tertiary">Qualidade</legend>
                                <div className="param-chips">
                                    {RES_OPTIONS.map(v => (
                                        <button
                                            key={v}
                                            className={`chip ${res === v ? 'chip--active' : ''}`}
                                            onClick={() => setRes(v)}
                                            type="button"
                                            aria-pressed={res === v}
                                        >{v}</button>
                                    ))}
                                </div>
                            </fieldset>

                            <fieldset className="param-group param-group--narrow">
                                <legend className="t-label text-tertiary">Qtd</legend>
                                <div className="param-chips">
                                    {N_OPTIONS.map(v => (
                                        <button
                                            key={v}
                                            className={`chip chip--square ${n === v ? 'chip--active' : ''}`}
                                            onClick={() => setN(v)}
                                            type="button"
                                            aria-pressed={n === v}
                                        >{v}</button>
                                    ))}
                                </div>
                            </fieldset>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Preview de imagens anexadas */}
            <AnimatePresence>
                {files.length > 0 && (
                    <motion.div
                        className="file-preview-row"
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 8 }}
                    >
                        {files.map((f, i) => {
                            const previewUrl = URL.createObjectURL(f);
                            return (
                            <div key={`${f.name}-${f.size}-${i}`} className="file-thumb">
                                <img
                                    src={previewUrl}
                                    alt={f.name}
                                    onLoad={() => URL.revokeObjectURL(previewUrl)}
                                />
                                <button
                                    className="file-remove"
                                    onClick={() => removeFile(i)}
                                    aria-label={`Remover ${f.name}`}
                                >
                                    <X size={10} />
                                </button>
                            </div>
                            );
                        })}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Input principal */}
            <div className="chat-input-box">
                <button
                    className="input-action-btn"
                    onClick={() => fileRef.current?.click()}
                    type="button"
                    aria-label="Anexar imagem"
                    title="Anexar imagem"
                >
                    <ImagePlus size={18} />
                </button>
                <input
                    ref={fileRef}
                    type="file"
                    accept="image/*"
                    multiple
                    style={{ display: 'none' }}
                    onChange={e => handleFiles(e.target.files)}
                    aria-hidden="true"
                />

                <textarea
                    ref={textareaRef}
                    className="chat-textarea"
                    placeholder={editTarget ? 'Descreva a modificação desejada…' : 'Descreva o que deseja ou envie fotos da peça…'}
                    value={prompt}
                    onChange={e => setPrompt(e.target.value)}
                    onKeyDown={handleKeyDown}
                    rows={1}
                    aria-label={editTarget ? 'Instrução de edição' : 'Prompt de geração'}
                    aria-describedby="chat-hint"
                />

{!editTarget && (
                <button
                    className="input-action-btn"
                    onClick={() => setShowParams(v => !v)}
                    type="button"
                    aria-label="Configurações avançadas"
                    aria-expanded={showParams}
                    title="Avançado"
                >
                    <SlidersHorizontal size={18} />
                    {showParams ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                </button>
)}

                <button
                    className={`send-btn ${editTarget ? 'send-btn--edit' : ''}`}
                    onClick={() => {
                        if (editTarget && onEditSubmit && prompt.trim()) {
                            onEditSubmit(prompt.trim(), files.length ? files : undefined);
                            setPrompt('');
                        } else {
                            handleSubmit();
                        }
                    }}
                    disabled={(!!editTarget && !prompt.trim()) || (!editTarget && !prompt.trim() && files.length === 0)}
                    type="button"
                    aria-label={editTarget ? 'Aplicar edição' : 'Gerar imagem'}
                >
                    {editTarget
                        ? <Pencil size={18} aria-hidden="true" />
                        : <Send size={18} aria-hidden="true" />
                    }
                </button>
            </div>

            <p id="chat-hint" className="t-xs text-tertiary" style={{ paddingLeft: 4 }}>
                {dragOver
                    ? 'Solte aqui para reutilizar a mídia como referência'
                    : editTarget
                        ? 'Enter para aplicar edição · Esc para cancelar'
                        : 'Enter para gerar · Shift+Enter para nova linha'
                }
            </p>

            {dropMessage && (
                <p className="t-xs text-secondary chat-drop-message" role="status" aria-live="polite">
                    {dropMessage}
                </p>
            )}
        </div>
    );
}
