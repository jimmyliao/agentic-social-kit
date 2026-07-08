"""Verifier sub-agent (maker ≠ grader) — OUR OWN engineering.

This is the "Sub-agents / independent verification" component of **loop
engineering**: the engine that *proposes* a social action must NOT be the same
component that *grades* it (self-validation bias). So the verifier lives behind
its own pluggable :class:`Verifier` ``Protocol`` — mirroring the ``SocialEngine``
seam in :mod:`social_engine` — with a deterministic, offline rule-based default
(:class:`RuleBasedVerifier`), exactly like the engine's rule-based fallback.

What the verifier does (and does NOT do):

  * It reviews a *proposed-and-gated* action — i.e. it runs **after** the
    Declarative Safety Gate has already decided APPROVE / DENY / DOWNGRADE /
    ASK_USER. The gate is the hard safety boundary; the verifier is *additional*
    governance (quality / goal-fitness), never a replacement for the gate.
  * It returns a small :class:`Critique` — a short human-readable reason plus a
    score in ``[0.0, 1.0]`` — judging three generic things:
      1. **advances** the actor's goal (did this nudge the target bond up?),
      2. **appropriate** for the gate verdict (a DENY/ASK_USER should not be
         re-tried at the same pressure next turn),
      3. **quality** of the move (compatibility + a sensible intensity).

The critique is then persisted to memory and injected into the SAME actor's
next turn, so behaviour self-corrects across turns (Verify → Iterate). None of
this comes from the SDK — the SDK governs single tool calls; the maker≠grader
review loop is the engineering P4 contributes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

from social_engine import Person, SocialEvent


# --- the thing a verifier produces --------------------------------------


@dataclass
class Critique:
    """One verifier verdict over one proposed-and-gated action.

    ``score`` is in ``[0.0, 1.0]`` (higher = better). ``advise_lighter`` is the
    actionable signal injected into the next turn: when ``True`` the actor
    should keep the next proposal low-pressure (e.g. after a DENY/ASK_USER).
    """

    score: float
    reason: str
    advance: bool          # did this action advance the actor's goal?
    appropriate: bool      # was it appropriate given the gate verdict?
    advise_lighter: bool   # next-turn steer: keep it gentle?

    def as_context(self) -> str:
        """One-line summary the next turn injects into the engine input."""
        steer = "keep the next move gentle/low-pressure" if self.advise_lighter \
            else "a slightly bolder move is OK if compatible"
        return f"last critique (score={self.score:.2f}): {self.reason} -> {steer}"


# --- the pluggable seam (mirrors SocialEngine) --------------------------


class Verifier(Protocol):
    """Pluggable grader. Implementations MUST be independent of the engine."""

    def review(
        self,
        actor: Person,
        event: SocialEvent,
        decision: str,
        bond_before: int,
        bond_after: int,
    ) -> Critique:
        ...


# --- deterministic, offline default -------------------------------------


# Generic "appropriateness" intuition: a hard NO from the gate should not be
# followed by an equally pushy retry; an APPROVE that moved nothing is weak.
def _clamp(x: float) -> float:
    return max(0.0, min(1.0, round(x, 2)))


class RuleBasedVerifier:
    """A transparent, deterministic grader (the offline default).

    Maker≠grader is enforced structurally: this class shares no state with any
    ``SocialEngine`` and only sees the *outcome* of a proposal (the event, the
    gate's decision, and how the bond moved), never the engine's internals.
    """

    def __init__(self, *, weak_score: float = 0.45) -> None:
        # Below this, the next turn is steered to a gentler proposal.
        self._weak = weak_score

    def review(
        self,
        actor: Person,
        event: SocialEvent,
        decision: str,
        bond_before: int,
        bond_after: int,
    ) -> Critique:
        advanced = bond_after > bond_before
        approved = decision.startswith("APPROVE")
        downgraded = "DOWNGRAD" in decision
        hard_no = decision.startswith("DENY") or "ASK_USER" in decision

        # 1) advance: did the bond actually move?
        advance_score = 0.5 if advanced else 0.0

        # 2) appropriate: did the gate verdict match the pressure chosen?
        #    - a clean APPROVE on a sensible event is appropriate
        #    - a DENY/ASK_USER means the engine over-reached -> inappropriate
        #    - a DOWNGRADE is a *correct* recovery -> appropriate, mild credit
        if hard_no:
            appropriate = False
            appropriate_score = 0.0
        elif downgraded:
            appropriate = True
            appropriate_score = 0.25
        else:
            appropriate = True
            appropriate_score = 0.3

        # 3) quality: compatibility of the pair + a not-too-extreme intensity.
        comp = max(0.0, min(1.0, event.compatibilityScore))
        intensity_fit = 1.0 - abs(event.intensity - 4) / 6.0  # sweet spot ~4
        quality_score = 0.2 * comp + 0.0 * max(0.0, intensity_fit)
        # (quality contributes up to ~0.2; advance/appropriate dominate)

        score = _clamp(advance_score + appropriate_score + quality_score)

        # Build a short, honest reason + the next-turn steer.
        if hard_no:
            reason = (
                f"action '{event.type}' (intensity {event.intensity}) was {decision.split()[0]}"
                f"; over-reached for the current safety context"
            )
            advise_lighter = True
        elif downgraded:
            reason = (
                f"recovered via downgrade to '{event.type}'; bond "
                f"{'advanced' if advanced else 'held'} (+{bond_after - bond_before})"
            )
            advise_lighter = True  # we were just denied; stay gentle once more
        elif approved and advanced:
            reason = (
                f"approved '{event.type}' advanced the goal (bond "
                f"+{bond_after - bond_before}); good fit (compat {comp:.2f})"
            )
            # A LOW-intensity approve that advanced is a lesson worth keeping:
            # the gentle move is working in this (tight) context, so don't let
            # the actor regress to an over-reaching proposal next turn. A
            # genuinely bold approve (high intensity that still passed) means the
            # context has room, so we can relax the steer.
            advise_lighter = event.intensity <= 3 or score < self._weak
        else:  # approved but no movement, or unknown
            reason = (
                f"'{event.type}' was allowed but did not advance the bond"
            )
            advise_lighter = True

        return Critique(
            score=score,
            reason=reason,
            advance=advanced,
            appropriate=appropriate,
            advise_lighter=advise_lighter,
        )
