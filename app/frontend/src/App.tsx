import { useCallback, useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  X,
  Copy,
  Download,
  Clock,
  Pencil,
  ChevronDown,
  ArrowDown,
  Lock,
  Unlock,
  RotateCw,
  ZoomIn,
  ZoomOut,
} from 'lucide-react';
import { Sidebar } from './components/Sidebar';
import type { Tab } from './components/Sidebar';
import { ChatInput } from './components/ChatInput';
import { Gallery } from './components/Gallery';
import { PoolPanel } from './components/PoolPanel';
import { ReviewPanel } from './components/ReviewPanel';
import { DEFAULT_CREATE_CATEGORY } from './config/createCategories';
import { listPool, listHistory, deleteHistoryEntry, getLatestReview, getReviewBySession } from './lib/api';
import {
  humanizeMode,
  humanizeFidelityMode,
  humanizeMarketplaceChannel,
  humanizeMarketplaceOperation,
  humanizePipelineMode,
  humanizePreset,
  humanizeScenePreference,
  humanizeSlotId,
} from './lib/humanize';
import { useJobQueue } from './hooks/useJobQueue';
import { useDialogA11y } from './hooks/useDialogA11y';
import type {
  AspectRatio,
  PoolItem,
  MediaHistoryItem,
  EditTarget,
  JobReviewPayload,
  CreateCategory,
  Resolution,
} from './types';
import './App.css';

const EDIT_AR_OPTIONS: AspectRatio[] = ['4:5', '1:1', '9:16', '16:9', '4:3', '3:4'];
const EDIT_RES_OPTIONS: Resolution[] = ['1K', '2K', '4K'];
interface LightboxEditDraft {
  angleMode: 'soft_turn' | 'back_view' | null;
  distanceMode: 'closer' | 'farther' | null;
  positionControl: 'locked' | 'flexible' | null;
  aspectRatio: AspectRatio;
  resolution: Resolution;
  freeText: string;
}

function coerceAspectRatio(value?: string): AspectRatio {
  return (EDIT_AR_OPTIONS.includes(value as AspectRatio) ? value : '4:5') as AspectRatio;
}

function coerceResolution(value?: string): Resolution {
  return (EDIT_RES_OPTIONS.includes(value as Resolution) ? value : '1K') as Resolution;
}

function makeLightboxEditDraft(item: MediaHistoryItem): LightboxEditDraft {
  return {
    angleMode: null,
    distanceMode: null,
    positionControl: null,
    aspectRatio: coerceAspectRatio(item.aspect_ratio),
    resolution: coerceResolution(item.resolution),
    freeText: '',
  };
}

function hasDeterministicEditSelection(draft: LightboxEditDraft): boolean {
  return Boolean(draft.angleMode || draft.distanceMode || draft.positionControl);
}

