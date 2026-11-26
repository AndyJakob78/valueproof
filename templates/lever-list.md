# Lever list — template

Fill this in before running any test.

## 1. What must stay good

> One paragraph: what the feature must keep doing for users. What would make them notice a change?

- Quality must: …
- Speed must not get worse than: …
- Never acceptable (hard failures): …

## 2. Where the money goes (one typical call)

| Part | Tokens / units | Price | Cost | Share |
|---|---|---|---|---|
| Tool fees (searches, retrievals, …) | | | | |
| Storing what the model reads (input / cache write) | | | | |
| Re-reading in loops (cache read) | | | | |
| Writing (output, incl. reasoning) | | | | |
| **Total** | | | | 100% |

Prices checked against the provider's current price list on: ____

## 3. Levers

| # | Lever (one change) | Targets which part | Estimate before testing | Risk to quality | Test switch |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

Ideas to consider: smaller model · less reasoning effort · shorter prompt · fewer tool calls · different tool version · caching · skipping a step · doing work only when a user will see it · a cheap model first with a strong fallback (Scout & Rescue) · domain rules from the product owner.

## 4. Fixed test set

| # | Request | Why it is in the set (easy / hard / feared case / market) |
|---|---|---|
| 1 | | |

Targeted cases for rare problems: …
