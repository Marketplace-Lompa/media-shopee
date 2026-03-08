import { useRef, useState } from 'react';
import type { DragEvent, KeyboardEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Send, ImagePlus, X, Loader2,
    SlidersHorizontal, ChevronDown, ChevronUp, Globe
} from 'lucide-react';
import type { AspectRatio, Resolution, GenerationStatus, GroundingStrategy } from '../types';
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
    }) => void;
}

const AR_OPTIONS: AspectRatio[] = ['1:1', '9:16', '16:9', '4:3', '3:4'];
const RES_OPTIONS: Resolution[] = ['1K', '2K', '4K'];
const N_OPTIONS = [1, 2, 3, 4];

interface HistoryDragPayload {
    url: string;
    filename?: string;
    prompt?: string;
}

export function ChatInput({ status, onSubmit }: Props) {
    const [prompt, setPrompt] = useState('');
    const [files, setFiles] = useState<File[]>([]);
    const [showParams, setShowParams] = useState(false);
    const [ar, setAr] = useState<AspectRatio>('1:1');
    const [res, setRes] = useState<Resolution>('1K');
    const [n, setN] = useState(1);
    const [groundingStrategy, setGroundingStrategy] = useState<GroundingStrategy>('auto');
    const [dragOver, setDragOver] = useState(false);
    const [dropMessage, setDropMessage] = useState<string | null>(null);
    const fileRef = useRef<HTMLInputElement>(null);
    const busy =
        status.type === 'mode_selected' ||
        status.type === 'researching' ||
        status.type === 'analyzing' ||
        status.type === 'triage_done' ||
        status.type === 'prompt_ready' ||
        status.type === 'generating';

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
        onSubmit({ prompt, files, n_images: n, aspect_ratio: ar, resolution: res, grounding_strategy: groundingStrategy });
        setPrompt('');
        setFiles([]);
    }

    function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
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
                    className="chat-textarea"
                    placeholder="Descreva a geração ou deixe vazio para o agente criar sozinho…"
                    value={prompt}
                    onChange={e => setPrompt(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={busy}
                    rows={1}
                    aria-label="Prompt de geração"
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
                    className="send-btn"
                    onClick={handleSubmit}
                    disabled={busy}
                    type="button"
                    aria-label={busy ? 'Gerando…' : 'Gerar imagem'}
                >
                    {busy
                        ? <Loader2 size={18} className="spin" aria-hidden="true" />
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
                            : `✦ Gerando ${n > 1 ? n + ' imagens' : 'imagem'}…`
                    : dragOver
                        ? 'Solte aqui para reutilizar a mídia como referência'
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
