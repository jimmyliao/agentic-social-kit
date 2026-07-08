# 🛰️ Agent 治理雷達 / Agent Governance Radar

![Agent 治理雷達](./radar-banner.svg)

> **2026-06-24 · Edition #1**
>
> 這是一份我每天人工策展的連結雷達，盯著一條主軸：**當人類把事情委派給 agent、agent 又彼此協同時，怎麼讓人留在迴圈裡、agent 留在邊界內。** 治理、法規、資安、人機協同的時事都收進來，每則配一兩句我自己的看法 — 不轉貼新聞稿，只給「所以呢 / 為什麼重要」。
>
> 🔁 本雷達**每天更新**。今天是第一期。

---

## 🔥 治理與法規 (Governance & Regulation)

**[Gartner：企業詢問 agentic AI 治理暴增 1,445%](https://www.gartner.com/en/newsroom/press-releases/2026-05-26-gartner-says-applying-uniform-governance-across-ai-agents-will-lead-to-enterprise-ai-agent-failure)**
不是大家突然有良心，是 agent 開始真的去動 production，出事了才想到要裝閘。同一份報告的真重點其實是：**「一刀切的統一治理一定失敗」** — 治理必須是 risk-based、宣告式的，不是全部都攔或全部都放。

**[EU AI Act 第 14 條 — high-risk AI 的人類監督](https://www.ishir.com/blog/329275/human-in-the-loop-is-not-enough-why-governance-in-the-loop-is-becoming-the-new-standard-for-ai-agent-risk-management.htm)**
**2026-08-02 全面生效**，這是硬期限不是建議。距今不到六週，「人留在迴圈」從架構口號變成合規義務 — 你的 agent 在 high-risk 場景沒有可稽核的人類介入點，就是裸奔上路。

**[Singapore IMDA — Model Governance Framework for Agentic AI](https://www.imda.gov.sg/-/media/imda/files/about/emerging-tech-and-research/artificial-intelligence/mgf-for-agentic-ai.pdf)**
新加坡把 agent 的決策詞彙標準化了：ALLOW / REQUIRE_HUMAN / CONSTRAIN / DENY / THROTTLE。值得讀，因為這正在變成**國家級的共通語言** — 你自己 gate 的 verdict 對得上這套，未來跨境就少打架。

**[Governance-in-the-Loop：為什麼 HITL 已經不夠](https://www.ishir.com/blog/329275/human-in-the-loop-is-not-enough-why-governance-in-the-loop-is-becoming-the-new-standard-for-ai-agent-risk-management.htm)**
天真版 human-in-the-loop 的死法叫 **consent fatigue** — 每個動作都要你按 yes，最後你反射性全按 yes，安全性反而下降。GITL 的解法是：低風險自動放行，只有高風險才升級給人。這才是宣告式、風險分級的治理。

**[Gartner：2027 年 40% 企業會把自主 agent 降級或下架](https://www.gartner.com/en/newsroom/press-releases/2026-05-26-gartner-says-applying-uniform-governance-across-ai-agents-will-lead-to-enterprise-ai-agent-failure)**
不是 agent 不行，是治理層沒補上。我的看法：先有 audit trail 和邊界，再談自主；順序反了，你就是那 40%。

---

## 🤖 Agent 亂象與資安 (When agents scale without a gate)

**[Moltbook 是什麼 — 一個只給 AI bot 用的社群網路（TIME 解說）](https://time.com/7364662/moltbook-ai-reddit-agents/)**
~150 萬個「自主」agent，背後只有 ~1.7 萬個真人。vibe coding 蓋出來、作者說自己「一行沒寫」。這是觀察 agent↔agent 大規模互動最赤裸的現場 — 沒有閘、沒有定義 scope，會變成什麼樣。

**[Fortune：「新網路如何崩壞的現場直播」](https://fortune.com/2026/02/03/moltbook-ai-social-network-security-researchers-agent-internet/)**
~19% 加密貨幣垃圾訊息、每 5 則有 1 則 toxic、主資料庫外洩 ~150 萬組 bot 憑證 + email + 私訊、ClawHub 上 14 個偽裝成工具的惡意 skill。這不是末日預言，是已經發生的事故報告。

**[SecurityScorecard：當 agentic AI 沒有 security 就 scale](https://securityscorecard.com/blog/what-are-moltbot-and-moltbook-and-what-happens-when-agentic-ai-assistants-scale-without-security/)**
一句話總結 Moltbook 教訓：**規模不是能力，沒有治理層的規模是放大器** — 放大 toxicity、放大洩漏、放大惡意。你不需要 150 萬個 agent 才看到這件事，幾個就夠。

---

## 🛰️ 蹭世界盃的 AI (AI riding the World Cup — lighter)

> ⚠️ 這一段是**預測/球迷服務賽道**，不是我們的治理主軸。看熱鬧，順便看別人怎麼把 AI 塞進熱點。

**[Google / Gemini 的世界盃球迷服務 + 生物辨識隱私角度](https://thenextweb.com/news/world-cup-2026-biometrics-google-gemini)**
大廠都想蹭世界盃流量，球迷體驗做得越沉浸，蒐集的生物辨識資料就越多 — fan-service 的另一面永遠是隱私帳單，看的時候記得問一句「資料去哪了」。

**[Willian Pinho：讓 Claude / GPT / Gemini 一起預測整屆世界盃](https://dev.to/willianpinho/i-made-claude-gpt-and-gemini-predict-the-entire-2026-world-cup-heres-the-experiment-design-2nm1)**
三模型對照、嚴格 Zod JSON、Brier 計分 — 實驗設計比預測結果好看。這條 multi-LLM benchmark 賽道已經有人做得很完整了，要跳進來得有差異化。

**[DataCamp：用古典 ML 預測世界盃冠軍](https://www.datacamp.com/tutorial/fifa-world-cup-2026-winner-prediction)**
10 個模型（XGBoost / Poisson / LSTM）+ 蒙地卡羅模擬。古典 ML 那條路也被教學文章鋪好了 — 印證一件事：**預測準度不是差異化點**，治理才是。

---

## 🎓 值得讀/看 (Worth your time)

**[李宏毅 — OpenClaw（小龍蝦）解剖](https://www.bilibili.com/video/BV1UqPQzXEmy/)**
想搞懂 Moltbook 那些 bot 到底怎麼運作，這是中文圈最好的入門 — 李宏毅把 OpenClaw（Moltbook 的引擎）拆開講 agent 內部機制。看完這條再回頭看上面的亂象，整條故事線就通了：**agent 能自主行動 → 沒護欄會怎樣 → 所以需要治理層。**

---

<sub>

## EN — Navigation

> **2026-06-24 · Edition #1** — A daily, hand-curated link radar on **Agent governance & human-AI collaboration**: keeping humans in the loop and agents in bounds. One opinionated take per item. Updates daily.

- 🔥 **Governance & Regulation** — Gartner +1,445% surge; EU AI Act Article 14 (full effect 2026-08-02); Singapore IMDA Model Governance Framework for Agentic AI; Governance-in-the-Loop; Gartner "uniform governance fails / 40% decommission by 2027".
- 🤖 **When agents scale without a gate** — Moltbook (TIME explainer; Fortune "live demo of how the internet could fail"; SecurityScorecard "scaling without security").
- 🛰️ **AI riding the World Cup (lighter)** — the prediction / fan lane, not our governance lane.
- 🎓 **Worth your time** — 李宏毅 / Hung-yi Lee dissecting OpenClaw as the zh on-ramp to agent internals.

</sub>
