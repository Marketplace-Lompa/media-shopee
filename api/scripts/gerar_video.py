#!/usr/bin/env python3
"""
Geração de vídeo com Veo 3.1 via API Gemini.

Uso:
    python scripts/gerar_video.py --prompt "texto" --duracao 6 --proporcao 9:16
    python scripts/gerar_video.py --prompt "texto" --frame input/foto.jpg
    python scripts/gerar_video.py --prompt "texto" --inicio input/f1.jpg --fim input/f2.jpg

Modelos disponíveis:
    veo3.1      : veo-3.1-generate-preview        (HD + áudio nativo, $0.75/s)
    veo3.1-fast : veo-3.1-fast-generate-preview   (mais rápido/barato)
    veo2        : veo-2.0-generate-001             (sem áudio, $0.35/s)
"""

import os
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ─── Configuração ───────────────────────────────────────────────────
load_dotenv()

MODELOS = {
    "veo3.1":      "veo-3.1-generate-preview",
    "veo3.1-fast": "veo-3.1-fast-generate-preview",
    "veo2":        "veo-2.0-generate-001",
}

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

POLL_INTERVAL = 10  # segundos entre verificações


# ─── Funções ────────────────────────────────────────────────────────

def gerar_nome_arquivo(modelo: str, proporcao: str, duracao: int) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prop = proporcao.replace(":", "x")
    return f"{OUTPUT_DIR}/video_{modelo}_{prop}_{duracao}s_{timestamp}.mp4"


def carregar_imagem(caminho: str) -> types.Image:
    """Carrega imagem do disco para uso como frame."""
    ext = Path(caminho).suffix.lower()
    mime_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime = mime_types.get(ext, "image/jpeg")
    with open(caminho, "rb") as f:
        return types.Image(image_bytes=f.read(), mime_type=mime)


def aguardar_video(client, operation, modelo_id: str) -> str | None:
    """Polling até o vídeo ficar pronto."""
    print(f"\n⏳ Aguardando geração do vídeo (pode levar 2–5 minutos)...")
    tentativas = 0
    max_tentativas = 60  # 10 min máximo

    while not operation.done and tentativas < max_tentativas:
        tentativas += 1
        print(f"   [{tentativas:02d}] Processando... aguardando {POLL_INTERVAL}s")
        time.sleep(POLL_INTERVAL)
        operation = client.operations.get(operation)

    if not operation.done:
        print("❌ Timeout — operação não concluída em tempo hábil.")
        return None

    return operation


# ─── CLI ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Gerador de vídeo via Veo (Google AI API)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--prompt", "-p", required=True, help="Descrição do vídeo")
    parser.add_argument("--modelo", "-m", default="veo3.1", choices=MODELOS.keys())
    parser.add_argument("--proporcao", "-r", default="9:16", choices=["16:9", "9:16"])
    parser.add_argument("--duracao", "-d", type=int, default=6, choices=[4, 5, 6, 8],
                        help="Duração em segundos")
    parser.add_argument("--resolucao", default="1080p", choices=["720p", "1080p", "4k"])
    parser.add_argument("--frame", help="Caminho da imagem para usar como primeiro frame")
    parser.add_argument("--inicio", help="Primeiro frame (para interpolação)")
    parser.add_argument("--fim", help="Último frame (para interpolação)")
    parser.add_argument("--negativo", help="Prompt negativo — o que evitar")

    args = parser.parse_args()

    # Verificar API Key
    api_key = os.getenv("GOOGLE_AI_API_KEY")
    if not api_key:
        print("❌ GOOGLE_AI_API_KEY não encontrada no .env")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    modelo_id = MODELOS[args.modelo]

    print(f"\n{'='*55}")
    print(f"🎬 GERADOR DE VÍDEO — Veo via Gemini API")
    print(f"{'='*55}")
    print(f"Modelo:    {modelo_id}")
    print(f"Prompt:    {args.prompt[:80]}...")
    print(f"Proporção: {args.proporcao} | Duração: {args.duracao}s | Res: {args.resolucao}")

    # Montar config
    config = {
        "aspectRatio": args.proporcao,
        "durationSeconds": str(args.duracao),
        "resolution": args.resolucao,
        "personGeneration": "allow_adult",
    }

    if args.negativo:
        config["negativePrompt"] = args.negativo

    # Montar kwargs
    kwargs = {"model": modelo_id, "prompt": args.prompt, "config": config}

    # Frame inicial (image-to-video)
    if args.frame:
        print(f"Frame inicial: {args.frame}")
        kwargs["image"] = carregar_imagem(args.frame)

    # Interpolação primeiro + último frame
    if args.inicio and args.fim:
        print(f"Interpolação: {args.inicio} → {args.fim}")
        kwargs["image"] = carregar_imagem(args.inicio)
        config["lastFrame"] = carregar_imagem(args.fim)

    # Iniciar geração (assíncrona)
    print("\n🚀 Enviando para Veo API...")
    operation = client.models.generate_videos(**kwargs)

    # Aguardar conclusão
    operation = aguardar_video(client, operation, modelo_id)
    if not operation:
        sys.exit(1)

    # Baixar e salvar
    video = operation.response.generated_videos[0]
    client.files.download(file=video.video)
    caminho = gerar_nome_arquivo(args.modelo, args.proporcao, args.duracao)
    video.video.save(caminho)

    print(f"\n{'='*55}")
    print(f"✅ Vídeo gerado com sucesso!")
    print(f"   → {caminho}")
    custo = args.duracao * (0.75 if "veo3" in args.modelo else 0.35)
    print(f"   💰 Custo estimado: ~${custo:.2f}")


if __name__ == "__main__":
    main()
