# HANDOFF — agentic-social-kit (GDE / Agentic Architect Sprint)

> Scope: this repo is a **generic, public-safe** GDE contribution. It contains
> only generic agentic-social patterns + a Declarative Safety Gate on the Google
> Antigravity Agent SDK. **Keep it that way** — no client/product names, no
> private datasets, no third-party design. Anything specific stays out of this repo.

## TL;DR for a fresh session
You are continuing a **personal GDE community contribution** for the
**Agentic Architect Sprint** (`#GoogleAntigravity #AgenticArchitect`,
deadline **2026-07-10**, GCP credits, host Soonson Kwon). The technical theme is
**"Declarative Safety Gate for Antigravity Agents"** — lifecycle hooks +
declarative policies (APPROVE / DENY / ASK_USER) governing autonomous social
agents, suited to privacy-sensitive, human-in-the-loop deployments.

The working demo is **"The Mixer"**: 5 AI personas socialize autonomously, but
every interaction is routed through the safety gate (visible approve/downgrade/
ask-user decisions).

## What's DONE ✅
- **P0** `p0_demo.py` — minimal hooks/policy mechanism on the SDK.
- **P1** `p1_demo.py` — two personalities → one safety-gated `SocialEvent` (3+ scenarios).
- **P2** `p2_demo.py` — multi-agent mixer over turns + persistent memory/relationships
  (bond ladder: stranger→acquaintance→friendly→walk_buddy→close; only approved
  interactions add bond).
- **P3** `p3_demo.py` — real-LLM persona engine (`google-genai`, `gemini-flash-latest`,
  `GOOGLE_API_KEY`, rule-based fallback) governed by the same gate; writes the UI turn-log.
- **Architecture**: `safety_gate.py` (declarative policy, fail-closed), pluggable
  `SocialEngine` interface (`social_engine.py` rule-based + `llm_social_engine.py`),
  `orchestrator.py` (turn loop), `memory_store.py` (SQLite, bond ladder).
- **Media/UI**: `docs/mixer.html` (live social feed view), `docs/the-mixer.mp4`
  (1440×936, ~2MB, 30fps H.264 — social-ready), `docs/the-mixer.gif` (1050×683, hi-res).
- **Writing**: `docs/blog-outline.md`, `docs/blog-draft.md`.

## What's NEXT 🎯 (priority order)
1. **First social post** — theme *Declarative Safety Gate*. Hook + `the-mixer.mp4`.
   Tags `#GoogleAntigravity #AgenticArchitect`. Draft below in "Social post drafts".
   Repo link filled in (repo went public 2026-07-08):
   https://github.com/jimmyliao/agentic-social-kit
2. **Loop-engineering deepening** (→ becomes 2nd post + strongest blog section):
   the current loop is **shallow** (turn loop + triggers + memory, but no independent
   verification). Deepen it into a **self-correcting (Reflexion-style) loop**:
   - add a **verifier sub-agent** (maker ≠ grader),
   - on a downgraded/denied action, generate a **critique**, write it back to
     `memory_store`, and **inject it into the next turn**,
   - add **goal-conditioned termination + budget cap** (iterate until good / stop
     responsibly) and surface the **LLM-call/token count** as a "responsible loop
     engineering" talking point.
   Narrative: *"from a shallow loop to a self-correcting loop."*
3. **Topical "World Cup" variant** (parked, optional, cheap) — see
   **`docs/WORLD-CUP-VARIANTS.md`** for the full brainstorm (4 variants:
   Fan Zone / Office Sweepstake / Cross-rivalry friendship arc / Predict & Banter).
   Recommendation: **Office Sweepstake** (best Sprint fit: "safe in high-privacy
   corporate environments") or **Cross-rivalry friendship arc** (best GIF). Decision pending.
4. **Blog finalize** by 2026-07-10. Three reader entry points (pick framing —
   open question): the **layered/stacked** framing reads well — *Spec = WHAT,
   Harness = the guardrails/environment, Loop = the time-control flow that consumes
   both each iteration.*

## How to run / verify (E2E)
```bash
cd agentic-social-kit
uv run --with google-antigravity python p0_demo.py
uv run --with google-antigravity python p1_demo.py
uv run --with google-antigravity python p2_demo.py --reset --turns 3
# P3 needs GOOGLE_API_KEY (falls back to rules if absent)
GOOGLE_API_KEY=... uv run --with google-antigravity --with google-genai python p3_demo.py
# then open docs/mixer.html (reads docs/turn-log.json)
```
Python via `uv run --with <pkg>` (no venv/pip — PEP668). `codex exec` CANNOT write
files in the sandbox here (bwrap RTM_NEWADDR) — do coding yourself / via Claude agents.

## Publishing gate ⚠️ — CLEARED 2026-07-08
Before this repo went **public** (or any post linked to it), it had to pass a
**"no confidential content" review** — generic patterns only. Review passed
(one client-name reference found in old commit history, squashed out before
going public); repo is now **public**.

## Social post drafts (ready to refine)
**X / LinkedIn (EN)**
> What if every move an autonomous agent makes had to pass a **declarative safety
> gate** first? I built **"The Mixer"** on the Google Antigravity SDK — 5 AI personas
> socializing on their own, but every interaction is routed through policy:
> ✅ approve · ↓ downgrade · 🔒 ask-user. The gate is the protagonist. 🎥👇
> https://github.com/jimmyliao/agentic-social-kit
> #GoogleAntigravity #AgenticArchitect

**小紅書 (ZH)**
> 如果讓 AI 分身自己社交，但每一步都先過一道「安全閘」會怎樣？我用 Google Antigravity
> SDK 做了 The Mixer：5 個 AI persona 自主社交，但每次互動都被 policy 治理——核准/降級/需同意。
> 治理才是主角。🎥 https://github.com/jimmyliao/agentic-social-kit
> #GoogleAntigravity #AgenticArchitect
