import { AlertTriangle, CheckCircle2, ClipboardList, Eye, RefreshCw, RotateCcw, SearchCode } from 'lucide-react';
import type { JobReviewPayload } from '../types';
import { imageUrl } from '../lib/api';
import { humanizeFidelityMode, humanizeMode, humanizePoseFlexMode, humanizePreset } from '../lib/humanize';
import './ReviewPanel.css';

interface Props {
    data: JobReviewPayload | null;
    loading: boolean;
    error: string | null;
    onRefresh: () => void;
    onUseInCreate?: (review: JobReviewPayload) => void;
    onGoToCreate?: () => void;
}

function verdictLabel(verdict: string): string {
    if (verdict === 'fail') return 'Falha estrutural';
    if (verdict === 'attention') return 'Pedir refinamento';
    return 'Estruturalmente ok';
}

function gateVerdictLabel(verdict?: string | null): string {
    if (verdict === 'hard_fail') return 'hard fail';
    if (verdict === 'soft_fail') return 'soft fail';
    if (verdict === 'pass') return 'pass';
    return 'sem leitura';
}

export function ReviewPanel({ data, loading, error, onRefresh, onUseInCreate, onGoToCreate }: Props) {
    if (loading) {
        return (
            <div className="review-layout">
                <div className="review-empty">
                    <RefreshCw size={18} className="spin" aria-hidden="true" />
                    <p className="t-sm text-tertiary">Carregando revisão do último job…</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="review-layout">
                <div className="review-empty">
                    <AlertTriangle size={18} className="text-error" aria-hidden="true" />
                    <p className="t-sm text-secondary">{error}</p>
                    <button className="review-action-btn" onClick={onRefresh} type="button">
                        <RefreshCw size={14} /> Tentar novamente
                    </button>
                </div>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="review-layout">
                <div className="review-empty">
                    <ClipboardList size={32} className="review-empty-icon" aria-hidden="true" />
                    <p className="t-sm text-secondary" style={{ fontWeight: 600 }}>Nenhuma geração revisada ainda</p>
                    <p className="t-xs text-tertiary" style={{ textAlign: 'center', maxWidth: 260, lineHeight: 1.5 }}>
                        Gere uma imagem e ela aparecerá aqui com análise de qualidade automática.
                    </p>
                    {onGoToCreate && (
                        <button className="review-action-btn review-action-btn--primary" onClick={onGoToCreate} type="button">
                            Criar agora
                        </button>
                    )}
                </div>
            </div>
        );
    }

    const baseImage = data.assets.base_image ? imageUrl(data.assets.base_image) : null;
    const finalImage = data.assets.final_images[0] ? imageUrl(data.assets.final_images[0]) : null;
    const stage1Gate = data.gate?.stage1;
    const stage2Gate = data.gate?.stage2_runs?.[0];

    return (
        <div className="review-layout">
            <header className="review-header">
                <div>
                    <h1 className="t-h3">Revisão</h1>
                    <p className="t-sm text-tertiary">
                        Último job analisado com o próprio bundle de produção
                    </p>
                </div>
                <div className="review-header-actions">
                    <button className="review-action-btn" onClick={onRefresh} type="button">
                        <RefreshCw size={14} /> Atualizar
                    </button>
                    {onUseInCreate && data.assets.reuse_reference_urls.length > 0 && (
                        <button className="review-action-btn review-action-btn--accent" onClick={() => onUseInCreate(data)} type="button">
                            <RotateCcw size={14} /> Refinar no app
                        </button>
                    )}
                </div>
            </header>

            <section className="review-summary-card">
                <div className="review-summary-top">
                    <span className={`review-verdict review-verdict--${data.review.verdict}`}>
                        {data.review.verdict === 'ok' ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
                        {verdictLabel(data.review.verdict)}
                    </span>
                    <a className="review-report-link" href={imageUrl(data.report_url)} target="_blank" rel="noreferrer">
                        <SearchCode size={14} /> Abrir report.json
                    </a>
                </div>
                <p className="t-sm text-secondary">{data.review.summary}</p>
                <div className="review-meta-row">
                    {data.context.mode && <span className="badge badge--sm badge--accent" title={data.context.mode}>{humanizeMode(data.context.mode)}</span>}
                    {data.context.preset && <span className="badge badge--sm" title={data.context.preset}>{humanizePreset(data.context.preset)}</span>}
                    {data.context.fidelity_mode && <span className="badge badge--sm" title={data.context.fidelity_mode}>{humanizeFidelityMode(data.context.fidelity_mode)}</span>}
                    {data.context.pose_flex_mode && <span className="badge badge--sm" title={data.context.pose_flex_mode}>{humanizePoseFlexMode(data.context.pose_flex_mode)}</span>}
                    {data.context.reference_guard_strength && <span className="badge badge--sm">guard: {data.context.reference_guard_strength}</span>}
                </div>
            </section>

            {data.gate && (
                <section className="review-card">
                    <div className="review-card-head">
                        <h2 className="t-label">Gate de fidelidade</h2>
                    </div>
                    <div className="review-gate-grid">
                        <div className="review-gate-panel">
                            <div className="review-gate-head">
                                <span className="t-xs text-tertiary">Política</span>
                                <span className={`badge badge--sm ${data.gate.enabled ? '' : ''}`}>
                                    {data.gate.enabled ? 'ativo' : 'inativo'}
                                </span>
                            </div>
                            <p className="t-xs text-secondary">
                                {(data.gate.reasons && data.gate.reasons.length > 0)
                                    ? data.gate.reasons.join(' • ')
                                    : 'Sem motivos especiais registrados'}
                            </p>
                        </div>
                        <div className="review-gate-panel">
                            <div className="review-gate-head">
                                <span className="t-xs text-tertiary">Stage 1</span>
                                <span className="badge badge--sm">base: {gateVerdictLabel(stage1Gate?.verdict)}</span>
                            </div>
                            <p className="t-xs text-secondary">
                                {stage1Gate?.summary || 'Sem leitura de gate para a base.'}
                            </p>
                            <div className="review-gate-meta">
                                {typeof stage1Gate?.fidelity_score === 'number' && <span className="badge badge--sm">score: {stage1Gate.fidelity_score.toFixed(2)}</span>}
                                {stage1Gate?.recovery_applied && <span className="badge badge--sm">recovery aplicado</span>}
                            </div>
                        </div>
                        <div className="review-gate-panel">
                            <div className="review-gate-head">
                                <span className="t-xs text-tertiary">Stage 2</span>
                                <span className="badge badge--sm">final: {gateVerdictLabel(stage2Gate?.verdict)}</span>
                            </div>
                            <p className="t-xs text-secondary">
                                {stage2Gate?.summary || 'Sem leitura de gate para o final.'}
                            </p>
                            <div className="review-gate-meta">
                                {typeof stage2Gate?.fidelity_score === 'number' && <span className="badge badge--sm">score: {stage2Gate.fidelity_score.toFixed(2)}</span>}
                                {stage2Gate?.recovery_applied && <span className="badge badge--sm">recovery aplicado</span>}
                                {(stage2Gate?.issue_codes?.length ?? 0) > 0 && <span className="badge badge--sm">{stage2Gate?.issue_codes.join(', ')}</span>}
                            </div>
                        </div>
                    </div>
                </section>
            )}

            <section className="review-grid">
                <article className="review-card">
                    <div className="review-card-head">
                        <h2 className="t-label">Findings</h2>
                    </div>
                    <div className="review-findings">
                        {data.review.findings.length === 0 ? (
                            <p className="t-sm text-tertiary">Nenhum finding estrutural relevante encontrado.</p>
                        ) : data.review.findings.map((finding, index) => (
                            <div key={`${finding.title}-${index}`} className={`review-finding review-finding--${finding.severity}`}>
                                <div className="review-finding-top">
                                    <span className="review-finding-severity">{finding.severity}</span>
                                    <span className="t-xs text-tertiary">{finding.category}</span>
                                </div>
                                <p className="t-sm text-primary review-finding-title">{finding.title}</p>
                                <p className="t-xs text-secondary">{finding.evidence}</p>
                                <p className="t-xs text-tertiary">{finding.refinement}</p>
                            </div>
                        ))}
                    </div>
                </article>

                <article className="review-card">
                    <div className="review-card-head">
                        <h2 className="t-label">Ações sugeridas</h2>
                    </div>
                    <div className="review-actions-list">
                        {data.review.recommended_actions.length === 0 ? (
                            <p className="t-sm text-tertiary">Sem ações pendentes.</p>
                        ) : data.review.recommended_actions.map((item, index) => (
                            <p key={`${item}-${index}`} className="review-action-line t-sm text-secondary">{item}</p>
                        ))}
                    </div>
                </article>
            </section>

            <section className="review-card">
                <div className="review-card-head">
                    <h2 className="t-label">Comparação visual</h2>
                </div>
                <div className="review-compare">
                    <div className="review-compare-slot">
                        <span className="t-xs text-tertiary">Referências</span>
                        <div className="review-ref-strip">
                            {data.assets.original_references.map((url, index) => (
                                <img key={`${url}-${index}`} src={imageUrl(url)} alt={`Referência ${index + 1}`} className="review-ref-thumb" />
                            ))}
                        </div>
                    </div>
                    <div className="review-compare-slot">
                        <span className="t-xs text-tertiary">Base selecionada</span>
                        {baseImage ? <img src={baseImage} alt="Base selecionada" className="review-main-image" /> : <div className="review-image-empty"><Eye size={16} />Sem base</div>}
                    </div>
                    <div className="review-compare-slot">
                        <span className="t-xs text-tertiary">Resultado final</span>
                        {finalImage ? <img src={finalImage} alt="Resultado final" className="review-main-image" /> : <div className="review-image-empty"><Eye size={16} />Sem resultado</div>}
                    </div>
                </div>
            </section>
        </div>
    );
}
