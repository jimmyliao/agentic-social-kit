# agentic-social-kit

A small, **generic** reference kit for building **agentic social** experiences with a
**Declarative Safety Gate** on top of the Google Antigravity Agent SDK
(`google.antigravity`, v0.1.4).

> Personal GDE contribution for the **Agentic Architect Sprint** (#GoogleAntigravity
> #AgenticArchitect). Demonstrates lifecycle hooks + declarative safety policies
> (APPROVE / DENY / ASK_USER) governing autonomous social agents — a pattern that
> fits **privacy-sensitive, human-in-the-loop** deployments.

## What this shows
- Declarative safety policies + lifecycle hooks via the SDK's `policy` /
  `pre_tool_call_decide` machinery (safe to run in privacy-sensitive contexts)
- A pluggable `SocialEngine` interface (swap the reasoning engine)
- Personality → social-event generation, gated by **visible** policy decisions
  (approve / deny / downgrade / ask-user)

## Run it
```bash
# P0 — minimal hooks/policies mechanism
uv run --with google-antigravity python p0_demo.py

# P1 — two personalities -> one safety-gated SocialEvent (3+ scenarios)
uv run --with google-antigravity python p1_demo.py

# P2 — multi-agent mixer over turns + persistent memory/relationships
uv run --with google-antigravity python p2_demo.py --reset --turns 3

# P3 — real-LLM persona engine, governed by the same gate; writes the UI turn-log
#   With a key  (real Gemini personas):
GOOGLE_API_KEY=... uv run --with google-antigravity --with google-genai \
    python p3_demo.py --engine llm --turns 4 --reset
#   No key (anyone, offline): auto-falls back to the rule engine
uv run --with google-antigravity python p3_demo.py --engine rule --turns 4 --reset

# P4 — the self-correcting (Reflexion-style) loop: independent verifier
#   (maker != grader) + critique writeback/injection + goal/budget termination
uv run --with google-antigravity python p4_demo.py --reset
```
P0–P2 need no API key (the policy hook runs over mock actions — deterministic,
offline). P3's LLM path uses `GOOGLE_API_KEY` and **gracefully falls back to the
rule engine when no key is set**, so the public demo runs for anyone.

## "The Mixer" web view
`p3_demo.py` writes `docs/turn-log.json`; `docs/mixer.html` is a **self-contained
vanilla-JS page** that replays it — no server required for logic. Avatar nodes show
personalities, relationship lines thicken/green by **bond tier**, and the live feed
shows each event's **LLM rationale + safety-gate badge** (✅ APPROVE / ↓ DOWNGRADED /
🔒 ASK_USER / ⛔ DENY). The gate badge is the visual hero.

```bash
# generate a log, then view (a tiny static server avoids the file:// fetch block)
python3 -m http.server 8099 -d docs   # then open http://localhost:8099/mixer.html
```
(Opened directly via `file://`, the page renders an embedded sample so it still works.)

![The Mixer](docs/mixer-ui.png)

## Files
- `safety_gate.py` — generic `SafetyGate` wrapper over `policy.enforce(...)`
- `social_engine.py` — generic data model + `SocialEngine` protocol + reference rule engine
- `llm_social_engine.py` — **P3** real-LLM persona engine (same `SocialEngine` seam, same gate, key/fallback)
- `verifier.py` — **P4** independent `Verifier` protocol (maker ≠ grader) + deterministic `RuleBasedVerifier`
- `orchestrator.py` / `memory_store.py` — self-built multi-agent loop + persistent relationships + **P4** `SelfCorrectingSimulation` and critique persistence
- `p0_demo.py` … `p4_demo.py` — runnable demos (outputs saved alongside)
- `docs/mixer.html` + `docs/turn-log.json` — "The Mixer" replay UI + its data

## SDK features used
`Agent` + `LocalAgentConfig` (`policies`, `triggers`, `response_schema`),
`policy.allow` / `policy.deny` / `policy.ask_user` with `when=` predicates,
`policy.enforce` → `PreToolCallDecideHook`, `Decision` enum (APPROVE/DENY/ASK_USER),
`triggers.every(...)`, `types.ToolCall` / `hooks.HookResult` / `hooks.HookContext`.

## Declarative safety gate (the Sprint hook)
Policies are evaluated by SDK priority — **Specific Deny > Specific Ask > Specific Allow**:
- `intensity > maxIntensity` → **DENY** (hard cap); engine may **downgrade** to a low-pressure event
- participant on `blockedIds` → **DENY**
- `requireConsent` on a non-trivial action → **ASK_USER**
- otherwise → **APPROVE**

## What the SDK gives us vs. what we built (the boundary stays clear)
- **SDK (Google Antigravity):** *per-action governance only* — the Declarative
  Safety Gate (`policy.allow/deny/ask_user` → `policy.enforce`). Both engines (rule
  and LLM) submit every proposed event through this same gate.
- **Our engineering:** the `SocialEngine` seam (pluggable reasoning), the rule engine,
  the **LLM persona engine** (P3), the multi-agent turn loop + shared world
  (`orchestrator.py`), and the **persistent memory / evolving relationships**
  (`memory_store.py`). The SDK has no concept of memory, multi-agent orchestration,
  or personas — that is all ours.
- **Engine is one-line pluggable:** `LLMSocialEngine()` vs `RuleBasedSocialEngine()`,
  behind the identical `proposeEvents(input) -> SocialEvent[]` interface and the
  identical gate. The LLM only *proposes*; the gate still *decides*.

