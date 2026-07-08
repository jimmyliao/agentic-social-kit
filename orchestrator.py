"""Multi-agent social orchestrator — OUR OWN engineering.

The Google Antigravity SDK gives us *per-action governance* (the Declarative
Safety Gate: allow / deny / ask-user). It does **not** provide multi-agent
orchestration or any shared world. P2 builds that coordinator here:

  * N autonomous agents, each with a generic personality, live in a shared
    world (a place + a clock).
  * Each **turn**, the coordinator lets every agent perceive who is nearby and
    propose a social event toward its best-matched neighbour, using the
    reusable ``SocialEngine`` from the kit.
  * **Every** proposed event is submitted to the SDK's Declarative Safety Gate.
    The gate's decision (APPROVE / DENY / DOWNGRADE / ASK_USER) is what the
    coordinator acts on and prints.
  * Approved (or downgraded-then-approved) interactions feed the **persistent
    memory layer**, so relationships evolve across turns and across re-runs.

Personality + accumulated memory + the safety policy together make each turn's
behaviour different — that is the emergent social dynamics we want to show.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from memory_store import MemoryStore, Relationship
from social_engine import (
    Context,
    EngineInput,
    Person,
    RuleBasedSocialEngine,
    Safety,
    SocialEngine,
    SocialEvent,
)
from verifier import Critique, RuleBasedVerifier, Verifier


@dataclass
class World:
    """The shared environment the agents act in (self-built)."""

    place: str = "park"
    timeOfDay: str = "afternoon"
    safety: Safety = field(default_factory=Safety)


# Bond points awarded by gate outcome (drives relationship evolution).
def _bond_points(event: SocialEvent, decision: str) -> int:
    if decision.startswith("APPROVE"):
        return max(1, event.intensity // 2)
    if "DOWNGRAD" in decision:
        return 1  # a gentle approved fallback still nudges the bond
    return 0  # DENY / ASK_USER do not strengthen the relationship


@dataclass
class TurnDecision:
    """A visible record of one agent's action in one turn."""

    turn: int
    actor: str
    target: str
    event: SocialEvent
    decision: str
    relationship_before: str
    relationship_after: str


class SocialSimulation:
    """Self-built coordinator: runs N agents over T turns on a shared world.

    SDK boundary: the per-event decision comes from the SDK's policy gate
    (via ``RuleBasedSocialEngine``); everything else here — turn loop, shared
    world, perception, memory updates, emergence — is our own code.
    """

    def __init__(
        self,
        agents: list[Person],
        world: World,
        store: MemoryStore,
        engine: SocialEngine | None = None,
        seed: int = 7,
    ) -> None:
        self.agents = agents
        self.world = world
        self.store = store
        self.engine = engine or RuleBasedSocialEngine()
        self._rng = random.Random(seed)

    # -- perception: who is "nearby" this turn (self-built) ---------------

    def _neighbours(self, actor: Person) -> list[Person]:
        others = [a for a in self.agents if a.id != actor.id]
        # A little turn-to-turn variability in who is around.
        self._rng.shuffle(others)
        return others

    def _context(self) -> Context:
        return Context(place=self.world.place, timeOfDay=self.world.timeOfDay, safety=self.world.safety)

    # -- one turn: every agent proposes -> gate -> memory -----------------

    def run_turn(self, turn: int) -> list[TurnDecision]:
        decisions: list[TurnDecision] = []
        for actor in self.agents:
            neighbours = self._neighbours(actor)
            if not neighbours:
                continue
            inp = EngineInput(subject=actor, candidates=neighbours, context=self._context())
            # SDK-governed proposal: engine proposes + every event passes the gate.
            events = self.engine.proposeEvents(inp)
            if not events:
                continue
            event = events[0]
            target_id = next((p for p in event.participants if p != actor.id), event.participants[-1])
            decision = event.decision or "UNKNOWN"

            before = self.store.get_relationship(actor.id, target_id)
            after = before
            points = _bond_points(event, decision)
            if points > 0:
                after = self.store.reinforce(actor.id, target_id, points)

            self.store.record_event(
                turn=turn,
                event_type=event.type,
                participants=event.participants,
                intensity=event.intensity,
                decision=decision,
                message=event.decisionMessage,
            )
            decisions.append(
                TurnDecision(
                    turn=turn,
                    actor=actor.id,
                    target=target_id,
                    event=event,
                    decision=decision,
                    relationship_before=f"{before.stage}({before.bond})",
                    relationship_after=f"{after.stage}({after.bond})",
                )
            )
        return decisions

    def run(self, turns: int) -> list[TurnDecision]:
        """Run ``turns`` more turns, continuing from any persisted history."""
        start = self.store.last_turn() + 1
        all_decisions: list[TurnDecision] = []
        for t in range(start, start + turns):
            all_decisions.extend(self.run_turn(t))
        return all_decisions


