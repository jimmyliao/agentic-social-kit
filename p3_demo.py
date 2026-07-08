"""P3 — real-LLM persona engine + "The Mixer" turn-log exporter.

Runs the multi-agent mixer with a pluggable engine and writes a self-contained
``turn-log JSON`` that the static ``mixer.html`` view replays. The LLM engine is
a one-line swap for the rule engine and is governed by the *same* Declarative
Safety Gate; with no ``GOOGLE_API_KEY`` it falls back to rules so anyone can run
this offline.

  uv run --with google-antigravity --with google-genai \
      python p3_demo.py --engine llm --turns 4 --reset

  # offline / no key — still works (auto-fallback to rules):
  uv run --with google-antigravity python p3_demo.py --engine rule --turns 4 --reset

Output: docs/turn-log.json  (open docs/mixer.html to replay it).
"""

from __future__ import annotations

import argparse
import json
import os

from llm_social_engine import LLMSocialEngine
from memory_store import MemoryStore
from orchestrator import SocialSimulation, World, default_cast
from social_engine import RuleBasedSocialEngine, Safety

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "leapie_memory.sqlite3")
LOG_PATH = os.path.join(HERE, "docs", "turn-log.json")


def _badge(decision: str) -> str:
    if decision.startswith("APPROVE"):
        return "APPROVE"
    if "DOWNGRAD" in decision:
        return "DOWNGRADED"
    if "ASK_USER" in decision:
        return "ASK_USER"
    return "DENY"


def build_turn_log(decisions, cast, world, engine_label, source_label) -> dict:
    agents = [
        {
            "id": p.id,
            "name": p.name,
            "traits": p.personality.traits,
            "energy": p.personality.energy,
            "mood": p.personality.mood,
        }
        for p in cast
    ]
    turns: dict[int, list] = {}
    for d in decisions:
        turns.setdefault(d.turn, []).append(
            {
                "actor": d.actor,
                "target": d.target,
                "type": d.event.type,
                "intensity": d.event.intensity,
                "suggestedAction": d.event.suggestedAction,
                "rationale": d.event.rationale,
                "decision": d.decision,
                "badge": _badge(d.decision),
                "gateMessage": d.event.decisionMessage,
                "relationshipBefore": d.relationship_before,
                "relationshipAfter": d.relationship_after,
            }
        )
    return {
        "scenario": "The Mixer",
        "engine": engine_label,
        "source": source_label,  # what actually produced events: "llm" or "rule"
        "world": {
            "place": world.place,
            "timeOfDay": world.timeOfDay,
            "maxIntensity": world.safety.maxIntensity,
            "requireConsent": world.safety.requireConsent,
        },
        "agents": agents,
        "turns": [{"turn": t, "events": turns[t]} for t in sorted(turns)],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="P3 LLM persona mixer + turn-log export")
    ap.add_argument("--engine", choices=["llm", "rule"], default="llm")
    ap.add_argument("--turns", type=int, default=4)
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--max-intensity", type=int, default=6)
    ap.add_argument("--require-consent", action="store_true")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    if args.reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    store = MemoryStore(DB_PATH)
    world = World(
        place="lounge",
        timeOfDay="evening",
        safety=Safety(maxIntensity=args.max_intensity, requireConsent=args.require_consent),
    )
    cast = default_cast()

    if args.engine == "llm":
        engine = LLMSocialEngine()
        if engine.llm_available:
            engine_label, source_label = "LLMSocialEngine (Gemini)", "llm"
        else:
            engine_label = "LLMSocialEngine (no key -> rule fallback)"
            source_label = "rule"
            print(f"[note] LLM unavailable ({engine.last_error}); using rule fallback.")
    else:
        engine = RuleBasedSocialEngine()
        engine_label, source_label = "RuleBasedSocialEngine", "rule"

    print("=== P3: The Mixer — LLM persona engine behind the Declarative Safety Gate ===")
    print(f"engine={engine_label}  world={world.place}/{world.timeOfDay} "
          f"maxIntensity={world.safety.maxIntensity} requireConsent={world.safety.requireConsent}")

    sim = SocialSimulation(agents=cast, world=world, store=store, engine=engine, seed=args.seed)
    decisions = sim.run(turns=args.turns)

    # If the LLM engine fell back mid-run for any reason, reflect its final source.
    if isinstance(engine, LLMSocialEngine):
        source_label = engine.last_source

    for d in decisions:
        print(f"  [{d.decision:<24}] {d.actor} -> {d.target}: {d.event.type} "
              f"(intensity {d.event.intensity})")
        print(f"      rationale: {d.event.rationale}")

    log = build_turn_log(decisions, cast, world, engine_label, source_label)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "w") as fh:
        json.dump(log, fh, indent=2)

    print(f"\nP3 OK: {len(decisions)} gated interactions; source={source_label}.")
    print(f"turn-log written to {LOG_PATH}")
    print("Open docs/mixer.html to replay 'The Mixer'.")
    store.close()


if __name__ == "__main__":
    main()
