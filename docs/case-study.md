# Case study: the news search in a language-learning app

## The product

The product is a language-learning app that turns a current story from the learner's own topics and places into a short reading lesson — in several languages, at the learner's level, with vocabulary and a quiz. Each lesson starts with an AI step that **searches the web for one fresh, true story**, followed by steps that write the lesson.

## The problem

The search step was the most expensive part of every lesson: about **$0.10 per search**, roughly half the cost of a whole lesson, run by a large model (Claude Sonnet 5.5) with web search. For a small app with a subscription of a few dollars a month, every lesson a free user reads is paid for out of pocket. The goal: **cut that cost without the learner noticing** — the same freshness, the same trust in the facts, no extra waiting, and never a lesson that fails to appear.

## Step 1 — Where the money went

One search, broken down (large model, advanced search tool):

| Part | Share |
|---|---|
| Storing the text the model reads (search results, opened pages, instructions) | ~42% |
| Search fees ($0.01 per query, ~3 queries) | ~26% |
| Re-reading that text at every step of the search loop | ~16% |
| Writing, including thinking | ~16% |

The team's first idea — "fewer searches" — targeted only a quarter of the cost.

## Step 2 — The levers and the ledger

Fixed test set: 9 requests (3 per course: big cities and topics), later 18 (adding 9 small towns), plus 6 targeted cases for rare problems. Every lever was run **at the same moment** as its baseline and judged **blind**. One run of 9 varies by about ±10%.

| # | Lever | Estimate before | Measured cost | Speed | Blind quality | Verdict |
|---|---|---|---|---|---|---|
| 1 | Less reasoning ("thinking") in the search step | 20–30% cheaper | **+11%** | ≈ | 206 vs 228 | ✗ Planned worse, searched more |
| 2 | Shorter search prompt | 10–15% cheaper | **+35%** | 9 s slower | 242 vs 228 | ✗ Better stories, but searched harder |
| 3 | Never open full pages, snippets only | ~10% cheaper | **+21%** | 4 s slower | 229 vs 230 | ✗ Searched more to make up for it |
| 4 | Simpler search tool (no result filtering) | unclear | **+43%** | **42% faster** | 231 vs 226 | ✗ as a saving — raw results are costly to store on a big model |
| 4b | Simpler tool **+ small model (Haiku)** | ~$0.03–0.04 | **−68%** | 40% faster | 211 vs 219 | ◐ Cheap and fast, but once found nothing |
| 4c | 4b first, big model as **safety net** (Scout & Rescue), 18 requests | — | **−25% avg, −75% median** | ≈ | 461 vs 436 | ✓ |
| 4d | **Town rule**: small towns may use stories up to 30 days old if still current (owner's idea) | fewer fallbacks | **−54%** on 9 towns | 33% faster | 221 vs 217 | ✓ |
| F1 | "Contact details are not facts" + one cheap follow-up for thin stories | no extra cost | ≈ (never fired) | ≈ | 460 vs 456 | ✓ kept: free safety rule |
| F2/F4 | No guessed descriptions of names; name source disagreements and keep them out of the lesson | no extra cost | ≈ | ≈ | hand-checked: 4 of 6 conflicts handled | ✓ kept, partial |
| F3 | Small town without the topic: switch openly to local life | no extra cost | ≈ | ≈ | lost both cases where it fired | ✗ |
| F3b | Same, but try the surrounding area first | no extra cost | ≈ | ≈ | 458 vs 468 | ✗ The search already widens on its own |
| L | "Lean" safety net (rescuer only when nothing at all is found) | cheaper | −22% vs 4c | 4 s faster | 440 vs 470 | ✗ Kept stale stories |

## Step 3 — The combined test against production

All accepted levers switched on together, against **the code running in production**, same 18 requests, same moment:

| | Production | New setup |
|---|---|---|
| Cost per search, average | $0.097 | **$0.046 (−53%)** |
| Cost per search, median | $0.092 | **$0.026 (−71%)** |
| Speed | 34 s | 34 s |
| No answer | 0 | 0 |
| Blind quality (max 540) | 434 | **472** |

A second side-by-side compared the new setup with lever 4b alone, which had looked fastest in its first test. Typical search: the new setup was faster and cheaper (13.8 s · $0.026 vs 16.3 s · $0.038); on average 4b alone was cheaper because the rescuer sometimes runs — but 4b alone left one learner without a lesson. Quality was level (437 vs 429).

**A human blind check (November 2026):** the product owner compared 14 pairs of German articles blind, the cheaper search against the previous one, each followed by the same writing steps. They preferred the cheaper search's article 6 times and the previous one's 7 times; 1 was equal. That is a tie, and it supports the AI review's finding that quality held. One reviewer and 14 pairs: a direction, not a rate.

## What shipped

- **Scout & Rescue**: the small model with the simpler search tool tries first; the big model with the full tool runs only if the scout returns nothing usable or only an old story.
- **Town rule** for places picked down to town level.
- **Fact rules**: contact details are not facts; names keep the source's words; disagreements between sources are named and left out of the lesson.
- Every rule behind a switch with an off position; the rescuer rate is logged.

## Before this work, in the same week

Two earlier experiments shaped the approach:

- **Searching in the place's own language** (Japanese for Japan, German for Germany) instead of English won a blind test 153 vs 131 — better sources, fresher stories.
- **A small model for the writing step** was cheaper per call but slower and worse (blind 201 vs 213), and saved only ~30% of a lesson's cost because the search dominated. That pointed the work at the search.
- A first small-model search test had been **dismissed because of a price assumption that was 10× too high** — corrected here, it became the winning lever.

## Still open

- When two sources disagree and the search does not notice, details can still mix (one wildlife story combined "hunters" from one source with "September" from another).
- Very small towns sometimes have no current story at all; the search then widens to the area or uses an older one.
