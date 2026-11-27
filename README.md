# Valueproof

**Prove an AI cost cut before you ship it. Measure cost per usable outcome, not cost per token.**

If you work on an AI product, you probably get two questions:

- "What is the value of it, and how do you prove it?"
- "Our token cost needs to go down, but we can't sacrifice the quality of outcomes."

The two sides often work apart. Engineering and FinOps bring token cost down; product managers worry that quality gets sacrificed. When an eval fails, it goes back to engineering, who often don't know what outcome is expected.

Valueproof is a playbook and a small open-source Python package that connects both ends:

- **An LLM cascade.** A cheap model answers first. A frontier model steps in only when the answer fails an eval check at runtime. The technique is not new ([FrugalGPT](https://github.com/stanford-futuredata/FrugalGPT)); this repo calls it *Scout & Rescue*.
- **Choose the eval check first, then the model.** In our test, the check decided the quality more than the choice of model did.
- **The eval check is owned by product.** Rules in code catch form (empty, missing order number). An eval check in plain language catches substance: a cheap model reads the answer against the source that defines "right", such as the refund policy, the price list or the tone-of-voice guide.
- **Every change is tested before it ships,** on a fixed set of your own real requests (taken from your logs), against what you run today, with a blind review by an LLM judge or a person.
- **The eval check itself is measured:** what it caught, what it missed, how many false alarms, what it cost.
- **The metric is cost per usable outcome,** with failed and rescued attempts counted.

## What we measured

**In short: same cheap model, different eval check, different result.** With rules in code as the check, a person reading blind preferred the frontier model's reply on 16 of 20 tickets. With an eval check in plain language that product owns, the same cheap model was as good or better on 13 of 20, and still about 70% cheaper. One task and one reviewer, so read it as a direction, not a rule.

**Support replies:** 40 made-up support tickets, five runs, against Claude Opus 5.5 alone. Claude Haiku 5.5 answers first, Opus rescues.

| Setup | Cost per usable reply | Quality, LLM judge | Quality, blind human check (20 tickets) | Serious mistakes |
|---|---|---|---|---|
| Code rules as the eval check | **82–92% cheaper** | 2–6% lower | Opus preferred on **16 of 20** | the code rules caught **0 of 10** (four runs) |
| + an eval check in plain language | **69–73% cheaper** | 3.5–4.9% lower | **as good or better on 13 of 20** | caught the one in its run; 2 of 20 still slipped through |
| + a mid-size model as the rescuer (one run) | 87% cheaper | 5% lower | not checked | none occurred in that run |

What it shows:

- **Code rules alone are not enough.** They are free, but they can't see a wrong policy statement. A person reading blind preferred the frontier model almost every time.
- **The eval check in plain language closes most of the gap.** It is one more call on every reply: about twice the cost of code rules, still about 70% cheaper than Opus alone, but 10–35% slower than Opus alone.
- **Levers win the speed back.** A mid-size model as the rescuer was as fast as Opus alone and 87% cheaper; checking only the topics product marks as high-risk was faster still. One run each, not yet checked by a person.
- **It still missed one kind of mistake twice:** offering a carrier trace for a parcel that had already arrived. That is the next line for whoever owns the check to add.
- **Check the judge too.** The LLM judge and the person agreed on only one of the three real mistakes the person found with code rules alone.

→ [Full support test](https://github.com/AndyJakob78/valueproof/blob/main/docs/support-test.md), with the lever ledger, check ratings and raw data.

**A live language-learning app:** the step that searches the web for a news story ran on Claude Sonnet 5.5 for every lesson, at 9.7 ¢ per article. With Haiku first and Sonnet only when a code check finds no usable or only an old story, it cost **4.6–7.7 ¢** across runs. An LLM judge scored 18 articles 472 vs 434 for the cheaper setup. A person compared 14 German article pairs blind: 6 for the cheaper search, 7 for the old one, 1 equal, which is a tie. Here the cheap model only finds the story; a strong model still writes the lesson. → [Case study](https://github.com/AndyJakob78/valueproof/blob/main/docs/case-study.md)

**Twelve cost ideas, tested one at a time:** 7 made things worse or saved nothing. A shorter prompt made the model search *more*. → [Lessons](https://github.com/AndyJakob78/valueproof/blob/main/docs/lessons.md)

## Quick start

```bash
pip install "valueproof[claude]"      # or [openai], [gemini], [all]
```

```python
from valueproof import scout_and_rescue
from valueproof.claude import claude

ticket = "Where is my order 48213?"
out = scout_and_rescue(
    "Reply to this support ticket: " + ticket,
    scout=claude("claude-haiku-5-5"),      # the cheap model answers first
    rescue=claude("claude-opus-5-5"),      # the frontier model runs only if the check fails
    check=lambda text: None if "48213" in text else "order number missing",
)
print(out.path, out.cost_usd)              # "scout" or "rescue", and what it cost
```

A check returns `None` when the answer is fine, or a reason when it is not. It can be a rule in code, as here, or a call to a cheap model with your policy; see the [support test example](https://github.com/AndyJakob78/valueproof/blob/main/examples/test_levers_support.py).

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
