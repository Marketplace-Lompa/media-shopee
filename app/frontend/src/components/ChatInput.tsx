import { useRef, useState, useEffect } from 'react';
import type { DragEvent, KeyboardEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Send, ImagePlus, X, Loader2,
    SlidersHorizontal, ChevronDown, ChevronUp, Globe, Wand2, Pencil
} from 'lucide-react';
import type { AspectRatio, Resolution, GenerationStatus, GroundingStrategy, GuidedBrief, EditTarget } from '../types';
import './ChatInput.css';

interface Props {
    status: GenerationStatus;
    onSubmit: (payload: {
        prompt: string;
        files: File[];
        n_images: number;
        aspect_ratio: AspectRatio;
        resolution: Resolution;
        grounding_strategy: GroundingStrategy;
        guided_brief?: GuidedBrief;
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

const AR_OPTIONS: AspectRatio[] = ['1:1', '9:16', '16:9', '4:3', '3:4'];
const RES_OPTIONS: Resolution[] = ['1K', '2K', '4K'];
const N_OPTIONS = [1, 2, 3, 4];
const AGE_OPTIONS = ['18-24', '25-34', '35-44', '45+'] as const;
const SET_OPTIONS = ['unica', 'conjunto'] as const;
const SCENE_OPTIONS = ['interno', 'externo'] as const;
const POSE_OPTIONS = ['tradicional', 'criativa'] as const;
const CAPTURE_OPTIONS = ['distante', 'media', 'proxima'] as const;

interface HistoryDragPayload {
    url: string;
    filename?: string;
    prompt?: string;
}

export function ChatInput({ status, onSubmit, externalData, onClearExternalData, editTarget, onEditSubmit, onEditCancel }: Props) {
    const [prompt, setPrompt] = useState('');
    const [files, setFiles] = useState<File[]>([]);
    const [showParams, setShowParams] = useState(false);
    const [ar, setAr] = useState<AspectRatio>('1:1');
    const [res, setRes] = useState<Resolution>('1K');
    const [n, setN] = useState(1);
    const [groundingStrategy, setGroundingStrategy] = useState<GroundingStrategy>('auto');
    const [guidedEnabled, setGuidedEnabled] = useState(false);
    const [guidedExpanded, setGuidedExpanded] = useState(true);
    const [guidedAgeRange, setGuidedAgeRange] = useState<(typeof AGE_OPTIONS)[number]>('25-34');
    const [guidedSetMode, setGuidedSetMode] = useState<(typeof SET_OPTIONS)[number]>('unica');
    const [guidedSceneType, setGuidedSceneType] = useState<(typeof SCENE_OPTIONS)[number]>('externo');
    const [guidedPoseStyle, setGuidedPoseStyle] = useState<(typeof POSE_OPTIONS)[number]>('tradicional');
    const [guidedCaptureDistance, setGuidedCaptureDistance] = useState<(typeof CAPTURE_OPTIONS)[number]>('media');
    const [dragOver, setDragOver] = useState(false);
    const [dropMessage, setDropMessage] = useState<string | null>(null);
    const fileRef = useRef<HTMLInputElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const busy =
        status.type === 'mode_selected' ||
        status.type === 'researching' ||
        status.type === 'analyzing' ||
        status.type === 'triage_done' ||
        status.type === 'prompt_ready' ||
        status.type === 'editing' ||
        status.type === 'generating';

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
        if (busy) return;
        if (guidedEnabled) {
            setGuidedExpanded(false);
        }
        const guidedBrief: GuidedBrief | undefined = guidedEnabled
            ? {
                enabled: true,
                model: { age_range: guidedAgeRange },
                garment: {
                    set_mode: guidedSetMode,
                },
                scene: { type: guidedSceneType },
                pose: { style: guidedPoseStyle },
                capture: { distance: guidedCaptureDistance },
                fidelity_mode: files.length > 0 && guidedSetMode === 'conjunto' ? 'estrita' : 'balanceada',
            }
            : undefined;
        onSubmit({
            prompt,
            files,
            n_images: n,
            aspect_ratio: ar,
            resolution: res,
            grounding_strategy: groundingStrategy,
            guided_brief: guidedBrief,
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

    function toggleGuidedMode() {
        setGuidedEnabled(v => !v);
        setGuidedExpanded(true);
    }

    const guidedSummary = `Idade ${guidedAgeRange} · ${guidedSetMode === 'conjunto' ? 'Conjunto' : 'Peça única'} · ${guidedSceneType} · ${guidedPoseStyle} · ${guidedCaptureDistance}`;

    function handleDragOver(event: DragEvent<HTMLDivElement>) {
        if (busy) return;
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
        if (busy) return;

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

            {/* Parâmetros de geração */}
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

                            <fieldset className="param-group param-group--toggle">
                                <div className="param-chips" role="group" aria-label="Estratégia de grounding">
                                    <button
                                        className={`chip chip--toggle ${groundingStrategy === 'auto' ? 'chip--active chip--grounding' : ''}`}
                                        onClick={() => setGroundingStrategy('auto')}
                                        type="button"
                                        aria-pressed={groundingStrategy === 'auto'}
                                        title="Decide automaticamente quando pesquisar"
                                    >
                                        <Globe size={14} />
                                        Auto
                                    </button>
                                    <button
                                        className={`chip chip--toggle ${groundingStrategy === 'on' ? 'chip--active chip--grounding' : ''}`}
                                        onClick={() => setGroundingStrategy('on')}
                                        type="button"
                                        aria-pressed={groundingStrategy === 'on'}
                                        title="Força pesquisa web"
                                    >
                                        On
                                    </button>
                                    <button
                                        className={`chip chip--toggle ${groundingStrategy === 'off' ? 'chip--active' : ''}`}
                                        onClick={() => setGroundingStrategy('off')}
                                        type="button"
                                        aria-pressed={groundingStrategy === 'off'}
                                        title="Desliga grounding"
                                    >
                                        Off
                                    </button>
                                </div>
                            </fieldset>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Modo guiado */}
            <AnimatePresence>
                {guidedEnabled && (
                    <motion.div
                        className="guided-panel"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.2, ease: 'easeOut' }}
                    >
                        <div className="guided-panel-head">
                            <span className="guided-panel-title">Modo Guiado</span>
                            <button
                                type="button"
                                className="guided-toggle-btn"
                                onClick={() => setGuidedExpanded(v => !v)}
                                disabled={busy}
                                aria-expanded={guidedExpanded}
                                aria-label={guidedExpanded ? 'Recolher modo guiado' : 'Expandir modo guiado'}
                            >
                                {guidedExpanded ? 'Recolher' : 'Editar'}
                            </button>
                        </div>

                        {guidedExpanded && (
                            <div className="guided-grid">
                                <fieldset className="param-group">
                                    <legend className="t-label text-tertiary">Faixa etária</legend>
                                    <div className="param-chips">
                                        {AGE_OPTIONS.map(v => (
                                            <button
                                                key={v}
                                                type="button"
                                                className={`chip ${guidedAgeRange === v ? 'chip--active' : ''}`}
                                                onClick={() => setGuidedAgeRange(v)}
                                                aria-pressed={guidedAgeRange === v}
                                                disabled={busy}
                                            >
                                                {v}
                                            </button>
                                        ))}
                                    </div>
                                </fieldset>

                                <fieldset className="param-group">
                                    <legend className="t-label text-tertiary">Peça</legend>
                                    <div className="param-chips">
                                        {SET_OPTIONS.map(v => (
                                            <button
                                                key={v}
                                                type="button"
                                                className={`chip ${guidedSetMode === v ? 'chip--active' : ''}`}
                                                onClick={() => setGuidedSetMode(v)}
                                                aria-pressed={guidedSetMode === v}
                                                disabled={busy}
                                            >
                                                {v === 'unica' ? 'Única' : 'Conjunto'}
                                            </button>
                                        ))}
                                    </div>
                                </fieldset>

                                <fieldset className="param-group">
                                    <legend className="t-label text-tertiary">Cenário</legend>
                                    <div className="param-chips">
                                        {SCENE_OPTIONS.map(v => (
                                            <button
                                                key={v}
                                                type="button"
                                                className={`chip ${guidedSceneType === v ? 'chip--active' : ''}`}
                                                onClick={() => setGuidedSceneType(v)}
                                                aria-pressed={guidedSceneType === v}
                                                disabled={busy}
                                            >
                                                {v}
                                            </button>
                                        ))}
                                    </div>
                                </fieldset>

                                <fieldset className="param-group">
                                    <legend className="t-label text-tertiary">Pose</legend>
                                    <div className="param-chips">
                                        {POSE_OPTIONS.map(v => (
                                            <button
                                                key={v}
                                                type="button"
                                                className={`chip ${guidedPoseStyle === v ? 'chip--active' : ''}`}
                                                onClick={() => setGuidedPoseStyle(v)}
                                                aria-pressed={guidedPoseStyle === v}
                                                disabled={busy}
                                            >
                                                {v}
                                            </button>
                                        ))}
                                    </div>
                                </fieldset>

                                <fieldset className="param-group">
                                    <legend className="t-label text-tertiary">Captura</legend>
                                    <div className="param-chips">
                                        {CAPTURE_OPTIONS.map(v => (
                                            <button
                                                key={v}
                                                type="button"
                                                className={`chip ${guidedCaptureDistance === v ? 'chip--active' : ''}`}
                                                onClick={() => setGuidedCaptureDistance(v)}
                                                aria-pressed={guidedCaptureDistance === v}
                                                disabled={busy}
                                            >
                                                {v}
                                            </button>
                                        ))}
                                    </div>
                                </fieldset>
                            </div>
                        )}

                        <p className="guided-summary-text">Brief Guiado: {guidedSummary}</p>
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
                        {files.map((f, i) => (
                            <div key={i} className="file-thumb">
                                <img
                                    src={URL.createObjectURL(f)}
                                    alt={f.name}
                                />
                                <button
                                    className="file-remove"
                                    onClick={() => removeFile(i)}
                                    aria-label={`Remover ${f.name}`}
                                >
                                    <X size={10} />
                                </button>
                            </div>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Input principal */}
            <div className="chat-input-box">
                <button
                    className="input-action-btn"
                    onClick={() => fileRef.current?.click()}
                    disabled={busy}
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
                    placeholder={editTarget ? 'Descreva a modificação desejada… (ex: troque o fundo por praia)' : 'Descreva a geração ou deixe vazio para o agente criar sozinho…'}
                    value={prompt}
                    onChange={e => setPrompt(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={busy}
                    rows={1}
                    aria-label={editTarget ? 'Instrução de edição' : 'Prompt de geração'}
                    aria-describedby="chat-hint"
                />

                <button
                    className="input-action-btn"
                    onClick={() => setShowParams(v => !v)}
                    type="button"
                    aria-label="Parâmetros de geração"
                    aria-expanded={showParams}
                    title="Configurações"
                >
                    <SlidersHorizontal size={18} />
                    {showParams ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                </button>

                <button
                    className={`input-action-btn ${guidedEnabled ? 'input-action-btn--guided' : ''}`}
                    onClick={toggleGuidedMode}
                    type="button"
                    aria-label="Alternar modo guiado"
                    aria-pressed={guidedEnabled}
                    title="Modo Guiado"
                    disabled={busy}
                >
                    <Wand2 size={18} />
                </button>

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
                    disabled={busy || (!!editTarget && !prompt.trim())}
                    type="button"
                    aria-label={busy ? 'Processando…' : editTarget ? 'Aplicar edição' : 'Gerar imagem'}
                >
                    {busy
                        ? <Loader2 size={18} className="spin" aria-hidden="true" />
                        : editTarget
                            ? <Pencil size={18} aria-hidden="true" />
                            : <Send size={18} aria-hidden="true" />
                    }
                </button>
            </div>

            <p id="chat-hint" className="t-xs text-tertiary" style={{ paddingLeft: 4 }}>
                {busy
                    ? status.type === 'mode_selected'
                        ? '✦ Definindo modo do pipeline…'
                        : status.type === 'analyzing'
                            ? '✦ Agente analisando…'
                            : status.type === 'triage_done'
                                ? '✦ Triage de grounding…'
                                : status.type === 'prompt_ready'
                                    ? '✦ Prompt criado, enviando ao Nano…'
                                    : status.type === 'editing'
                                        ? '✏️ Editando imagem…'
                                        : `✦ Gerando ${n > 1 ? n + ' imagens' : 'imagem'}…`
                    : dragOver
                        ? 'Solte aqui para reutilizar a mídia como referência'
                        : editTarget
                            ? 'Enter para aplicar edição · Esc para cancelar'
                            : 'Enter para gerar · Shift+Enter para nova linha · Sem prompt = modo autônomo'
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
