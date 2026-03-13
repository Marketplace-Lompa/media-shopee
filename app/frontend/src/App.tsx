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
import type {
  GenerationStatus,
  PoolItem,
  AspectRatio,
  Resolution,
  Preset,
  ScenePreference,
  FidelityMode,
  PoseFlexMode,
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
  const [status, setStatus] = useState<GenerationStatus>({ type: 'idle' });
  const [pool, setPool] = useState<PoolItem[]>([]);
  const [poolLoading, setPoolLoading] = useState(false);
  const [mediaHistory, setMediaHistory] = useState<MediaHistoryItem[]>([]);
  const [lightbox, setLightbox] = useState<{ url: string; item?: MediaHistoryItem } | null>(null);
  const [reuseData, setReuseData] = useState<{ prompt?: string; references?: string[] } | null>(null);
  const [editTarget, setEditTarget] = useState<EditTarget | null>(null);
  const [reviewData, setReviewData] = useState<JobReviewPayload | null>(null);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const pollTimerRef = useRef<number | null>(null);
  const activeJobRef = useRef<string | null>(null);

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

  useEffect(() => {
    return () => {
      if (pollTimerRef.current != null) {
        window.clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };
  }, []);

  function applyStageEvent(event: Record<string, any>) {
    switch (event.stage) {
      // ── V2 pipeline stages ──
      case 'preparing_references':
        setStatus({ type: 'preparing_references', message: event.message || 'Preparando referências…' });
        break;
      case 'stabilizing_garment':
        setStatus({ type: 'stabilizing_garment', message: event.message || 'Estabilizando a peça…' });
        break;
      case 'creating_listing':
        setStatus({
          type: 'creating_listing',
          message: event.message || 'Criando o anúncio…',
          current: typeof event.current === 'number' ? event.current : undefined,
          total: typeof event.total === 'number' ? event.total : undefined,
        });
        break;
      // ── Legacy stages ──
      case 'mode_selected':
        setStatus({ type: 'mode_selected', message: event.message, pipeline_mode: event.pipeline_mode });
        break;
      case 'researching':
        setStatus({ type: 'researching', message: event.message });
        break;
      case 'analyzing':
        setStatus({ type: 'analyzing', message: event.message });
        break;
      case 'triage_done':
        setStatus({
          type: 'triage_done',
          message: event.message,
          grounding_mode: event.grounding_mode,
          grounding_score: event.grounding_score,
          garment_hypothesis: event.garment_hypothesis,
          complexity_score: event.complexity_score,
          hint_confidence: event.hint_confidence,
          trigger_reason: event.trigger_reason,
          classifier_summary: event.classifier_summary,
          reason_codes: event.reason_codes || [],
        });
        break;
      case 'prompt_ready':
        setStatus({
          type: 'prompt_ready',
          message: event.message,
          prompt: event.prompt,
          image_analysis: event.image_analysis,
          grounding: event.grounding,
          quality_contract: event.quality_contract,
          classifier_summary: event.classifier_summary,
          reference_pack_stats: event.reference_pack_stats,
          guided_applied: event.guided_applied,
          guided_summary: event.guided_summary,
        });
        break;
      // ── Common stages ──
      case 'generating':
        setStatus({ type: 'generating', message: event.message, current: event.current, total: event.total });
        break;
    }
  }

  /* ── Handle Edit (edição pontual) ───────────────── */
  async function handleEdit(editInstruction: string, target: EditTarget, files?: File[]) {
    setStatus({ type: 'editing', message: 'Preparando edição…' });
    setEditTarget(null); // Remove banner

    const fd = new FormData();
    fd.append('source_url', target.url);
    fd.append('edit_instruction', editInstruction);
    if (target.prompt) fd.append('source_prompt', target.prompt);
    if (target.session_id) fd.append('source_session_id', target.session_id);
    if (target.aspect_ratio) fd.append('aspect_ratio', target.aspect_ratio);
    if (target.resolution) fd.append('resolution', target.resolution);
    // Anexar imagens de referência
    if (files?.length) {
      for (const f of files) fd.append('images', f);
    }

    try {
      const res = await fetch('/edit/stream', { method: 'POST', body: fd });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Erro desconhecido' }));
        throw new Error(err.detail ?? `HTTP ${res.status}`);
      }

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      if (!reader) throw new Error('Stream indisponível');

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const event = JSON.parse(line.slice(6));
            if (event.stage === 'editing') {
              setStatus({ type: 'editing', message: event.message || 'Editando…' });
            } else if (event.stage === 'prompt_ready') {
              setStatus({ type: 'editing', message: event.change_summary || 'Prompt de edição pronto…' });
            } else if (event.stage === 'generating') {
              setStatus({ type: 'generating', message: event.message || 'Gerando…', current: 1, total: 1 });
            } else if (event.stage === 'done') {
              setStatus({ type: 'done', response: event });
              fetchHistory();
            } else if (event.stage === 'error') {
              setStatus({ type: 'error', message: event.message || 'Erro na edição' });
            }
          } catch { /* ignore parse errors */ }
        }
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro inesperado na edição';
      setStatus({ type: 'error', message: msg });
    }
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
      prompt: item.edit_instruction || item.prompt || item.optimized_prompt,
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

  async function handleGenerate(payload: {
    prompt: string;
    files: File[];
    n_images: number;
    aspect_ratio: AspectRatio;
    resolution: Resolution;
    preset: Preset;
    scene_preference: ScenePreference;
    fidelity_mode: FidelityMode;
    pose_flex_mode: PoseFlexMode;
  }) {
    if (pollTimerRef.current != null) {
      window.clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
    setStatus({ type: 'preparing_references', message: 'Iniciando…' });

    const fd = new FormData();
    if (payload.prompt) fd.append('prompt', payload.prompt);
    fd.append('n_images', String(payload.n_images));
    fd.append('aspect_ratio', payload.aspect_ratio);
    fd.append('resolution', payload.resolution);
    fd.append('preset', payload.preset);
    fd.append('scene_preference', payload.scene_preference);
    fd.append('fidelity_mode', payload.fidelity_mode);
    fd.append('pose_flex_mode', payload.pose_flex_mode);
    payload.files.forEach(f => fd.append('images', f));

    try {
      const res = await fetch('/generate/async', {
        method: 'POST',
        body: fd,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Erro desconhecido' }));
        throw new Error(err.detail ?? `HTTP ${res.status}`);
      }

      const submit = await res.json();
      const jobId = String(submit?.job_id || '').trim();
      if (!jobId) throw new Error('Job assíncrono inválido');
      activeJobRef.current = jobId;
      setStatus({ type: 'analyzing', message: `Job enfileirado (${jobId})…` });

      let polling = false;
      pollTimerRef.current = window.setInterval(async () => {
        if (polling) return;
        polling = true;
        try {
          const statusRes = await fetch(`/generate/jobs/${jobId}`);
          if (!statusRes.ok) {
            throw new Error(`Falha ao consultar job (${statusRes.status})`);
          }
          const job = await statusRes.json();
          const stage = job?.stage as string | undefined;
          const event = (job?.event || {}) as Record<string, any>;
          if (stage && !event.stage) event.stage = stage;

          if (job?.status === 'queued') {
            setStatus({ type: 'preparing_references', message: 'Job na fila…' });
          } else if (job?.status === 'running') {
            if (event.stage) applyStageEvent(event);
            else setStatus({ type: 'preparing_references', message: 'Processando…' });
          } else if (job?.status === 'done') {
            const response = job?.response;
            setStatus({
              type: Array.isArray(response?.failed_indices) && response.failed_indices.length > 0 ? 'done_partial' : 'done',
              response,
            });
            fetchHistory();
            if (response?.session_id) {
              fetchReviewSessionData(String(response.session_id)).catch(() => undefined);
            }
            if (pollTimerRef.current != null) {
              window.clearInterval(pollTimerRef.current);
              pollTimerRef.current = null;
            }
          } else if (job?.status === 'error') {
            const message = String(job?.error || 'Erro no job assíncrono');
            setStatus({ type: 'error', message });
            if (pollTimerRef.current != null) {
              window.clearInterval(pollTimerRef.current);
              pollTimerRef.current = null;
            }
          }
        } catch (pollErr: unknown) {
          const msg = pollErr instanceof Error ? pollErr.message : 'Falha ao consultar job';
          setStatus({ type: 'error', message: msg });
          if (pollTimerRef.current != null) {
            window.clearInterval(pollTimerRef.current);
            pollTimerRef.current = null;
          }
        } finally {
          polling = false;
        }
      }, 1200);

    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro inesperado';
      setStatus({ type: 'error', message: msg });
    }
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

                <div className="generate-content scroll-y" aria-live="polite">
                  <Gallery
                    status={status}
                    mediaHistory={mediaHistory}
                    onDelete={handleHistoryDelete}
                    onReuse={handleReuse}
                    onLightbox={(url) => setLightbox({ url })}
                    onLightboxItem={(item) => setLightbox({ url: item.url.startsWith('http') ? item.url : `${window.location.origin}${item.url}`, item })}
                  />
                </div>

                <ChatInput
                  status={status}
                  onSubmit={handleGenerate}
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
                <div className="generate-content scroll-y" aria-live="polite">
                  <Gallery
                    status={{ type: 'idle' }}
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
                      <a href={lightbox.url} download={lightbox.item.filename} className="lightbox-action-btn" title="Baixar">
                        <Download size={14} />
                      </a>
                    </div>
                  </div>

                  {/* Configs como badges */}
                  <div className="lightbox-badges">
                    {lightbox.item.aspect_ratio && <span className="badge">{lightbox.item.aspect_ratio}</span>}
                    {lightbox.item.resolution && <span className="badge">{lightbox.item.resolution}</span>}
                    {lightbox.item.thinking_level && <span className="badge badge--accent">{lightbox.item.thinking_level}</span>}
                    {lightbox.item.shot_type && <span className="badge">{lightbox.item.shot_type}</span>}
                    {lightbox.item.grounding_effective != null && (
                      <span className={`badge ${lightbox.item.grounding_effective ? 'badge--success' : ''}`}>
                        {lightbox.item.grounding_effective ? '🌐 Pesquisa web ativa' : 'Sem pesquisa web'}
                      </span>
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
