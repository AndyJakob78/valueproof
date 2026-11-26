# Example: a customer-service chatbot

An illustrative example of how to apply the method to a typical service chatbot. **The numbers are an estimate from assumptions, not a measurement — and an upper estimate:** they assume the small model handles most turns well enough, which you must test, and they leave out prompt caching. Use them to see where the money goes, then measure your own feature.

## The setup today

An online shop runs a chatbot for orders, returns, delivery and billing. Answers must be right: a wrong refund rule or delivery promise costs money and trust. So every turn of every chat goes to the strongest model, **Claude Opus 5.5**, together with the shop's policy documents and the chat so far.

**Assumptions:**

| | |
|---|---|
| Chats per month | 100,000 |
| Customer messages per chat | 5 → **500,000 turns a month** |
| Text the model reads per turn | 5,000 tokens (instructions + policy excerpts + chat history) |
| Text the model writes per turn | 300 tokens |
| Prices (per million tokens, in / out) | Opus 5.5: $4 / $20 · Sonnet 5.5: $2 / $10 · Haiku 5.5: $0.10 / $0.50 |

**Cost today:** 5,000 × $4 + 300 × $20 per million = **2.6 cents per turn** → $13,000 a month → **$156,000 a year**.

## The same chatbot, split into steps

| Step | What it does | Model | Cost per turn |
|---|---|---|---|
| 1. Understand | Reads the message, finds the topic (return, delivery, billing) and pulls out the order number | Haiku 5.5 | 0.02 ¢ |
| 2. Answer | **Scout & Rescue:** Haiku 5.5 drafts the answer; Opus 5.5 answers again only if a check in code rejects the draft | Haiku 5.5 → Opus 5.5 when needed | 0.07 ¢ + 2.6 ¢ for each rescued turn |
| 3. Summarize | One summary of the day's chats for the support team, instead of one per chat | Sonnet 5.5, once a day | 11 ¢ a day |

**Checks in code that send a draft to the rescuer:**
- The answer doesn't name the order number the customer gave.
- It quotes no policy section from the documents it was given (for refund, return or billing questions).
- It contains "I'm not sure", "I can't", or a placeholder.
- The customer is writing about the same problem for the third time, or asks for a human — then the strong model takes the turn.

## What it saves

The main unknown is how often the rescuer runs. Three cases:

| How often Opus is needed | Cost per turn | Cost per year | Saved per year |
|---|---|---|---|
| Today (Opus for every turn) | 2.6 ¢ | $156,000 | — |
| 1 in 10 turns | 0.34 ¢ | $20,600 | **$135,400 (−87%)** |
| 1 in 5 turns | 0.60 ¢ | $36,200 | **$119,800 (−77%)** |
| 2 in 5 turns | 1.12 ¢ | $67,400 | **$88,600 (−57%)** |

Even when the strong model is still needed for 40% of turns, the estimated cost falls by more than half, because routine turns cost about **40 times less** on the small model.

Prompt caching would lower both "before" and "after", since the instructions and policy documents repeat in every turn. It is left out here to keep the comparison simple — but it helps the expensive "before" setup most, so the real saving would be smaller than shown.

**What the checks cannot catch:** an answer that names the right order and quotes a policy section, but applies the policy wrongly. For refunds, billing and anything with legal weight, test those cases by hand in the blind review — and if the small model gets them wrong, route those topics straight to the strong model.

## How to prove it before you ship

1. **Pick 50–100 real chats** from your logs, including the hard ones: angry customers, mixed issues, unusual refund cases.
2. **Run both setups at the same moment** on those chats.
3. **Review blind:** a reviewer scores each answer pair, labelled only A and B — correct, follows policy, polite, solves the problem.
4. **Count the hard failures separately:** wrong policy, invented promise, no answer. One of these matters more than a cent saved.
5. **Log how often the rescuer runs.** That rate decides your real saving — see the table above.

Keep the split only if quality holds. If it doesn't, the checks are usually what needs work, not the model.

**What a real test showed:** we ran the answer step on 40 made-up support tickets. Scout & Rescue cost 81–88% less than Opus 5.5 alone and scored 2–6% lower in a blind review; one cheap reply promised a refund the policy didn't allow, and no check caught it. → [Support test](support-test.md)

→ Runnable code for a support-ticket version of this: [examples/demo_support.py](../examples/demo_support.py) · The full method: [method.md](method.md)
