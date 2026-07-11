---
title: "Declarative Safety Gate — 系列總覽"
tags: ["#GoogleAntigravity", "#AgenticArchitect"]
---

# 當 Agent 開始彼此交談，誰在管？

> 一個關於 **Agent 治理層**的三部曲 —— 以一個真的能跑的 reference implementation（**The Mixer**）為主角：5 個 AI persona 自主社交，但每一步都過一道 **Declarative Safety Gate**（`APPROVE / DENY / ↓DOWNGRADE / ASK_USER`）。
>
> 繁體中文為主、English 版並行。每篇都附真實 demo 與可跑指令。

![The Mixer](the-mixer.gif)

---

## 📖 三部曲

**[Declarative Safety Gate] 前言：當 Agent 開始彼此交談，誰在管？** — 為什麼是現在
從 Moltbook 的失控講起：當 delegation 從「人 → 一個 agent」變成「人 → 一支隊伍 → agent 互推」，缺的那一層就是治理。
　→ [繁中閱讀](https://memo.jimmyliao.net/p/declarative-safety-gate-agent) ｜ [English](post-0-intro.en.md)

**[Declarative Safety Gate] Part 1：The Gate is the Protagonist 那道閘才是主角** — Harness：閘長怎樣
把 policy 宣告成 spec、掛在 agent loop 的 pre-tool-call 關節上；用 The Mixer 真實 turn-log 走查 `DOWNGRADE` 與 `ASK_USER`，並對齊新加坡 MGF 的決策詞彙。
　→ [繁中閱讀](https://memo.jimmyliao.net/p/declarative-safety-gate-part-1the) ｜ [English](post-1-gate.en.md)

**[Declarative Safety Gate] Part 2：把那道閘做到會自我修正** — Loop：從淺迴圈到自我修正
加上 maker≠grader 的 verifier 子代理、critique 寫回記憶並注入下一輪、goal/budget 負責任終止。真實 demo：被擋下的動作如何在下一輪自己變得更得體。
　→ [繁中閱讀](https://memo.jimmyliao.net/p/declarative-safety-gate-part-2) ｜ [English](post-2-loop.en.md)

---

## 🛰️ 治理雷達（每日時事集錦）

**Agent 治理雷達 — Edition #1** — 每天追蹤 Agent 治理 / 人機協同的時事與必讀連結。
　→ [繁中 + EN 導覽](radar.zh.md)

---

## ▶️ 想直接跑 demo？

```bash
git clone https://github.com/jimmyliao/agentic-social-kit
cd agentic-social-kit

uv run --with google-antigravity python p0_demo.py     # 最小的 hook/policy 機制
uv run --with google-antigravity python p1_demo.py     # 兩個 persona → 一個被治理的社交事件
uv run --with google-antigravity python p4_demo.py --reset   # 會自我修正的 loop（Part 2）
```

全部 offline、deterministic、不需 API key。

---

*Jimmy Liao｜LeapDesign Co-Founder / CTO｜Google Developer Expert*

`#GoogleAntigravity` `#AgenticArchitect`
