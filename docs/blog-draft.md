# The Declarative Safety Gate: governing autonomous social agents on the Google Antigravity SDK

> A GDE **Agentic Architect Sprint** writeup. One pattern — the *Declarative Safety
> Gate* — built on the Google Antigravity Agent SDK (`google.antigravity`), told as a
> running demo called **The Mixer**. Everything here is real and runnable; the honesty
> ledger at the end tells you exactly which claims are strong and which are just a
> useful lens.
>
> Tags: **#GoogleAntigravity #AgenticArchitect**

![The Mixer](./mixer-ui.png)

---

## 1. The hook: a room full of autonomous agents

Picture **The Mixer**: a generic social space where a handful of people-shaped agents —
Jordan, Riley, Quinn, Sasha, Theo — each have their own personality and are turned
loose to *socialize on their own*. Jordan is outgoing and high-energy and wants to set
up a hangout. Quinn is shy and reserved and would rather just wave hello. Left alone,
they perceive who's nearby, decide who to approach, and propose an interaction — no
human in the loop, every turn.

That is the promise of autonomous agents: they don't wait to be prompted, they *act*.

It is also the danger. **Autonomy without governance is a liability**, and it gets worse
the more sensitive the setting. An agent that can initiate contact with another person
can also be too forward, too frequent, or simply act in a situation where a human should
have been asked first. "It usually behaves well" is not a safety story. In a
privacy-sensitive, human-in-the-loop product, *usually* ships nothing.

So the real question of the Sprint isn't "can agents be autonomous?" — they obviously
can. It's: **how do you let them be autonomous and keep a hard, visible boundary around
what they're allowed to do?**

---

## 2. The problem: autonomy needs a control surface

The instinct is to bury the rules inside the agent's reasoning: "remember to be polite,
don't be too intense, ask permission for big asks." But prose decays. A prompt-level
guardrail is a *suggestion* the model may or may not honor, it's invisible at runtime,
and you can't audit it.

What we actually want is a **control surface** with three properties:

1. **Declarative** — the rule is stated as data/spec, not tangled into imperative
   control flow. You can read it, diff it, and change behavior without rewriting logic.
2. **Enforced at a control point** — it runs *between the agent deciding to act and the
   action happening*, every single time, deterministically. Not "if the model
   remembers."
3. **Visible** — every decision comes back as an observable verdict a human (or a log,
   or a dashboard) can see and reason about.

That control surface is the **Declarative Safety Gate**, and the Google Antigravity SDK
gives us exactly the primitives to build it: lifecycle **hooks** + declarative
**policies**.

---

## 3. ★ The Declarative Safety Gate (the main course)

The Antigravity SDK lets you attach declarative **policies** to a tool, and compile them
into a `pre_tool_call_decide` **hook** — a deterministic gate that fires *before* any
tool call executes. Policies are evaluated by SDK priority: **Specific Deny > Specific
Ask > Specific Allow**. So a matching `deny` always beats an `ask_user`, which always
beats an `allow`.

We declare the entire safety boundary of The Mixer as a short, priority-ordered list of
policies over one tool, `social_action`:

```python
def build_policies() -> list[policy.Policy]:
    """A declarative safety gate as a priority-ordered policy list.

    The SDK buckets these by specificity/safety, so a matching DENY always
    beats ASK_USER, which beats ALLOW.
    """
    return [
        # Hard cap: never exceed the caller's max intensity.
        policy.deny(
            "social_action",
            when=lambda a: a.get("intensity", 0) > a.get("maxIntensity", 10),
            name="cap_intensity",
        ),
        # Require explicit human consent for non-trivial interactions.
        policy.ask_user(
            "social_action",
            handler=_ask_user,
            when=_needs_consent,
            name="require_consent",
        ),
        # Otherwise approve.
        policy.allow("social_action", name="default_allow"),
    ]
```

That's the whole gate. Three rules. No `if` ladder buried in the social engine — the
*behavior is the data*. The policies get compiled into a real hook and wired into a real
`Agent`, alongside a structured `response_schema` and a `triggers.every(...)` heartbeat,
so this is the full governance surface, not a toy:

