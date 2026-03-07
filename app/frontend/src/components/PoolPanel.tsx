import React, { useCallback, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Trash2, User, Shirt, Mountain, Loader2 } from 'lucide-react';
import type { PoolItem, PoolType } from '../types';
import { addToPool, removeFromPool, imageUrl } from '../lib/api';
import './PoolPanel.css';

interface Props {
    items: PoolItem[];
    loading: boolean;
    onRefresh: () => void;
}

const TYPE_META: Record<PoolType, { label: string; icon: React.ElementType; color: string }> = {
    modelo: { label: 'Modelo', icon: User, color: 'var(--c-violet-400)' },
    roupa: { label: 'Roupa', icon: Shirt, color: 'var(--c-pink-400)' },
    cenario: { label: 'Cenário', icon: Mountain, color: 'var(--c-emerald-400)' },
};

const TYPES: PoolType[] = ['modelo', 'roupa', 'cenario'];

export function PoolPanel({ items, loading, onRefresh }: Props) {
    const [uploading, setUploading] = useState(false);
    const [removing, setRemoving] = useState<string | null>(null);
    const [activeType, setActiveType] = useState<PoolType | 'all'>('all');
    const [dragging, setDragging] = useState(false);

    const filtered = activeType === 'all'
        ? items
        : items.filter(i => i.type === activeType);

    async function handleUpload(files: FileList | null, type: PoolType) {
        if (!files?.length) return;
        setUploading(true);
        try {
            for (const file of Array.from(files)) {
                const fd = new FormData();
                fd.append('file', file);
                fd.append('type', type);
                await addToPool(fd);
            }
            onRefresh();
        } catch (e: unknown) {
            console.error(e);
        } finally {
            setUploading(false);
        }
    }

    async function handleRemove(id: string) {
        setRemoving(id);
        try {
            await removeFromPool(id);
            onRefresh();
        } catch (e: unknown) {
            console.error(e);
        } finally {
            setRemoving(null);
        }
    }

    const handleDrop = useCallback((e: React.DragEvent, type: PoolType) => {
        e.preventDefault();
        setDragging(false);
        handleUpload(e.dataTransfer.files, type);
    }, []);

    return (
        <div className="pool-panel">
            <header className="pool-header">
                <div>
                    <h2 className="t-h4">Reference Pool</h2>
                    <p className="t-sm text-tertiary" style={{ marginTop: 2 }}>
                        Imagens de referência para o Agente — estilo LoRA
                    </p>
                </div>
                <span className="pool-count t-label text-tertiary">{items.length} refs</span>
            </header>

            {/* Filtro por tipo */}
            <div className="pool-filter" role="tablist" aria-label="Filtrar por tipo">
                {(['all', ...TYPES] as const).map(t => (
                    <button
                        key={t}
                        role="tab"
                        aria-selected={activeType === t}
                        className={`filter-tab ${activeType === t ? 'active' : ''}`}
                        onClick={() => setActiveType(t)}
                    >
                        {t === 'all' ? 'Todos' : TYPE_META[t].label}
                        <span className="filter-count">
                            {t === 'all' ? items.length : items.filter(i => i.type === t).length}
                        </span>
                    </button>
                ))}
            </div>

            {/* Upload zones */}
            <div className="upload-zones">
                {TYPES.map(type => {
                    const { label, icon: Icon, color } = TYPE_META[type];
                    return (
                        <label
                            key={type}
                            className={`upload-zone ${dragging ? 'dragging' : ''}`}
                            onDragOver={e => { e.preventDefault(); setDragging(true); }}
                            onDragLeave={() => setDragging(false)}
                            onDrop={e => handleDrop(e, type)}
                            aria-label={`Upload de ${label}`}
                        >
                            <input
                                type="file"
                                accept="image/*"
                                multiple
                                style={{ display: 'none' }}
                                onChange={e => handleUpload(e.target.files, type)}
                                disabled={uploading}
                                aria-hidden="true"
                            />
                            <Icon size={16} style={{ color }} aria-hidden="true" />
                            <span className="t-sm" style={{ color }}>{label}</span>
                            <Upload size={12} className="upload-icon" aria-hidden="true" />
                        </label>
                    );
                })}
            </div>

            {/* Lista de itens */}
            <div className="pool-items scroll-y" role="list" aria-label="Itens do pool">
                {loading ? (
                    <div className="pool-loading" role="status" aria-live="polite">
                        <Loader2 size={20} className="spin text-secondary" />
                        <span className="t-sm text-tertiary">Carregando pool…</span>
                    </div>
                ) : filtered.length === 0 ? (
                    <div className="pool-empty" role="status">
                        <p className="t-sm text-tertiary">Nenhuma referência adicionada.</p>
                        <p className="t-xs text-tertiary">Arraste imagens ou clique nos botões acima.</p>
                    </div>
                ) : (
                    <AnimatePresence>
                        {filtered.map(item => {
                            const meta = TYPE_META[item.type];
                            const Icon = meta.icon;
                            return (
                                <motion.div
                                    key={item.id}
                                    className="pool-item"
                                    role="listitem"
                                    initial={{ opacity: 0, x: -8 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -8 }}
                                    transition={{ duration: 0.18 }}
                                >
                                    <img
                                        src={imageUrl(item.url)}
                                        alt={item.filename}
                                        className="pool-item-thumb"
                                        loading="lazy"
                                    />
                                    <div className="pool-item-info">
                                        <span className="t-sm text-primary pool-item-name">{item.filename}</span>
                                        <div className="flex items-center gap-2">
                                            <Icon size={11} style={{ color: meta.color }} aria-hidden="true" />
                                            <span className="t-xs" style={{ color: meta.color }}>{meta.label}</span>
                                        </div>
                                    </div>
                                    <button
                                        className="pool-item-remove"
                                        onClick={() => handleRemove(item.id)}
                                        disabled={removing === item.id}
                                        aria-label={`Remover ${item.filename}`}
                                        title="Remover"
                                    >
                                        {removing === item.id
                                            ? <Loader2 size={14} className="spin" aria-hidden="true" />
                                            : <Trash2 size={14} aria-hidden="true" />
                                        }
                                    </button>
                                </motion.div>
                            );
                        })}
                    </AnimatePresence>
                )}
            </div>

            {uploading && (
                <div className="upload-toast" role="status" aria-live="polite">
                    <Loader2 size={14} className="spin" aria-hidden="true" />
                    <span className="t-sm">Enviando referências…</span>
                </div>
            )}
        </div>
    );
}
