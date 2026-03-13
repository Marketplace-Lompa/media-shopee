"""
image_utils.py — Utilitários compartilhados de imagem.

Centraliza helpers que são usados por múltiplos módulos (generator, edit_agent)
para evitar duplicação e garantir comportamento consistente.
"""


def detect_image_mime(image_bytes: bytes) -> str:
    """Detecta o MIME type real de uma imagem a partir de seus bytes iniciais (magic bytes)."""
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"
