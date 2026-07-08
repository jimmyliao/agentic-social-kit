"""Generic personality -> SocialEvent engine, gated by the Safety Gate.

Framework-agnostic data model + a pluggable ``SocialEngine`` interface, plus a
reference ``RuleBasedSocialEngine`` that proposes social events from two
personalities and submits each to a declarative :class:`SafetyGate` (built on
the Google Antigravity SDK). The gate can APPROVE, DENY, downgrade (when a
high-intensity event is denied, the engine retries a low-pressure variant), or
require human consent (ASK_USER) — all visibly.

No domain-specific content: subjects are generic people with generic traits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol

from safety_gate import GateResult, Outcome, SafetyGate


# --- generic data model -------------------------------------------------


@dataclass
class Personality:
    traits: list[str] = field(default_factory=list)
    energy: int = 5  # 0..10
    mood: Optional[str] = None


@dataclass
class Person:
    id: str
    name: str
    personality: Personality


@dataclass
class Safety:
    maxIntensity: int = 6
    requireConsent: bool = False
    blockedIds: list[str] = field(default_factory=list)


@dataclass
class Context:
    place: str = "cafe"
    timeOfDay: str = "afternoon"
    safety: Safety = field(default_factory=Safety)


@dataclass
class EngineInput:
    subject: Person
    candidates: list[Person]
    context: Context
    # P4 (self-correcting loop): the latest verifier critique steer injected
    # from the SAME actor's previous turn. When ``advise_lighter`` is set, an
    # engine SHOULD keep its next proposal low-pressure. ``critiqueNote`` is a
    # human-readable one-liner (also useful as an LLM prompt hint). Optional and
    # backward-compatible — engines that ignore it still work as before.
    adviseLighter: bool = False
    critiqueNote: str = ""


@dataclass
class SocialEvent:
    type: str
    participants: list[str]
    rationale: str
    intensity: int
    suggestedAction: str
    compatibilityScore: float
    decision: Optional[str] = None  # filled in after the gate runs
    decisionMessage: str = ""


class SocialEngine(Protocol):
    def proposeEvents(self, input: EngineInput) -> list[SocialEvent]:
        ...


# --- reference engine ---------------------------------------------------

_TIMID = {"shy", "timid", "reserved", "cautious", "introvert"}


def _compatibility(a: Personality, b: Personality) -> float:
    shared = len(set(a.traits) & set(b.traits))
    union = len(set(a.traits) | set(b.traits)) or 1
    jaccard = shared / union
    energy_fit = 1.0 - abs(a.energy - b.energy) / 10.0
    return round(0.5 * jaccard + 0.5 * energy_fit, 2)


def _is_timid(p: Personality) -> bool:
    return bool(set(t.lower() for t in p.traits) & _TIMID) or p.energy <= 3


class RuleBasedSocialEngine:
    """Proposes one gated SocialEvent for the best candidate.

    The declarative gate is built once per proposal from the context's safety
    block, so the same engine code produces APPROVE / DENY / downgrade /
    ASK_USER outcomes purely from data.
    """

    def _build_gate(self, safety: Safety) -> SafetyGate:
        gate = SafetyGate("social_action").set_consent_default(False)
        # Specific DENY rules (highest priority in the SDK bucket model):
        gate.deny_when(
            lambda a: a.get("intensity", 0) > a.get("maxIntensity", 10),
            name="cap_intensity",
        )
        gate.deny_when(
            lambda a: bool(set(a.get("participants", [])) & set(a.get("blockedIds", []))),
            name="blocked_ids",
        )
        # ASK_USER when consent is required for a non-trivial interaction:
        gate.ask_user_when(
            lambda a: bool(a.get("requireConsent")) and a.get("intensity", 0) >= 3,
            name="require_consent",
        )
        gate.allow_rest()
        return gate

    def _gate_args(self, event: SocialEvent, safety: Safety) -> dict:
        return {
            "intensity": event.intensity,
            "maxIntensity": safety.maxIntensity,
            "requireConsent": safety.requireConsent,
            "participants": event.participants,
            "blockedIds": safety.blockedIds,
        }

    def _propose_one(
        self, subject: Person, other: Person, ctx: Context, advise_lighter: bool = False
    ) -> SocialEvent:
        score = _compatibility(subject.personality, other.personality)
        # P4: if the verifier's last critique steered us gentler, treat the pair
        # as timid this turn so the proposal self-corrects to a low-pressure move.
        timid = advise_lighter or _is_timid(subject.personality) or _is_timid(other.personality)
        if timid:
            why = (
                "prior critique advised a gentler move"
                if advise_lighter and not (_is_timid(subject.personality) or _is_timid(other.personality))
                else f"{subject.name} or {other.name} reads as low-energy/reserved"
            )
            return SocialEvent(
                type="gentle_intro",
                participants=[subject.id, other.id],
                rationale=f"{why}; start light at the {ctx.place}.",
                intensity=3,
                suggestedAction=f"Wave hello at the {ctx.place}",
                compatibilityScore=score,
            )
        return SocialEvent(
            type="visit",
            participants=[subject.id, other.id],
            rationale=(
                f"{subject.name} and {other.name} share energy/traits; propose an "
                f"active meetup at the {ctx.place}."
            ),
            intensity=8,
            suggestedAction=f"Set up a {ctx.place} hangout this {ctx.timeOfDay}",
            compatibilityScore=score,
        )

    def _downgrade(self, event: SocialEvent, ctx: Context) -> SocialEvent:
        return SocialEvent(
            type="leave_a_note",
            participants=event.participants,
            rationale=event.rationale + " | downgraded: high-intensity action was denied.",
            intensity=2,
            suggestedAction=f"Leave a friendly note at the {ctx.place}",
            compatibilityScore=event.compatibilityScore,
        )

    def proposeEvents(self, input: EngineInput) -> list[SocialEvent]:
        ctx = input.context
        safety = ctx.safety
        # Pick the most compatible, non-blocked candidate.
        ranked = sorted(
            (c for c in input.candidates if c.id not in safety.blockedIds),
            key=lambda c: _compatibility(input.subject.personality, c.personality),
            reverse=True,
        )
        if not ranked:
            return []
        best = ranked[0]
        gate = self._build_gate(safety)

        event = self._propose_one(input.subject, best, ctx, advise_lighter=input.adviseLighter)
        result: GateResult = gate.evaluate(self._gate_args(event, safety))

        if result.outcome == Outcome.DENY and event.intensity > safety.maxIntensity:
            # Try a low-pressure downgrade instead of dropping the interaction.
            downgraded = self._downgrade(event, ctx)
            dresult = gate.evaluate(self._gate_args(downgraded, safety))
            downgraded.decision = f"DOWNGRADED (orig DENY) -> {dresult.outcome.value}"
            downgraded.decisionMessage = (
                f"original '{event.type}' (intensity {event.intensity}) "
                f"denied: {result.message}; downgraded to '{downgraded.type}'."
            )
            return [downgraded]

        event.decision = result.outcome.value
        event.decisionMessage = result.message
        return [event]
