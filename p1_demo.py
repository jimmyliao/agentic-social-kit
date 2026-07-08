"""P1 — two personalities -> one safety-gated SocialEvent.

Run:  uv run --with google-antigravity python p1_demo.py

Runs three generic scenarios through the RuleBasedSocialEngine. Each proposed
SocialEvent passes through the declarative SafetyGate, and the gate's decision
(APPROVE / DENY / DOWNGRADED / ASK_USER) is printed alongside the event.
"""

from __future__ import annotations

from social_engine import (
    Context,
    EngineInput,
    Person,
    Personality,
    RuleBasedSocialEngine,
    Safety,
)


def _print_event(scenario: str, inp: EngineInput, events) -> None:
    s = inp.subject
    print(f"\n### {scenario}")
    print(f"  subject:  {s.name} traits={s.personality.traits} energy={s.personality.energy}")
    for c in inp.candidates:
        print(f"  candidate:{c.name} traits={c.personality.traits} energy={c.personality.energy}")
    sf = inp.context.safety
    print(f"  safety:   maxIntensity={sf.maxIntensity} requireConsent={sf.requireConsent} blockedIds={sf.blockedIds}")
    if not events:
        print("  -> no eligible candidates (all blocked)")
        return
    for e in events:
        print(f"  EVENT:    type={e.type} intensity={e.intensity} score={e.compatibilityScore}")
        print(f"            action='{e.suggestedAction}'")
        print(f"            rationale={e.rationale}")
        print(f"  DECISION: {e.decision}  | {e.decisionMessage}")


def main() -> None:
    print("=== P1: personality -> SocialEvent, gated by a declarative safety gate ===")
    engine = RuleBasedSocialEngine()

    # Scenario A: two outgoing people, generous safety -> APPROVE high-intensity.
    a = EngineInput(
        subject=Person("p_jordan", "Jordan", Personality(["outgoing", "playful"], energy=8, mood="upbeat")),
        candidates=[Person("p_riley", "Riley", Personality(["outgoing", "curious"], energy=7))],
        context=Context(place="park", timeOfDay="afternoon", safety=Safety(maxIntensity=9, requireConsent=False)),
    )

    # Scenario B: same pair, but safety tightened (low maxIntensity) -> DENY then DOWNGRADE.
    b = EngineInput(
        subject=Person("p_jordan", "Jordan", Personality(["outgoing", "playful"], energy=8)),
        candidates=[Person("p_riley", "Riley", Personality(["outgoing", "curious"], energy=7))],
        context=Context(place="coworking", timeOfDay="morning", safety=Safety(maxIntensity=4, requireConsent=False)),
    )

    # Scenario C: a reserved/low-energy subject + requireConsent -> gentle event, ASK_USER.
    c = EngineInput(
        subject=Person("p_quinn", "Quinn", Personality(["shy", "reserved"], energy=2, mood="quiet")),
        candidates=[Person("p_sasha", "Sasha", Personality(["calm", "gentle"], energy=4))],
        context=Context(place="cafe", timeOfDay="evening", safety=Safety(maxIntensity=6, requireConsent=True)),
    )

    # Scenario D: only candidate is on the blocklist -> no event proposed.
    d = EngineInput(
        subject=Person("p_jordan", "Jordan", Personality(["outgoing"], energy=8)),
        candidates=[Person("p_riley", "Riley", Personality(["outgoing"], energy=7))],
        context=Context(place="park", safety=Safety(maxIntensity=9, blockedIds=["p_riley"])),
    )

    _print_event("Scenario A — outgoing pair, relaxed safety", a, engine.proposeEvents(a))
    _print_event("Scenario B — outgoing pair, tightened maxIntensity", b, engine.proposeEvents(b))
    _print_event("Scenario C — reserved subject, consent required", c, engine.proposeEvents(c))
    _print_event("Scenario D — only candidate is blocked", d, engine.proposeEvents(d))

    print("\nP1 OK: every event carries a visible, declaratively-derived gate decision.")


if __name__ == "__main__":
    main()