```python
config = LocalAgentConfig(
    system_instructions=(
        "You are an autonomous social agent. Every interaction you take is "
        "governed by a declarative safety gate; respect its decisions."
    ),
    policies=build_policies(),
    triggers=[triggers.every(3600, heartbeat)],
    response_schema=ActionDecision,
)
return Agent(config), config
```

To prove the gate works *without* needing a live model or an API key, **P0** drives the
compiled hook directly over three mock actions and prints the verdict. This runs offline
and is fully deterministic:

```text
=== P0: declarative safety gate on the Google Antigravity SDK ===
Agent built (Agent). policies=6 triggers=1 response_schema=True

Policy decisions over mock actions (offline, no model call):
  calm low-intensity wave                    -> APPROVE   allow=True
  over-cap visit (should DENY)               -> DENY      allow=False Denied by policy 'cap_intensity'.
        [ASK_USER] consent prompt raised -> (demo answers: no)
  consent-required meetup (should ASK_USER)  -> ASK_USER  allow=False User denied tool 'social_action' (policy 'require_consent').

P0 OK: APPROVE / DENY / ASK_USER all observable, decided declaratively.
```

Three verdicts, all visible, all derived purely from the declared policy data:

- A calm, low-intensity action → **APPROVE**.
- An over-cap action → **DENY** (the hard intensity boundary, a circuit breaker).
- A non-trivial action flagged `requireConsent` → **ASK_USER** (the human-in-the-loop
  steering signal).

This is the core contribution: **a safety boundary you declare as policy, enforce
mechanically at a pre-tool-call control point, and read back as a visible decision.**

---

## 4. Personality → a governed event (graceful, not blunt)

A gate that only knows DENY is a brick wall. The interesting design move is what happens
*when a rule trips*. The principle here is **low-pressure / least-disruptive**: prefer to
*degrade* an over-eager action into a gentler one rather than slam the door.

**P1** takes two personalities and runs one proposed `SocialEvent` through the gate
across several scenarios. The headline is Scenario B: Jordan (outgoing, energy 8) wants a
high-intensity `visit`, but the world's `maxIntensity` is tightened to 4. The raw event
is denied — and instead of dropping it, the engine **downgrades** to a low-intensity
`leave_a_note` and re-submits, which the gate approves:

```text
### Scenario A — outgoing pair, relaxed safety
  EVENT:    type=visit intensity=8 score=0.62
            action='Set up a park hangout this afternoon'
  DECISION: APPROVE  | APPROVE (social_action)

### Scenario B — outgoing pair, tightened maxIntensity
  EVENT:    type=leave_a_note intensity=2 score=0.62
            action='Leave a friendly note at the coworking'
  DECISION: DOWNGRADED (orig DENY) -> APPROVE  | original 'visit' (intensity 8) denied: Denied by policy 'cap_intensity'.; downgraded to 'leave_a_note'.

### Scenario C — reserved subject, consent required
  EVENT:    type=gentle_intro intensity=3 score=0.4
            action='Wave hello at the cafe'
  DECISION: ASK_USER  | User denied tool 'social_action' (policy 'require_consent').

### Scenario D — only candidate is blocked
  -> no eligible candidates (all blocked)
```

Read the four scenarios as a behavior table:

- **A** — relaxed safety, high-intensity action sails through → APPROVE.
- **B** — tightened cap → the denied `visit` is **DOWNGRADED** to a `leave_a_note` and
  then approved. *Graceful degradation, not a dead stop.*
- **C** — consent required for a non-trivial action → **ASK_USER** hands control back to
  the human.
- **D** — the only available partner is on the blocklist → **no event is even proposed**.

Notice the gate produces all four outcomes from the *same engine code* — the difference
is entirely in the declared `Safety` data (`maxIntensity`, `requireConsent`,
`blockedIds`). That's the declarative payoff: you tune the agent's social behavior by
editing a spec, not by re-coding it. And DOWNGRADE is the humane default — the agent
still gets to be social, just within the boundary.

---

## 5. Multi-agent + memory: where the SDK stops and our engineering starts

The first two parts are the SDK at its best. The third part is the honest, important
boundary: **the Antigravity SDK governs individual tool calls. It does *not* give you
multi-agent orchestration, a shared world, or any notion of memory.** Those are exactly
what a real social simulation needs — so we built them.

