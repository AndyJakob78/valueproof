# Valueproof

**Prove an AI cost cut before you ship it. Measure cost per usable outcome, not cost per token.**

## Cheapest isn't the win

The same cheap model answered 40 support tickets twice, with two different eval checks. A frontier model stepped in whenever the check failed. Then a person compared 20 of the replies blind with the frontier model's own replies.

| | Eval check: rules in code only | Eval check: the PM's acceptance criteria, in plain language |
|---|---|---|
| **Replies as good as the frontier model's** (blind human review, 20 tickets) | ❌ **4 of 20** | ✅ **13 of 20** |
| **Serious mistakes that reached the customer** | 3 of 20 | 2 of 20 |
| **Cost vs. the frontier model alone** | 82–92% cheaper | 69–73% cheaper |
| **Verdict** | Biggest saving, worse outcomes: less value | **Higher value, for a somewhat smaller saving** |

Claude Haiku 5.5 answers first, Claude Opus 5.5 steps in; compared with Opus 5.5 alone. The check in plain language is one more call, so replies were 10–35% slower than Opus alone; a mid-size model as the rescuer made it as fast as Opus again (one run). **So choose the eval check first, then the model.**

Made-up tickets, one human reviewer: read it as a direction, not a rule. [Full results](#full-results)

## Two questions, two sides

If you work on an AI product, you probably get two questions:

- "What is the value of it, and how do you prove it?"
- "Our token cost needs to go down, but we can't sacrifice the quality of outcomes."

The two sides often work apart. Engineering and FinOps bring token cost down; product managers worry that quality gets sacrificed. When an eval fails, it goes back to engineering, who often don't know what outcome is expected.

## Acceptance criteria that run on every answer

**Today:** the PM writes acceptance criteria → engineering builds → a user acceptance test checks a sample, late → failures go back to engineering, who guess what "right" means.

**With an eval check:** the PM writes the acceptance criteria once, with the source that defines "right" → they run on every answer at runtime; an answer that fails goes to the frontier model before the user sees it → before shipping, a blind review measures how good the check is.

Each acceptance criterion becomes two kinds of check, and most tasks need both:

| Use case | Your acceptance criterion | Becomes a rule in code (free, instant) | Becomes a check in plain language (a cheap model reads the answer against the source) |
|---|---|---|---|
| A **support chatbot** answers routine tickets | "A reply applies our refund policy correctly to this ticket." | The order number is in the reply; no voucher is offered | Is the right rule applied to *this* case? From our test: it offered a carrier trace for a parcel the customer had already received. |
| An app **writes a match report** after every game | "The report tells the match as it happened." | Score, teams and scorers match the match data | Does it invent quotes or events? |
| An AI **writes product descriptions** | "It sounds like our brand." | No word from the banned list; length within limits | Calm, friendly, no exaggerated claims? |
| An **in-car travel guide** tells stories along the route | "Stories are true, family-friendly and safe to hear while driving." | Every place is on the route and in the database; under 60 seconds read aloud | Do the facts match the database? Does it ever ask the driver to look away from the road? |

Two things to know:

- **The check in plain language has a price:** one more call on every answer, so about twice the cost of rules in code and 10–35% slower than the frontier model alone. A mid-size rescuer, or checking only the topics the PM marks as high-risk, won the speed back in our test.
- **The blind review doesn't go away; its job changes.** It now tests the check. Ours found a mistake the check had missed twice. Where a wrong answer can hurt someone, such as a vehicle warning or a medical or legal answer, don't let a model write it at all: show fixed, approved text.

## What Valueproof is

A playbook and a small open-source Python package:

- **An LLM cascade.** A cheap model answers first; a frontier model steps in only when the answer fails an eval check. The technique is not new ([FrugalGPT](https://github.com/stanford-futuredata/FrugalGPT)); this repo calls it *Scout & Rescue*.
- **A test before you ship:** your current setup against the cheaper one, on a fixed set of your own real requests (taken from your logs), with a blind review by an LLM judge or a person.
- **A measure of the check itself:** what it caught, what it missed, how many false alarms, what it cost.
- **Cost per usable outcome,** with failed and rescued attempts counted.

## Full results

**Support replies:** 40 made-up tickets, five runs, against Claude Opus 5.5 alone.

| Setup | As good as Opus (blind human review, 20 tickets) | Serious mistakes | Quality, LLM judge | Cost per usable reply | Response time vs. Opus alone |
|---|---|---|---|---|---|
| Rules in code as the eval check | ❌ 4 of 20 | the rules caught 0 of 10 (four runs) | 2–6% lower | 82–92% cheaper | 22–35% faster |
| + an eval check in plain language | ✅ 13 of 20 | caught the one in its run; 2 of 20 got past it in the human review | 3.5–4.9% lower | 69–73% cheaper | 10–35% slower |
| + a mid-size model as the rescuer (one run) | not checked by a person | none occurred in that run | 5% lower | 87% cheaper | about as fast |

- **The LLM judge looked kinder than the person.** "2–6% lower" sounded close; a person preferred the frontier model almost every time. The judge and the person agreed on only one of the three real mistakes the person found with rules in code alone. Check the judge too.
- **The mistake that got past the check twice:** offering a carrier trace for a parcel that had already arrived. That is the next line for the PM to add to the check.

→ [Full support test](https://github.com/AndyJakob78/valueproof/blob/main/docs/support-test.md), with the lever ledger, check ratings and raw data.

**A live language-learning app:** the step that searches the web for a news story ran on Claude Sonnet 5.5 for every lesson, at 9.7 ¢ per article. With Haiku first and Sonnet only when a code check finds no usable or only an old story, it cost **4.6–7.7 ¢**. Quality held: an LLM judge scored 18 articles 472 vs 434 for the cheaper setup, and a person comparing 14 German article pairs blind found a tie (6 for the cheaper search, 7 for the old one, 1 equal). Here the cheap model only finds the story; a strong model still writes the lesson. → [Case study](https://github.com/AndyJakob78/valueproof/blob/main/docs/case-study.md)

**Twelve cost ideas, tested one at a time:** 7 made things worse or saved nothing. A shorter prompt made the model search *more*. → [Lessons](https://github.com/AndyJakob78/valueproof/blob/main/docs/lessons.md)

## Quick start

```bash
pip install "valueproof[claude]"      # or [openai], [gemini], [all]
```

```python
from valueproof import scout_and_rescue
from valueproof.claude import claude

POLICY = open("refund_policy.md").read()          # the source that defines "right"
ticket = "Order 48213 arrived yesterday, but the box is damaged."
checker = claude("claude-haiku-5-5")                # a cheap model reads each reply against the policy

def check(reply):
    if "48213" not in reply:                        # rule in code: free and instant
        return "order number missing"
    verdict = checker(                              # check in plain language: one more cheap call
        f"Policy:\n{POLICY}\n\nTicket:\n{ticket}\n\nReply:\n{reply}\n\n"
        "Does the reply apply the policy correctly to this ticket, without assuming facts "
        "the ticket doesn't give? Answer OK, or NO and the reason."
    ).text
    return None if verdict.strip().startswith("OK") else verdict

out = scout_and_rescue(
    f"Reply to this support ticket, following this policy:\n{POLICY}\n\nTicket: {ticket}",
    scout=claude("claude-haiku-5-5"),               # the cheap model answers first
    rescue=claude("claude-opus-5-5"),               # the frontier model runs only if the check fails
    check=check,
)
print(out.path, out.cost_usd)                       # "scout" or "rescue", and what the answers cost
```

A check returns `None` when the answer is fine, or a reason when it is not. Start with the rules in code, and add the check in plain language where a wrong answer is not acceptable. `out.cost_usd` covers the answers; the check's own cost comes on top (about 0.02 ¢ per reply in our test). The [support test example](https://github.com/AndyJakob78/valueproof/blob/main/examples/test_levers_support.py) counts it, and caches it.

## Test a change before you ship it

```bash
valueproof init my_test.py                          # a starter test that runs straight away, with fake models
valueproof compare my_test.py                       # offline, free
valueproof compare my_test.py --live --estimate     # runs 2 requests for real and prints the projected bill
valueproof compare my_test.py --live --max-spend 5  # the full test; stops starting new requests at $5
```

`compare` runs every setup on every request in the same moment and prints:

- **cost per usable outcome**, average and median cost, time, and how often the frontier model ran
- **blind-review quality**, with hard failures counted separately so no average can hide them
- **check quality:** how many of the judge's hard failures each eval check caught, missed, and how many false alarms it raised
- **the lever ledger:** each change against the setup it changes, your estimate written down before the test, and a keep-or-drop verdict

To rate a new eval check on replies you already paid for, without running the models again: `--from-results results.json`.

**Blind review, two ways.** An LLM judge gets one answer at a time, in random order, never the setup's name. Give it the reference that defines "right"; without it, a judge can only tell whether an answer looks usable. Or review it yourself: every run writes `blind_review.csv` and a separate `blind_key.csv`.

→ How to write `my_test.py`, and a demo that runs without an API key: [examples/](https://github.com/AndyJakob78/valueproof/tree/main/examples/) · The step-by-step method: [docs/method.md](https://github.com/AndyJakob78/valueproof/blob/main/docs/method.md)

## When it fits

It fits when your product sends many requests to a frontier model, most of them routine, and you can say what a usable answer is: support replies, data extraction, document summaries, search and research assistants, code review, code migration (does it compile, do the tests pass).

Be careful where a wrong answer carries legal, money or safety risk. Measure your eval check against a blind review first, or keep that step on the frontier model until the check catches the mistakes that matter.

## How this differs from other tools

| Tool | What it does | How it relates |
|---|---|---|
| [RouteLLM](https://github.com/lm-sys/RouteLLM) | Trained routers that pick a model per request | A routing technique. Test it against your setup with `valueproof compare`. |
| [cascadeflow](https://github.com/lemony-ai/cascadeflow) | A cascading runtime for agents | A runtime for production. Test it here first. |
| [LiteLLM](https://github.com/BerriAI/litellm) | A gateway to 100+ model APIs | Infrastructure to call models. Works as the model behind a setup here. |
| [promptfoo](https://github.com/promptfoo/promptfoo) | Broad testing of prompts, agents and RAG | A general eval suite. This repo is narrower. |

**Cost-first, not QA-first.** Eval suites such as promptfoo and Braintrust are built around quality regression and observability, and show cost alongside. Valueproof starts from the decision a product manager or CFO has to make: cost per usable outcome, an estimate before the test, and a keep-or-drop verdict after it. Use it to get evidence on your own requests before you commit to a router or gateway.

## More

- [Why this exists](https://github.com/AndyJakob78/valueproof/blob/main/docs/why.md): who it is for, cost per outcome vs value shipped, and real-world signals from 2026
- [Support test](https://github.com/AndyJakob78/valueproof/blob/main/docs/support-test.md) · [Case study](https://github.com/AndyJakob78/valueproof/blob/main/docs/case-study.md) · [Game article test](https://github.com/AndyJakob78/valueproof/blob/main/docs/game-article-test.md) · [A chatbot estimate](https://github.com/AndyJakob78/valueproof/blob/main/docs/example-service-chatbot.md)
- [Scout & Rescue in detail](https://github.com/AndyJakob78/valueproof/blob/main/docs/scout-and-rescue.md) · [Method](https://github.com/AndyJakob78/valueproof/blob/main/docs/method.md) · [Lessons](https://github.com/AndyJakob78/valueproof/blob/main/docs/lessons.md) · [Templates](https://github.com/AndyJakob78/valueproof/tree/main/templates/)

## Install

Version 0.6, early: the API may still change. Python 3.10+ (the Gemini adapter needs 3.11+). The core has no dependencies; a model is any function `prompt -> ModelResult`, so a local model works too. Adapters come as extras: `[claude]`, `[openai]`, `[gemini]`, `[all]`.

The old package name `ai-mixed-model-cost-optimization` still installs and pulls in `valueproof`.

## Terms

- **LLM cascade / Scout & Rescue:** a cheap model (the scout) answers first; a frontier model (the rescuer) runs only when the answer fails an eval check.
- **Eval check:** judges one answer at runtime and decides whether the rescuer runs. A rule in code, or a cheap model asked in plain language with a reference.
- **Eval:** the fixed test before shipping: real requests, the eval checks, and a blind review, run the same way for every change.
- **Blind review:** answers scored on a fixed rubric without knowing which setup wrote them, by an LLM judge or a person.
- **Hard failure / serious mistake:** a wrong policy rule, a promise the policy doesn't allow, an invented fact, or no answer.
- **Usable outcome:** a final answer that passed the checks and had no hard failure.
- **Cost per usable outcome:** everything a setup spent, failed and rescued attempts included, divided by its usable outcomes.
- **Lever:** one change meant to lower cost, tested on its own.

## About

Built from a real cost-reduction project on a live language-learning app. Engineering, testing and blind reviews were done with an AI coding assistant (Claude); a product owner made every keep-or-drop decision and did the human blind checks.

Text: [CC BY 4.0](https://github.com/AndyJakob78/valueproof/blob/main/LICENSE). Code in [src/](https://github.com/AndyJakob78/valueproof/tree/main/src/) and [examples/](https://github.com/AndyJakob78/valueproof/tree/main/examples/): [MIT](https://github.com/AndyJakob78/valueproof/blob/main/LICENSE-CODE).
