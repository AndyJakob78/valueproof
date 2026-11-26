# Blind review — rubric and reviewer prompt

## How to prepare the pairs

1. Run baseline and lever on the same requests at the same moment.
2. For each request, put the two outputs into one file as **A** and **B**, swapped at random. Keep the key (which side is which) in a separate file.
3. Give the reviewer only the pairs file, never the key or your hypothesis.
4. Map the scores back with the key afterwards.

## Rubric (0–5 each, 30 per side)

Adapt the six criteria to your feature; keep them **fixed for the whole project**.

| # | Criterion | 5 means | 0 means |
|---|---|---|---|
| 1 | Freshness / timeliness | Current, inside the allowed window | Outdated or already over |
| 2 | Fit to the request | Exactly what was asked, for the right place / user / context | Off-topic or wrong place |
| 3 | Substance | Concrete facts that carry the answer | Filler, contact details, generic text |
| 4 | Source quality | Original or official source, real outlet | Blog, aggregator, listing, unknown |
| 5 | Trust | Nothing guessed, invented or contradictory | Invented details or unresolved contradictions |
| 6 | Value to the user | Useful and engaging for the actual user | Dull or useless |

A side with **no output** scores 0 — and counts as a hard failure.

## Reviewer prompt (adapt the first paragraph)

```
You are a blind reviewer for <product>. Each <output> is used to <purpose>.

Read <pairs file>. It has N items, each with a request and two results, A and B.
A null side found nothing: score it 0. Today is <date>.

Judge only from the file; do not look anything up.

For each of A and B, score 0–5 on:
1. <criterion 1>; 2. <criterion 2>; 3. <criterion 3>;
4. <criterion 4>; 5. <criterion 5>; 6. <criterion 6>.

Total per side: 30. Pick a winner per item (or tie) with a very short reason.

Reply with one compact table (item, A, B, winner, reason), then the sums of A and B,
then any item where something looks invented or contradictory.
Don't guess which method produced which side.
```

## Reading the result

- Report: sum per side, wins / losses / ties, hard failures.
- Read the flagged problems — they often matter more than the totals.
- Differences of a few points out of hundreds are noise; look at the items where one side lost badly.