function buildAngleInstruction(draft: LightboxEditDraft): string {
  if (!hasDeterministicEditSelection(draft)) {
    return '';
  }
  const parts: string[] = [];
  if (draft.angleMode) {
    parts.push(
      draft.angleMode === 'back_view'
        ? 'mostrar costas da peça com fidelidade'
        : 'mudar o ângulo de forma leve e comercial',
    );
  }
  if (draft.distanceMode === 'closer') {
    parts.push('mais próximo');
  } else if (draft.distanceMode === 'farther') {
    parts.push('mais distante');
  }
  if (draft.positionControl === 'flexible') {
    parts.push('liberar um pouco a posição');
  } else if (draft.positionControl === 'locked') {
    parts.push('travar posição');
  }
  return parts.join('. ');
}

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
  const createCategory: CreateCategory = DEFAULT_CREATE_CATEGORY;
  const [tab, setTab] = useState<Tab>('criar');
  const [pool, setPool] = useState<PoolItem[]>([]);
  const [poolLoading, setPoolLoading] = useState(false);
  const [mediaHistory, setMediaHistory] = useState<MediaHistoryItem[]>([]);
  const [lightbox, setLightbox] = useState<{ url: string; item?: MediaHistoryItem } | null>(null);
  const [lightboxEditMode, setLightboxEditMode] = useState(false);
  const [lightboxEditDraft, setLightboxEditDraft] = useState<LightboxEditDraft | null>(null);
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
        category: e.category as CreateCategory | undefined,
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
        mode: e.mode as string | undefined,
        preset: e.preset as string | undefined,
        scene_preference: e.scene_preference as string | undefined,
        fidelity_mode: e.fidelity_mode as string | undefined,
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
  const { jobs, submitGenerateJob, submitFreeformEditJob, submitGuidedAngleJob, submitMarketplaceJob, dismissJob } = useJobQueue({
    onJobComplete: fetchHistory,
  });

  useEffect(() => {
    if (!lightbox?.item) {
      setLightboxEditMode(false);
      setLightboxEditDraft(null);
      return;
    }
    setLightboxEditMode(false);
    setLightboxEditDraft(makeLightboxEditDraft(lightbox.item));
  }, [lightbox?.item]);

  /* ── Handle Edit — agora assíncrono via job queue ────────── */
  function handleEdit(editInstruction: string, target: EditTarget, files?: File[]) {
    setEditTarget(null);
    submitFreeformEditJob({ editInstruction, target, files });
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

  function handleLightboxAngleEdit() {
    if (!lightbox?.item || !lightboxEditDraft) return;
    const guidedMode = hasDeterministicEditSelection(lightboxEditDraft);
    const freeInstruction = lightboxEditDraft.freeText.trim();
    const editInstruction = guidedMode ? buildAngleInstruction(lightboxEditDraft) : freeInstruction;
    if (!editInstruction) return;
    const target: EditTarget = {
      session_id: lightbox.item.session_id || '',
      filename: lightbox.item.filename,
      url: lightbox.item.url,
      prompt: lightbox.item.prompt || lightbox.item.optimized_prompt,
      aspect_ratio: lightbox.item.aspect_ratio,
      resolution: lightbox.item.resolution,
      shot_type: lightbox.item.shot_type,
    };
    if (guidedMode) {
      submitGuidedAngleJob({
        editInstruction,
        target,
        commandCenter: {
          editSubmode: 'angle_transform',
          viewIntent: lightboxEditDraft.angleMode ?? 'preserve',
          distanceIntent: lightboxEditDraft.distanceMode ?? 'preserve',
          poseFreedom: lightboxEditDraft.positionControl ?? undefined,
          angleTarget: lightboxEditDraft.angleMode === 'back_view' ? 'back' : undefined,
          preserveFraming: true,
          preserveCameraHeight: true,
          preserveDistance: lightboxEditDraft.distanceMode === null,
          preservePose: lightboxEditDraft.positionControl === 'locked',
          aspect_ratio: lightboxEditDraft.aspectRatio,
          resolution: lightboxEditDraft.resolution,
          sourceShotType: lightbox.item.shot_type,
        },
      });
    } else {
      submitFreeformEditJob({
        editInstruction,
        target,
      });
    }
    setLightbox(null);
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
                <header className="generate-header generate-header--create">
                  <div className="generate-header-copy">
                    <span className="generate-header-kicker t-label">Moda</span>
                    <h1 className="t-h3">Criar</h1>
                    <p className="t-sm text-tertiary">
                      Escolha o modo de trabalho e monte imagens profissionais para vender melhor a sua peça.
                    </p>
                  </div>
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
                  category={createCategory}
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
                  className={`lightbox-details ${lightboxEditMode ? 'lightbox-details--edit' : ''}`}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 }}
                >
                  <div className="lightbox-details-header">
                    <span className="t-label text-secondary">{lightboxEditMode ? 'Editar imagem' : 'Detalhes da geração'}</span>
                    {lightbox.item.session_id && (
                      <span className="badge" style={{ fontFamily: 'monospace', fontSize: 10, opacity: 0.7 }} title="Session ID">
                        #{lightbox.item.session_id}
                      </span>
                    )}
                    <div className="lightbox-details-actions">
                      <button
                        className="lightbox-action-btn lightbox-edit-btn"
                        title={lightboxEditMode ? 'Voltar para detalhes' : 'Modificar esta imagem'}
                        onClick={() => {
                          if (lightbox.item) {
                            setLightboxEditDraft(prev => prev ?? makeLightboxEditDraft(lightbox.item as MediaHistoryItem));
                            setLightboxEditMode(current => !current);
                          }
                        }}
                      >
                        <Pencil size={14} /> {lightboxEditMode ? 'Detalhes' : 'Modificar'}
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
                    {lightboxEditMode ? (
                      <>
                        {lightbox.item.mode && <span className="badge badge--accent" title={lightbox.item.mode}>{humanizeMode(lightbox.item.mode)}</span>}
                        {lightbox.item.shot_type && <span className="badge">{lightbox.item.shot_type}</span>}
                      </>
                    ) : (
                      <>
                        {lightbox.item.mode && <span className="badge badge--accent" title={lightbox.item.mode}>{humanizeMode(lightbox.item.mode)}</span>}
                        {lightbox.item.preset && <span className="badge badge--accent" title={lightbox.item.preset}>{humanizePreset(lightbox.item.preset)}</span>}
                        {lightbox.item.fidelity_mode && <span className="badge" title={lightbox.item.fidelity_mode}>{humanizeFidelityMode(lightbox.item.fidelity_mode)}</span>}
                        {lightbox.item.scene_preference && <span className="badge" title={lightbox.item.scene_preference}>{humanizeScenePreference(lightbox.item.scene_preference)}</span>}
                        {lightbox.item.pipeline_mode && <span className="badge" title={lightbox.item.pipeline_mode}>{humanizePipelineMode(lightbox.item.pipeline_mode)}</span>}
                        {lightbox.item.thinking_level && lightbox.item.thinking_level !== 'MINIMAL' && <span className="badge badge--accent">{lightbox.item.thinking_level}</span>}
                        {lightbox.item.shot_type && <span className="badge">{lightbox.item.shot_type}</span>}
                        {lightbox.item.marketplace_channel && <span className="badge badge--accent" title={lightbox.item.marketplace_channel}>{humanizeMarketplaceChannel(lightbox.item.marketplace_channel)}</span>}
                        {lightbox.item.marketplace_operation && <span className="badge" title={lightbox.item.marketplace_operation}>{humanizeMarketplaceOperation(lightbox.item.marketplace_operation)}</span>}
                        {lightbox.item.slot_id && <span className="badge" title={lightbox.item.slot_id}>{humanizeSlotId(lightbox.item.slot_id)}</span>}
                        {lightbox.item.grounding_effective && (
                          <span className="badge badge--success">🌐 Pesquisa web ativa</span>
                        )}
                      </>
                    )}
                  </div>

                  {lightboxEditMode && lightboxEditDraft ? (
                    <div className="lightbox-edit-panel">
                      <div className="lightbox-edit-scroll">
                        <div className="lightbox-edit-compose">
                          <div className="lightbox-edit-title-row">
                            <span className="t-xs text-tertiary">Modificar</span>
                            <span className="t-xs text-tertiary">
                              {hasDeterministicEditSelection(lightboxEditDraft) ? 'Ajuste guiado ativo' : 'Instrução livre'}
                            </span>
                          </div>
                          <textarea
                            className="lightbox-edit-textarea"
                            value={lightboxEditDraft.freeText}
                            onChange={(e) => setLightboxEditDraft(prev => prev ? { ...prev, freeText: e.target.value } : prev)}
                            onClick={(e) => e.stopPropagation()}
                            onKeyDown={(e) => e.stopPropagation()}
                            placeholder={
                              hasDeterministicEditSelection(lightboxEditDraft)
                                ? 'Ajuste livre indisponível enquanto um controle guiado estiver ativo'
                                : 'Descreva a modificação que deseja fazer'
                            }
                            rows={3}
                            disabled={hasDeterministicEditSelection(lightboxEditDraft)}
                          />
                        </div>

                        <div className="lightbox-edit-section">
                          <div className="lightbox-edit-title-row">
                            <span className="t-xs text-tertiary">Ângulo</span>
                            <span className="t-xs text-tertiary">Direção principal</span>
                          </div>
                          <div className="lightbox-edit-choice-grid">
                          <button
                            type="button"
                            className={`lightbox-edit-choice-card ${lightboxEditDraft.angleMode === 'soft_turn' ? 'lightbox-edit-choice-card--active' : ''}`}
                            onClick={() => setLightboxEditDraft(prev => prev ? {
                              ...prev,
                              angleMode: prev.angleMode === 'soft_turn' ? null : 'soft_turn',
                            } : prev)}
                          >
                              <span className="lightbox-edit-choice-icon" aria-hidden="true">
                                <RotateCw size={16} />
                              </span>
                              <span className="lightbox-edit-choice-copy">
                                <span className="lightbox-edit-choice-label">Mudar ângulo</span>
                                <span className="lightbox-edit-choice-sublabel">Giro leve decidido pelo agente</span>
                              </span>
                            </button>
                          <button
                            type="button"
                            className={`lightbox-edit-choice-card ${lightboxEditDraft.angleMode === 'back_view' ? 'lightbox-edit-choice-card--active' : ''}`}
                            onClick={() => setLightboxEditDraft(prev => prev ? {
                              ...prev,
                              angleMode: prev.angleMode === 'back_view' ? null : 'back_view',
                            } : prev)}
                          >
                              <span className="lightbox-edit-choice-icon" aria-hidden="true">
                                <ArrowDown size={16} />
                              </span>
                              <span className="lightbox-edit-choice-copy">
                                <span className="lightbox-edit-choice-label">Ângulo de costas</span>
                                <span className="lightbox-edit-choice-sublabel">Prioriza a leitura das costas</span>
                              </span>
                            </button>
                          </div>
                        </div>

                        <div className="lightbox-edit-inline-grid">
                          <div className="lightbox-edit-inline-group">
                            <span className="lightbox-edit-config-label">Close</span>
                            <div className="lightbox-edit-chip-row">
                              <button
                                type="button"
                                className={`lightbox-edit-chip ${lightboxEditDraft.distanceMode === 'closer' ? 'lightbox-edit-chip--active' : ''}`}
                                onClick={() => setLightboxEditDraft(prev => prev ? { ...prev, distanceMode: prev.distanceMode === 'closer' ? null : 'closer' } : prev)}
                              >
                                <ZoomIn size={14} />
                                <span>Mais próximo</span>
                              </button>
                              <button
                                type="button"
                                className={`lightbox-edit-chip ${lightboxEditDraft.distanceMode === 'farther' ? 'lightbox-edit-chip--active' : ''}`}
                                onClick={() => setLightboxEditDraft(prev => prev ? { ...prev, distanceMode: prev.distanceMode === 'farther' ? null : 'farther' } : prev)}
                              >
                                <ZoomOut size={14} />
                                <span>Mais distante</span>
                              </button>
                            </div>
                          </div>
                          <div className="lightbox-edit-inline-group">
                            <span className="lightbox-edit-config-label">Controle</span>
                            <div className="lightbox-edit-chip-row">
                              <button
                                type="button"
                                className={`lightbox-edit-chip ${lightboxEditDraft.positionControl === 'locked' ? 'lightbox-edit-chip--active' : ''}`}
                                onClick={() => setLightboxEditDraft(prev => prev ? {
                                  ...prev,
                                  positionControl: prev.positionControl === 'locked' ? null : 'locked',
                                } : prev)}
                              >
                                <Lock size={14} />
                                <span>Travar posição</span>
                              </button>
                              <button
                                type="button"
                                className={`lightbox-edit-chip ${lightboxEditDraft.positionControl === 'flexible' ? 'lightbox-edit-chip--active' : ''}`}
                                onClick={() => setLightboxEditDraft(prev => prev ? {
                                  ...prev,
                                  positionControl: prev.positionControl === 'flexible' ? null : 'flexible',
                                } : prev)}
                              >
                                <Unlock size={14} />
                                <span>Liberar posição</span>
                              </button>
                            </div>
                          </div>
                        </div>

                        <div className="lightbox-edit-inline-grid lightbox-edit-inline-grid--compact">
                          <div className="lightbox-edit-inline-group">
                            <span className="lightbox-edit-config-label">Proporção</span>
                            <div className="lightbox-edit-chip-row">
                              {EDIT_AR_OPTIONS.map(option => (
                                <button
                                  key={option}
                                  type="button"
                                  className={`lightbox-edit-chip ${lightboxEditDraft.aspectRatio === option ? 'lightbox-edit-chip--active' : ''}`}
                                  onClick={() => setLightboxEditDraft(prev => prev ? { ...prev, aspectRatio: option } : prev)}
                                >
                                  {option}
                                </button>
                              ))}
                            </div>
                          </div>
                          <div className="lightbox-edit-inline-group">
                            <span className="lightbox-edit-config-label">Qualidade</span>
                            <div className="lightbox-edit-chip-row">
                              {EDIT_RES_OPTIONS.map(option => (
                                <button
                                  key={option}
                                  type="button"
                                  className={`lightbox-edit-chip ${lightboxEditDraft.resolution === option ? 'lightbox-edit-chip--active' : ''}`}
                                  onClick={() => setLightboxEditDraft(prev => prev ? { ...prev, resolution: option } : prev)}
                                >
                                  {option}
                                </button>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="lightbox-edit-footer">
                        <button
                          type="button"
                          className="lightbox-copy-btn"
                          onClick={() => setLightboxEditMode(false)}
                        >
                          Voltar
                        </button>
                        <button
                          type="button"
                          className="lightbox-edit-apply-btn"
                          disabled={!lightboxEditDraft.freeText.trim() && !hasDeterministicEditSelection(lightboxEditDraft)}
                          onClick={handleLightboxAngleEdit}
                        >
                          {hasDeterministicEditSelection(lightboxEditDraft)
                            ? 'Aplicar ajuste guiado'
                            : (lightboxEditDraft.freeText.trim() ? 'Aplicar modificação' : 'Descreva ou selecione um ajuste')}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
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

                      {lightbox.item.created_at && (
                        <div className="lightbox-timestamp">
                          <Clock size={11} />
                          <span className="t-xs text-tertiary">
                            {new Date(lightbox.item.created_at).toLocaleString('pt-BR')}
                          </span>
                        </div>
                      )}

                      <LightboxMeta item={lightbox.item} />
                    </>
                  )}
                </motion.div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
