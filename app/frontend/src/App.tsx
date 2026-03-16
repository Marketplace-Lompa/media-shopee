import { useCallback, useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { X, Copy, Download, Clock, Pencil, ChevronDown } from 'lucide-react';
import { Sidebar } from './components/Sidebar';
import type { Tab } from './components/Sidebar';
import { ChatInput } from './components/ChatInput';
import { Gallery } from './components/Gallery';
import { PoolPanel } from './components/PoolPanel';
import { ReviewPanel } from './components/ReviewPanel';
import { listPool, listHistory, deleteHistoryEntry, getLatestReview, getReviewBySession } from './lib/api';
import {
  humanizeFidelityMode,
  humanizeMarketplaceChannel,
  humanizeMarketplaceOperation,
  humanizePipelineMode,
  humanizePoseFlexMode,
  humanizePreset,
  humanizeScenePreference,
  humanizeSlotId,
} from './lib/humanize';
import { useJobQueue } from './hooks/useJobQueue';
import { useDialogA11y } from './hooks/useDialogA11y';
import type {
  PoolItem,
  MediaHistoryItem,
  EditTarget,
  JobReviewPayload,
} from './types';
import './App.css';

/* ── LightboxMeta: metadados técnicos colapsável ─────────── */
function LightboxMeta({ item }: { item: MediaHistoryItem }) {
  const [open, setOpen] = useState(false);
  const hasMeta = item.base_prompt || item.camera_and_realism || item.camera_profile;
  if (!hasMeta) return null;
  return (
    <div className="lightbox-meta">
      <button className="lightbox-meta-toggle" onClick={() => setOpen(o => !o)}>
        <span className="t-xs text-tertiary">Detalhes técnicos</span>
        <ChevronDown size={12} style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s' }} />
      </button>
      {open && (
        <div className="lightbox-meta-body">
          {item.camera_profile && (
            <div className="lightbox-meta-row">
              <span className="lightbox-meta-label">Câmera</span>
              <span className="lightbox-meta-value">{item.camera_profile}</span>
            </div>
          )}
          {item.camera_and_realism && (
            <div className="lightbox-meta-row">
              <span className="lightbox-meta-label">Configuração</span>
              <span className="lightbox-meta-value lightbox-meta-value--mono">{item.camera_and_realism}</span>
            </div>
          )}
          {item.base_prompt && (
            <div className="lightbox-meta-row">
              <span className="lightbox-meta-label">Prompt base</span>
              <span className="lightbox-meta-value lightbox-meta-value--mono">{item.base_prompt}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ── App ──────────────────────────────────────────────────── */
export default function App() {
  const [tab, setTab] = useState<Tab>('criar');
  const [pool, setPool] = useState<PoolItem[]>([]);
  const [poolLoading, setPoolLoading] = useState(false);
  const [mediaHistory, setMediaHistory] = useState<MediaHistoryItem[]>([]);
  const [lightbox, setLightbox] = useState<{ url: string; item?: MediaHistoryItem } | null>(null);
  const [reuseData, setReuseData] = useState<{ prompt?: string; references?: string[] } | null>(null);
  const [editTarget, setEditTarget] = useState<EditTarget | null>(null);
  const [reviewData, setReviewData] = useState<JobReviewPayload | null>(null);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const lightboxRef = useRef<HTMLDivElement>(null);

  useDialogA11y(!!lightbox, lightboxRef, () => setLightbox(null));

  const fetchPool = useCallback(async () => {
    setPoolLoading(true);
    try {
      const data = await listPool();
      setPool(data.items ?? []);
    } catch {
      setPool([]);
    } finally {
      setPoolLoading(false);
    }
  }, []);

  const fetchHistory = useCallback(async () => {
    try {
      const data = await listHistory();
      const items: MediaHistoryItem[] = (data.items ?? []).map((e: Record<string, unknown>) => ({
        id: e.id as string,
        session_id: e.session_id as string | undefined,
        filename: e.filename as string,
        url: e.url as string,
        prompt: e.prompt as string | undefined,
        optimized_prompt: e.optimized_prompt as string | undefined,
        edit_instruction: e.edit_instruction as string | undefined,
        thinking_level: e.thinking_level as string | undefined,
        shot_type: e.shot_type as string | undefined,
        aspect_ratio: e.aspect_ratio as string | undefined,
        resolution: e.resolution as string | undefined,
        grounding_effective: e.grounding_effective as boolean | undefined,
        references: e.references as string[] | undefined,
        created_at: e.created_at as number,
        base_prompt: e.base_prompt as string | undefined,
        camera_and_realism: e.camera_and_realism as string | undefined,
        camera_profile: e.camera_profile as string | undefined,
        grounding_mode: e.grounding_mode as string | undefined,
        reason_codes: e.reason_codes as string[] | undefined,
        preset: e.preset as string | undefined,
        scene_preference: e.scene_preference as string | undefined,
        fidelity_mode: e.fidelity_mode as string | undefined,
        pose_flex_mode: e.pose_flex_mode as string | undefined,
        pipeline_mode: e.pipeline_mode as string | undefined,
        marketplace_channel: e.marketplace_channel as string | undefined,
        marketplace_operation: e.marketplace_operation as string | undefined,
        slot_id: e.slot_id as string | undefined,
      }));
      setMediaHistory(items);
    } catch {
      console.warn('Histórico não disponível no backend');
    }
  }, []);

  const fetchLatestReviewData = useCallback(async (refresh = false) => {
    setReviewLoading(true);
    setReviewError(null);
    try {
      const data = await getLatestReview(refresh);
      setReviewData(data as JobReviewPayload);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Falha ao carregar revisão';
      setReviewError(message);
    } finally {
      setReviewLoading(false);
    }
  }, []);

  const fetchReviewSessionData = useCallback(async (sessionId: string, refresh = false) => {
    setReviewLoading(true);
    setReviewError(null);
    try {
      const data = await getReviewBySession(sessionId, refresh);
      setReviewData(data as JobReviewPayload);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Falha ao carregar revisão';
      setReviewError(message);
    } finally {
      setReviewLoading(false);
    }
  }, []);

  useEffect(() => { fetchPool(); fetchHistory(); }, [fetchPool, fetchHistory]);

  useEffect(() => {
    if (tab === 'revisao' && !reviewData && !reviewLoading) {
      fetchLatestReviewData();
    }
  }, [tab, reviewData, reviewLoading, fetchLatestReviewData]);

  // ── Job Queue ─────────────────────────────────────────────
  const { jobs, submitGenerateJob, submitEditJob, submitMarketplaceJob, dismissJob } = useJobQueue({
    onJobComplete: fetchHistory,
  });

  /* ── Handle Edit — agora assíncrono via job queue ────────── */
  function handleEdit(editInstruction: string, target: EditTarget, files?: File[]) {
    setEditTarget(null);
    submitEditJob({ editInstruction, target, files });
  }

  async function handleHistoryDelete(id: string) {
    try {
      await deleteHistoryEntry(id);
      setMediaHistory(prev => prev.filter(item => item.id !== id));
    } catch (err) {
      console.error('Erro ao deletar:', err);
    }
  }

  function handleReuse(item: MediaHistoryItem) {
    setReuseData({
      // edit_instruction describe a past edit, not a generation prompt — skip it
      prompt: item.prompt || item.optimized_prompt,
      references: item.references || [],
    });
    // Rola para o topo onde está o input
    document.querySelector('.generate-content')?.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function handleUseReviewInCreate(review: JobReviewPayload) {
    setReuseData({
      prompt: review.context.prompt || undefined,
      references: review.assets.reuse_reference_urls || [],
    });
    setTab('criar');
  }

  function handleGenerate(payload: Parameters<typeof submitGenerateJob>[0]) {
    submitGenerateJob(payload);
  }

  function handleMarketplaceSubmit(payload: Parameters<typeof submitMarketplaceJob>[0]) {
    submitMarketplaceJob(payload);
  }

  return (
    <>
      <a href="#main-content" className="skip-link">Ir para conteúdo principal</a>

      <div className="app-shell">
        <Sidebar activeTab={tab} onTabChange={setTab} />

        <main id="main-content" className="app-main">
          <AnimatePresence mode="wait">
            {tab === 'criar' && (
              <motion.div
                key="criar"
                className="generate-layout"
                initial={{ opacity: 0, x: 12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -12 }}
                transition={{ duration: 0.2 }}
              >
                <header className="generate-header">
                  <h1 className="t-h3">Criar</h1>
                  <p className="t-sm text-tertiary">
                    Envie fotos da peça e gere imagens profissionais para o seu anúncio
                  </p>
                </header>

                <div className="generate-content scroll-y">
                  <Gallery
                    mediaHistory={mediaHistory}
                    onDelete={handleHistoryDelete}
                    onReuse={handleReuse}
                    onLightbox={(url) => setLightbox({ url })}
                    onLightboxItem={(item) => setLightbox({ url: item.url.startsWith('http') ? item.url : `${window.location.origin}${item.url}`, item })}
                    activeJobs={jobs}
                    onDismissJob={dismissJob}
                  />
                </div>

                <ChatInput
                  onSubmit={handleGenerate}
                  onMarketplaceSubmit={handleMarketplaceSubmit}
                  externalData={reuseData}
                  onClearExternalData={() => setReuseData(null)}
                  editTarget={editTarget}
                  onEditSubmit={(instruction, files) => editTarget && handleEdit(instruction, editTarget, files)}
                  onEditCancel={() => setEditTarget(null)}
                />
              </motion.div>
            )}

            {tab === 'revisao' && (
              <motion.div
                key="revisao"
                className="generate-layout"
                initial={{ opacity: 0, x: 12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -12 }}
                transition={{ duration: 0.2 }}
              >
                <ReviewPanel
                  data={reviewData}
                  loading={reviewLoading}
                  error={reviewError}
                  onRefresh={() => {
                    if (reviewData?.session_id) {
                      fetchReviewSessionData(reviewData.session_id, true);
                    } else {
                      fetchLatestReviewData(true);
                    }
                  }}
                  onUseInCreate={handleUseReviewInCreate}
                  onGoToCreate={() => setTab('criar')}
                />
              </motion.div>
            )}

            {tab === 'historico' && (
              <motion.div
                key="historico"
                className="generate-layout"
                initial={{ opacity: 0, x: 12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -12 }}
                transition={{ duration: 0.2 }}
              >
                <header className="generate-header">
                  <h1 className="t-h3">Histórico</h1>
                  <p className="t-sm text-tertiary">Suas gerações anteriores</p>
                </header>
                <div className="generate-content scroll-y">
                  <Gallery
                    mediaHistory={mediaHistory}
                    onDelete={handleHistoryDelete}
                    onReuse={handleReuse}
                    onLightbox={(url) => setLightbox({ url })}
                    onLightboxItem={(item) => setLightbox({ url: item.url.startsWith('http') ? item.url : `${window.location.origin}${item.url}`, item })}
                  />
                </div>
              </motion.div>
            )}

            {tab === 'biblioteca' && (
              <motion.div
                key="biblioteca"
                className="pool-layout"
                initial={{ opacity: 0, x: 12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -12 }}
                transition={{ duration: 0.2 }}
              >
                <PoolPanel
                  items={pool}
                  loading={poolLoading}
                  onRefresh={fetchPool}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>

      {/* Lightbox global com detalhes */}
      <AnimatePresence>
        {lightbox && (
          <motion.div
            className="lightbox"
            ref={lightboxRef}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setLightbox(null)}
            role="dialog"
            aria-modal="true"
            aria-label="Imagem ampliada"
            tabIndex={-1}
          >
            <button
              className="lightbox-close"
              onClick={() => setLightbox(null)}
              aria-label="Fechar"
            >
              <X size={20} />
            </button>

            <div className={`lightbox-content ${lightbox.item ? 'lightbox-content--with-details' : ''}`} onClick={e => e.stopPropagation()}>
              <motion.img
                src={lightbox.url}
                alt="Imagem ampliada"
                className="lightbox-img"
                initial={{ scale: 0.9 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0.9 }}
              />

              {lightbox.item && (
                <motion.div
                  className="lightbox-details"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 }}
                >
                  <div className="lightbox-details-header">
                    <span className="t-label text-secondary">Detalhes da geração</span>
                    {lightbox.item.session_id && (
                      <span className="badge" style={{ fontFamily: 'monospace', fontSize: 10, opacity: 0.7 }} title="Session ID">
                        #{lightbox.item.session_id}
                      </span>
                    )}
                    <div className="lightbox-details-actions">
                      <button
                        className="lightbox-action-btn lightbox-edit-btn"
                        title="Modificar esta imagem"
                        onClick={() => {
                          if (lightbox.item) {
                            setEditTarget({
                              session_id: lightbox.item.session_id || '',
                              filename: lightbox.item.filename,
                              url: lightbox.item.url,
                              prompt: lightbox.item.prompt || lightbox.item.optimized_prompt,
                              aspect_ratio: lightbox.item.aspect_ratio,
                              resolution: lightbox.item.resolution,
                            });
                            setLightbox(null);
                          }
                        }}
                      >
                        <Pencil size={14} /> Modificar
                      </button>
                      <a
                        href={lightbox.url}
                        download={lightbox.item.filename}
                        className="lightbox-action-btn"
                        title="Baixar"
                        aria-label={`Baixar ${lightbox.item.filename}`}
                      >
                        <Download size={14} />
                      </a>
                    </div>
                  </div>

                  {/* Configs como badges */}
                  <div className="lightbox-badges">
                    {lightbox.item.aspect_ratio && <span className="badge">{lightbox.item.aspect_ratio}</span>}
                    {lightbox.item.resolution && <span className="badge">{lightbox.item.resolution}</span>}
                    {lightbox.item.preset && <span className="badge badge--accent" title={lightbox.item.preset}>{humanizePreset(lightbox.item.preset)}</span>}
                    {lightbox.item.fidelity_mode && <span className="badge" title={lightbox.item.fidelity_mode}>{humanizeFidelityMode(lightbox.item.fidelity_mode)}</span>}
                    {lightbox.item.scene_preference && <span className="badge" title={lightbox.item.scene_preference}>{humanizeScenePreference(lightbox.item.scene_preference)}</span>}
                    {lightbox.item.pose_flex_mode && lightbox.item.pose_flex_mode !== 'auto' && <span className="badge" title={lightbox.item.pose_flex_mode}>{humanizePoseFlexMode(lightbox.item.pose_flex_mode)}</span>}
                    {lightbox.item.pipeline_mode && <span className="badge" title={lightbox.item.pipeline_mode}>{humanizePipelineMode(lightbox.item.pipeline_mode)}</span>}
                    {lightbox.item.thinking_level && lightbox.item.thinking_level !== 'MINIMAL' && <span className="badge badge--accent">{lightbox.item.thinking_level}</span>}
                    {lightbox.item.shot_type && <span className="badge">{lightbox.item.shot_type}</span>}
                    {lightbox.item.marketplace_channel && <span className="badge badge--accent" title={lightbox.item.marketplace_channel}>{humanizeMarketplaceChannel(lightbox.item.marketplace_channel)}</span>}
                    {lightbox.item.marketplace_operation && <span className="badge" title={lightbox.item.marketplace_operation}>{humanizeMarketplaceOperation(lightbox.item.marketplace_operation)}</span>}
                    {lightbox.item.slot_id && <span className="badge" title={lightbox.item.slot_id}>{humanizeSlotId(lightbox.item.slot_id)}</span>}
                    {lightbox.item.grounding_effective && (
                      <span className="badge badge--success">🌐 Pesquisa web ativa</span>
                    )}
                  </div>

                  {/* Prompt */}
                  {(lightbox.item.prompt || lightbox.item.optimized_prompt) && (
                    <div className="lightbox-prompt-section">
                      <div className="lightbox-prompt-header">
                        <span className="t-xs text-tertiary">Prompt</span>
                        <button
                          className="lightbox-copy-btn"
                          onClick={() => navigator.clipboard.writeText(lightbox.item?.prompt || lightbox.item?.optimized_prompt || '')}
                          title="Copiar prompt"
                          aria-label="Copiar prompt"
                        >
                          <Copy size={12} /> Copiar
                        </button>
                      </div>
                      <p className="lightbox-prompt-text">
                        {lightbox.item.prompt || lightbox.item.optimized_prompt}
                      </p>
                    </div>
                  )}

                  {/* Timestamp */}
                  {lightbox.item.created_at && (
                    <div className="lightbox-timestamp">
                      <Clock size={11} />
                      <span className="t-xs text-tertiary">
                        {new Date(lightbox.item.created_at).toLocaleString('pt-BR')}
                      </span>
                    </div>
                  )}

                  {/* Metadados técnicos (colapsável) */}
                  <LightboxMeta item={lightbox.item} />
                </motion.div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
