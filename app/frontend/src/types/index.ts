export type AspectRatio = '1:1' | '9:16' | '16:9' | '4:3' | '3:4' | '4:5';
export type Resolution = '1K' | '2K' | '4K';
export type AngleTarget = 'front' | 'left_3q' | 'right_3q' | 'left_profile' | 'right_profile' | 'back' | 'left_3q_back' | 'right_3q_back';
export type PoolType = 'modelo' | 'roupa' | 'cenario';
export type PipelineMode = 'reference_mode' | 'reference_mode_strict' | 'text_mode';
export type CreateCategory = 'fashion';
export type Mode = 'catalog_clean' | 'natural' | 'lifestyle' | 'editorial_commercial';

// ── V2 types ──
export type Preset = 'catalog_clean' | 'marketplace_lifestyle' | 'premium_lifestyle' | 'ugc_real_br';
export type ScenePreference = 'auto_br' | 'indoor_br' | 'outdoor_br';
export type FidelityMode = 'balanceada' | 'estrita';

// ── Marketplace types ──
export type MarketplaceChannel = 'shopee' | 'mercado_livre';
export type MarketplaceOperation = 'main_variation' | 'color_variations';

// ── Legacy types (mantidos para compatibilidade de leitura do histórico) ──
export type GroundingStrategy = 'auto' | 'on' | 'off';
export type GuidedAgeRange = '18-24' | '25-34' | '35-44' | '45+';
export type GuidedSetMode = 'unica' | 'conjunto';
export type GuidedSceneType = 'interno' | 'externo';
export type GuidedPoseStyle = 'tradicional' | 'criativa';
export type GuidedCaptureDistance = 'distante' | 'media' | 'proxima';

export interface EditTarget {
    session_id: string;
    filename: string;
    url: string;
    prompt?: string;
    aspect_ratio?: AspectRatio | string;
    resolution?: Resolution | string;
    shot_type?: string;
}

export interface EditCommandCenterOptions {
    editSubmode?: 'angle_transform';
    viewIntent?: 'soft_turn' | 'back_view' | 'preserve';
    distanceIntent?: 'preserve' | 'closer' | 'farther';
    poseFreedom?: 'locked' | 'flexible';
    angleTarget?: AngleTarget;
    preserveFraming?: boolean;
    preserveCameraHeight?: boolean;
    preserveDistance?: boolean;
    preservePose?: boolean;
    aspect_ratio?: AspectRatio;
    resolution?: Resolution;
    sourceShotType?: string;
    freeText?: string;
}

export interface GuidedBrief {
    enabled: boolean;
    model: { age_range: GuidedAgeRange };
    garment: { set_mode: GuidedSetMode };
    scene: { type: GuidedSceneType };
    pose: { style: GuidedPoseStyle };
    capture: { distance: GuidedCaptureDistance };
    fidelity_mode?: 'balanceada' | 'estrita';
}

export interface GuidedSummary {
    applied: boolean;
    shot_type: 'wide' | 'medium' | 'close-up' | 'auto';
    set_mode: GuidedSetMode;
    detected_garment_roles?: string[];
    set_pattern_score?: number;
    set_pattern_cues?: string[];
    set_lock_mode?: 'off' | 'generic' | 'explicit';
    age_range: GuidedAgeRange;
    scene: GuidedSceneType;
    pose: GuidedPoseStyle;
}

export interface GenerateRequest {
    category?: CreateCategory;
    prompt?: string;
    n_images?: number;
    aspect_ratio?: AspectRatio;
    resolution?: Resolution;
    session_id?: string;
    grounding_strategy?: GroundingStrategy;
    guided_brief?: GuidedBrief;
    mode?: Mode;
    preset?: Preset;
    scene_preference?: ScenePreference;
    fidelity_mode?: FidelityMode;
}

export interface GeneratedImage {
    filename: string;
    url: string;
    index: number;
}

export interface GroundingSource {
    title: string;
    uri: string;
    snippet?: string;
}

