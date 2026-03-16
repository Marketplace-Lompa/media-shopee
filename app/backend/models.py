"""
Schemas Pydantic para request/response da API.
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Payload do POST /generate"""
    prompt: Optional[str] = Field(
        default=None,
        description="Descrição em pt-BR (opcional — agente age mesmo sem prompt)"
    )
    aspect_ratio: str = Field(
        default="4:5",
        description="Proporção da imagem: 4:5, 1:1, 3:4, 4:3, 9:16, 16:9"
    )
    resolution: str = Field(
        default="1K",
        description="Resolução: 1K (padrão), 2K, 4K"
    )
    n_images: int = Field(
        default=1,
        ge=1,
        le=4,
        description="Número de imagens a gerar (1-4)"
    )
    guided_brief: Optional[dict] = Field(
        default=None,
        description="Brief guiado opcional para parametrização determinística do agente"
    )
    preset: Optional[str] = Field(
        default=None,
        description="Preset v2: catalog_clean | marketplace_lifestyle | premium_lifestyle | ugc_real_br"
    )
    scene_preference: Optional[str] = Field(
        default=None,
        description="Preferência de cena v2: auto_br | indoor_br | outdoor_br"
    )
    fidelity_mode: Optional[str] = Field(
        default=None,
        description="Modo de fidelidade v2: balanceada | estrita"
    )
    pose_flex_mode: Optional[str] = Field(
        default=None,
        description="Flexibilidade de pose v2: auto | controlled | balanced | dynamic"
    )


class GeneratedImage(BaseModel):
    """Uma imagem gerada"""
    index: int
    filename: str
    url: str          # caminho relativo servido pelo FastAPI: /outputs/{session}/{file}
    size_kb: float
    mime_type: str


class PromptCompilerDebug(BaseModel):
    """Telemetria leve do Prompt Compiler V2 — por job."""
    used_clauses:      List[dict] = Field(default_factory=list,  description="Cláusulas incluídas: [{text, source}]")
    discarded_clauses: List[dict] = Field(default_factory=list,  description="Cláusulas descartadas: [{text, reason}]")
    base_words:        int        = Field(default=0,             description="Palavras do prompt base (saída do modelo)")
    base_truncated:    bool       = Field(default=False,         description="Se o base foi truncado por sentença para caber o budget")
    total_words:       int        = Field(default=0,             description="Total de palavras no prompt final")
    word_budget:       int        = Field(default=220,           description="Orçamento de palavras configurado")
    residual_negatives: List[str] = Field(default_factory=list, description="Tokens negativos não mapeados no prompt final (para tuning)")
    camera_words:      int        = Field(default=0,             description="Palavras no bloco de câmera e realismo")
    base_budget:       int        = Field(default=0,             description="Orçamento base calculado (budget - camera_words)")
    final_words:       int        = Field(default=0,             description="Qtd real de palavras do prompt consolidado")
    camera_profile:    Optional[str] = Field(default=None,       description="Perfil de câmera/realismo selecionado: catalog_clean | catalog_natural | editorial_analog")