**P2** is the full Mixer: five autonomous agents acting over multiple turns in a shared
world, *every* proposed interaction passing through the same SDK Declarative Safety Gate,
and approved interactions feeding a **persistent memory layer** (SQLite) so relationships
*evolve across turns and across re-runs*.

The boundary is stated bluntly in the code itself:

```python
#   * SDK provides : the per-event policy decision (the safety gate).
#   * WE provide    : the multi-agent turn loop, shared world, perception, and the
#                     memory / relationship persistence layer.
```

Relationships climb a generic ladder — `stranger → acquaintance → friendly →
walk_buddy → close` — and only *approved* (or downgraded-then-approved) interactions
add bond points. Here's a real run, three turns from a fresh start:

```text
=== P2: multi-agent social simulation + self-built memory layer ===
SDK governs each event (Declarative Safety Gate); the loop + memory are ours.
persisted state on entry: last_turn=0, events=0 (fresh start)

--- Turn 1 ---
  [DOWNGRADED (orig DENY) -> APPROVE] a_jordan -> a_theo: leave_a_note (intensity 2)
      relationship: stranger(0) -> stranger(1)
  [APPROVE               ] a_quinn -> a_sasha: gentle_intro (intensity 3)
      relationship: stranger(0) -> stranger(1)
  ...

--- Turn 3 ---
  [DOWNGRADED (orig DENY) -> APPROVE] a_jordan -> a_theo: leave_a_note (intensity 2)
      relationship: acquaintance(4) -> acquaintance(5)
  [APPROVE               ] a_quinn -> a_sasha: gentle_intro (intensity 3)
      relationship: stranger(2) -> acquaintance(3)

=== Relationship state (persisted memory) ===
  a_jordan <-> a_theo:  acquaintance bond=6  interactions=6
  a_jordan <-> a_riley: acquaintance bond=3  interactions=3
  a_quinn  <-> a_sasha: acquaintance bond=3  interactions=3
```

Two things matter here. First, **every line went through the gate** — Jordan's
high-intensity overtures keep getting downgraded under the world's cap, exactly as
declared; Quinn's gentle intros pass straight through. The governance from §3 holds at
scale, across many autonomous actors. Second, the state is **durable**: re-run without
`--reset` and the bonds keep climbing from where they left off. That memory layer — the
turn loop, the perception of who's nearby, the relationship ladder — is **our
engineering, sitting on top of the SDK's per-action gate, not handed to us by it.**

This is the part to be precise about. The SDK is the right tool for *governance*. The
*emergent social dynamics* are a system you design around it.

---

## 6. Three doors into one pattern (with an honesty ledger)

The "engineering beyond prompting" conversation has three camps right now. The
Declarative Safety Gate lands in all three — but with *different* strength of fit, and I
won't pretend otherwise. One sentence ties them together:

> **A Declarative Safety Gate is a behavior you *declare as a spec* (SDD), *enforce at a
> control point inside the agent's loop* (loop engineering), which together form the
> *governance harness* around an autonomous agent (harness engineering).**

```
            declared as a spec            installed at a loop joint
   (SDD: behavior-as-spec, contract)   (loop eng: pre-tool-call control point)
                     \                         /
                      \                       /
                   [ Declarative Safety Gate ]
                              |
                  forms the governance harness
            (harness eng: Safety Boundary primitive)
                              |
                APPROVE / DENY / DOWNGRADE / ASK_USER  (visible)
```

### Door 1 — Harness Engineering (strongest fit, lead with this)

A *harness* is the full equipment that lets a powerful, uncontrolled model be "safely
ridden" — it governs direction, speed, and recovery without changing what the model
*can* do. One of its five dimensions is **Safety Boundaries**, enforced by
*mechanical enforcement* ("documentation decays; lint rules don't"). Our gate **is** that
Safety Boundary made concrete: the pre-tool-call hook is a deterministic *Guide* that
intercepts an action before it executes; DENY is a hard boundary, DOWNGRADE is recovery,
ASK_USER is the human steering signal.

- **Honest strength: STRONG.** A pre-tool-call policy hook is the most literal possible
  reading of "mechanical enforcement of a safety boundary," and the visible verdict is
  the steering loop.
