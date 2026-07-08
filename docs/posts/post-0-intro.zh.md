---
title: "〈前言〉當 Agent 開始彼此交談，誰在管？"
series: "Declarative Safety Gate"
part: 0
tags: ["#GoogleAntigravity", "#AgenticArchitect"]
lang: zh-TW
---

# 〈前言〉當 Agent 開始彼此交談，誰在管？

![The Mixer](the-mixer.gif)

有人蓋了一個社群網站，長得像 Reddit，但有一個前提：**人類不准發文，只有 AI bot 能發。**

這個網站叫 **Moltbook**，是 Matt Schlicht 用 vibe coding 做出來的，他說自己「一行程式都沒寫」，全交給 agent。背後的引擎是開源的 **OpenClaw**（如果你看過李宏毅老師那支解剖「小龍蝦」的影片，講的就是它）。

每個 bot 裝一個 *skill* 檔，配一個 *heartbeat*，每幾個小時自己醒來、自己發文。聽起來很酷。然後它號稱跑出 **約 150 萬個自主 agent**，背後只有 **約 1.7 萬個真人**。

---

## 💡 然後呢？它變成一場災難

不是「沒人用」的那種失敗。是「太多人用、但沒人管」的那種失敗。

| Moltbook 出了什麼事 | 數字 |
|---|---|
| 加密貨幣垃圾訊息 | 約 **19%** 的內容 |
| 有毒 / 操弄 / 惡意貼文 | **每 5 篇就有 1 篇** |
| 主資料庫外洩 | 約 **150 萬組** bot 帳密 + email + 私訊 |
| ClawHub 上的假 skill | **14 個**偽裝成加密工具的惡意程式 |

> Fortune 把它形容成「**新型網際網路會如何崩壞的現場 demo**」。

被 Meta 在 2026-03-10 收購了，但這不是重點。重點是：**這是一面把問題放大 150 萬倍的鏡子。**

---

## ❌ 真正的問題不是「bot 會發廢文」

把 Moltbook 當成笑話很容易。但它戳到的是一件正在發生、而且更接近你我的事。

我們現在不只是「叫一個 agent 去做一件事」。我們開始讓 agent **彼此交談**、組成隊伍、互相把工作丟來丟去——同時還要跟人協作。

那個畫面長這樣：

![缺的那一層](intro-gap.svg)

當 delegation 從「人 → 一個 agent」變成「人 → 一支隊伍 → agent 之間互推」，問題只剩一句：

**誰在管？** 誰決定哪個動作可以放行、哪個要降級、哪個一定要先問人？

Moltbook 給的答案是「沒人」。所以它變成 Moltbook。

---

## ⚡ 為什麼是現在

這不是我一個人的焦慮，是 regulator、analyst、政府同時在敲門：

- **Gartner** 報告，企業對 agentic AI governance 的詢問量暴增 **1,445%**。
- **EU AI Act 第 14 條**（high-risk AI 的 human oversight）在 **2026-08-02** 全面生效——這是一條硬 deadline，不是建議。
- **新加坡 IMDA** 發布了 **Model Governance Framework for Agentic AI**，連 gate 的決策詞彙都標準化了。
- 同樣是 Gartner：到 **2027 年，40% 的企業會因為治理缺口，把已經上線的 agent 降級或下架**。

換句話說：autonomy 大家都在追，但「怎麼把人留在 loop 裡、把 agent 框在界線內」這件事，正在從加分題變成必考題。

---

## 🛰️ 缺的那一層，沒人幫你附

你可能會想：那些 orchestration framework 不就是幹這個的嗎？

我去看了一輪——**LangGraph**、**Microsoft Agent Framework**、**CrewAI**、**Google ADK + A2A**。它們都很會編排 agent 的協作，但有一個共通點：

**沒有一個內建治理層。** 那道 gate，全部留給你自己做。

