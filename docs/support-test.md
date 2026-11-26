# Measured: Scout & Rescue on support replies

A live test of the Scout & Rescue code in [examples/](../examples/), against the strong model alone, on made-up support tickets. Two runs, November 2026.

**In one sentence:** Scout & Rescue cost **81–88% less** than Claude Opus 5.5 alone and scored **2–6% lower** in a blind review. It is a much stronger cost lever than tuning the strong model, but **expect some loss of quality**: the cheap model's replies that pass the checks are good, but not always as good as the strong model's, and a few wrong policy statements got through.

## The setup

- **The task:** write a 3–6 sentence reply to a support ticket, following a 7-rule shop policy (damage, late delivery, double charge, invoices, returns, escalation, no vouchers).
- **Tickets:** 20 routine ones in run 1; the same 20 plus 20 harder ones in run 2 (several issues at once, edge cases of the policy, threats of legal action, no order number).
- **Checks in code** that send a draft to the rescuer: length, mentions the order number (or asks for it and invents none), cites every policy section the ticket needs, no promised voucher, discount or date, hands over to a colleague where the policy says so.
- **Paired in time:** every ticket ran through every setup before the next ticket started. The Scout & Rescue setups share one scout call per ticket, so they differ only in what happens after a rejection.
- **Blind review:** Claude Opus 5.5 scored each distinct reply on a fixed rubric — policy correct, solves the issue, tone, clarity, 10 points each — without seeing which setup wrote it. Hard failures (a wrong policy rule, a promise the policy doesn't allow, an invented order number, no answer) are counted separately.

| Setup | What it is |
|---|---|
| **Scout & Rescue** (published) | Haiku 5.5 (effort low) writes; Opus 5.5 (effort medium) rewrites only if a check fails |
| Rescuer at low effort | Same, Opus at effort low |
| Handoff | Same as published, and the rescuer also sees the rejected draft and why it failed |
| Opus low alone | Opus 5.5 at effort low for every ticket |
| Opus medium alone | Opus 5.5 at effort medium for every ticket — the "before" setup |

## Results

**Run 1** — 20 tickets, quality out of 800:

| Setup | Avg cost per reply | vs. published | Rescued | Avg time | Quality | Hard failures |
|---|---|---|---|---|---|---|
| Scout & Rescue (published) | 0.143 ¢ | — | 3 of 20 | 2.5 s | 679 | 0 |
| Rescuer at low effort | 0.108 ¢ | **−25%** | 3 of 20 | 2.4 s | 677 | 0 |
| Handoff | 0.161 ¢ | +12% | 3 of 20 | 2.5 s | 677 | 0 |
| Opus low alone | 0.534 ¢ | +272% | — | 2.3 s | 683 | 1 |
| Opus medium alone | 0.755 ¢ | +426% | — | 3.2 s | 693 | 1 |

**Run 2** — 40 tickets (20 harder), quality out of 1,600:

| Setup | Avg cost per reply | vs. published | Rescued | Avg time | Quality | Hard failures |
|---|---|---|---|---|---|---|
| Scout & Rescue (published) | 0.108 ¢ | — | 4 of 40 | 2.9 s | 1,300 | 3 |
| Rescuer at low effort | 0.082 ¢ | **−24%** | 4 of 40 | 2.7 s | 1,304 | 3 |
| Opus low alone | 0.550 ¢ | +411% | — | 2.4 s | 1,380 | 1 |
| Opus medium alone | 0.916 ¢ | +752% | — | 4.1 s | 1,380 | 2 |

Costs are the reply step only, at the API prices in [claude.py](../src/mixed_model_cost/claude.py); the reviewer's own cost is not included. Raw results: [run 1](data/support-test-run1.json) · [run 2](data/support-test-run2.json).

## What it means

### 1. Scout & Rescue: much cheaper, a little lower quality

| | Scout & Rescue | Opus medium alone |
|---|---|---|
| Cost per reply | **81–88% less** | — |
| Quality (blind review) | **2–6% lower** | — |
| Time per reply | 22–29% faster | — |
| Hard failures, run 2 | 3 of 40 | 2 of 40 |

**Why quality is lower:** the rescuer only runs when a check fails — here on 3–4 of 20 tickets. The other replies come from the cheap model. Most are good, but some are weaker in ways a check in code doesn't see: one ignored the customer's refund request, another asked again for a photo on the customer's third message.

**The hard failures:** on one ticket the cheap model said a parcel was over 10 days late — the ticket didn't say so — and promised a shipping refund. The checks didn't catch it. The other two were the same mistake about the trace rule that Opus also made, which points to the policy wording more than the model.

**Even the harder tickets rarely triggered the rescuer** (2 of 20). The cheap model passes the checks on tricky cases too. So the lever for quality is **the checks**, not the rescuer: a reply is only rescued if a check catches its mistake.

**Read with care:** the reviewer is Opus 5.5, the same model as the "alone" setups, and may favour its own style — the real gap may be smaller. The same ticket was rescued in one run and passed in the other, so results vary between runs. We did not measure that variance.

### 2. Rescuer at low effort: keep it (for tasks like this)

- **24–25% cheaper in both runs**, with the same number of rescues.
- Quality on the 7 rescued tickets across both runs: 247 vs. 245 for medium effort.
- The strong model alone points the same way: Opus at low effort scored 2,063 vs. 2,073 at medium (0.5% lower over 60 tickets) and cost 29–40% less.

**Limits:** only 7 rescued tickets, and these are short replies. Effort may matter more for long reasoning — test it on your task.

### 3. Handoff: rejected

Giving the rescuer the scout's rejected draft and the reason **cost 12% more** (it reads more text) and scored the same or 1 point lower on the 3 rescued tickets. It stays in the code as an option, off by default.

## When the trade-off is worth it

- **Worth it:** high volume, mostly routine requests, and a few percent of quality is acceptable — or your checks catch the mistakes that matter.
- **Not worth it as-is:** refunds, money, legal or medical answers where one wrong rule is expensive. Write a check for that mistake first, or send those topics straight to the strong model.

## Run it yourself

```bash
pip install "ai-mixed-model-cost-optimization[claude] @ git+https://github.com/AndyJakob78/ai-mixed-model-cost-optimization"
mmco compare examples/test_levers_support.py --live --hard
```

About $2–3 per run with all setups, including the reviewer. Without `--live` it runs on stub models to check the wiring, at no cost. Replace the policy, tickets and checks with your own — see [examples/README.md](../examples/README.md).
