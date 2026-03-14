import re

# Dicionários baseados no REFERENCE_KNOWLEDGE do agente
_PT_EN_DICT = {
    # Garment
    "tricot": "flat-knit pullover",
    "croche": "crochet open-work",
    "cropped": "cropped length",
    "regata": "sleeveless top",
    "tomara que caia": "strapless bandeau",
    "gola polo": "collared polo",
    "moletom": "fleece hoodie",
    "calca pantalona": "wide-leg pleated trousers",
    "calça pantalona": "wide-leg pleated trousers",
    "calca jogger": "elastic-cuffed jogger pants",
    "calça jogger": "elastic-cuffed jogger pants",
    "saia midi": "mid-calf length skirt",
    "saia longa": "floor-length skirt",
    "vestido longo": "floor-length dress",
    "vestido midi": "mid-calf length dress",
    "manga bufante": "puffed balloon sleeves",
    "manga longa": "long sleeves",
    "decote v": "v-neckline",
    "fenda": "thigh-high slit",
    "renda": "lace overlay",
    "transparencia": "sheer see-through material",
    "transparência": "sheer see-through material",
    "estampa floral": "floral print pattern",
    "listrado": "striped pattern",
    "listras": "stripes",
    "liso": "solid color",
    "alfaiataria": "tailored structured fabric",
    
    # Adjetivos BR comuns
    "soltinho": "relaxed fluid fit",
    "justo": "form-fitting",
    "colado": "tight bodycon fit",
    "decotado": "deep neckline",
    "estampado": "patterned",
    
    # Cenario / Vibe
    "praia": "beach setting with natural sunlight",
    "piscina": "resort poolside setting",
    "festa": "evening event lighting",
    "urbano": "urban city street setting",
    "rua": "city street setting",
    "natureza": "natural outdoor setting with greenery",
    "studio": "clean studio backdrop",
    "estudio": "clean studio backdrop",
    "fundo branco": "clean seamless white background",
    
    # Pose / Composição
    "pose natural": "natural relaxed pose",
    "sorrindo": "gentle natural smile",
    "andando": "dynamic walking pose",
    "de costas": "back view showing garment back details",
    "de perfil": "side profile view",
    "corpo inteiro": "full body wide shot",
    "meio corpo": "medium shot waist up",
    "detalhe": "macro close-up shot",
    "zoom": "close-up shot",
    
    # Styling extras
    "sem sapato": "barefoot",
    "descalço": "barefoot",
    "descalca": "barefoot",
    "salto alto": "wearing high heels",
    "tenis": "wearing clean sneakers",
    "tênis": "wearing clean sneakers",
    "bolsa": "carrying a minimalist handbag",
    "oculos": "wearing elegant sunglasses",
    "óculos": "wearing elegant sunglasses",
    
    # Modelo
    "modelo": "natural adult woman model",
    "mulher": "natural adult woman",
    "loira": "blonde hair",
    "morena": "brunette hair",
    "ruiva": "red hair",
    "pele negra": "dark skin tone",
    "pele clara": "fair skin tone",
}

def normalize_user_intent(raw_text: str, max_len: int = 220) -> dict:
    """
    Traduz texto casual do usuário pt-BR para inglês técnico de moda (para prompts).
    Operação puramente baseada em regras (Rule-based, O(1)).
    """
    if not raw_text or not str(raw_text).strip():
        return {
            "raw": "",
            "normalized": "",
            "intent_tags": [],
            "normalizer_source": "rule_based_v1"
        }
    
    text = str(raw_text).strip().lower()
    
    # Detecção se já está primariamente em inglês e técnico o suficiente
    # Heurística simples: se as palavras-chave principais do dict em inglês existem
    # Pode ser expandida no futuro
    
    # 1. Pipeline de "Tradução/Substituição" Simples
    # Itera pelas chaves mais longas primeiro para evitar substituições parciais
    normalized_words = []
    
    # Substituição exata de substring (simples, não lida com plurais complexos mas atende MVP)
    translated_text = text
    found_tags = []
    
    # Ordenar por tamanho da chave (maiores primeiro) para evitar que "vestido" substitua dentro de "vestido longo"
    sorted_keys = sorted(_PT_EN_DICT.keys(), key=len, reverse=True)
    
    for pt_key in sorted_keys:
        if pt_key in translated_text:
            en_val = _PT_EN_DICT[pt_key]
            # Replace case-insensitive regex boundary
            pattern = re.compile(r'\b' + re.escape(pt_key) + r'\b', re.IGNORECASE)
            
            # Conta se aplicou (para tags)
            if pattern.search(translated_text):
                translated_text = pattern.sub(en_val, translated_text)
                found_tags.append(pt_key)

    # Limpeza básica (remover acentos residuais ou pontuações estranhas se precisasse, mas o Nano tolera bem)
    translated_text = translated_text.strip()
    
    # Se bater max_len, trunca na última palavra inteira
    if len(translated_text) > max_len:
        translated_text = translated_text[:max_len].rsplit(' ', 1)[0]
        
    return {
        "raw": raw_text[:250],
        "normalized": translated_text,
        "intent_tags": list(set(found_tags)),
        "normalizer_source": "rule_based_v1"
    }

