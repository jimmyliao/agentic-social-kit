# Agentic Architect Sprint — 3 日連載社群宣傳文案

> 建議配圖：附上 `the-mixer.gif` 或是程式碼截圖。
> 統一導流網址：`https://memo.jimmyliao.net/p/agent`

---

## 🚀 Day 1 (今天發布)：點出痛點與發布預告 (對應〈前言〉)

### 🇹🇼 中文版 (FB 粉絲頁 / Threads)
當我們開始讓 AI Agent 彼此交談、自己組隊工作時，**誰在管它們？**

龍蝦/Moltbook/Hermes Agent 該玩的應該都差不多 (也沒話題了?)，這段時間應該是討論 AI Native / 數位分身是嗎？

不過在企業導入 AI 的現場，讓「人留在迴圈 (Human-in-the-loop)、Agent 留在邊界內」已經是顯學。上個月的工作坊，透過 Antigravity CLI/SDK，現場一起完成了 Harness Engineering 的初級體驗。而這次我們來手刻了一個真正能跑的 **「Agent 安全閘 (Safety Gate)」** 實作。

接下來連續幾天，會連載這套《Agent 治理三部曲》的實戰拆解。第一篇前言，來看看我們現在到底缺了哪一塊拼圖

🔗 系列總覽與第一集：https://memo.jimmyliao.net/p/agent
#GoogleAntigravity #AgenticAI #AgenticArchitect

### 🇬🇧 英文版 (LinkedIn)
When AI agents start talking to each other and delegating tasks—**who's in charge?**

The initial hype around open-source agents (like Moltbook or Hermes) has settled, and the conversation is shifting towards AI Native applications and Digital Twins.

But on the frontlines of enterprise AI adoption, the mandate is clear: "Keep humans in the loop, and agents in bounds." Following our workshop last month where we explored the basics of Harness Engineering using the Antigravity CLI/SDK, I’ve now built a truly runnable **"Agent Safety Gate"** implementation.

Over the next few days, I’ll be serializing a deep dive into this "Agentic Architect Trilogy." Part 1 is out today, looking at the missing puzzle piece in agent governance. Check it out 👇

🔗 Full series & repo: https://memo.jimmyliao.net/p/agent
#GoogleAntigravity #AgenticArchitect #SovereignAI

---

## 🚀 Day 2 (明天發布)：展示「那道閘」與對齊法規 (對應 Part 1)

### 🇹🇼 中文版 (FB 粉絲頁 / Threads)
如果讓 5 個 AI 分身自己社交，但每一步都必須過海關，會發生什麼事？🚦

昨天提到了 Agent 治理的痛點，今天直接上 Code。我開源了 **"The Mixer"** 專案，把安全規則寫成一道「宣告式」的閘。它不是藏在黑箱裡的 Prompt，而是攔截在每一次行動前的硬邊界。

最好玩的是，這道週末刻出來的閘，吐出的四個決策（APPROVE / DENY / DOWNGRADE / ASK_USER），竟然剛好完美對齊了**新加坡政府最新的 MGF 決策標準**！

不要再迷信「每一筆都讓人類按同意」的天真做法了，來看怎麼做到真正的 Governance-in-the-Loop 👇

🔗 Part 1 實戰拆解：https://memo.jimmyliao.net/p/agent
#GoogleAntigravity #AgenticArchitect 

### 🇬🇧 英文版 (LinkedIn)
Human-in-the-loop is not enough; it leads to consent fatigue. We need **Governance-in-the-loop**.

In Part 1 of my Agentic Architect series, I open-sourced **"The Mixer"**—a runnable multi-agent demo built on the Google Antigravity SDK. Every interaction must pass through a **Declarative Safety Gate** before execution.

The best part? The gate's routing decisions (APPROVE / DENY / DOWNGRADE / ASK_USER) map perfectly to **Singapore's IMDA Model Governance Framework (MGF)**. 

See how we can transform implicit guardrails into an explicit, auditable policy layer. 🎥👇

🔗 Read Part 1 & get the code: https://memo.jimmyliao.net/p/agent
#GoogleAntigravity #AIArchitecture #AgenticAI

---

## 🚀 Day 3 (後天發布)：自我修正的 Loop 與收尾 (對應 Part 2)

### 🇹🇼 中文版 (FB 粉絲頁 / Threads)
當 AI 提出一個「越界」的動作被擋下來時，它能自己學乖嗎？🔄

《Agent 治理三部曲》最終回！一道只會說 NO 的閘是不夠的，我們要把單次的判定，升級成一個**「會自我修正的迴圈」**。

在 Part 2 的實作中，我加入了一個 Verifier 子代理。當 AI 的動作被 DENY 時，它會自動產生 critique（反思）並注入記憶，讓 AI 在下一個回合自動提出一個「降級但更安全」的替代方案。

從淺層迴圈到懂得自我退讓的 Agentic Workflow，附上完整開源 Repo，週末趕快 clone 下來玩玩看👇

🔗 最終回與開源程式碼：https://memo.jimmyliao.net/p/agent
#GoogleAntigravity #AgenticArchitect #開源

### 🇬🇧 英文版 (LinkedIn)
A safety gate that only says "NO" is a bottleneck. What if the agent could learn from the rejection and propose a safer alternative? 🔄

In the finale of the Agentic Architect series, we upgrade our Declarative Safety Gate into a **Self-Correcting Loop**. By injecting a Verifier sub-agent, denied actions gracefully degrade—turning a blocked, high-risk request into a safer, approved alternative within a single turn.

Moving from a shallow loop to a goal-conditioned, self-correcting workflow is how we scale enterprise agents responsibly.

The full trilogy and the open-source repo are now live. Dive into the code this weekend! 👇

🔗 Finale & GitHub Repo: https://memo.jimmyliao.net/p/agent
#GoogleAntigravity #AgenticArchitect #SovereignAI