export interface GroundingInfo {
    effective: boolean;
    attempted?: boolean;
    queries: string[];
    sources: GroundingSource[];
    engine: string;
    source_engine?: string;
    mode?: string;
    trigger_reason?: string;
    garment_hint?: string;
    hint_confidence?: number;
    complexity_score?: number;
    grounded_images_count?: number;
}

export interface ClassifierSummary {
    garment_type?: string;
    garment_category?: string;
    silhouette_tokens?: string[];
    atypical?: boolean;
    complexity_score?: number;
    uncertainty_score?: number;
    confidence?: number;
}

export interface QualityContract {
    effective_formula?: string;
    category?: string;
    thresholds?: { fidelity?: number; commercial?: number };
    fidelity_score?: number;
    commercial_score?: number;
    diversity_score?: number;
    grounding_reliability?: number;
    global_score?: number;
    generation_score?: number;
    needs_repair?: boolean;
    reason_codes?: string[];
}

export interface PromptCompilerDebugClause {
    text: string;
    source: string;
}

export interface PromptCompilerDebugDropped {
    text: string;
    reason: string;
}

export interface PromptCompilerDebug {
    used_clauses:       PromptCompilerDebugClause[];
    discarded_clauses:  PromptCompilerDebugDropped[];
    base_words:         number;
    base_truncated:     boolean;
    total_words:        number;
    word_budget:        number;
    residual_negatives: string[];
}

export interface UserIntent {
    raw?: string;
    normalized?: string;
    intent_tags?: string[];
    normalizer_source?: string;
}

export interface GenerateResponse {
    category?: CreateCategory;
    session_id: string;
    optimized_prompt: string;
    pipeline_mode?: PipelineMode;
    pipeline_version?: 'v2';
    thinking_level?: string;
    thinking_reason?: string;
    shot_type?: 'wide' | 'medium' | 'close-up' | 'auto';
    realism_level?: 1 | 2 | 3;
    images: GeneratedImage[];
    failed_indices?: number[] | null;
    generation_time?: number;
    pool_refs_used?: number;
    grounding?: GroundingInfo;
    quality_contract?: QualityContract;
    fidelity_score?: number;
    commercial_score?: number;
    diversity_score?: number;
    grounding_reliability?: number;
    reason_codes?: string[];
    repair_applied?: boolean;
    reference_pack_stats?: Record<string, number>;
    classifier_summary?: ClassifierSummary;
    guided_applied?: boolean;
    guided_summary?: GuidedSummary;
    prompt_compiler_debug?: PromptCompilerDebug;
    user_intent?: UserIntent;
    art_direction_summary?: Record<string, string>;
    mode?: Mode;
    preset?: Preset;
    scene_preference?: ScenePreference;
    fidelity_mode?: FidelityMode;
    debug_report_url?: string;
    debug_report_path?: string;
}

export interface ReviewFinding {
    severity: 'high' | 'medium' | 'low';
    category: string;
    title: string;
    evidence: string;
    refinement: string;
}

export interface ReviewGateResult {
    available: boolean;
    verdict?: 'pass' | 'soft_fail' | 'hard_fail' | null;
    fidelity_score?: number | null;
    issue_codes: string[];
    summary?: string | null;
    recovery_applied?: boolean;
    index?: number;
    selected?: string | null;
}

export interface JobReviewPayload {
    session_id: string;
    written_at: number;
    report_url: string;
    report_path: string;
    assets: {
        original_references: string[];
        selected_base_references: string[];
        selected_edit_anchors: string[];
        selected_identity_safe: string[];
        base_image?: string | null;
        final_images: string[];
        reuse_reference_urls: string[];
    };
    context: {
        prompt?: string | null;
        mode?: string | null;
        preset?: string | null;
        scene_preference?: string | null;
        fidelity_mode?: string | null;
        reference_guard_strength?: string | null;
        selected_names?: Record<string, string[]>;
        structural_contract?: Record<string, unknown> | null;
        set_detection?: Record<string, unknown> | null;
    };
    gate?: {
        enabled: boolean;
        reasons: string[];
        stage1: ReviewGateResult;
        stage2_runs: ReviewGateResult[];
    };
    review: {
        verdict: 'ok' | 'attention' | 'fail';
        summary: string;
        findings: ReviewFinding[];
        recommended_actions: string[];
    };
}

