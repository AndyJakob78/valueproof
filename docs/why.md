# Why this exists

Background for the [README](../README.md): who it is for, what it measures, and the signals behind it.

## Target audience

| Role | What you get |
|---|---|
| **Product Manager** | A way to cut AI cost per user with evidence, and to defend every keep-or-drop decision |
| **System Designer** | A pattern for splitting one AI job into steps, each with the right model |
| **AI Engineer** | A small Python package: Scout & Rescue, multi-model pipelines, and a test runner (`valueproof compare`) |
| **Prompt & Context Engineer** | A test routine that shows whether a prompt change really saves tokens — or quietly costs more |
| **AI Builder** | A way to test cheaper setups for an AI app on a small budget, and keep only those that hold quality |
| **AI Evaluation** | A blind review (LLM-as-judge or a person) on a fixed rubric, plus a measure of how good your eval checks are |
| **LLMOps** | Code checks and logging that track how often the expensive model runs |
| **FinOps** | A clear before-and-after cost per request, and the yearly saving at your scale |

## What this measures

Most cost tools stop at the first row. This method measures the second before you ship, and tells you how to track the third after.

| Layer | The question | Who asks it | Where it is measured |
|---|---|---|---|
| Model output | What does a token cost? How fast is the model? | Engineers | Price lists, benchmarks |
| **Outcome** (before shipping) | Did the user get a usable, correct result — and what did that result cost, including failed attempts? | Product, engineering | **The eval: `valueproof compare` on your own requests** |
| **Value shipped** (after shipping) | How much margin did we bank per user, without more complaints, escalations or refunds? | CFO, VP Product | Ship behind a switch, keep measuring — [method, step 9](method.md#step-9--ship-behind-a-switch-keep-measuring) |

**The eval proves you won't break the product. The switch and the ledger prove the margin you banked.**

## The problem

Some AI features cannot afford a weak answer. **Compliance, regulation or safety** may demand it — a wrong fact in a financial, medical or legal answer is a real risk. Or the **user experience** depends on it — one confidently wrong answer and users stop trusting the product.

So teams do the safe thing: **one strong model does the whole job, end to end, for every request.** Quality is high. But:
- **You pay top price for easy work.** Most requests are routine and don't need the strongest model. They are still billed at its rate.
- **The cost grows with every user.** At scale, a request can cost more than it earns.
- **The usual fixes put quality at risk.** "Switch to a smaller model" or "shorten the prompt" may save money, or may quietly lower quality, or may even raise cost. Without a test, you can't tell.

**What this method can and cannot do:** it saves money on the requests where a cheap model's mistakes can be caught by an eval check. Rules in code catch form: an empty result, a missing field, an old date, an invalid format. They do **not** catch an answer that looks right but is wrong, such as a plausible but false refund rule. An eval check in plain language, run by a cheap model with the policy as its reference, catches some of those ([support test](support-test.md)), but not all. Where such errors carry legal or safety risk, measure your check before you rely on it, or keep that step on the strong model.

## Real-world signals (2026)

**AI cost is squeezing companies:**
- **Harvey** (legal AI): in March it updated its AI agents, and customers began using them far more — token use grew about 20× during the year. Harvey mostly charges customers a fixed price per seat but pays the model providers per token, so its gross margin reportedly fell from about **+50% to −50%** by June: serving customers cost about $1.50 for every $1 of revenue. In August it moved its flagship to its own model built on an open-weight model, and margins reportedly turned positive again. [Bloomberg](https://www.bloomberg.com/news/articles/2026-09-21/startups-like-harvey-embrace-open-models-to-cut-reliance-on-anthropic-openai) · [Artificial Lawyer](https://artificiallawyer.com/2026/07/08/harvey-increases-token-use-14x-in-just-6-months)
- **Industry survey** (Mavvrik, a cost-management vendor, with Benchmarkit; 396 companies, April–May 2026):
  - **62%** say an unexpected AI cost changed a business decision in the past year. Of those, 40% had to escalate it to the board, 33% froze spending, and 25% delayed or cancelled an AI project.
  - **49%** had to raise prices of their AI products because costs rose more than expected.
  - Only **11%** can forecast their AI spend within ±10% (down from 15% in 2025).
  - **43%** name token costs as a top source of surprise spend. Agents are a growing blind spot: almost all companies run them, but only about a third include them in cost reports.
  - [Channel Insider](https://www.channelinsider.com/ai/mavvrik-state-of-ai-cost-governance/) · [CFO Dive](https://cfodive.com/news/1-in-4-companies-delay-cancel-ai-projects-over-cost/827524) · [Diginomica](https://diginomica.com/tokenomics-ai-bill-shock-goes-mainstream-key-cost-driver-becomes-task-complexity)

**And when an AI answer is wrong, courts hold the company liable:**
- **Hamm, Germany (May 2026):** a clinic's website chatbot invented specialist titles for its doctors. The Higher Regional Court held the clinic responsible — even though the bot had been trained on correct data and was run by an IT provider. Switching the bot off was not enough; the clinic also had to sign a cease-and-desist declaration. Not yet final: an appeal to the Federal Court of Justice is allowed. [Court press release (German)](https://www.justiz.nrw/presse/2026-05-12) · [DLA Piper](https://www.dlapiper.com/en/insights/publications/2026/06/german-court-addresses-liability)
- **Munich, Germany (May 2026):** Google's AI Overviews made false claims about two publishers that did not appear in the linked sources. The Regional Court of Munich treated the AI summary as Google's own statement and barred Google from repeating it, with fines of up to €250,000 per violation. Not yet final. [Court press release (German)](https://www.justiz.bayern.de/gerichte-und-behoerden/landgericht/muenchen-1/presse/2026/13.php) · [The Decoder](https://the-decoder.com/landmark-german-ruling-declares-googles-ai-overviews-are-googles-own-words-and-makes-it-liable-for-false-answers/)

The lesson: cut cost **and** prove quality, one change at a time — with tests on real requests, not just offline benchmarks.

## An estimate: a service chatbot (estimate)

An online shop's chatbot sends every turn to Claude Opus 5.5: **2.6 cents per turn, about $156,000 a year** at 500,000 turns a month. Split into steps — Haiku 5.5 to understand the message, Scout & Rescue (Haiku first, Opus only when a check rejects the draft) to answer, and Sonnet 5.5 for one daily summary:

| How often Opus is still needed | Cost per year | Saved |
|---|---|---|
| 1 in 5 turns | $36,200 | **$119,800 (−77%)** |
| 2 in 5 turns | $67,400 | **$88,600 (−57%)** |

These numbers come from assumptions, not a measurement, and are an upper estimate: they leave out prompt caching, which would make the "before" setup cheaper and the saving smaller. → [Full chatbot example, with the checks and how to prove it](example-service-chatbot.md)
