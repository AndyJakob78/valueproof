# Pattern: Scout & Rescue

**A cheap model tries first. A strong model steps in only when a check in code says the cheap answer is not good enough.**

## How it works

```
request ──► SCOUT (small, cheap model, lean tools)
                │
        code checks the answer
        (anything usable? enough facts? fresh enough?)
                │
        ┌───────┴────────┐
      passes            fails
        │                 │
     answer          RESCUER (strong model, full tools)
                          │
                       answer
```

- The **scout** handles the typical request at a fraction of the price.
- The **checks are code, not another model call** — free and instant: "did it return anything?", "at least 6 facts?", "is the newest source inside the allowed time window?".
- The **rescuer** is the setup you trusted before. It only runs when needed, so the worst case is never worse than before — just slower and as expensive as before.

In research this family of designs is called an **LLM cascade** (see FrugalGPT, Chen et al.). Scout & Rescue is a practical version of it: the decision to escalate is a plain check in code, not a model's confidence score or another model call.

## Results in the case study

Same 18 requests, run at the same moment, blind review:

| | Strong model only (before) | Scout only | Scout & Rescue |
|---|---|---|---|
| Typical cost (median) | $0.092 | $0.038 | **$0.026** |
| Average cost | $0.097 | **$0.044** | $0.046–0.077 * |
| Requests with no answer | 0 | 1 | **0** |
| Blind quality | 434 / 540 | 429 / 540 ** | **437–472 / 540** ** |

\* Depends on how often the rescuer runs: 2 to 5 times in 18 across runs.
\** Scored in different paired runs; compare within a row only as a rough guide.

## Results in a support test

On 40 made-up support tickets, Scout & Rescue (Haiku 5.5 → Opus 5.5) cost 81–92% less than Opus 5.5 alone and scored 2–6% lower in a blind review. The quality cost comes from cheap replies that pass the checks but are weaker than the strong model's. Running the rescuer at effort low saved another 24–25% with no measurable loss. In a third run, the cheap model alone was nearly as good: the rescuer ran on 2 of 40 tickets. → [Support test](support-test.md)

## When it fits

- Most requests are **routine**, a minority are **hard**.
- A failure can be **detected by code** (empty result, too few items, wrong date, schema violation).
- The cheap path's typical answer is **as good** as the strong one's — check this blind, it often is.
- A **missing answer is unacceptable**, so a scout alone is not an option.

## When it does not fit

- Failures are subtle and only a human or a strong model can spot them — then the check itself costs a strong call.
- The rescuer is needed for most requests — then you pay twice.
- Latency is critical *and* the rescuer runs often — the fallback path is slow (scout time + rescuer time).

## Tuning lessons

- **Don't make the rescuer lazier to save money.** A "lean rescuer" that accepted the scout's stale results was 22% cheaper but clearly worse (440 vs 470).
- **Let the scout use the cheap tool variant.** A small model with a simpler tool beat the small model with the advanced tool, because the advanced tool's extra steps cost more than they saved.
- **Use the checks to log.** Record which path ran; the rescuer rate is your main cost driver over time.
- **A tool's price model matters more than the model's.** With the simpler search tool, raw results were stored in full — expensive on the big model (+43%), cheap on the small one. The same tool choice was wrong for one model and right for the other.
