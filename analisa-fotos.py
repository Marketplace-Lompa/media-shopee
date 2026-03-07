#!/usr/bin/env python3
"""
analisa-fotos.py — Analisa imagens, renomeia por cor (HSV) e deixa tudo em diretório único.

Comportamento:
  1. Varre a pasta (incluindo subpastas) e coleta TODAS as imagens
  2. Detecta cor dominante usando HSV (matiz), muito mais preciso que RGB
  3. Renomeia no padrão: {prefixo}-{cor}{N:02d}.ext
  4. Move renomeado para a RAIZ da pasta
  5. Remove subpastas de cor criadas anteriormente

Uso:
    python3 analisa-fotos.py <PASTA> [--prefixo NOME]

Opções:
    --prefixo   Prefixo manual (ex: vovo). Se omitido, deriva do nome da pasta.
"""

import os
import re
import sys
import json
import shutil
import argparse
import colorsys
import unicodedata
from pathlib import Path

try:
    import numpy as np
    from PIL import Image
    from sklearn.cluster import KMeans
except ImportError:
    print("❌ Dependências faltando. Instale com:")
    print("   pip3 install Pillow scikit-learn numpy")
    sys.exit(1)


EXTENSOES_VALIDAS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".heic"}

# Subpastas criadas pelo script que devem ser removidas/consolidadas
SUBPASTAS_COR = {
    "branco", "bege", "cinza", "preto", "vermelho", "rosa", "pink", "roxo",
    "azul", "verde", "amarelo", "laranja", "marrom", "caramelo", "nude",
    "estampado", "creme", "azul-escuro", "verde-militar",
}

# Forma feminina das cores para nomes de arquivo
# (blusa vermelha, calça preta, camiseta branca…)
CORES_FEMININAS = {
    "vermelho":  "vermelha",
    "preto":     "preta",
    "branco":    "branca",
    "roxo":      "roxa",
    "amarelo":   "amarela",
    "estampado": "estampada",
    # Invariáveis: marrom, bege, cinza, azul, verde, rosa, laranja
}

PALAVRAS_CATEGORIA = {
    "casaco", "camiseta", "blusa", "vestido", "vestidos", "calca", "calcas",
    "saia", "saias", "conjunto", "conjuntos", "camisa", "camisas", "regata",
    "regatas", "top", "cropped", "moletom", "jaqueta", "jaquetas", "sobretudo",
    "plus", "size", "feminino", "feminina", "masculino", "masculina",
    "infantil", "kids", "adulto", "adulta", "novo", "nova", "ml", "shopee",
    "ecommerce", "produto",
}


# ─────────────────────────────────────────────────────────────────────────────
# CLASSIFICAÇÃO DE COR — baseada em HSV (matiz/saturação/brilho)
# ─────────────────────────────────────────────────────────────────────────────

def hsv_para_nome(H: float, S: float, V: float) -> str:
    """
    Classifica uma cor HSV em nome de categoria.
    H: 0-360 graus | S: 0-1 | V: 0-1

    Regras chave:
    - Preto: V muito baixo E sem saturacao (nao descarta azul marinho)
    - Cores escuras MAS saturadas (azul marinho, bordo) -> classificadas pelo matiz
    - Neutros (branco/cinza): saturacao baixa
    """
    # Preto absoluto: muito escuro E dessaturado
    if V < 0.08:
        return "preto"
    if V < 0.30 and S < 0.50:
        return "preto"

    # Acromáticos: saturação baixa
    if S < 0.12:
        if V > 0.82:
            return "branco"
        elif V > 0.40:
            return "cinza"
        else:
            return "preto"

    # Tons terrosos de baixa saturação
    if S < 0.40 and 18 <= H <= 52:
        if V > 0.72:
            return "bege"
        else:
            return "marrom"

    # Coloridos por matiz (cores escuras saturadas como azul marinho chegam aqui)
    if H < 15 or H >= 340:
        return "vermelho"           # inclui marsala, bordo, vinho

    elif 15 <= H < 38:
        # Laranja vivo apenas se brilhante e vibrante
        # Caramelo (V~0.59) e marrom quente ficam em marrom
        if V < 0.70 or S < 0.65:
            return "marrom"
        return "laranja"

    elif 38 <= H < 66:
        if S < 0.40:
            return "bege"
        return "amarelo"

    elif 66 <= H < 155:
        return "verde"

    elif 155 <= H < 200:
        return "azul"               # ciano / turquesa

    elif 200 <= H < 262:
        return "azul"               # azul / azul marinho / navy

    elif 262 <= H < 295:
        return "roxo"

    elif 295 <= H < 340:
        if V < 0.55:
            return "roxo"
        return "rosa"

    return "estampado"



