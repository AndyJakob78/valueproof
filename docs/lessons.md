# Lessons

What the ledger taught, in order of how much it changed our decisions.

### 1. The system compensates
Most "obvious" savings moved the cost somewhere else instead of removing it. Less reasoning → worse plans → more searches. No full pages → fewer facts → more searches. A shorter prompt → less guidance → longer searching. **7 of 12 ideas made things worse or saved nothing.** Without measuring, all seven would have shipped as "optimisations".

### 2. Find the biggest cost part before having ideas
Everyone's first idea was "fewer web searches", which targeted about a quarter of the cost. The largest part was storing and re-reading the text the model works with. The winning lever (a small model) attacked exactly that part, because a small model reads text about 20× cheaper.

### 3. A tool's cost behaviour depends on the model using it
The simpler search tool stores raw results in full. On the big model that made it 43% more expensive; on the small model it was the cheapest option of all. **Test combinations, not just components.**

### 4. Pair every test in time
Provider speed and search results change during the day. Run the baseline and the lever **at the same moment**. Measure the noise by running the baseline twice. Our noise was about ±10%; anything smaller was ignored.

### 5. Blind judging beats opinion
The person who builds a change always likes it. A blind A/B review on a fixed rubric, with the labels mapped back only afterwards, settled every argument in this project, including two where the builder's favourite lost.

### 6. Medians and failures, not just averages
The cheapest setup on average once returned **no answer at all**. The average also hid that a typical request was much cheaper than the mean. Report the median, the average and the count of hard failures.

### 7. Write the estimate down first
Our pre-test estimates were wrong far more often than right ("20–30% cheaper" became 11% more expensive). Seeing that, lever after lever, built trust in measuring over guessing — for the engineer and the product owner alike.

### 8. Rare problems need targeted tests
Invented descriptions and sources that disagree showed up in about 1 of 18 requests — invisible in averages. A small set of targeted cases, checked by hand, was the only way to see whether a fix worked.

### 9. Check price assumptions
An earlier test dismissed the small model using a price that was 10× too high. Re-checking the current price list turned the "rejected" idea into the winner.

### 10. Ship the combination you tested
Levers interact. A rule that helped alone (switching topic openly) lost when the full setup already handled the case. Only the final combined run against production decides what ships.

### 11. Domain rules from the product owner can beat technical levers
The single most effective quality-and-cost change for small towns came from the product owner, not from engineering: *"for town stories, be more generous with freshness."* It halved the cost for small towns and kept quality. Product judgement belongs in the lever list.

### 12. An AI coding agent makes this method cheap
Every lever here was implemented, run, reviewed blind and written to the ledger by an AI coding agent, with the product owner deciding from a phone. Twelve levers, roughly 450 test searches and over a dozen blind reviews cost in the order of $40 in API fees, done in one working day.

## From the support test

### 13. The checks decide the quality
Scout & Rescue only fixes the mistakes a check catches. In our [support test](support-test.md) the rescuer ran on just 2 of 20 hard tickets, and one cheap reply that passed every check promised a refund the policy didn't allow. Put your effort into checks for the costly mistakes, not into a better rescuer.

### 14. Try lower effort before a smaller model
Running the strong model at effort low instead of medium cost 24–40% less with no measurable quality loss on short support replies. It is the cheapest lever to test, because nothing else in the setup changes.

### 15. More context for the rescuer is not free
Giving the rescuer the cheap model's rejected draft sounded smart. It cost 12% more and did not improve quality. Test "obvious" improvements like any other lever.