- **Honest weakness:** A harness is a *broad* discipline (resource mgmt, state
  persistence, info-flow, orchestration). We implement **one of five dimensions** well,
  plus a sliver of resource control (the intensity cap). We built *one harness primitive*,
  not "a harness." Don't claim the latter.

### Door 2 — Spec-Driven Development (moderate–strong)

SDD inverts the usual power structure: **code serves the spec**; the spec is the source
of truth and the *contract* for how code must behave. Our policies are
**behavior-as-spec** — `deny_when(intensity > maxIntensity)`,
`ask_user_when(requireConsent and intensity >= 3)` are a declared contract, not control
flow. The `SocialEngine` `Protocol` is a genuine contract-first interface: swap the
reasoning engine, keep the gate.

- **Honest strength: MODERATE–STRONG.** "Declarative policy = the contract your tools
  validate against" lands cleanly; the `Protocol` is a real contract-first artifact.
- **Honest weakness:** We do **not** use SpecKit's workflow (`/specify → /plan → /tasks
  → /implement`), and we do **not** generate code *from* a spec. Ours is "declarative
  *configuration* as spec," which is *spirit-aligned* with SDD — not the same thing.
  Frame it that way.

### Door 3 — Loop Engineering (a useful lens, most adjacent)

Loop engineering replaces "you manually prompting the AI" with a system that runs the
interaction cycle for you. The useful framing: lifecycle hooks/triggers are the loop's
**control points**, and the **pre-tool-call hook is the joint of the loop** where the
gate lives — between *Plan* (propose event) and *Execute* (take action). The
downgrade-and-retry in §4 is a genuine mini Verify→Iterate loop.

- **Honest strength: MODERATE.** "The gate sits at a joint of the loop" is accurate and
  genuinely clarifying; downgrade-as-iteration is a real feedback loop;
  `triggers.every(...)` is in the SDK feature set we use.
- **Honest weakness:** Our demos are **not a long-running autonomous loop** — they're
  deterministic single-pass evaluations per scenario/turn. No sub-agent verifier, no
  scheduled automation heartbeat actually firing. Use loop engineering as a *lens on
  where the gate lives*, **not** a claim that we built a loop engine. This is the most
  adjacent of the three.

### The synthesis

The three paradigms aren't competitors — they're three altitudes of the same control
surface:

> **Spec = *what* the rule is. Loop = *where* it fires. Harness = *why* it makes
> autonomy safe.**

---

## 7. Run it yourself

Everything above is reproducible offline. No API key needed — the compiled policy hook is
driven directly over mock actions, so decisions are deterministic.

```bash
# P0 — minimal hooks/policies mechanism (APPROVE / DENY / ASK_USER)
uv run --with google-antigravity python p0_demo.py

# P1 — two personalities -> one safety-gated SocialEvent (4 scenarios, incl. DOWNGRADE)
uv run --with google-antigravity python p1_demo.py

# P2 — multi-agent Mixer + persistent memory (fresh start)
uv run --with google-antigravity python p2_demo.py --reset --turns 3
# ...then re-run without --reset to watch relationships keep evolving
uv run --with google-antigravity python p2_demo.py --turns 2
```

Read in this order: `safety_gate.py` (the gate) → `social_engine.py` (data model +
`SocialEngine` protocol + reference engine) → `p1_demo.py`. For the multi-agent layer:
`orchestrator.py` (turn loop + shared world) and `memory_store.py` (persistent
relationships). Saved verdicts live in `p0_demo_output.txt` and `p1_demo_output.txt`.

The kit is **generic and self-contained** — generic sample data and an open pattern, no
product data, MIT licensed.

---

## 8. Why this matters

Declarative, visible safety decisions are what make autonomous agents *shippable* in
privacy-sensitive, human-in-the-loop contexts. You don't get there by asking the model
nicely; you get there by putting a deterministic gate at the control point and letting it
say APPROVE / DENY / DOWNGRADE / ASK_USER out loud, every time.

If you came in from any of the three doors: try it. Swap the `SocialEngine` for your own
reasoning, or add one policy to the gate and watch the verdicts change. The pattern is the
point; the demo just proves it runs.

**#GoogleAntigravity #AgenticArchitect**
