import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, ZoomIn, X, CheckCircle } from 'lucide-react';
import type { GenerationStatus } from '../types';
import { imageUrl } from '../lib/api';
import './Gallery.css';

interface Props {
    status: GenerationStatus;
}

export function Gallery({ status }: Props) {
    const [lightbox, setLightbox] = useState<string | null>(null);

    if (status.type === 'idle') {
        return (
            <div className="gallery-empty" role="status" aria-live="polite">
                <div className="empty-icon" aria-hidden="true">✦</div>
                <p className="t-h4 text-secondary">Pronto para gerar</p>
                <p className="t-sm text-tertiary" style={{ maxWidth: 320, textAlign: 'center' }}>
                    Escreva um prompt ou deixe em branco para o agente criar autonomamente.
                </p>
            </div>
        );
    }

    if (status.type === 'thinking') {
        return (
            <div className="gallery-loading" role="status" aria-live="polite" aria-label="Agente refinando prompt">
                <motion.div
                    className="thinking-orb"
                    animate={{ scale: [1, 1.12, 1], opacity: [0.6, 1, 0.6] }}
                    transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
                    aria-hidden="true"
                />
                <p className="t-sm text-secondary">Agente refinando prompt…</p>
            </div>
        );
    }

    if (status.type === 'generating') {
        const { progress } = status;
        return (
            <div className="gallery-loading" role="status" aria-live="polite" aria-label={`Gerando imagens ${progress}%`}>
                <div className="skeleton-grid" aria-hidden="true">
                    {[0, 1, 2, 3].map(i => (
                        <div key={i} className="skeleton skeleton-card" />
                    ))}
                </div>
                <div className="progress-bar-wrap" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
                    <motion.div
                        className="progress-bar-fill"
                        initial={{ width: 0 }}
                        animate={{ width: `${progress}%` }}
                        transition={{ ease: 'easeOut' }}
                    />
                </div>
                <p className="t-xs text-tertiary">Gerando imagens… {progress}%</p>
            </div>
        );
    }

    if (status.type === 'error') {
        return (
            <div className="gallery-empty" role="alert">
                <p className="t-h4 text-error">Erro na geração</p>
                <p className="t-sm text-secondary" style={{ maxWidth: 360, textAlign: 'center' }}>{status.message}</p>
            </div>
        );
    }

    // Done — type guard seguro
    if (status.type !== 'done') return null;
    const { images, optimized_prompt, thinking_level, generation_time } = status.response;

    return (
        <>
            <div className="gallery-done">
                {/* Prompt otimizado */}
                <motion.div
                    className="prompt-result-card"
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                >
                    <div className="flex items-center gap-2" style={{ marginBottom: 6 }}>
                        <CheckCircle size={14} className="text-success" aria-hidden="true" />
                        <span className="t-label text-success">Prompt otimizado pelo Agente</span>
                        {thinking_level && (
                            <span className="badge">{thinking_level}</span>
                        )}
                        {generation_time && (
                            <span className="t-xs text-tertiary" style={{ marginLeft: 'auto' }}>
                                {generation_time.toFixed(1)}s
                            </span>
                        )}
                    </div>
                    <p className="t-sm text-secondary prompt-text">{optimized_prompt}</p>
                </motion.div>

                {/* Grid de imagens */}
                <div
                    className={`image-grid image-grid--${Math.min(images.length, 4)}`}
                    role="list"
                    aria-label={`${images.length} imagens geradas`}
                >
                    <AnimatePresence>
                        {images.map((img, i) => (
                            <motion.div
                                key={img.filename}
                                className="image-card"
                                role="listitem"
                                initial={{ opacity: 0, scale: 0.92 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{ duration: 0.3, delay: i * 0.08 }}
                            >
                                <img
                                    src={imageUrl(img.url)}
                                    alt={`Imagem gerada ${i + 1}`}
                                    className="image-card-img"
                                    loading="lazy"
                                />
                                <div className="image-card-actions" role="group" aria-label={`Ações imagem ${i + 1}`}>
                                    <button
                                        className="img-action-btn"
                                        onClick={() => setLightbox(imageUrl(img.url))}
                                        aria-label={`Ver imagem ${i + 1} em tela cheia`}
                                        title="Ampliar"
                                    >
                                        <ZoomIn size={15} />
                                    </button>
                                    <a
                                        href={imageUrl(img.url)}
                                        download={img.filename}
                                        className="img-action-btn"
                                        aria-label={`Baixar imagem ${i + 1}`}
                                        title="Baixar"
                                    >
                                        <Download size={15} />
                                    </a>
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            </div>

            {/* Lightbox */}
            <AnimatePresence>
                {lightbox && (
                    <motion.div
                        className="lightbox"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setLightbox(null)}
                        role="dialog"
                        aria-modal="true"
                        aria-label="Imagem ampliada"
                    >
                        <button
                            className="lightbox-close"
                            onClick={() => setLightbox(null)}
                            aria-label="Fechar"
                        >
                            <X size={20} />
                        </button>
                        <motion.img
                            src={lightbox}
                            alt="Imagem ampliada"
                            className="lightbox-img"
                            initial={{ scale: 0.9 }}
                            animate={{ scale: 1 }}
                            exit={{ scale: 0.9 }}
                            onClick={e => e.stopPropagation()}
                        />
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}
