import { useCallback, useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Sidebar } from './components/Sidebar';
import { ChatInput } from './components/ChatInput';
import { Gallery } from './components/Gallery';
import { PoolPanel } from './components/PoolPanel';
import { generateImages, listPool } from './lib/api';
import type {
  GenerationStatus,
  PoolItem,
  AspectRatio,
  Resolution,
} from './types';
import './App.css';

type Tab = 'generate' | 'pool' | 'settings';

export default function App() {
  const [tab, setTab] = useState<Tab>('generate');
  const [status, setStatus] = useState<GenerationStatus>({ type: 'idle' });
  const [pool, setPool] = useState<PoolItem[]>([]);
  const [poolLoading, setPoolLoading] = useState(false);

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

  useEffect(() => { fetchPool(); }, [fetchPool]);

  async function handleGenerate(payload: {
    prompt: string;
    files: File[];
    n_images: number;
    aspect_ratio: AspectRatio;
    resolution: Resolution;
  }) {
    setStatus({ type: 'thinking' });

    const fd = new FormData();
    if (payload.prompt) fd.append('prompt', payload.prompt);
    fd.append('n_images', String(payload.n_images));
    fd.append('aspect_ratio', payload.aspect_ratio);
    fd.append('resolution', payload.resolution);
    payload.files.forEach(f => fd.append('uploads', f));

    try {
      // Simula progress enquanto espera
      let progress = 0;
      const progressInterval = setInterval(() => {
        progress = Math.min(progress + Math.random() * 12, 88);
        setStatus({ type: 'generating', progress: Math.round(progress) });
      }, 300);

      const res = await generateImages(fd);
      clearInterval(progressInterval);

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Erro desconhecido' }));
        throw new Error(err.detail ?? `HTTP ${res.status}`);
      }

      const data = await res.json();
      setStatus({ type: 'done', response: data });

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

        <main id="main-content" className="app-main" role="main">
          <AnimatePresence mode="wait">
            {tab === 'generate' && (
              <motion.div
                key="generate"
                className="generate-layout"
                initial={{ opacity: 0, x: 12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -12 }}
                transition={{ duration: 0.2 }}
              >
                <header className="generate-header">
                  <h1 className="t-h3">Studio</h1>
                  <p className="t-sm text-tertiary">
                    Geração de imagens com Nano Banana 2 · Agente de prompt autônomo
                  </p>
                </header>

                <div className="generate-content scroll-y" aria-live="polite">
                  <Gallery status={status} />
                </div>

                <ChatInput status={status} onSubmit={handleGenerate} />
              </motion.div>
            )}

            {tab === 'pool' && (
              <motion.div
                key="pool"
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

            {tab === 'settings' && (
              <motion.div
                key="settings"
                className="settings-layout"
                initial={{ opacity: 0, x: 12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -12 }}
                transition={{ duration: 0.2 }}
              >
                <div className="settings-placeholder">
                  <span className="t-h4 text-secondary">Configurações</span>
                  <p className="t-sm text-tertiary">Em breve — API key, defaults globais e temas.</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </>
  );
}
