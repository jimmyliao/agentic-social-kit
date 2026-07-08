"""P3 — real-LLM persona engine, plugged into the same ``SocialEngine`` seam.

``LLMSocialEngine`` implements the existing ``SocialEngine.proposeEvents`` so it
is a drop-in swap for ``RuleBasedSocialEngine``. It asks a real LLM to look at
two personalities + context and **invent a believable social event with a
personality-flavoured rationale**, then routes that event through the *same*
Declarative Safety Gate (APPROVE / DENY / downgrade / ASK_USER). Governance is
unchanged: the LLM only proposes; the gate decides.

Key + fallback:
  * The LLM uses ``GOOGLE_API_KEY`` from the environment (the variable name is
    read, never a hard-coded key). For local runs you can export the value from
    your own ``.env`` (e.g. ``GOOGLE_API_KEY=$GEMINI_API_KEY_...``).
  * With **no key (or no SDK, or any API error)** the engine *gracefully falls
    back* to the deterministic ``RuleBasedSocialEngine`` — so a public demo
    runs for anyone, offline, with zero setup.

The two engines are interchangeable in one line:

    engine = LLMSocialEngine() if use_llm else RuleBasedSocialEngine()
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from safety_gate import GateResult, Outcome, SafetyGate
from social_engine import (
    Context,
    EngineInput,
    Person,
    RuleBasedSocialEngine,
    Safety,
    SocialEvent,
)

DEFAULT_MODEL = "gemini-flash-latest"

# Generic action vocabulary the LLM picks from, with a nominal intensity so the
# safety gate stays meaningful regardless of phrasing.
_ACTION_INTENSITY = {
    "leave_a_note": 2,
    "gentle_intro": 3,
    "small_talk": 4,
    "share_a_drink": 5,
    "invite_to_group": 6,
    "visit": 8,
    "plan_outing": 9,
}

_SYSTEM = (
    "You orchestrate a social mixer of autonomous, generic personas. Given an "
    "actor and a target persona plus the venue context, propose ONE believable "
    "social move the actor makes toward the target. Reflect both personalities "
    "(an outgoing/bold actor pushes harder; a shy/reserved actor or target keeps "
    "it light). Keep it generic and friendly — no real people, no sensitive "
    "topics."
)


def _prompt(actor: Person, target: Person, ctx: Context) -> str:
    actions = ", ".join(f"{k} (intensity {v})" for k, v in _ACTION_INTENSITY.items())
    return (
        f"VENUE: {ctx.place}, {ctx.timeOfDay}.\n"
        f"ACTOR: {actor.name} — traits={actor.personality.traits}, "
        f"energy={actor.personality.energy}/10, mood={actor.personality.mood}.\n"
        f"TARGET: {target.name} — traits={target.personality.traits}, "
        f"energy={target.personality.energy}/10, mood={target.personality.mood}.\n\n"
        f"Choose exactly one action type from: {actions}.\n"
        "Pick an intensity that matches BOTH personalities (lower if either is shy/"
        "reserved/low-energy).\n"
        "Return STRICT JSON only, no markdown, with keys:\n"
        '  "type" (one of the action types above),\n'
        '  "intensity" (integer 1-10),\n'
        '  "suggestedAction" (one short imperative sentence),\n'
        '  "rationale" (one sentence, in-character, citing a trait of each persona).'
    )


class LLMSocialEngine:
    """LLM persona engine behind the same gate; falls back to rules if needed."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key_env: str = "GOOGLE_API_KEY",
        consent_default: bool = False,
    ) -> None:
        self.model = model
        self.api_key_env = api_key_env
        self.consent_default = consent_default
        self._fallback = RuleBasedSocialEngine()
        self.last_source = "rule"  # "llm" or "rule" — surfaced to the UI/log
        self.last_error: Optional[str] = None
        self._client = self._make_client()

    # -- LLM client (lazy, optional) -------------------------------------

    def _make_client(self):
        key = os.environ.get(self.api_key_env)
        if not key:
            self.last_error = f"no {self.api_key_env} in env"
            return None
        try:
            from google import genai  # type: ignore

            return genai.Client(api_key=key)
        except Exception as exc:  # SDK missing or init failure
            self.last_error = f"genai client init failed: {exc}"
            return None

    @property
    def llm_available(self) -> bool:
        return self._client is not None

    # -- gate (identical policy to the rule engine) ----------------------

    def _build_gate(self, safety: Safety) -> SafetyGate:
        gate = SafetyGate("social_action").set_consent_default(self.consent_default)
        gate.deny_when(
            lambda a: a.get("intensity", 0) > a.get("maxIntensity", 10),
            name="cap_intensity",
        )
        gate.deny_when(
            lambda a: bool(set(a.get("participants", [])) & set(a.get("blockedIds", []))),
            name="blocked_ids",
        )
        gate.ask_user_when(
            lambda a: bool(a.get("requireConsent")) and a.get("intensity", 0) >= 3,
            name="require_consent",
        )
        gate.allow_rest()
        return gate

    @staticmethod
    def _gate_args(event: SocialEvent, safety: Safety) -> dict[str, Any]:
        return {
            "intensity": event.intensity,
            "maxIntensity": safety.maxIntensity,
            "requireConsent": safety.requireConsent,
            "participants": event.participants,
            "blockedIds": safety.blockedIds,
        }

    # -- LLM call --------------------------------------------------------

    def _ask_llm(self, actor: Person, target: Person, ctx: Context) -> Optional[dict]:
        try:
            from google.genai import types as gtypes  # type: ignore

            resp = self._client.models.generate_content(
                model=self.model,
                contents=_prompt(actor, target, ctx),
                config=gtypes.GenerateContentConfig(
                    system_instruction=_SYSTEM,
                    temperature=0.9,
                    response_mime_type="application/json",
                ),
            )
            text = (resp.text or "").strip()
            if text.startswith("```"):  # strip stray fences defensively
                text = text.strip("`").lstrip("json").strip()
            return json.loads(text)
        except Exception as exc:
            self.last_error = f"llm call failed: {exc}"
            return None

    def _event_from_llm(self, data: dict, actor: Person, target: Person) -> SocialEvent:
        etype = str(data.get("type", "small_talk"))
        nominal = _ACTION_INTENSITY.get(etype, 4)
        # Clamp model-chosen intensity to a sane range, anchored by the action.
        intensity = int(data.get("intensity", nominal) or nominal)
        intensity = max(1, min(10, intensity))
        return SocialEvent(
            type=etype,
            participants=[actor.id, target.id],
            rationale=str(data.get("rationale", "")).strip()
            or f"{actor.name} approaches {target.name}.",
            intensity=intensity,
            suggestedAction=str(data.get("suggestedAction", "")).strip()
            or f"{actor.name}: {etype.replace('_', ' ')}",
            compatibilityScore=0.0,
        )

    def _downgrade(self, event: SocialEvent, ctx: Context) -> SocialEvent:
        return SocialEvent(
            type="leave_a_note",
            participants=event.participants,
            rationale=event.rationale + " | downgraded: high-intensity move was denied.",
            intensity=2,
            suggestedAction=f"Leave a friendly note at the {ctx.place}",
            compatibilityScore=event.compatibilityScore,
        )

    # -- SocialEngine interface ------------------------------------------

    def proposeEvents(self, input: EngineInput) -> list[SocialEvent]:
        ctx = input.context
        safety = ctx.safety
        ranked = [c for c in input.candidates if c.id not in safety.blockedIds]
        if not ranked:
            return []
        # Without scoring info from the LLM, just take the first eligible neighbour
        # (the orchestrator already shuffles candidates each turn for variety).
        best = ranked[0]

        # No LLM? hand the whole proposal to the deterministic rule engine.
        if not self.llm_available:
            self.last_source = "rule"
            return self._fallback.proposeEvents(input)

        data = self._ask_llm(input.subject, best, ctx)
        if data is None:  # transient API failure -> graceful fallback
            self.last_source = "rule"
            return self._fallback.proposeEvents(input)

        self.last_source = "llm"
        event = self._event_from_llm(data, input.subject, best)
        gate = self._build_gate(safety)
        result: GateResult = gate.evaluate(self._gate_args(event, safety))

        if result.outcome == Outcome.DENY and event.intensity > safety.maxIntensity:
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
