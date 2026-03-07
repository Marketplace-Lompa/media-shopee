#!/usr/bin/env python3
"""
Geração de imagens com Nano Banana (Gemini Image) via API.
Suporta proporção configurável — ideal para Shopee 9:16.

Uso:
    python scripts/gerar_imagem.py --prompt "sua descrição" --proporcao 9:16 --resolucao 2K
    python scripts/gerar_imagem.py --prompt "sua descrição" --modelo imagen4

Modelos disponíveis:
    nano2       : gemini-3.1-flash-image-preview  (padrão, rápido + qualidade)
    nano-pro    : gemini-3-pro-image-preview       (máxima qualidade, texto legível)
    nano        : gemini-2.5-flash-image           (produção, alto volume)
    imagen4-fast: imagen-4.0-fast-generate-001     (barato, rápido)
    imagen4     : imagen-4.0-generate-001          (qualidade/custo)
    imagen4-ultra: imagen-4.0-ultra-generate-001   (máximo fotorrealismo)
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ─── Configuração ───────────────────────────────────────────────────
load_dotenv()

MODELOS = {
    "nano2":         "gemini-3.1-flash-image-preview",
    "nano-pro":      "gemini-3-pro-image-preview",
    "nano":          "gemini-2.5-flash-image",
    "imagen4-fast":  "imagen-4.0-fast-generate-001",
    "imagen4":       "imagen-4.0-generate-001",
    "imagen4-ultra": "imagen-4.0-ultra-generate-001",
}

PROPORCOES_VALIDAS = [
    "1:1", "3:4", "4:3", "9:16", "16:9",
    "21:9", "3:2", "2:3", "5:4", "4:5",
    "4:1", "1:4", "8:1", "1:8"  # Somente Nano Banana 2
]

# Máxima permissividade — projeto de moda/lingerie, sem infração de TOS
# Elimina falsos positivos em biquíni, lingerie, decotes, costas expostas
SAFETY_CONFIG = [
    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT",         threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH",        threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT",  threshold="BLOCK_NONE"),
]

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


# ─── Funções ────────────────────────────────────────────────────────

def gerar_nome_arquivo(modelo: str, proporcao: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prop_sanitizada = proporcao.replace(":", "x")
    return f"{OUTPUT_DIR}/{modelo}_{prop_sanitizada}_{timestamp}.png"


def gerar_com_nano_banana(client, modelo_id: str, prompt: str,
                           proporcao: str, resolucao: str) -> list[str]:
    """Gera imagem usando família Nano Banana (Gemini Image)."""
    print(f"\n🍌 Gerando com {modelo_id}...")
    print(f"   Proporção: {proporcao} | Resolução: {resolucao}")

    config = types.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=types.ImageConfig(
            aspect_ratio=proporcao,
            image_size=resolucao if modelo_id != "gemini-2.5-flash-image" else None,
        ),
        safety_settings=SAFETY_CONFIG  # máxima permissividade para moda/lingerie
    )

    response = client.models.generate_content(
        model=modelo_id,
        contents=[prompt],
        config=config
    )

    arquivos_salvos = []
    for part in response.parts:
        if part.inline_data is not None:
            image = part.as_image()
            caminho = gerar_nome_arquivo(modelo_id.replace("/", "_"), proporcao)
            image.save(caminho)
            arquivos_salvos.append(caminho)
            print(f"   ✅ Salvo: {caminho} | Tamanho: {image.size}")

    return arquivos_salvos


def gerar_com_imagen4(client, modelo_id: str, prompt: str,
                      proporcao: str, quantidade: int = 1) -> list[str]:
    """Gera imagem usando família Imagen 4."""
    print(f"\n🖼️  Gerando com {modelo_id}...")
    print(f"   Proporção: {proporcao} | Quantidade: {quantidade}")

    proporcoes_imagen = ["1:1", "3:4", "4:3", "9:16", "16:9"]
    if proporcao not in proporcoes_imagen:
        print(f"   ⚠️  Imagen 4 não suporta {proporcao}. Usando 9:16.")
        proporcao = "9:16"

    response = client.models.generate_images(
        model=modelo_id,
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=quantidade,
            aspect_ratio=proporcao,
            person_generation="allow_adult",
        )
    )

    arquivos_salvos = []
    for i, img in enumerate(response.generated_images):
        caminho = gerar_nome_arquivo(f"{modelo_id}_{i}", proporcao)
        img.image.save(caminho)
        arquivos_salvos.append(caminho)
        print(f"   ✅ Salvo: {caminho}")

    return arquivos_salvos


# ─── CLI ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Gerador de imagens via Google AI API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--prompt", "-p", required=True, help="Descrição da imagem")
    parser.add_argument("--modelo", "-m", default="nano2", choices=MODELOS.keys(),
                        help="Modelo a usar (padrão: nano2)")
    parser.add_argument("--proporcao", "-r", default="9:16", choices=PROPORCOES_VALIDAS,
                        help="Proporção da imagem (padrão: 9:16)")
    parser.add_argument("--resolucao", default="1K", choices=["0.5K", "1K", "2K", "4K"],
                        help="Resolução (padrão: 1K)")
    parser.add_argument("--quantidade", "-q", type=int, default=1, choices=[1, 2, 3, 4],
                        help="Quantidade de imagens (1–4, padrão: 1)")

    args = parser.parse_args()

    # Verificar API Key
    api_key = os.getenv("GOOGLE_AI_API_KEY")
    if not api_key:
        print("❌ GOOGLE_AI_API_KEY não encontrada no .env")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    modelo_id = MODELOS[args.modelo]
    eh_imagen = "imagen" in args.modelo

    print(f"\n{'='*50}")
    print(f"🎨 GERADOR DE IMAGENS — Google AI API")
    print(f"{'='*50}")
    print(f"Prompt: {args.prompt[:80]}{'...' if len(args.prompt) > 80 else ''}")
    print(f"Modelo: {modelo_id}")

    if eh_imagen:
        arquivos = gerar_com_imagen4(client, modelo_id, args.prompt,
                                      args.proporcao, args.quantidade)
    else:
        arquivos = gerar_com_nano_banana(client, modelo_id, args.prompt,
                                          args.proporcao, args.resolucao)

    print(f"\n{'='*50}")
    print(f"✅ {len(arquivos)} imagem(ns) gerada(s) com sucesso!")
    for f in arquivos:
        print(f"   → {f}")


if __name__ == "__main__":
    main()
