from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Optional

from agent_runtime.preset_patch import PresetPatch, get_preset_patch


@dataclass(frozen=True)
class EngineWeights:
    casting: float
    scene: float
    capture: float
    styling: float
    pose: float


@dataclass(frozen=True)
class SurfaceBudget:
    subject: int
    scene: int
    capture: int
    styling: int
    pose: int


@dataclass(frozen=True)
class ModeProfile:
    mode_id: str
    label: str
    engine_weights: EngineWeights
    invention_budget: float
    surface_budget: SurfaceBudget
    guardrail_profile: str
    hard_rules: tuple[str, ...]


@dataclass(frozen=True)
class ResolvedOperationalProfile:
    mode_id: str
    label: str
    engine_weights: EngineWeights
    invention_budget: float
    surface_budget: SurfaceBudget
    guardrail_profile: str
    hard_rules: tuple[str, ...]
    applied_preset_id: Optional[str]
    preset_scope: Optional[str]
    exclusions: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


_MODE_PROFILE_REGISTRY: dict[str, ModeProfile] = {
    "catalog_clean": ModeProfile(
        mode_id="catalog_clean",
        label="Catálogo Clean",
        engine_weights=EngineWeights(
            casting=0.75,
            scene=0.35,
            capture=1.0,
            styling=0.50,
            pose=0.60,
        ),
        invention_budget=0.20,
        surface_budget=SurfaceBudget(
            subject=3,
            scene=1,
            capture=2,
            styling=1,
            pose=2,
        ),
        guardrail_profile="strict_catalog",
        hard_rules=(
            "garment primacy must stay high",
            "scene cannot compete with the garment",
            "styling must remain commercially complete and restrained",
        ),
    ),
    "natural": ModeProfile(
        mode_id="natural",
        label="Natural",
        engine_weights=EngineWeights(
            casting=0.90,
            scene=0.85,
            capture=0.75,
            styling=0.65,
            pose=0.80,
        ),
        invention_budget=0.40,
        surface_budget=SurfaceBudget(
            subject=4,
            scene=3,
            capture=2,
            styling=2,
            pose=3,
        ),
        guardrail_profile="natural_commercial",
        hard_rules=(
            "brazil anchor must stay believable and non-stereotyped",
            "pose should feel human and commercially plausible",
            "scene should feel specific but not overpower the garment",
        ),
    ),
    "lifestyle": ModeProfile(
        mode_id="lifestyle",
        label="Lifestyle",
        engine_weights=EngineWeights(
            casting=0.85,
            scene=1.0,
            capture=0.80,
            styling=0.75,
            pose=0.90,
        ),
        invention_budget=0.55,
        surface_budget=SurfaceBudget(
            subject=4,
            scene=4,
            capture=3,
            styling=2,
            pose=3,
        ),
        guardrail_profile="lifestyle_permissive",
        hard_rules=(
            "garment must remain readable even with stronger context",
            "lived-in context cannot collapse into generic travel editorial",
            "gesture can open up, but product clarity stays intact",
        ),
    ),
    "editorial_commercial": ModeProfile(
        mode_id="editorial_commercial",
        label="Editorial Comercial",
        engine_weights=EngineWeights(
            casting=0.90,
            scene=0.90,
            capture=0.95,
            styling=0.85,
            pose=0.95,
        ),
        invention_budget=0.65,
        surface_budget=SurfaceBudget(
            subject=4,
            scene=3,
            capture=4,
            styling=3,
            pose=4,
        ),
        guardrail_profile="editorial_controlled",
        hard_rules=(
            "fashion direction can rise without losing product legibility",
            "premium context should not turn theatrical or luxury-campaign generic",
            "pose and capture may become more expressive, but not chaotic",
        ),
    ),
}


def list_mode_profiles() -> list[ModeProfile]:
    return list(_MODE_PROFILE_REGISTRY.values())


def get_mode_profile(mode_id: Optional[str]) -> ModeProfile:
    normalized = str(mode_id or "natural").strip().lower()
    return _MODE_PROFILE_REGISTRY.get(normalized, _MODE_PROFILE_REGISTRY["natural"])


def resolve_operational_profile(
    *,
    mode_id: Optional[str],
    preset_patch: Optional[PresetPatch | str] = None,
) -> ResolvedOperationalProfile:
    base = get_mode_profile(mode_id)
    applied_patch = preset_patch
    if isinstance(preset_patch, str):
        applied_patch = get_preset_patch(preset_patch)

    if applied_patch is None:
        return ResolvedOperationalProfile(
            mode_id=base.mode_id,
            label=base.label,
            engine_weights=base.engine_weights,
            invention_budget=base.invention_budget,
            surface_budget=base.surface_budget,
            guardrail_profile=base.guardrail_profile,
            hard_rules=base.hard_rules,
            applied_preset_id=None,
            preset_scope=None,
            exclusions=(),
        )

    if base.mode_id not in applied_patch.allowed_modes:
        raise ValueError(
            f"Preset patch '{applied_patch.id}' is not allowed for mode '{base.mode_id}'."
        )

    weights = base.engine_weights
    patched_weights = replace(
        weights,
        casting=max(0.0, weights.casting + float(applied_patch.engine_deltas.get("casting", 0.0))),
        scene=max(0.0, weights.scene + float(applied_patch.engine_deltas.get("scene", 0.0))),
        capture=max(0.0, weights.capture + float(applied_patch.engine_deltas.get("capture", 0.0))),
        styling=max(0.0, weights.styling + float(applied_patch.engine_deltas.get("styling", 0.0))),
        pose=max(0.0, weights.pose + float(applied_patch.engine_deltas.get("pose", 0.0))),
    )

    return ResolvedOperationalProfile(
        mode_id=base.mode_id,
        label=base.label,
        engine_weights=patched_weights,
        invention_budget=base.invention_budget,
        surface_budget=base.surface_budget,
        guardrail_profile=base.guardrail_profile,
        hard_rules=base.hard_rules,
        applied_preset_id=applied_patch.id,
        preset_scope=applied_patch.scope,
        exclusions=applied_patch.exclusions,
    )
