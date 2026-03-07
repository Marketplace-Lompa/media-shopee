export type AspectRatio = '1:1' | '9:16' | '16:9' | '4:5' | '3:4';
export type Resolution = '1K' | '2K' | '4K';
export type PoolType = 'modelo' | 'roupa' | 'cenario';

export interface GenerateRequest {
    prompt?: string;
    n_images?: number;
    aspect_ratio?: AspectRatio;
    resolution?: Resolution;
    session_id?: string;
}

export interface GeneratedImage {
    filename: string;
    url: string;
    index: number;
}

export interface GenerateResponse {
    session_id: string;
    optimized_prompt: string;
    thinking_level?: string;
    thinking_reason?: string;
    shot_type?: 'wide' | 'medium' | 'close-up' | 'auto';
    realism_level?: 1 | 2 | 3;
    images: GeneratedImage[];
    generation_time?: number;
    pool_refs_used?: number;
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
    | { type: 'thinking' }
    | { type: 'generating'; progress: number }
    | { type: 'done'; response: GenerateResponse }
    | { type: 'error'; message: string };
