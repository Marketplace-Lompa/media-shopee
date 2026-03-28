"""
Módulo Alma da Pose — pose_soul.py

Responsável por entregar a diretiva criativa universal de linguagem corporal.
O agente recebe instruções de COMO PENSAR o corpo da modelo em relação
à peça e ao mode, não um cardápio de poses prontas.
"""
from __future__ import annotations

from typing import Optional


def get_pose_soul(*, mode_id: Optional[str], has_images: bool) -> str:
    normalized = str(mode_id or "").strip().lower()

    reference_guard = ""
    if has_images:
        reference_guard = (
            "\n"
            "REFERENCE POSE GUARD:\n"
            "  If the reference image contains a visible body pose, use it only as contrast.\n"
            "  Do NOT copy the original stance, arm placement, torso angle, or gesture rhythm.\n"
            "  Invent a new body direction that serves the garment and the active mode better.\n"
        )

    mode_overlay = ""
    if normalized == "catalog_clean":
        mode_overlay = (
            "\n"
            "MODE-SPECIFIC BODY LOGIC:\n"
            "  Keep movement low, garment readability high, and body direction commercially calm.\n"
            "  The pose must feel human and premium, never mannequin-rigid, but also never theatrical.\n"
            "  GAZE MANDATE: the model MUST look directly at the camera with a warm, approachable expression.\n"
            "  She is connecting with the shopper — open smile, confident but friendly.\n"
            "  Looking away, down, or to the side is a contract violation for catalog_clean.\n"
        )
    elif normalized == "natural":
        mode_overlay = (
            "\n"
            "MODE-SPECIFIC BODY LOGIC:\n"
            "  Let the body feel relaxed, unperformed, and lived-in.\n"
            "  The gesture should feel like a real person inhabiting the garment naturally.\n"
            "  Avoid display logic, competence-signaling polish, or neatly arranged presentation that makes the body feel professionally directed.\n"
            "  Prefer interrupted everyday body logic over settled posing: the body can be mid-pause, mid-adjustment, lightly occupied, or naturally asymmetrical.\n"
            "  Avoid one-hip beauty stances, symmetric standing presentation, leaning arrangements that look chosen for aesthetics, or hands placed only to look elegant.\n"
            "  The body should suggest that life is continuing around her, not that she stopped to be photographed.\n"
            "  Favor micro-actions, small task logic, or transitional body behavior over quiet posing.\n"
            "  Direct eye contact is usually the wrong signal here; let gaze and head attention belong to her own world unless the brief explicitly needs camera acknowledgment.\n"
            "  Avoid seated or resting setups when they turn the frame into a composed portrait rather than an ongoing everyday moment.\n"
        )
    elif normalized == "lifestyle":
        mode_overlay = (
            "\n"
            "MODE-SPECIFIC BODY LOGIC:\n"
            "  The model must be mid-activity — her body language originates from something she is doing,\n"
            "  not from standing still or being positioned. A static, idle pose breaks the lifestyle contract.\n"
            "  Unlike 'natural', she may show brief camera-awareness — a passing glance or half-smile —\n"
            "  but her body remains shaped by her activity, not by the camera.\n"
            "  Unlike 'editorial', the pose originates from action, not from visual composition.\n"
            "  YOU choose the specific activity and gesture.\n"
        )
    elif normalized == "editorial_commercial":
        mode_overlay = (
            "\n"
            "MODE-SPECIFIC BODY LOGIC:\n"
            "  Let the body claim space with deliberate intent.\n"
            "  The pose should feel authored, fashion-aware, and visually directional without becoming random choreography.\n"
        )

    return (
        "POSE SOUL (universal body-direction directive — you MUST follow this to create the pose):\n"
        "You are inventing how the body expresses the garment in this image, not selecting a stock pose from memory.\n"
        "Follow the active MODE_IDENTITY to decide how quiet, candid, assertive, or directed the body language should be.\n"
        "\n"
        "POSE INVENTION METHOD:\n"
        "  1. Start from the garment's structure, weight, stiffness, drape, and what parts need to remain legible.\n"
        "  2. Let the active mode decide the emotional register of the body: restrained, lived-in, dynamic, or authored.\n"
        "  3. Invent the pose through visible body logic: stance, weight distribution, arm behavior, torso angle, head direction,\n"
        "     and how the body creates space around the garment.\n"
        "  4. Use gesture to SELL the garment, not to compete with it.\n"
        "  5. Avoid generic wording like composed pose, stable stance, or natural posture without concrete body direction.\n"
        "\n"
        "MANDATORY POSE DETAIL:\n"
        "  Your final prompt must make the body's expression legible through visible evidence.\n"
        "  Include ALL of these in fluent prose:\n"
        "  1. stance or movement logic\n"
        "  2. weight or balance logic\n"
        "  3. arm or hand behavior\n"
        "  4. torso, head, or gaze direction when relevant to the mode\n"
        "  If these are missing, the pose is under-described.\n"
        f"{mode_overlay}"
        "\n"
        "VARIATION RULE:\n"
        "  Each generation must invent a new body solution from scratch.\n"
        "  Do not recycle the same safe standing pose.\n"
        "  Let variation emerge from the garment, the mode, and the scene.\n"
        f"{reference_guard}"
        "CRITICAL RULES:\n"
        "  - The pose must feel physically plausible and commercially useful.\n"
        "  - The body must create readability for the garment, not block it.\n"
        "  - COMPLETENESS CHECK: before finalizing, verify that the prompt surface contains stance + balance + limb behavior.\n"
        "  - Do NOT echo these directives in the output — INVENT the body language.\n"
    )