# -- a small generic cast (no domain content) ----------------------------


def default_cast() -> list[Person]:
    from social_engine import Personality

    return [
        Person("a_jordan", "Jordan", Personality(["outgoing", "playful"], energy=8, mood="upbeat")),
        Person("a_riley", "Riley", Personality(["outgoing", "curious"], energy=7)),
        Person("a_quinn", "Quinn", Personality(["shy", "reserved"], energy=2, mood="quiet")),
        Person("a_sasha", "Sasha", Personality(["calm", "gentle", "curious"], energy=4)),
        Person("a_theo", "Theo", Personality(["playful", "bold"], energy=9)),
    ]


# ======================================================================
# P4 — the self-correcting (Reflexion-style) loop
# ======================================================================
#
# P2/P3 ran a *single-pass* turn loop: engine proposes -> gate decides ->
# memory updates. P4 closes the feedback loop by adding, per step, an
# INDEPENDENT verifier (maker != grader) that critiques the gated action; the
# critique is written back to memory and INJECTED into the same actor's next
# turn so behaviour self-corrects. The loop runs until a GOAL is met or a BUDGET
# cap is hit, and reports WHY it stopped plus responsible-loop metrics.
#
# Step order per actor (the safety gate still governs every step):
#   engine proposes -> GATE decides -> VERIFIER critiques -> critique to memory
#   -> next turn reads the critique back.


@dataclass
class LoopMetrics:
    """Responsible-loop-engineering counters (printed in the summary)."""

    engine_calls: int = 0
    verifier_calls: int = 0
    gate_evaluations: int = 0  # how many times the safety gate decided
    sim_tokens: int = 0        # simulated token tally (mock-deterministic)

    def line(self) -> str:
        return (
            f"responsible loop engineering: engine_calls={self.engine_calls} "
            f"verifier_calls={self.verifier_calls} gate_evaluations={self.gate_evaluations} "
            f"sim_tokens={self.sim_tokens}"
        )


@dataclass
class CorrectingStep:
    """A visible record of one actor's full propose->gate->verify step."""

    turn: int
    actor: str
    target: str
    event: SocialEvent
    decision: str
    relationship_before: str
    relationship_after: str
    injected_note: str       # the critique injected INTO this proposal (if any)
    critique: Critique       # the critique this step PRODUCED (writeback)


@dataclass
class StopReason:
    """Why the loop terminated (printed responsibly)."""

    kind: str    # "goal_reached" | "budget_turns" | "budget_engine_calls" | "stalled"
    detail: str