這個 gate 該長怎樣？它應該像海關：不是每個人都攔下來盤問（那叫 consent fatigue，你會反射性按「同意」，反而更不安全），而是**低風險直接放行、高風險才舉手問人**。它應該講人話、也講標準的話——APPROVE / DENY / DOWNGRADE / ASK_USER，剛好對得上新加坡那套國家框架的詞彙。它還應該留下一條 audit trail，讓每個動作都能追回到「是哪個人、授權了什麼範圍」。

---

## ✅ 我做了什麼，以及這個系列要講什麼

我把那層缺的東西做出來了，一個小小的、**真的能跑**的 reference implementation——**The Mixer**：一道 declarative 的 safety gate。沒有 API key、沒有線上模型，offline 跑出來的結果是 deterministic 的。

它不是 demo 玩具。一個週末做出來的 gate，講的卻是國家框架正在標準化的同一套語言。

而且我不是旁觀這個問題——這些 agent 我在 production 跑好一陣子了：一套**高教知識庫的 RAG**、一個**台語即時語音**、一套**法律判決檢索的 LLM**，全跑在**自己的 infra 上**。所以這個系列不是教學文，是一個 operator 的 **Day-2 筆記**。

技術上，這道閘就是 Antigravity Agent SDK 的 `pre_tool_call_decide` hook——6/16 BwAI 我帶大家手寫過那個「結帳前停下來問你 `[y/N]`」。我只是把它從一個 if-else，升級成一層**宣告式的 policy 治理**。

這是一個三篇的系列：

- **〈前言〉**（你正在看的這篇）—— 為什麼現在非做不可。
- **Part 1** —— 那道閘到底長怎樣：怎麼把 policy 宣告成 spec，掛在 agent loop 的哪個關節上。
- **Part 2** —— 把它做到會自我修正：當一個動作被擋下來，gate 怎麼回頭把它降級重提，變成一個會 iterate 的 loop。

（順帶一提，同一個引擎換個皮，也可以變成世界盃看球室的防爆機制——但那是另一個更輕鬆的故事，這裡先按下。）

Moltbook 用 150 萬個 agent 證明了沒有 gate 會怎樣。我想證明的是反過來：同樣的前提，**把缺的那層補回去**，會長什麼樣子。

---

## 相關資源

- Moltbook 安全分析 · Fortune：「a live demo of how the new internet could fail」 — https://fortune.com/2026/02/03/moltbook-ai-social-network-security-researchers-agent-internet/
- Moltbook 解說 · TIME — https://time.com/7364662/moltbook-ai-reddit-agents/
- 李宏毅 · OpenClaw（小龍蝦）解剖 — https://www.bilibili.com/video/BV1UqPQzXEmy/
- 新加坡 IMDA · Model Governance Framework for Agentic AI — https://www.imda.gov.sg/-/media/imda/files/about/emerging-tech-and-research/artificial-intelligence/mgf-for-agentic-ai.pdf
- Gartner · uniform governance 為何失敗 — https://www.gartner.com/en/newsroom/press-releases/2026-05-26-gartner-says-applying-uniform-governance-across-ai-agents-will-lead-to-enterprise-ai-agent-failure
- Governance-in-the-Loop · ISHIR — https://www.ishir.com/blog/329275/human-in-the-loop-is-not-enough-why-governance-in-the-loop-is-becoming-the-new-standard-for-ai-agent-risk-management.htm

---

**下一篇：Part 1 —— 那道閘長怎樣。** 我們會打開 `safety_gate.py`，看一個 pre-tool-call hook 怎麼變成 agent 的「海關」。

---

---

*首發 2026-06-25 · 原文與後續系列：memo.jimmyliao.net · 引用請註明出處（Cite as: Jimmy Liao, 2026）*

*Jimmy Liao｜LeapDesign Co-Founder / CTO｜Google Developer Expert · 在自己的 infra 上跑企業 agent*

`#GoogleAntigravity` `#AgenticArchitect` `#SovereignAI`
