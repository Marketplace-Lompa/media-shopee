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
            "  TENSION: human warmth held inside commercial discipline.\n"
            "  The pose presents, it does not narrate — no activity, no editorial drama.\n"
            "  Weight: choose a deliberate asymmetry (cross-step, offset stance, subtle hip shift) to keep the body from reading as mannequin.\n"
            "  Arms: one specific solution per garment. Avoid both stiff parallel hang and the recycled waist-touch.\n"
            "  Gaze: direct, shopper-facing — warm, calm, or composed, never the same open-smile default.\n"
            "  The body must keep silhouette, length, and key construction details fully readable.\n"
            "  Anti-repeat: do not return to the same safe standing center-weight catalog pose.\n"
        )
    elif normalized == "natural":
        mode_overlay = (
            "\n"
            "MODE-SPECIFIC BODY LOGIC:\n"
            "  TENSION: a real person caught mid-moment, not a model caught mid-pose.\n"
            "  The body originates from daily life logic: mid-pause, mid-adjustment, transitional asymmetry.\n"
            "  Avoid display logic, symmetric beauty stances, hands placed only to look elegant.\n"
            "  Favor micro-actions or small task logic over quiet presentational posing.\n"
            "  Gaze: usually belongs to her own world. Camera acknowledgment breaks the mode contract unless explicitly needed.\n"
            "  Do not use seated or resting setups that turn the frame into a composed portrait.\n"
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
            "  Let the body claim space with deliberate intent — she is a compositional element in the frame,\n"
            "  not a person caught in a moment. Every angle of her body is a CHOICE, not an accident.\n"
            "  The pose should feel authored, fashion-aware, and visually directional without becoming random choreography.\n"
            "  Unlike natural (body at rest in life) and lifestyle (body shaped by activity),\n"
            "  editorial body language is STAGED — she is placed, she is directed, she is aware.\n"
            "  Weight distribution can be asymmetrical and dramatic — one hip dropped, shoulders angled,\n"
            "  chin elevated, arms creating geometric negative space against architecture.\n"
            "  Hands should feel positioned with intention — pressed against a wall, resting on a ledge,\n"
            "  holding the garment's hem — never hanging idle at the sides.\n"
            "  GAZE: she looks at the camera with INTENTION and COMMAND. Not warm (catalog), not averted (natural),\n"
            "  not passing (lifestyle) — she HOLDS the viewer. Think editorial cover energy.\n"
            "  Avoid poses that feel randomly choreographic or contemporary-dance-inspired.\n"
            "  The body must look POWERFUL and DELIBERATE, not artistic for art's sake.\n"
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
        "  1. action logic appropriate to the mode: only lifestyle requires a visible ongoing action; natural and catalog_clean may use stable inhabited stance logic when it feels more human and believable\n"
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