class SelfCorrectingSimulation(SocialSimulation):
    """Extends the P2 turn loop into a self-correcting loop.

    Adds (a) a pluggable independent ``Verifier`` (default: deterministic
    ``RuleBasedVerifier``), (b) critique writeback + next-turn injection via the
    memory store, (c) goal-conditioned termination + a budget cap, and (d)
    responsible-loop metrics. The Declarative Safety Gate from the SDK still
    decides every step; the verifier is ADDITIONAL governance, not a swap.
    """

    def __init__(
        self,
        agents: list[Person],
        world: World,
        store: MemoryStore,
        engine: SocialEngine | None = None,
        verifier: Verifier | None = None,
        seed: int = 7,
        *,
        goal_stage: str = "walk_buddy",  # stop once ANY pair reaches this
        max_turns: int = 12,             # budget cap (turns)
        max_engine_calls: int = 60,      # budget cap (engine invocations)
        stall_patience: int = 3,         # stop after N turns with no approved progress
    ) -> None:
        super().__init__(agents, world, store, engine, seed)
        self.verifier: Verifier = verifier or RuleBasedVerifier()
        self.goal_stage = goal_stage
        self.max_turns = max_turns
        self.max_engine_calls = max_engine_calls
        self.stall_patience = stall_patience
        self.metrics = LoopMetrics()
        self.steps: list[CorrectingStep] = []
        self.stop_reason: StopReason | None = None

    # -- one self-correcting turn -----------------------------------------

    def _stage_index(self, stage: str) -> int:
        from memory_store import RELATIONSHIP_STAGES

        return RELATIONSHIP_STAGES.index(stage) if stage in RELATIONSHIP_STAGES else 0

    def _goal_met(self) -> bool:
        target_idx = self._stage_index(self.goal_stage)
        return any(self._stage_index(r.stage) >= target_idx for r in self.store.all_relationships())

    def run_correcting_turn(self, turn: int) -> tuple[list[CorrectingStep], bool]:
        """Run one turn; returns (steps, made_approved_progress)."""
        steps: list[CorrectingStep] = []
        made_progress = False
        for actor in self.agents:
            if self.metrics.engine_calls >= self.max_engine_calls:
                break
            neighbours = self._neighbours(actor)
            if not neighbours:
                continue

            # (injection) read back this actor's latest critique and inject it.
            prior = self.store.latest_critique(actor.id)
            inp = EngineInput(
                subject=actor,
                candidates=neighbours,
                context=self._context(),
                adviseLighter=bool(prior.advise_lighter) if prior else False,
                critiqueNote=prior.reason if prior else "",
            )

            # (propose) engine proposes — this is one engine call.
            self.metrics.engine_calls += 1
            self.metrics.sim_tokens += 120  # mock: per-proposal token estimate
            events = self.engine.proposeEvents(inp)
            # The reference engine may evaluate the gate once or twice (downgrade).
            self.metrics.gate_evaluations += 2 if events and "DOWNGRAD" in (events[0].decision or "") else 1
            if not events:
                continue
            event = events[0]
            target_id = next(
                (p for p in event.participants if p != actor.id), event.participants[-1]
            )
            decision = event.decision or "UNKNOWN"

            # (memory: relationship update — same rule as P2)
            before = self.store.get_relationship(actor.id, target_id)
            after = before
            points = _bond_points(event, decision)
            if points > 0:
                after = self.store.reinforce(actor.id, target_id, points)
                made_progress = True

            self.store.record_event(
                turn=turn,
                event_type=event.type,
                participants=event.participants,
                intensity=event.intensity,
                decision=decision,
                message=event.decisionMessage,
            )

            # (verify) INDEPENDENT grader reviews the gated action (maker != grader).
            self.metrics.verifier_calls += 1
            self.metrics.sim_tokens += 60  # mock: per-review token estimate
            critique = self.verifier.review(
                actor=actor,
                event=event,
                decision=decision,
                bond_before=before.bond,
                bond_after=after.bond,
            )

            # (writeback) persist the critique so the next turn can read it.
            self.store.record_critique(
                turn=turn,
                actor=actor.id,
                target=target_id,
                score=critique.score,
                reason=critique.reason,
                advise_lighter=critique.advise_lighter,
            )

            steps.append(
                CorrectingStep(
                    turn=turn,
                    actor=actor.id,
                    target=target_id,
                    event=event,
                    decision=decision,
                    relationship_before=f"{before.stage}({before.bond})",
                    relationship_after=f"{after.stage}({after.bond})",
                    injected_note=(prior.reason if prior else ""),
                    critique=critique,
                )
            )
        return steps, made_progress

    def run_until_goal_or_budget(self) -> StopReason:
        """The self-correcting loop: iterate until goal met OR budget hit.

        Stops responsibly and records WHY. Continues from any persisted turn so
        re-runs pick up where the last one left off (durable memory).
        """
        start = self.store.last_turn() + 1
        stalled_for = 0

        if self._goal_met():
            self.stop_reason = StopReason("goal_reached", f"a pair already at/above '{self.goal_stage}'")
            return self.stop_reason

        for offset in range(self.max_turns):
            turn = start + offset
            steps, made_progress = self.run_correcting_turn(turn)
            self.steps.extend(steps)

            if self._goal_met():
                self.stop_reason = StopReason(
                    "goal_reached", f"a pair reached '{self.goal_stage}' on turn {turn}"
                )
                return self.stop_reason

            stalled_for = 0 if made_progress else stalled_for + 1
            if stalled_for >= self.stall_patience:
                self.stop_reason = StopReason(
                    "stalled", f"{stalled_for} turns with no approved bond progress (patience={self.stall_patience})"
                )
                return self.stop_reason
            if self.metrics.engine_calls >= self.max_engine_calls:
                self.stop_reason = StopReason(
                    "budget_engine_calls", f"engine-call budget hit ({self.max_engine_calls})"
                )
                return self.stop_reason

        self.stop_reason = StopReason("budget_turns", f"turn budget hit ({self.max_turns} turns)")
        return self.stop_reason
