"""P4 — the self-correcting (Reflexion-style) loop.

Run (offline, deterministic — no API key):
    uv run --with google-antigravity python p4_demo.py --reset

P0–P3 ran a *single-pass* turn loop (engine proposes -> safety gate decides ->
memory updates). P4 closes the feedback loop. Per step we add an **independent
verifier sub-agent** (maker != grader) that critiques the *gated* action; the
critique is **written back** to the persistent memory and **injected** into the
SAME actor's next turn, so behaviour **self-corrects**. The loop runs until a
**goal** condition is met OR a **budget** cap is hit, then prints WHY it stopped
plus **responsible-loop metrics**.

The Declarative Safety Gate (from the Google Antigravity SDK) still governs
EVERY step — the verifier is *additional* governance, not a replacement:

    engine proposes -> GATE decides (APPROVE/DENY/DOWNGRADE/ASK_USER)
        -> VERIFIER critiques -> critique to memory -> next turn injects it.

  * SDK provides : the per-action policy decision (the safety gate).
  * WE provide   : the turn loop, the persistent memory, the independent
                   verifier, the critique writeback/injection, and the
                   goal/budget termination + metrics.
"""

from __future__ import annotations

import argparse
import os

from memory_store import MemoryStore
from orchestrator import SelfCorrectingSimulation, World, default_cast
from social_engine import RuleBasedSocialEngine, Safety
from verifier import RuleBasedVerifier

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "leapie_memory.sqlite3")


def _badge(decision: str) -> str:
    if decision.startswith("APPROVE"):
        return "APPROVE"
    if "DOWNGRAD" in decision:
        return "DOWNGRADED"
    if "ASK_USER" in decision:
        return "ASK_USER"
    return "DENY"


def _print_step(step) -> None:
    c = step.critique
    print(f"  [{_badge(step.decision):<10}] {step.actor} -> {step.target}: "
          f"{step.event.type} (intensity {step.event.intensity})")
    if step.injected_note:
        # This is the self-correction: last turn's critique shaped THIS proposal.
        print(f"      <- injected critique : {step.injected_note}")
    print(f"      proposal rationale  : {step.event.rationale}")
    if step.event.decisionMessage:
        print(f"      gate                : {step.event.decisionMessage}")
    print(f"      verifier (grader)   : score={c.score:.2f} advance={c.advance} "
          f"appropriate={c.appropriate} | {c.reason}")
    print(f"      relationship        : {step.relationship_before} -> {step.relationship_after}")


def main() -> None:
    ap = argparse.ArgumentParser(description="P4 self-correcting loop")
    ap.add_argument("--reset", action="store_true", help="wipe persisted memory before running")
    ap.add_argument("--max-intensity", type=int, default=4,
                    help="world safety cap (low cap makes bold actors over-reach -> critique steers them)")
    ap.add_argument("--goal-stage", default="walk_buddy", help="stop once any pair reaches this stage")
    ap.add_argument("--max-turns", type=int, default=12, help="budget cap: max turns")
    ap.add_argument("--max-engine-calls", type=int, default=60, help="budget cap: max engine calls")
    ap.add_argument("--stall-patience", type=int, default=4, help="stop after N turns with no approved progress")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    if args.reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    store = MemoryStore(DB_PATH)
    world = World(
        place="park",
        timeOfDay="afternoon",
        safety=Safety(maxIntensity=args.max_intensity, requireConsent=False),
    )

    # Maker = the engine (proposes). Grader = a SEPARATE verifier (reviews).
    engine = RuleBasedSocialEngine()
    verifier = RuleBasedVerifier()

    sim = SelfCorrectingSimulation(
        agents=default_cast(),
        world=world,
        store=store,
        engine=engine,
        verifier=verifier,
        seed=args.seed,
        goal_stage=args.goal_stage,
        max_turns=args.max_turns,
        max_engine_calls=args.max_engine_calls,
        stall_patience=args.stall_patience,
    )

    print("=== P4: the self-correcting (Reflexion-style) loop ===")
    print(f"maker={type(engine).__name__}  grader={type(verifier).__name__}  (maker != grader)")
    print(f"world={world.place}/{world.timeOfDay} maxIntensity={world.safety.maxIntensity}  "
          f"goal_stage='{args.goal_stage}' max_turns={args.max_turns} "
          f"max_engine_calls={args.max_engine_calls} stall_patience={args.stall_patience}")
    print("step order: engine proposes -> SAFETY GATE decides -> independent VERIFIER "
          "critiques -> writeback -> next turn injects it.\n")

    stop = sim.run_until_goal_or_budget()

    # Print the loop turn-by-turn so the self-correction is visible.
    by_turn: dict[int, list] = {}
    for s in sim.steps:
        by_turn.setdefault(s.turn, []).append(s)
    for turn in sorted(by_turn):
        print(f"--- Turn {turn} ---")
        for s in by_turn[turn]:
            _print_step(s)
        print()

    # Relationship state (durable memory).
    print("=== Relationship state (persisted memory) ===")
    rels = store.all_relationships()
    if not rels:
        print("  (none yet)")
    for r in rels:
        print(f"  {r.person_a} <-> {r.person_b}: {r.stage:<12} bond={r.bond:<3} interactions={r.interactions}")

    # Termination reason + responsible-loop metrics.
    print(f"\nSTOP: {stop.kind} — {stop.detail}")
    print(sim.metrics.line())
    print(f"persisted: events={store.event_count()} critiques={store.critique_count()} "
          f"across {store.last_turn()} turns.")
    print("\nP4 OK: every step was gate-governed AND independently verified; "
          "critiques are durable and self-correct the next turn.")
    store.close()


if __name__ == "__main__":
    main()
