"""P2 — multi-agent social simulation + self-built memory layer.

Run (fresh):     uv run --with google-antigravity python p2_demo.py --reset --turns 3
Run (continue):  uv run --with google-antigravity python p2_demo.py --turns 2

Shows N autonomous agents acting over several turns on a shared world. Each
turn, every agent proposes a social event (via the reusable SocialEngine);
**every event is decided by the Google Antigravity SDK's Declarative Safety
Gate** (APPROVE / DENY / DOWNGRADE / ASK_USER). Approved interactions feed a
**persistent memory layer** (SQLite) so relationships evolve and re-runs
continue where the last run stopped.

  * SDK provides : the per-event policy decision (the safety gate).
  * WE provide    : the multi-agent turn loop, shared world, perception, and the
                    memory / relationship persistence layer.
"""

from __future__ import annotations

import argparse
import os

from memory_store import MemoryStore
from orchestrator import SocialSimulation, World, default_cast
from social_engine import Safety

DB_PATH = "leapie_memory.sqlite3"


def _print_turn(decisions) -> None:
    by_turn: dict[int, list] = {}
    for d in decisions:
        by_turn.setdefault(d.turn, []).append(d)
    for turn in sorted(by_turn):
        print(f"\n--- Turn {turn} ---")
        for d in by_turn[turn]:
            print(f"  [{d.decision:<22}] {d.actor} -> {d.target}: "
                  f"{d.event.type} (intensity {d.event.intensity})")
            print(f"      relationship: {d.relationship_before} -> {d.relationship_after}")
            if d.event.decisionMessage:
                print(f"      gate: {d.event.decisionMessage}")


def _print_relationships(store: MemoryStore) -> None:
    print("\n=== Relationship state (persisted memory) ===")
    rels = store.all_relationships()
    if not rels:
        print("  (none yet)")
    for r in rels:
        print(f"  {r.person_a} <-> {r.person_b}: {r.stage:<12} bond={r.bond:<3} interactions={r.interactions}")


def main() -> None:
    parser = argparse.ArgumentParser(description="P2 multi-agent social sim")
    parser.add_argument("--turns", type=int, default=3, help="how many turns to run this invocation")
    parser.add_argument("--reset", action="store_true", help="wipe persisted memory before running")
    parser.add_argument("--max-intensity", type=int, default=6, help="world safety cap")
    parser.add_argument("--require-consent", action="store_true", help="require human consent for non-trivial events")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    if args.reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    store = MemoryStore(DB_PATH)
    prior_turns = store.last_turn()
    prior_events = store.event_count()

    print("=== P2: multi-agent social simulation + self-built memory layer ===")
    print(f"SDK governs each event (Declarative Safety Gate); the loop + memory are ours.")
    print(f"persisted state on entry: last_turn={prior_turns}, events={prior_events} "
          f"({'continuing' if prior_turns else 'fresh start'})")

    world = World(
        place="park",
        timeOfDay="afternoon",
        safety=Safety(maxIntensity=args.max_intensity, requireConsent=args.require_consent),
    )
    sim = SocialSimulation(agents=default_cast(), world=world, store=store, seed=args.seed)

    decisions = sim.run(turns=args.turns)
    _print_turn(decisions)
    _print_relationships(store)

    print(f"\nP2 OK: {len(decisions)} gated interactions this run; "
          f"total events persisted = {store.event_count()} across {store.last_turn()} turns.")
    print("Re-run without --reset to see relationships keep evolving (durable memory).")
    store.close()


if __name__ == "__main__":
    main()
