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

---

## 決策紀錄（怎麼走到今天這個狀態）

依時間序，這個 repo 從「私有 WIP」變成「public GDE 投稿」經過這些明確決策點——**每一個都是 Jimmy 明確拍板，不是 agent 自己決定的**：

1. **No-confidential-content review**（review 全 repo：client 名、私有資料、第三方設計）→ PASS，
   唯一問題：舊 commit history 裡藏著 client 名 "NTU"。
2. **修法方式選 2**：整個 history squash 成單一 commit（非逐 commit 手術式清除）。
   舊 11-commit history 保留在本機分支 `master-old-history-backup`（未 push，僅本機備份，未刪除）。
3. **確認執行 squash + force-push** → `origin/master` 變成單一 root commit `429ec0a`。
4. **確認翻牌 public** → `gh repo edit jimmyliao/agentic-social-kit --visibility public --accept-visibility-change-consequences`（2026-07-08）。
5. **決定發文平台**：Medium（Google Cloud group publication，英文）＋ Jimmy 自己的 Substack
   `memo.jimmyliao.net`（中文）。
6. **決定內容結構**：捨棄舊的單篇 `docs/blog-draft.md`（3-paradigm 框架，沒收錄 P4 self-correcting
   loop），改用現有的三部曲系列（`docs/posts/post-0/1/2-*.md`）—— Medium 英文拆 3 篇分開發，
   Substack 中文版整套對應翻譯。
7. **抓到並修正一個真的 bug**：英文版三篇 posts 引用的圖是**中文標籤的 SVG**（i18n 沒做完整，
   只翻了文字沒翻圖）。已補 `intro-gap.en.svg` / `gate-flow.en.svg` / `loop-cycle.en.svg` 並改
   `.en.md` 的圖片引用（commit `3917455`）。
8. **補上 repo 連結**：`docs/HANDOFF.md` 內的 GitHub repo 連結填入（commit `09818e4`，
   Publishing gate 標記為 CLEARED）。注意這**不是** `docs/posts/social-teaser.md` 裡的 `[LINK]`——
   那個指向的是 Substack 首篇文章網址，要等 Jimmy 手動貼完 Substack 才能填。

**沒有自動化發文能力**：Substack 無官方 API（非官方寫入需 session cookie，有 ToS 風險）；
Medium 沒有可用憑證。素材已備好放在 scratchpad（Medium-EN 用 `.png`，Substack-ZH 用 `.png`），
但**實際上稿是 Jimmy 手動做**，agent 能做的是準備好逐字稿/圖檔/checklist。

---

## 跨 agent 接手（agy / codex / 新開的 Claude session）

任何 agent 接手這個 repo 的收尾工作，**先讀完這份 `docs/HANDOFF.md`**——這是唯一持續維護的
狀態文件，跟 git commit 同步更新，比 `git log` 多了「為什麼」的脈絡。跨 session 的完整版
index 另外存在 `~/.agents/personal/projects/gde-agentic-architect-sprint.md`（含 memory 連結）。

**非互動呼叫範例（agy）：**
```bash
cd ~/workspace/personal/agentic-social-kit
agy -p "$(cat docs/HANDOFF.md)

你現在接手這個 repo。目前唯一剩下的工作是：
1. Medium（英文，3 篇，post-0/1/2-en.md）與 Substack（中文，3 篇，post-0/1/2-zh.md）手動上稿
   —— 這兩個平台都沒有可用的發文 API，你能做的是整理好逐字稿+圖檔清單，不要嘗試自動發文。
2. Advocu activity log：跑 ~/.agents/personal/projects/blog/advocu-sync.py
   （預設 dry-run，--post 才真的送出，token 在 ~/workspace/.env 的 ADVOCU=）。
先做 dry-run 回報結果，不要加 --post。"
```

**非互動呼叫範例（codex，適合純程式碼/文字產出類任務，例如重新轉一批圖）：**
```bash
codex exec "cd ~/workspace/personal/agentic-social-kit && \
把 docs/posts/*.svg 全部轉成同名 .png（uv run --with cairosvg），輸出到 /tmp 給我看清單"
```

**安全邊界（跨 agent 一律遵守，寫在最上面那條 Scope 也是同一件事）：**
- 這是**通用、無機密**的 GDE 貢獻，不可把任何私有專案（PetCircle/HISP/LISOC/client 名）內容寫進來。
- 破壞性 git 操作（squash / force-push / push 到 default branch）**每次都要重新明確跟 Jimmy 確認**，
  不可用之前某一輪的簡短回覆當作默許（即使是同一個 repo、同一個晚上）。
- 上 public、上稿發佈，都是 Jimmy 的決定，agent 不可自行執行。
