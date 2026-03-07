import { useRef, useState } from 'react';
import type { KeyboardEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Send, ImagePlus, X, Loader2,
    SlidersHorizontal, ChevronDown, ChevronUp
} from 'lucide-react';
import type { AspectRatio, Resolution, GenerationStatus } from '../types';
import './ChatInput.css';

interface Props {
    status: GenerationStatus;
    onSubmit: (payload: {
        prompt: string;
        files: File[];
        n_images: number;
        aspect_ratio: AspectRatio;
        resolution: Resolution;
    }) => void;
}

const AR_OPTIONS: AspectRatio[] = ['1:1', '9:16', '16:9', '4:5', '3:4'];
const RES_OPTIONS: Resolution[] = ['1K', '2K', '4K'];
const N_OPTIONS = [1, 2, 3, 4];

export function ChatInput({ status, onSubmit }: Props) {
    const [prompt, setPrompt] = useState('');
    const [files, setFiles] = useState<File[]>([]);
    const [showParams, setShowParams] = useState(false);
    const [ar, setAr] = useState<AspectRatio>('1:1');
    const [res, setRes] = useState<Resolution>('1K');
    const [n, setN] = useState(1);
    const fileRef = useRef<HTMLInputElement>(null);
    const busy = status.type === 'thinking' || status.type === 'generating';

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
        onSubmit({ prompt, files, n_images: n, aspect_ratio: ar, resolution: res });
        setPrompt('');
        setFiles([]);
    }

    function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    }

    return (
        <div className="chat-input-wrapper">

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
                    ? status.type === 'thinking'
                        ? '✦ Agente refinando prompt…'
                        : `✦ Gerando ${n > 1 ? n + ' imagens' : 'imagem'}…`
                    : 'Enter para gerar · Shift+Enter para nova linha · Sem prompt = modo autônomo'
                }
            </p>
        </div>
    );
}
