# Blog Outline — Declarative Safety Gate, told to three engineering audiences

> A multi-entry-point outline for a GDE blog post about the **Declarative Safety Gate**
> pattern built on the Google Antigravity Agent SDK (`google.antigravity`, lifecycle
> hooks + declarative policies). One idea, three doors — each door is one of the
> emerging "engineering beyond prompting" paradigms, so the post can land with the
> reader regardless of which camp they came from.
>
> Tags: **#GoogleAntigravity #AgenticArchitect**

---

## 0. Anchor: the running demo (this is real, not a thought experiment)

Everything below maps back to a tiny, runnable, **generic** kit (`agentic-social-kit`):

- A declarative policy layer (`safety_gate.py`) wrapping the SDK's
  `policy.allow / policy.deny / policy.ask_user` rules into a single
  `policy.enforce(...)` → `PreToolCallDecideHook`.
- Decisions are **visible** and four-valued: **APPROVE / DENY / DOWNGRADE / ASK_USER**.
- A pluggable `SocialEngine` interface (swap the reasoning engine) that proposes
  generic person-to-person social events, each one gated before it's allowed to act.
- Two runnable demos with deterministic, offline output (no API key, no live model):
  - **P0** — minimal hooks/policies mechanism (`p0_demo.py`).
  - **P1** — two personalities → one safety-gated social event across 3+ scenarios
    (`p1_demo.py`): relaxed-allow, tightened-deny-then-downgrade, consent-required,
    all-blocked.

The single sentence the whole post defends:

> **A Declarative Safety Gate is a behavior you *declare as a spec* (SDD), enforce
> at a *control point inside the agent's loop* (loop engineering), and which together
> forms the *governance harness* around an autonomous agent (harness engineering).**

---

## Entry point 1 — Harness Engineering (the primary frame, most direct)

**Core vocabulary of the paradigm** (from the source articles):
- *Harness* = the full equipment that lets a powerful-but-uncontrolled model be
  "safely ridden" — it doesn't change what the model *can* do, it governs
  direction / speed / distance / recovery.
- The five harness dimensions include **Safety Boundaries** (tool permissions +
  behavior constraints) and **Resource Management** (budgets, circuit breakers).
- **Guides (前饋控制)** = proactive controls *before* action; **Sensors (回饋控制)**
  = reactive controls *after* action; the **Steering / Control Loop** ties them
  together with human steering signals.
- **Mechanical Enforcement** — "documentation decays; lint rules don't" — invariants
  enforced by deterministic code, not prose.

**Mapping to our work:**
- The Safety Gate **is** the agent's governance harness — specifically the
  *Safety Boundary* dimension made concrete.
- `hooks` / `policies` / `policy.enforce` are **harness primitives**: the
  pre-tool-call hook is a deterministic **Guide** that intercepts an action *before*
  it executes.
- DENY = a hard boundary (a circuit breaker on intensity); DOWNGRADE = recovery /
  graceful degradation instead of a dead stop; ASK_USER = the human-in-the-loop
  steering signal.

**Honest strength of fit:** **STRONG.** This is the most literal mapping. A
pre-tool-call policy hook is exactly what "Mechanical Enforcement of a Safety
Boundary" describes; "visible decision back to a human" is the steering loop.

**Honest weakness:** The harness articles describe a *broad* discipline (resource
mgmt, state persistence, info-flow, orchestration). We only implement **one of five
dimensions** (Safety Boundaries) plus a sliver of resource control (the intensity
cap). Don't claim we built "a harness" — we built one harness primitive well.

---

## Entry point 2 — Spec-Driven Development / SpecKit

**Core vocabulary of the paradigm:**
- SDD *inverts the power structure*: **code serves specifications**, not the reverse.
  The spec is the **source of truth** and the **contract** for how code must behave.
- SpecKit's loop: `/specify → /plan → /tasks → /implement` — structured, repeatable.
- Agents are treated as **literal-minded pair programmers**: they need *unambiguous*
  instructions; a clear spec up front improves agent efficacy.

**Mapping to our work:**
- Our policies are **behavior-as-spec**: `deny_when(intensity > maxIntensity)`,
  `ask_user_when(requireConsent and intensity >= 3)` are a *declared contract* for
  agent behavior, not imperative control flow buried in the engine.
- The `SocialEngine` `Protocol` is **contract-first / interface-as-spec**: the
  reasoning engine is swappable behind a fixed interface, so the spec (what events
  look like, what gets gated) is stable while the implementation varies.
- The same engine code produces APPROVE / DENY / DOWNGRADE / ASK_USER **purely from
  data** (the `Safety` block) — i.e. behavior is driven by the declared spec, not
  by re-coding.

**Honest strength of fit:** **MODERATE–STRONG.** "Declarative policy = the contract
your tools and agents validate against" lands cleanly. The `Protocol` interface is a
genuine contract-first artifact.

**Honest weakness / don't oversell:** We do **not** use SpecKit's actual workflow
(`/specify → /plan → /tasks`), and we don't generate code *from* a spec. Ours is
"declarative *configuration* as spec," which is adjacent to — not the same as — SDD's
"spec *generates* implementation." Frame it as *spirit-aligned*, not tooling-aligned.

---

## Entry point 3 — Loop Engineering

**Core vocabulary of the paradigm:**
- *Loop engineering* = replacing "you, manually prompting the AI" with **a system
  that runs the interaction cycle for you**.
