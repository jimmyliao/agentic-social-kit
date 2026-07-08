"""Memory & relationship persistence layer — OUR OWN engineering.

The Google Antigravity SDK governs *individual tool calls* (allow / deny /
ask-user); it has **no notion of memory, history, or evolving relationships**.
P2's value is the architecture we add on top: this module is a persistent store
(SQLite) that records, across turns and across re-runs:

  * every social event that the multi-agent loop produced (with its gate
    decision), and
  * a per-pair **relationship** that *evolves* as approved interactions
    accumulate — e.g. ``stranger -> acquaintance -> walk_buddy -> close``.

Because it is durable, re-running the simulation **continues** from where the
last run left off (relationships keep climbing, history keeps growing). None of
this comes from the SDK — it is the engineering P2 contributes.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from typing import Optional

# Relationship ladder. Approved, higher-intensity interactions move a pair up;
# the stage name is generic (no domain content).
RELATIONSHIP_STAGES = [
    "stranger",
    "acquaintance",
    "friendly",
    "walk_buddy",
    "close",
]

# Bond points needed to *reach* each stage index (cumulative thresholds).
STAGE_THRESHOLDS = [0, 3, 8, 15, 25]


def _pair_key(a: str, b: str) -> tuple[str, str]:
    """Relationships are symmetric; store the canonical (sorted) ordering."""
    return (a, b) if a <= b else (b, a)


@dataclass
class Relationship:
    person_a: str
    person_b: str
    bond: int
    stage: str
    interactions: int


@dataclass
class EventRecord:
    turn: int
    ts: float
    event_type: str
    participants: str  # comma-joined ids
    intensity: int
    decision: str
    message: str


@dataclass
class CritiqueRecord:
    """A persisted verifier critique (P4 — the self-correcting loop).

    Stored per (actor, turn) so the SAME actor's next turn can read back its
    latest critique and self-correct. ``advise_lighter`` is the actionable
    next-turn steer (1 = keep it gentle).
    """

    turn: int
    ts: float
    actor: str
    target: str
    score: float
    reason: str
    advise_lighter: int  # 0/1 (SQLite has no bool)


class MemoryStore:
    """Durable store for events + evolving relationships (self-built layer)."""

    def __init__(self, path: str = "leapie_memory.sqlite3") -> None:
        self.path = path
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                turn        INTEGER NOT NULL,
                ts          REAL    NOT NULL,
                event_type  TEXT    NOT NULL,
                participants TEXT   NOT NULL,
                intensity   INTEGER NOT NULL,
                decision    TEXT    NOT NULL,
                message     TEXT    NOT NULL
            );
            CREATE TABLE IF NOT EXISTS relationships (
                person_a     TEXT NOT NULL,
                person_b     TEXT NOT NULL,
                bond         INTEGER NOT NULL DEFAULT 0,
                interactions INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (person_a, person_b)
            );
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                val TEXT NOT NULL
            );
            -- P4: persisted verifier critiques (maker != grader feedback).
            -- One row per (actor, turn); the next turn reads the latest by actor.
            CREATE TABLE IF NOT EXISTS critiques (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                turn           INTEGER NOT NULL,
                ts             REAL    NOT NULL,
                actor          TEXT    NOT NULL,
                target         TEXT    NOT NULL,
                score          REAL    NOT NULL,
                reason         TEXT    NOT NULL,
                advise_lighter INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_critiques_actor ON critiques(actor, id);
            """
        )
        self._conn.commit()

    # -- turn bookkeeping (lets re-runs continue, not restart) ------------

    def last_turn(self) -> int:
        row = self._conn.execute("SELECT MAX(turn) AS t FROM events").fetchone()
        return int(row["t"]) if row and row["t"] is not None else 0

    # -- relationships ----------------------------------------------------

    @staticmethod
    def _stage_for(bond: int) -> str:
        stage = RELATIONSHIP_STAGES[0]
        for idx, threshold in enumerate(STAGE_THRESHOLDS):
            if bond >= threshold:
                stage = RELATIONSHIP_STAGES[idx]
        return stage

    def get_relationship(self, a: str, b: str) -> Relationship:
        pa, pb = _pair_key(a, b)
        row = self._conn.execute(
            "SELECT bond, interactions FROM relationships WHERE person_a=? AND person_b=?",
            (pa, pb),
        ).fetchone()
        bond = int(row["bond"]) if row else 0
        interactions = int(row["interactions"]) if row else 0
        return Relationship(pa, pb, bond, self._stage_for(bond), interactions)

    def reinforce(self, a: str, b: str, points: int) -> Relationship:
        """Strengthen a pair's bond by ``points`` (only on approved interactions).

        Returns the updated relationship so the caller can observe stage
        transitions (the emergent behaviour).
        """
        pa, pb = _pair_key(a, b)
        cur = self.get_relationship(pa, pb)
        new_bond = max(0, cur.bond + points)
        self._conn.execute(
            """
            INSERT INTO relationships (person_a, person_b, bond, interactions)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(person_a, person_b)
            DO UPDATE SET bond = ?, interactions = interactions + 1
            """,
            (pa, pb, new_bond, new_bond),
        )
        self._conn.commit()
        return Relationship(pa, pb, new_bond, self._stage_for(new_bond), cur.interactions + 1)

    def all_relationships(self) -> list[Relationship]:
        rows = self._conn.execute(
            "SELECT person_a, person_b, bond, interactions FROM relationships ORDER BY bond DESC"
        ).fetchall()
        return [
            Relationship(r["person_a"], r["person_b"], r["bond"], self._stage_for(r["bond"]), r["interactions"])
            for r in rows
        ]

    # -- events -----------------------------------------------------------

    def record_event(
        self,
        turn: int,
        event_type: str,
        participants: list[str],
        intensity: int,
        decision: str,
        message: str,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO events (turn, ts, event_type, participants, intensity, decision, message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (turn, time.time(), event_type, ",".join(participants), intensity, decision, message),
        )
        self._conn.commit()

    def history(self, limit: Optional[int] = None) -> list[EventRecord]:
        sql = "SELECT turn, ts, event_type, participants, intensity, decision, message FROM events ORDER BY id"
        if limit is not None:
            sql += f" DESC LIMIT {int(limit)}"
        rows = self._conn.execute(sql).fetchall()
        recs = [
            EventRecord(r["turn"], r["ts"], r["event_type"], r["participants"], r["intensity"], r["decision"], r["message"])
            for r in rows
        ]
        return list(reversed(recs)) if limit is not None else recs

    def event_count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS c FROM events").fetchone()
        return int(row["c"]) if row else 0

    # -- critiques (P4: verifier writeback + next-turn injection) ----------

    def record_critique(
        self,
        turn: int,
        actor: str,
        target: str,
        score: float,
        reason: str,
        advise_lighter: bool,
    ) -> None:
        """Persist one verifier critique for ``actor`` on ``turn``."""
        self._conn.execute(
            """
            INSERT INTO critiques (turn, ts, actor, target, score, reason, advise_lighter)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (turn, time.time(), actor, target, float(score), reason, 1 if advise_lighter else 0),
        )
        self._conn.commit()

    def latest_critique(self, actor: str) -> Optional[CritiqueRecord]:
        """The most recent critique for ``actor`` (None if it has none yet).

        This is what the next turn injects so the actor self-corrects. Durable,
        so the steer survives across re-runs just like relationships do.
        """
        row = self._conn.execute(
            """
            SELECT turn, ts, actor, target, score, reason, advise_lighter
            FROM critiques WHERE actor = ? ORDER BY id DESC LIMIT 1
            """,
            (actor,),
        ).fetchone()
        if not row:
            return None
        return CritiqueRecord(
            turn=row["turn"],
            ts=row["ts"],
            actor=row["actor"],
            target=row["target"],
            score=float(row["score"]),
            reason=row["reason"],
            advise_lighter=int(row["advise_lighter"]),
        )

    def critique_count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS c FROM critiques").fetchone()
        return int(row["c"]) if row else 0

    def close(self) -> None:
        self._conn.close()
