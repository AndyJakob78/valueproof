# Ledger — template

One card per lever. Rejected levers stay on the page.

**Noise level** (baseline run twice): cost ± __ %, time ± __ %
**Fixed test set:** N requests, listed in the lever list.

---

## Lever <#>: <name>

- **What changed:** …
- **Targets:** <cost part>
- **Estimate before testing:** …
- **Test switch:** `ENV_NAME=1`
- **Paired baseline:** <which setup>, run at the same moment

| | Baseline | Lever |
|---|---|---|
| Cost per call — average | | |
| Cost per call — median | | |
| Time — average | | |
| Time — median | | |
| Hard failures | | |
| Blind score (of N×30) | | |
| Wins / losses / ties | | |

**Verdict:** ✓ keep · ◐ keep with conditions · ✗ drop

> One paragraph in plain language: what happened, why, and what it means.

---

## Decision rules

Keep a lever only if:

1. its cost or speed gain is larger than the noise,
2. its blind score is not lower than the paired baseline (allow a few points),
3. it adds no hard failures.

A lever that costs nothing and showed no effect may be kept as a safety rule — say so.

Before shipping: switch all kept levers on together and run one final paired test against **production**.
