# Measured: an AI-written article in a game

A second real test, on a different kind of feature: a game writes a short German newspaper article after each match day from a fact sheet the game builds. A cheap model is **already** in use. The question was whether a strong model — as a rescuer, or on its own — is worth paying for.

**In one sentence:** the rescuer never ran, because the cheap model passed every check; the strong model alone cost 18× more and wrote somewhat better text, but the blind review found fact errors in both that **no check caught**. The answer here is: keep the cheap model, and put the effort into better checks.

Only aggregate numbers are published. The article texts and fact sheets come from a private save game and stay private.

## The setup

- **The feature:** Claude Haiku 5.5 (effort low, thinking off) writes the article from a fact sheet. Checks in code reject an article that contains a number not in the fact sheet, a real-world club name, or a wrong result word. On a rejection the game tries once more; if that fails too, the reader gets a template article built by code.
- **Test set:** 12 fact sheets from one long-running save, each run in 3 rounds — 36 articles per setup. The setup used the game's own prompt, checks and 10-second time limit, and changed nothing in the game.
- **Paired:** the three Haiku setups share the first Haiku call per article.
- **Blind review:** Claude Opus 5.5 scored every distinct article against its fact sheet — facts, readability, tone, content, 10 points each — without seeing the setup, and flagged articles that contradict the fact sheet or invent something essential.

| Setup | What happens after a rejection |
|---|---|
| **Today** | Haiku once more, then the template |
| Sonnet as rescuer | Sonnet 5.5 (effort low, thinking off), then the template |
| Haiku, one attempt | the template straight away |
| Sonnet alone | Sonnet for every article, two attempts, then the template |

## Results

| Setup | Avg cost per article | Median | Avg time | AI text shown | Quality per AI article | Flagged for fact errors |
|---|---|---|---|---|---|---|
| **Today** | 0.075 ¢ | 0.068 ¢ | 4.6 s | 36 of 36 | 22.1 / 40 | 17 of 36 |
| Sonnet as rescuer | same — never triggered | | | | | |
| Haiku, one attempt | same — never needed | | | | | |
| Sonnet alone | 1.33 ¢ (**18×**) | 1.48 ¢ | 10.8 s | 30 of 36 | 25.0 / 40 (+13%) | 18 of 30 |

**Cost per outcome** (AI text shown, not flagged by the reviewer): 0.14 ¢ today (19 of 36) vs. 3.98 ¢ for Sonnet alone (12 of 36) — 28× more per outcome. With a strict reviewer, read the outcome counts as a lower bound.

Cost per round: 0.075–0.076 ¢ for today's setup, 1.19–1.47 ¢ for Sonnet alone. The reviewer cost $1.17 and is not in the table.

## What it means

1. **The cheap model passed every check on the first try** — 36 of 36. So the second attempt and the rescuer cost nothing here, and also added nothing. Scout & Rescue only spends money when a check fires.
2. **The strong model isn't worth it for this feature.** Its articles scored 13% higher, but it cost 18× more, took more than twice as long, and ran past the 10-second limit in 13 calls — so 6 of 36 readers got the plainer template. Counting those, its lead shrinks to 3%.
3. **The checks miss the errors that matter.** The reviewer flagged about half of the articles from both models, mostly misread form lines (a loss described as a draw) and invented claims. The code checks test numbers, names and result words, so none of these were caught.

**Read with care:** the reviewer was strict — it also counted missing facts, and it marked the template down for figures the game does supply. Treat the flag count as "worth a look", not as an error rate, until a person has checked a sample by hand.

## The lesson

The same as in the [support test](support-test.md), from the other side: **the checks decide the quality, and the rescuer only helps where a check fires.** Before paying for a stronger model, write a check for the most common mistake — here, a check that the article's description of recent form matches the fact sheet.
