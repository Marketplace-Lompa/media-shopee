"""
Módulo Alma da Captura — capture_soul.py

Responsável por entregar a diretiva criativa universal de câmera/captura.
O agente recebe instruções de COMO PENSAR a relação entre câmera, sujeito,
peça e espaço, não um cardápio de lentes ou presets de shot.
"""
from __future__ import annotations

from typing import Optional


def get_capture_soul(*, mode_id: Optional[str], has_images: bool) -> str:
    normalized = str(mode_id or "").strip().lower()

    reference_guard = ""
    if has_images:
        reference_guard = (
            "\n"
            "REFERENCE CAPTURE GUARD:\n"
            "  If the reference image contains a strong crop, angle, or camera signature, use it only as contrast.\n"
            "  Do NOT copy the original framing, camera height, angle, lens compression feel, or spatial composition.\n"
            "  Invent a new camera relationship that serves the garment and the active mode better.\n"
        )

    mode_overlay = ""
    if normalized == "catalog_clean":
        mode_overlay = (
            "\n"
            "MODE-SPECIFIC CAMERA LOGIC:\n"
            "  Keep the camera commercially clean, calm, and product-first.\n"
            "  The camera should disappear behind garment readability rather than draw attention to itself.\n"
        )
    elif normalized == "natural":
        mode_overlay = (
            "\n"
            "MODE-SPECIFIC CAMERA LOGIC:\n"
            "  Let the camera feel observational, contemporary, and human-scaled.\n"
            "  The viewing relation should feel believable for a real person in a real place, never over-directed.\n"
            "  Avoid prestige framing, showroom polish, or composed image-authority that makes the frame feel editorially arranged.\n"
            "  Avoid portrait-first crops that isolate face and torso too cleanly unless garment readability truly demands it.\n"
            "  Prefer enough body and environmental context to make the moment feel encountered rather than composed for a portrait.\n"
            "  Avoid clean medium portrait distance as a default. Let the frame catch more of her body, action, or surrounding routine than a polished portrait naturally would.\n"
            "  When uncertain, bias away from hip-up beauty portrait crops and toward an observed medium-wide or wider relation that keeps body and place alive together.\n"
            "  Avoid letting the face become the sole anchor of the composition; the body and everyday world should share the frame's meaning.\n"
            "  The frame can sit slightly off-center or feel casually found, but should never look sloppy or accidental.\n"
        )
    elif normalized == "lifestyle":
        mode_overlay = (
            "\n"
            "MODE-SPECIFIC CAMERA LOGIC:\n"
            "  The camera accompanies the action — it moves with the model's activity, not around her as a subject.\n"
            "  The framing should feel like a visual account from someone present in the moment,\n"
            "  not passive observation (natural) and not authored spatial composition (editorial).\n"
            "  Social proximity matters: the viewer should feel close enough to be part of the scene.\n"
            "  The camera can acknowledge the model's awareness without becoming a portrait setup.\n"
            "  YOU choose the specific distance and angle — the soul only requires the camera to feel participatory.\n"
        )
    elif normalized == "editorial_commercial":
        mode_overlay = (
            "\n"
            "MODE-SPECIFIC CAMERA LOGIC:\n"
            "  Let the camera feel authored, fashion-aware, and compositionally intentional.\n"
            "  Use angle, height, and spatial control to create authority, but never at the expense of garment legibility.\n"
        )

    return (
        "CAPTURE SOUL (universal camera-direction directive — you MUST follow this to create the camera language):\n"
        "You are inventing how the camera sees the garment, the model, and the setting in this image, not selecting a stock shot formula.\n"
        "Follow the active MODE_IDENTITY to decide whether the camera should feel quiet, observational, socially alive, or art-directed.\n"
        "\n"
        "CAPTURE INVENTION METHOD:\n"
        "  1. Start from what the garment needs to stay readable: silhouette, length, neckline, texture, movement, and proportion.\n"
        "  2. Decide the camera through separate visible axes: distance, camera height, view relation, and how much environment enters the frame.\n"
        "  3. Let the mode decide whether the camera should observe, accompany, energize, or author the scene.\n"
        "  4. Use capture to connect body, garment, and setting into one image direction rather than three disconnected descriptions.\n"
        "  5. Avoid generic wording like cinematic shot, fashion angle, premium framing, or realistic photo without concrete camera behavior.\n"
        "\n"
        "MANDATORY CAPTURE DETAIL:\n"
        "  Your final prompt must make the camera's behavior legible through visible evidence.\n"
        "  Include ALL of these in fluent prose:\n"
        "  1. framing or distance relation\n"
        "  2. angle or camera-height relation\n"
        "  3. how the subject sits against the background or space\n"
        "  If these are missing, the capture is under-described.\n"
        f"{mode_overlay}"
        "\n"
        "VARIATION RULE:\n"
        "  Each generation must invent a fresh camera relationship from scratch.\n"
        "  Do not recycle the same safe full-body, eye-level, centered commercial view unless the mode truly demands it.\n"
        f"{reference_guard}"
        "CRITICAL RULES:\n"
        "  - The camera must serve the garment first, even when it becomes expressive.\n"
        "  - Never expose preset labels, shot recipes, or metatextual camera jargon in the final prompt.\n"
        "  - COMPLETENESS CHECK: before finalizing, verify that the prompt surface contains distance/framing + angle/height + subject-space relation.\n"
        "  - Do NOT echo these directives in the output — INVENT the camera behavior.\n"
    )
