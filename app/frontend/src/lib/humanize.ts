const PRESET_LABELS: Record<string, string> = {
  catalog_clean: 'Catálogo',
  marketplace_lifestyle: 'Com contexto',
  premium_lifestyle: 'Premium',
  ugc_real_br: 'Conteúdo real',
};

const SCENE_LABELS: Record<string, string> = {
  auto_br: 'Cena sugerida',
  indoor_br: 'Ambiente interno',
  outdoor_br: 'Ambiente externo',
};

const FIDELITY_LABELS: Record<string, string> = {
  estrita: 'Fidelidade alta',
  balanceada: 'Fidelidade equilibrada',
};

const POSE_LABELS: Record<string, string> = {
  auto: 'Pose automática',
  controlled: 'Pose estável',
  balanced: 'Pose equilibrada',
  dynamic: 'Pose dinâmica',
};

const PIPELINE_LABELS: Record<string, string> = {
  reference_mode_strict: 'Modo referência (estrito)',
  reference_mode: 'Modo referência',
  text_mode: 'Modo texto',
};

const MARKETPLACE_CHANNEL_LABELS: Record<string, string> = {
  shopee: 'Canal: Shopee',
  mercado_livre: 'Canal: Mercado Livre',
};

const MARKETPLACE_OPERATION_LABELS: Record<string, string> = {
  main_variation: 'Objetivo: Fotos principais',
  color_variations: 'Objetivo: Variações de cor',
};

const SLOT_LABELS: Record<string, string> = {
  hero_front: 'Capa principal',
  front_3_4: 'Ângulo frontal 3/4',
  back_or_side: 'Costas ou lateral',
  fabric_closeup: 'Close de tecido',
  functional_detail_or_size: 'Detalhe funcional/medidas',
  color_hero_front: 'Capa da cor',
  color_front_3_4: 'Ângulo 3/4 da cor',
  color_detail: 'Detalhe da cor',
};

function titleizeToken(value?: string | null): string {
  if (!value) return '';
  return value
    .replace(/_/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, ch => ch.toUpperCase());
}

function labelFor(map: Record<string, string>, value?: string | null): string {
  if (!value) return '';
  return map[value] ?? titleizeToken(value);
}

export function humanizePreset(value?: string | null): string {
  return labelFor(PRESET_LABELS, value);
}

export function humanizeScenePreference(value?: string | null): string {
  return labelFor(SCENE_LABELS, value);
}

export function humanizeFidelityMode(value?: string | null): string {
  return labelFor(FIDELITY_LABELS, value);
}

export function humanizePoseFlexMode(value?: string | null): string {
  return labelFor(POSE_LABELS, value);
}

export function humanizePipelineMode(value?: string | null): string {
  return labelFor(PIPELINE_LABELS, value);
}

export function humanizeMarketplaceChannel(value?: string | null): string {
  return labelFor(MARKETPLACE_CHANNEL_LABELS, value);
}

export function humanizeMarketplaceOperation(value?: string | null): string {
  return labelFor(MARKETPLACE_OPERATION_LABELS, value);
}

export function humanizeSlotId(value?: string | null): string {
  return labelFor(SLOT_LABELS, value);
}

/**
 * Transforma mensagens brutas do pipeline em copy user-friendly.
 * Ex: "Gerando slot 3/5: back_or_side" → "Criando foto 3 de 5 · Costas ou lateral"
 */
export function humanizeJobMessage(raw?: string | null): string | null {
  if (!raw) return null;

  // Match: "Gerando slot X/Y: slot_id"
  const slotMatch = raw.match(/^Gerando slot (\d+)\/(\d+):\s*(\S+)/i);
  if (slotMatch) {
    const [, current, total, slotId] = slotMatch;
    const slotLabel = SLOT_LABELS[slotId] ?? titleizeToken(slotId);
    return `Criando foto ${current} de ${total} · ${slotLabel}`;
  }

  // Match: "Gerando cor X/Y: ..."
  const colorMatch = raw.match(/^Gerando cor (\d+)\/(\d+):\s*(\S+)/i);
  if (colorMatch) {
    const [, current, total, slotId] = colorMatch;
    const slotLabel = SLOT_LABELS[slotId] ?? titleizeToken(slotId);
    return `Variação de cor ${current} de ${total} · ${slotLabel}`;
  }

  // Fallback: retorna a mensagem original
  return raw;
}
