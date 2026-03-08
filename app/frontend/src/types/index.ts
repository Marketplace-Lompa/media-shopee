export type AspectRatio = '1:1' | '9:16' | '16:9' | '4:3' | '3:4';
export type Resolution = '1K' | '2K' | '4K';
export type PoolType = 'modelo' | 'roupa' | 'cenario';
export type GroundingStrategy = 'auto' | 'on' | 'off';
export type PipelineMode = 'reference_mode' | 'text_mode';
export type GuidedAgeRange = '18-24' | '25-34' | '35-44' | '45+';
export type GuidedSetMode = 'unica' | 'conjunto';
export type GuidedSceneType = 'interno' | 'externo';
export type GuidedPoseStyle = 'tradicional' | 'criativa';
export type GuidedCaptureDistance = 'distante' | 'media' | 'proxima';

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
    prompt?: string;
    n_images?: number;
    aspect_ratio?: AspectRatio;
    resolution?: Resolution;
    session_id?: string;
    grounding_strategy?: GroundingStrategy;
    guided_brief?: GuidedBrief;
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

export interface GenerateResponse {
    session_id: string;
    optimized_prompt: string;
    pipeline_mode?: PipelineMode;
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
}

export interface MediaHistoryItem {
    id: string;
    session_id?: string;
    filename: string;
    url: string;
    prompt?: string;
    optimized_prompt?: string;
    thinking_level?: string;
    shot_type?: string;
    aspect_ratio?: string;
    resolution?: string;
    grounding_effective?: boolean;
    references?: string[];
    created_at: number;
}

export interface PoolItem {
    id: string;
    type: PoolType;
    filename: string;
    path: string;
    url: string;
    added_at: string;
}

export type GenerationStatus =
    | { type: 'idle' }
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
    }
    | { type: 'generating'; message: string; current: number; total: number }
    | { type: 'done'; response: GenerateResponse }
    | { type: 'done_partial'; response: GenerateResponse }
    | { type: 'error'; message: string };