export interface MediaHistoryItem {
    category?: CreateCategory;
    id: string;
    session_id?: string;
    filename: string;
    url: string;
    prompt?: string;
    optimized_prompt?: string;
    edit_instruction?: string;
    thinking_level?: string;
    shot_type?: string;
    aspect_ratio?: string;
    resolution?: string;
    grounding_effective?: boolean;
    references?: string[];
    created_at: number;
    // Auditoria — presente apenas em gerações novas
    base_prompt?: string;
    camera_and_realism?: string;
    camera_profile?: string;
    grounding_mode?: string;
    reason_codes?: string[];
    // Parâmetros de geração (observabilidade)
    mode?: string;
    preset?: string;
    scene_preference?: string;
    fidelity_mode?: string;
    pipeline_mode?: string;
    // Marketplace
    marketplace_channel?: string;
    marketplace_operation?: string;
    slot_id?: string;
}

export interface PoolItem {
    id: string;
    type: PoolType;
    filename: string;
    path: string;
    url: string;
    added_at: string;
}

// ── Job Queue Types ──────────────────────────────────────────────────────────
export type JobType = 'generate' | 'edit' | 'marketplace';
export type JobStatus = 'queued' | 'running' | 'done' | 'error';

export interface EditJobResult {
    session_id: string;
    images: Array<{ url: string; filename: string; size_kb?: number; mime_type?: string }>;
    edit_instruction: string;
    edit_type?: string;
    edit_submode?: string;
    change_summary?: string;
    optimized_prompt?: string;
    aspect_ratio?: string;
    resolution?: string;
    source_session_id?: string;
}

export interface JobEntry {
    id: string;
    type: JobType;
    status: JobStatus;
    stage: string | null;
    message: string | null;
    progress: { current: number; total: number } | null;
    result: GenerateResponse | null;      // jobs de geração / marketplace
    editResult: EditJobResult | null;     // jobs de edição
    error: string | null;
    createdAt: number;
    inputThumbnails: string[];            // object URLs para preview (revogados no dismiss)
    prompt: string | null;               // texto resumido para exibir no card
    count: number;                       // nº de imagens esperadas → nº de cards skeleton
    meta: Record<string, unknown> | null; // parâmetros do job (para observabilidade em erros)
}

export type GenerationStatus =
    | { type: 'idle' }
    // ── V2 pipeline stages (seller-facing) ──
    | { type: 'stabilizing_garment'; message: string }
    | { type: 'creating_listing'; message: string; current?: number; total?: number }
    // ── Legacy stages (mantidos para fluxo antigo) ──
    | { type: 'mode_selected'; message: string; pipeline_mode: PipelineMode }
    | { type: 'researching'; message: string }
    | { type: 'analyzing'; message: string }
    | {
        type: 'triage_done';
        message: string;
        grounding_mode: 'off' | 'lexical' | 'full';
        grounding_score?: number;
        garment_hypothesis?: string;
        complexity_score?: number;
        hint_confidence?: number;
        trigger_reason?: string;
        classifier_summary?: ClassifierSummary;
        reason_codes?: string[];
    }
    | {
        type: 'prompt_ready';
        message: string;
        prompt: string;
        image_analysis?: string;
        grounding?: GroundingInfo;
        quality_contract?: QualityContract;
        classifier_summary?: ClassifierSummary;
        reference_pack_stats?: Record<string, number>;
        guided_applied?: boolean;
        guided_summary?: GuidedSummary;
        prompt_compiler_debug?: PromptCompilerDebug;
    }
    // ── Common stages ──
    | { type: 'editing'; message: string }
    | { type: 'generating'; message: string; current: number; total: number }
    | { type: 'done'; response: GenerateResponse }
    | { type: 'done_partial'; response: GenerateResponse }
    | { type: 'error'; message: string };
