"""
compress_shopee.py
==================
Comprime todas as imagens da pasta INPUT para no máximo 2MB.
Salva os resultados na pasta OUTPUT e remove os originais do INPUT após sucesso.
Proporção e dimensões da imagem são sempre preservadas.

USO:
    python compress_shopee.py

Coloque as imagens na pasta: input/
Os arquivos comprimidos ficam em:  output/
"""

from PIL import Image
import os
import sys

# ─── CONFIGURAÇÕES ─────────────────────────────────────────────
INPUT_DIR   = "input"        # Pasta com as imagens originais
OUTPUT_DIR  = "output"       # Pasta onde os resultados são salvos
MAX_SIZE_MB = 2.0            # Limite em MB
MAX_BYTES   = int(MAX_SIZE_MB * 1024 * 1024)
MIN_QUALITY = 30             # Qualidade mínima permitida (0-100)
START_QUAL  = 92             # Qualidade inicial de tentativa
# ───────────────────────────────────────────────────────────────

SUPPORTED = (".jpg", ".jpeg", ".png", ".webp")


def compress_image(input_path: str, output_path: str) -> dict:
    """Comprime uma imagem até ficar abaixo de MAX_BYTES."""
    img = Image.open(input_path).convert("RGB")
    ext = os.path.splitext(output_path)[1].lower()

    # PNG → salvar como JPEG para compressão mais eficiente
    if ext == ".png":
        output_path = output_path.replace(".png", ".jpg")

    quality = START_QUAL
    import io

    while quality >= MIN_QUALITY:
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        size = buffer.tell()

        if size <= MAX_BYTES:
            with open(output_path, "wb") as f:
                f.write(buffer.getvalue())
            return {
                "status": "ok",
                "output": output_path,
                "size_kb": round(size / 1024, 1),
                "quality": quality,
            }

        quality -= 5

    # Qualidade mínima atingida e ainda acima de 2MB — não redimensiona
    return {"status": "error", "msg": f"Não foi possível atingir {MAX_SIZE_MB}MB só com compressão. Imagem não alterada."}


def main():
    # Garantir que as pastas existem
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(SUPPORTED)]

    if not files:
        print(f"\n⚠️  Nenhuma imagem encontrada em '{INPUT_DIR}/'")
        print(f"   Coloque seus arquivos (.jpg/.jpeg/.png/.webp) na pasta '{INPUT_DIR}/' e rode novamente.\n")
        sys.exit(0)

    print(f"\n🗜️  Shopee Image Compressor  |  Limite: {MAX_SIZE_MB} MB")
    print(f"   {len(files)} imagem(ns) encontrada(s) em '{INPUT_DIR}/'\n")
    print(f"{'Arquivo':<35} {'Original':>10} {'Comprimido':>12} {'Qualidade':>10}  Status")
    print("─" * 80)

    for filename in sorted(files):
        input_path  = os.path.join(INPUT_DIR, filename)
        output_path = os.path.join(OUTPUT_DIR, filename)

        original_kb = round(os.path.getsize(input_path) / 1024, 1)
        result = compress_image(input_path, output_path)

        if result["status"] == "ok":
            qual = result.get("quality", MIN_QUALITY)
            # Remove original do input após salvar com sucesso
            os.remove(input_path)
            print(
                f"{filename:<35} {original_kb:>8} KB  {result['size_kb']:>9} KB"
                f"  {qual:>6}%   ✅  🗑️ original removido"
            )
        else:
            print(f"{filename:<35} {original_kb:>8} KB  {'—':>9}      {'—':>6}   ❌ {result['msg']}")

    print("─" * 80)
    print(f"\n✅ Concluído! Imagens salvas em '{OUTPUT_DIR}/'\n")


if __name__ == "__main__":
    main()