class GenerateResponse(BaseModel):
    """Resposta do POST /generate"""
    session_id: Optional[str] = Field(default=None, description="ID da sessão de geração")
    optimized_prompt: str = Field(description="Prompt otimizado pelo agente")
    pipeline_mode: str = Field(default="text_mode", description="Modo aplicado: reference_mode | text_mode | reference_mode_strict")
    thinking_level: str   = Field(default="MINIMAL", description="Nível de thinking decidido pelo agente")
    thinking_reason: str  = Field(default="", description="Justificativa do thinking em pt-BR")
    shot_type: str        = Field(default="auto", description="Tipo de shot decidido pelo agente: wide, medium, close-up, auto")
    realism_level: int    = Field(default=2, description="Nível de realismo 1-3 decidido pelo agente")
    aspect_ratio: str
    resolution: str
    images: List[GeneratedImage]
    failed_indices: Optional[List[int]] = Field(default=None, description="Índices que falharam em lote (quando houver)")
    pool_refs_used: int   = Field(default=0, description="Qtd de refs do pool enviadas ao Nano")
    grounding: Optional[dict] = Field(default=None, description="Metadados de grounding aplicados")
    quality_contract: Optional[dict] = Field(default=None, description="Contrato de qualidade e score global")
    fidelity_score: Optional[float] = Field(default=None, description="Score de fidelidade da peça")
    commercial_score: Optional[float] = Field(default=None, description="Score de qualidade comercial")
    diversity_score: Optional[float] = Field(default=None, description="Score de diversidade de modelo")
    grounding_reliability: Optional[float] = Field(default=None, description="Score de robustez do grounding")
    reason_codes: Optional[List[str]] = Field(default=None, description="Códigos de motivo para diagnóstico")
    repair_applied: Optional[bool] = Field(default=None, description="Se aplicou repair pass")
    reference_pack_stats: Optional[dict] = Field(default=None, description="Stats da curadoria de referências")
    classifier_summary: Optional[dict] = Field(default=None, description="Resumo do classificador visual")
    image_analysis: Optional[str] = Field(default=None, description="Análise visual da peça extraída na triagem unificada")
    guided_applied: Optional[bool] = Field(default=None, description="Se o modo guiado foi aplicado no job")
    guided_summary: Optional[dict] = Field(default=None, description="Resumo do brief guiado efetivamente aplicado")
    prompt_compiler_debug: Optional[PromptCompilerDebug] = Field(default=None, description="Telemetria do Prompt Compiler V2")
    user_intent: Optional[dict] = Field(default=None, description="Normalização do texto do usuário para intenção técnica (raw/normalized/tags)")
    # ── Campos V2 ──
    pipeline_version: Optional[str] = Field(default=None, description="Versão do pipeline: v2 para o novo fluxo")
    art_direction_summary: Optional[dict] = Field(default=None, description="Resumo de art direction aplicado (casting, scene, pose, camera, lighting, styling)")
    lighting_signature: Optional[dict] = Field(default=None, description="Assinatura de iluminação inferida das referências para compatibilidade de cena/luz")
    action_context: Optional[str] = Field(default=None, description="Intenção corporal semântica gerada para orientar pose/cena de forma natural")
    preset: Optional[str] = Field(default=None, description="Preset usado: catalog_clean | marketplace_lifestyle | premium_lifestyle | ugc_real_br")
    scene_preference: Optional[str] = Field(default=None, description="Preferência de cena: auto_br | indoor_br | outdoor_br")
    fidelity_mode: Optional[str] = Field(default=None, description="Modo de fidelidade: balanceada | estrita")
    pose_flex_mode: Optional[str] = Field(default=None, description="Flexibilidade de pose: auto | controlled | balanced | dynamic")
    pose_flex_guideline: Optional[str] = Field(default=None, description="Guia textual efetivo aplicado para flexibilidade de pose")
    generation_time: Optional[float] = Field(default=None, description="Tempo total de geração em segundos")
    debug_report_url: Optional[str] = Field(default=None, description="URL do relatório de observabilidade do pipeline v2")
    debug_report_path: Optional[str] = Field(default=None, description="Caminho local do relatório de observabilidade do pipeline v2")


class PoolItem(BaseModel):
    """Um item do Reference Pool"""
    id: str
    filename: str
    type: str       # modelo | roupa | cenario
    size_kb: float
    added_at: str


class PoolAddResponse(BaseModel):
    """Resposta do POST /pool/add"""
    id: str
    filename: str
    type: str
    message: str


class PoolListResponse(BaseModel):
    """Resposta do GET /pool"""
    items: List[PoolItem]
    total: int


class MarketplaceSlotImage(BaseModel):
    """Imagem final de um slot no fluxo Marketplace."""
    index: int = 1
    filename: Optional[str] = None
    url: Optional[str] = None
    size_kb: Optional[float] = None
    mime_type: Optional[str] = None


class MarketplaceSlotResult(BaseModel):
    """Status detalhado de um slot gerado no fluxo Marketplace."""
    slot_id: str
    slot_type: str
    color: Optional[str] = None
    status: Literal["done", "error"]
    session_id: Optional[str] = None
    pipeline_mode: Optional[str] = None
    image: Optional[MarketplaceSlotImage] = None
    error: Optional[str] = None
    debug_report_url: Optional[str] = None


class MarketplaceSummary(BaseModel):
    """Resumo final de execução do fluxo Marketplace."""
    requested_slots: int
    completed_slots: int
    failed_slots: int


class MarketplaceGenerateResponse(BaseModel):
    """Payload consolidado do fluxo Marketplace."""
    session_id: str
    pipeline_version: str = "marketplace_v1"
    marketplace_channel: Literal["shopee", "mercado_livre"]
    operation: Literal["main_variation", "color_variations"]
    detected_colors: List[dict] = Field(default_factory=list)
    slots: List[MarketplaceSlotResult] = Field(default_factory=list)
    summary: MarketplaceSummary
    config: dict = Field(default_factory=dict)