def analisar_cor(caminho: str) -> tuple:
    """
    Retorna (nome_cor, (R, G, B)) detectando cor dominante via HSV.

    Estratégia:
    1. Recortar região central da imagem (torso do modelo) — ignora cabeça e pés
    2. Filtrar pixels de background branco
    3. Se pixels coloridos com matizes genuinamente díspares → estampado
    4. Classificar pelo cluster HSV dominante
    """
    img = Image.open(caminho).convert("RGB")
    img.thumbnail((250, 250))

    # ── Crop central: foca no torso (exclui cabeça e pés/calças) ─────────────
    w, h = img.size
    top    = int(h * 0.12)   # ignora 12% do topo (cabeça)
    bottom = int(h * 0.88)   # ignora 12% do rodapé (calças/pés)
    left   = int(w * 0.05)
    right  = int(w * 0.95)
    img = img.crop((left, top, right, bottom))

    pixels = np.array(img).reshape(-1, 3).astype(np.float32)

    # Converter cada pixel para HSV usando vectorizado numpy
    r_n = pixels[:, 0] / 255.0
    g_n = pixels[:, 1] / 255.0
    b_n = pixels[:, 2] / 255.0

    V = np.max(pixels / 255.0, axis=1)
    mn = np.min(pixels / 255.0, axis=1)
    diff = V - mn

    # Saturação
    S = np.where(V > 0, diff / V, 0.0)

    # Matiz (H em graus)
    H = np.zeros(len(pixels))
    mask_r = (V == r_n) & (diff > 0)
    mask_g = (V == g_n) & (diff > 0)
    mask_b = (V == b_n) & (diff > 0)
    H[mask_r] = (60 * ((g_n[mask_r] - b_n[mask_r]) / diff[mask_r])) % 360
    H[mask_g] = 60 * ((b_n[mask_g] - r_n[mask_g]) / diff[mask_g]) + 120
    H[mask_b] = 60 * ((r_n[mask_b] - g_n[mask_b]) / diff[mask_b]) + 240

    # ── Filtrar background branco puro ──────────────────────────────────────
    # Background = S baixo + V muito alto (paredes brancas, fundo de estúdio)
    bg_mask = (S < 0.12) & (V > 0.88)
    fg_mask = ~bg_mask

    # Se mais de 90% é fundo branco, usar tudo
    if fg_mask.sum() < max(30, len(pixels) * 0.10):
        fg_mask = np.ones(len(pixels), dtype=bool)

    H_fg = H[fg_mask]
    S_fg = S[fg_mask]
    V_fg = V[fg_mask]
    px_fg = pixels[fg_mask]

    # ── Separar pixels coloridos vs acromáticos ──────────────────────────────
    colorido_mask = S_fg > 0.18
    acromatico_mask = ~colorido_mask

    n_colorido = colorido_mask.sum()
    n_total_fg = len(H_fg)

    # ── Detectar estampado por dispersão de matizes coloridos ────────────────
    # Threshold alto (40%+) e consistência muito baixa (<0.25) para evitar
    # falso positivo de cabelo/pele da modelo que aparecem no quadro.
    if n_colorido > 0.40 * n_total_fg:
        H_coloridos = H_fg[colorido_mask]
        H_rad = np.deg2rad(H_coloridos)
        mean_cos = np.mean(np.cos(H_rad))
        mean_sin = np.mean(np.sin(H_rad))
        consistencia = np.sqrt(mean_cos**2 + mean_sin**2)
        if consistencia < 0.25:
            # Matizes genuinamente espalhados = estampado
            r, g, b = px_fg.mean(axis=0)
            return "estampado", (int(r), int(g), int(b))

    # ── Encontrar cluster de cor dominante via KMeans ─────────────────────────
    n_clusters = min(6, max(2, n_total_fg // 30))
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=5)
    km.fit(px_fg)
    counts = np.bincount(km.labels_)

    # Pontuar clusters: tamanho × saturação da cor do cluster
    scores = np.zeros(n_clusters)
    for i, center in enumerate(km.cluster_centers_):
        # Calcular saturação deste cluster
        cr, cg, cb = center / 255.0
        mx = max(cr, cg, cb)
        diff_c = mx - min(cr, cg, cb)
        sat = diff_c / mx if mx > 0 else 0
        val = mx
        # Penalizar clusters de fundo (alta luminosidade + baixa sat)
        if sat < 0.12 and val > 0.88:
            score = counts[i] * 0.1       # cluster de fundo → peso mínimo
        elif sat < 0.15:
            score = counts[i] * 0.5       # neutro
        else:
            score = counts[i] * (1 + sat * 2)  # colorido → boost
        scores[i] = score

    melhor = int(np.argmax(scores))
    r, g, b = km.cluster_centers_[melhor]
    R, G, B = int(r), int(g), int(b)

    # Converter cluster dominante para HSV
    r_n2, g_n2, b_n2 = R / 255.0, G / 255.0, B / 255.0
    Vf = max(r_n2, g_n2, b_n2)
    mnf = min(r_n2, g_n2, b_n2)
    df = Vf - mnf
    Sf = df / Vf if Vf > 0 else 0
    if df == 0:
        Hf = 0.0
    elif Vf == r_n2:
        Hf = (60 * ((g_n2 - b_n2) / df)) % 360
    elif Vf == g_n2:
        Hf = 60 * ((b_n2 - r_n2) / df) + 120
    else:
        Hf = 60 * ((r_n2 - g_n2) / df) + 240

    nome = hsv_para_nome(Hf, Sf, Vf)
    return nome, (R, G, B)


# ─────────────────────────────────────────────────────────────────────────────
# PREFIXO
# ─────────────────────────────────────────────────────────────────────────────

def derivar_prefixo(nome_pasta: str) -> str:
    nome = unicodedata.normalize("NFKD", nome_pasta)
    nome = "".join(c for c in nome if not unicodedata.combining(c)).lower()
    partes = re.split(r"[-_\s]+", nome)
    filtradas = [p for p in partes if p and p not in PALAVRAS_CATEGORIA]
    if not filtradas:
        return nome[:10].rstrip("-_")
    return "-".join(filtradas)[:20].rstrip("-")


# ─────────────────────────────────────────────────────────────────────────────
# FLUXO PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def coletar_imagens(pasta: Path) -> list:
    return sorted([
        f for f in pasta.rglob("*")
        if f.is_file() and f.suffix.lower() in EXTENSOES_VALIDAS
    ])


def organizar_flat(pasta_entrada: str, prefixo_manual=None):
    pasta = Path(pasta_entrada).resolve()
    if not pasta.is_dir():
        print(f"❌ Pasta não encontrada: {pasta}")
        sys.exit(1)

    prefixo = prefixo_manual if prefixo_manual else derivar_prefixo(pasta.name)
    todas = coletar_imagens(pasta)

    if not todas:
        print(f"⚠️  Nenhuma imagem encontrada em: {pasta}")
        sys.exit(0)

    print(f"\n📁 Pasta   : {pasta}")
    print(f"🏷️  Prefixo : {prefixo}")
    print(f"📸 Total   : {len(todas)} imagem(ns) encontrada(s)")
    print("─" * 65)

    contador_cor = {}
    relatorio = {}
    detalhes = []
    arquivos_temp = []

    # ── FASE 1: analisar e copiar para nomes temporários na raiz ─────────────
    for i, caminho in enumerate(todas, 1):
        rel = caminho.relative_to(pasta)
        print(f"[{i:02d}/{len(todas)}] {rel} ...", end=" ", flush=True)

        try:
            cor, rgb = analisar_cor(str(caminho))
            ext = caminho.suffix.lower()
            contador_cor[cor] = contador_cor.get(cor, 0) + 1
            n = contador_cor[cor]
            cor_nome = CORES_FEMININAS.get(cor, cor)
            nome_final = f"{prefixo}-{cor_nome}{n:02d}{ext}"
            nome_temp = f"__tmp_{i:04d}__{nome_final}"
            destino_temp = pasta / nome_temp

            shutil.copy2(str(caminho), str(destino_temp))
            arquivos_temp.append((caminho, destino_temp, nome_final, cor, rgb))

            print(f"→  {nome_final}  (HSV RGB:{rgb[0]},{rgb[1]},{rgb[2]})")
            relatorio.setdefault(cor_nome, []).append(nome_final)
            detalhes.append({
                "arquivo_original": str(rel),
                "arquivo_final": nome_final,
                "cor": cor,
                "rgb": list(rgb),
            })

        except Exception as e:
            print(f"❌ Erro: {e}")

    # ── FASE 2: remover originais e renomear temporários ─────────────────────
    print("\n🔄 Finalizando renomeação...")
    for caminho, destino_temp, nome_final, cor, rgb in arquivos_temp:
        try:
            if caminho.exists() and caminho != destino_temp:
                caminho.unlink()
        except Exception:
            pass

    for caminho, destino_temp, nome_final, cor, rgb in arquivos_temp:
        destino_final = pasta / nome_final
        try:
            destino_temp.rename(destino_final)
        except Exception as e:
            print(f"  ⚠️  {destino_temp.name}: {e}")

    # ── FASE 3: remover subpastas de cor ─────────────────────────────────────
    print("🗑️  Removendo subpastas...")
    removidas = 0
    for item in sorted(pasta.iterdir()):
        if item.is_dir() and item.name in SUBPASTAS_COR:
            try:
                shutil.rmtree(str(item))
                print(f"   ✅ Removida: {item.name}/")
                removidas += 1
            except Exception as e:
                print(f"   ⚠️  {item.name}/: {e}")

    # ── Relatório JSON — salvo FORA da pasta de imagens ────────────────────
    # Armazenado em MEDIA-SHOPEE/relatorios/{nome_pasta}_relatorio.json
    dir_relatorios = Path(__file__).parent / "relatorios"
    dir_relatorios.mkdir(exist_ok=True)
    relatorio_path = dir_relatorios / f"{pasta.name}_relatorio.json"
    with open(relatorio_path, "w", encoding="utf-8") as f:
        json.dump({
            "pasta": str(pasta),
            "prefixo": prefixo,
            "total_imagens": len(detalhes),
            "cores_encontradas": sorted(relatorio.keys()),
            "por_cor": {c: sorted(v) for c, v in sorted(relatorio.items())},
            "detalhes": detalhes,
        }, f, ensure_ascii=False, indent=2)

    # ── Resumo ────────────────────────────────────────────────────────────────
    print("\n" + "─" * 65)
    print("📊 RESUMO POR COR:")
    for cor, arqs in sorted(relatorio.items()):
        print(f"   🎨 {cor:<16} {len(arqs):>2} foto(s)  "
              f"→ {prefixo}-{cor}01 … {prefixo}-{cor}{len(arqs):02d}")
    print(f"\n✅ {len(detalhes)} imagens renomeadas com prefixo '{prefixo}'")
    print(f"✅ {removidas} subpasta(s) removida(s)")
    print(f"📄 Relatório: {relatorio_path}")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Renomeia imagens de roupas por cor (HSV) em diretório único."
    )
    parser.add_argument("pasta", help="Pasta com as fotos")
    parser.add_argument(
        "--prefixo", default=None,
        help="Prefixo manual (ex: vovo). Se omitido, derivado do nome da pasta."
    )
    args = parser.parse_args()
    organizar_flat(args.pasta, prefixo_manual=args.prefixo)