- Five-stage lifecycle: **Discover → Plan → Execute → Verify → Iterate**.
- Six components include **Automations** (scheduled execution + **trigger
  conditions** — the "heartbeat") and **Sub-agents** (independent verification to
  avoid self-validation bias).
- Emphasis: system design for **self-correcting feedback loops**, not one-shot output.

**Mapping to our work:**
- Lifecycle **hooks / triggers** are the **loop's control points**. The SDK's
  `triggers.every(...)` is the heartbeat; the **pre-tool-call hook is the joint of
  the loop** where the Safety Gate is installed — between *Plan* (propose event) and
  *Execute* (take the action).
- DOWNGRADE is a **self-correcting iteration**: a denied high-intensity event is
  re-proposed as a low-pressure variant and re-evaluated — a mini Verify→Iterate
  loop inside one proposal.

**Honest strength of fit:** **MODERATE.** The "gate sits at a joint of the loop"
framing is genuinely useful and accurate; the downgrade-retry is a real feedback
loop. `triggers.every(...)` exists in the SDK feature set we use.

**Honest weakness / don't force it:** Our demo is **not a long-running autonomous
loop** — it's a deterministic, single-pass evaluation per scenario. We don't run the
full Discover→…→Iterate lifecycle, no sub-agent verifier, no automation heartbeat
actually scheduled. Use loop engineering as a *lens on where the gate lives*, not a
claim that we built a loop engine. **This is the most adjacent of the three — label
it as a lens, not a 1:1 mapping.**

---

## Unifying section — one gate, three names

Short synthesis restating the thesis sentence, with a single diagram:

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

Takeaway: the three paradigms aren't competitors — they're three altitudes of the
same control surface. **Spec = *what* the rule is. Loop = *where* it fires.
Harness = *why* it makes autonomy safe.**

---

## "Where's the code / how do I run it" section

Point readers at the public repo and the two demos:

```bash
# P0 — minimal hooks/policies mechanism
uv run --with google-antigravity python p0_demo.py

# P1 — two personalities -> one safety-gated SocialEvent (3+ scenarios)
uv run --with google-antigravity python p1_demo.py
```

- No API key needed — the compiled policy hook runs over mock actions, so output is
  deterministic and reproducible offline.
- Files to read first: `safety_gate.py` (the gate), `social_engine.py`
  (data model + `SocialEngine` protocol + reference engine), then `p1_demo.py`.
- Saved outputs: `p0_demo_output.txt`, `p1_demo_output.txt`.

---

## Closing / CTA

- One line on *why this matters*: declarative, visible safety decisions are what make
  autonomous agents shippable in privacy-sensitive, human-in-the-loop contexts.
- Invite readers from each camp to try swapping the `SocialEngine` or adding a policy.
- Tags: **#GoogleAntigravity #AgenticArchitect**

---

## Appendix — source notes & honesty ledger

**Terms harvested per source (all four fetched successfully):**
- **Loop engineering** (bnext): 迴圈工程; 5-stage lifecycle Discover→Plan→Execute→Verify→Iterate;
  6 components — Automations (triggers/heartbeat), Worktree, Skills, Connectors,
  Sub-agents, Memory; "prompt eng = precise language for one output / loop eng =
  system design for self-correcting feedback loops."
- **Harness engineering** (wenwender): 韌繩工程; equestrian metaphor; 5 dimensions —
  Resource Mgmt, State Persistence, Information-Flow Control, **Safety Boundaries**,
  Task Orchestration; distinguished from Prompt vs Context engineering. *Note: this
  article does NOT define hooks/policies/middleware as named primitives.*
- **Harness engineering** (hackmd @BASHCAT): Guides (前饋控制) vs Sensors (回饋控制);
  Steering Loop; Computational vs Inferential Sensor; AGENTS.md; Repository Knowledge
  as System of Record.
- **Harness engineering** (github deusyu): 6 concepts — Repo as Source of Truth,
  Map over Manual, **Mechanical Enforcement**, Agent Readability, Throughput changes
  Merge logic, Entropy as GC; Control Loop; Ralph Cycle (fresh context + backpressure
  gates + disposable plans + disk-persisted state + human steering).
- **SpecKit / SDD** (WebSearch — github/spec-kit, GitHub Blog, Fowler): SDD inverts
  power structure (code serves specs); spec = source of truth + contract; agents =
  literal-minded pair programmers; SpecKit loop `/specify → /plan → /tasks → /implement`.
- **LinkedIn cross-source:** not attempted / not fetched (per instructions, cross-host
  redirect; no loss of required terms).

**Honesty ledger — which mappings are strong vs. a stretch:**
- Harness → Safety Boundary primitive: **STRONG** (most literal; lead with this).
- SDD → declarative policy as contract + `Protocol` interface: **MODERATE–STRONG**
  (spirit-aligned; we do NOT use SpecKit tooling or generate code from specs).
- Loop → gate at a loop joint + downgrade-as-iteration: **MODERATE / adjacent**
  (a lens, not a built loop engine; no sub-agent verifier, no scheduled heartbeat).
- Avoid claiming: "we built a harness" (only one of five dimensions);
  "this is SpecKit/SDD" (it's declarative config, adjacent); "this is a loop engine"
  (it's single-pass deterministic evaluation).
```