## P3 — real LLM persona engine
`LLMSocialEngine` asks Gemini (via `google-genai`, model `gemini-flash-latest`) to
read two personalities + venue context and invent one believable social move with an
in-character rationale (JSON out). That event is then handed to the same SafetyGate.
Key handling: reads `GOOGLE_API_KEY` from env (never hard-coded); **no key / no SDK /
any API error → graceful fallback to the rule engine**, with the active `source`
("llm" | "rule") surfaced in the turn-log and the UI.

## P4 — the self-correcting (Reflexion-style) loop
P0–P3 ran a **single-pass** turn loop (engine proposes → safety gate decides →
memory updates). P4 closes the feedback loop, **without replacing the gate**:

- **Independent verifier (maker ≠ grader)** — `verifier.py` adds a pluggable
  `Verifier` protocol (mirrors the `SocialEngine` seam) with a deterministic,
  offline `RuleBasedVerifier`. It reviews a *proposed-and-gated* action and
  returns a small **critique** = a short reason + a `score ∈ [0,1]` over three
  generic axes: **advance** the goal (did the bond move?), **appropriate** for
  the gate verdict (a DENY/ASK_USER shouldn't be re-tried at the same pressure),
  and **quality** (compatibility + sensible intensity). The grader is a separate
  component from the engine that proposed the action.
- **Critique writeback + injection** — each critique is persisted to the SQLite
  store (`critiques` table), and on the **same actor's next turn** its latest
  critique is injected into the engine input (`adviseLighter` / `critiqueNote`)
  so behaviour self-corrects (after a DENY/DOWNGRADE, the next proposal goes
  gentle).
- **Goal-conditioned termination + budget cap** — the loop iterates until a
  **goal** (any pair reaches a target relationship stage) **OR** a budget cap
  (`--max-turns`, `--max-engine-calls`) **OR** a stall (`--stall-patience` turns
  with no approved progress). It prints **why** it stopped.
- **Responsible-loop metrics** — engine calls, verifier calls, gate evaluations,
  and a simulated token tally, printed as a "responsible loop engineering" line.

Order, every step: **engine proposes → safety gate decides
(APPROVE/DENY/DOWNGRADE/ASK_USER) → verifier critiques → critique to memory →
next turn injects it.** The gate is still the hard boundary; the verifier is
*additional* governance.

```bash
uv run --with google-antigravity python p4_demo.py --reset
# tighten the world so bold actors over-reach and get steered gentle:
uv run --with google-antigravity python p4_demo.py --reset --max-intensity 4 --goal-stage walk_buddy
```
Saved output: [`p4_demo_output.txt`](p4_demo_output.txt).

## Status
- [x] P0 — replicate SDK hooks/policies mechanism
- [x] P1 — two personalities → one safety-gated SocialEvent
- [x] P2 — multi-agent mixer over turns + persistent memory/relationships
- [x] P3 — real-LLM persona engine (same gate, key + offline fallback) + "The Mixer" web view
- [x] P4 — self-correcting loop: independent verifier (maker ≠ grader) + critique writeback/injection + goal/budget termination + responsible-loop metrics

## Demo output (excerpt)

P0:
```
Agent built (Agent). policies=6 triggers=1 response_schema=True
  calm low-intensity wave                    -> APPROVE   allow=True
  over-cap visit (should DENY)               -> DENY      allow=False Denied by policy 'cap_intensity'.
  consent-required meetup (should ASK_USER)  -> ASK_USER  allow=False User denied tool 'social_action' (policy 'require_consent').
```

P1:
```
### Scenario A — outgoing pair, relaxed safety
  EVENT:    type=visit intensity=8 score=0.62
  DECISION: APPROVE

### Scenario B — outgoing pair, tightened maxIntensity
  EVENT:    type=leave_a_note intensity=2 score=0.62
  DECISION: DOWNGRADED (orig DENY) -> APPROVE  | original 'visit' (intensity 8) denied...; downgraded to 'leave_a_note'.

### Scenario C — reserved subject, consent required
  EVENT:    type=gentle_intro intensity=3 score=0.4
  DECISION: ASK_USER

### Scenario D — only candidate is blocked
  -> no eligible candidates (all blocked)
```
Full logs: [`p0_demo_output.txt`](p0_demo_output.txt), [`p1_demo_output.txt`](p1_demo_output.txt).

P3 (real Gemini rationales, each then gated):
```
[APPROVE]   Jordan -> Theo (share_a_drink, intensity 5)
   "Since I'm feeling extremely outgoing tonight, sharing a drink is the perfect
    way to match Theo's bold and high-energy vibe."
[APPROVE]   Theo -> Quinn (gentle_intro, intensity 3)
   "I want to share my playful energy with Quinn, but since they seem so shy and
    reserved tonight, I should start with a gentle introduction so I don't overwhelm them."
[DOWNGRADED] Jordan -> Theo (leave_a_note, intensity 2)   # orig share_a_drink (5) > maxIntensity 4
   gate: original 'share_a_drink' (intensity 5) denied by 'cap_intensity'; downgraded to 'leave_a_note'.
```

## Scope / firewall
This repo is **generic and self-contained**. It contains **no client/employer
confidential material, no product data, and no third-party IP** — only generic sample
data and the open pattern. MIT licensed.
