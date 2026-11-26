# Changelog

## 0.6.0
- **Check quality** in `valueproof compare`: when a judge ran, the output shows how the eval checks did against it, over every distinct reply: hard failures caught and missed, false alarms, and how many clearly weaker replies a check flagged. Also as `check_quality(report, setups)`.
- **Lever ledger**: add `"levers": {setup: {"baseline": other_setup, "estimate": "..."}}` to your test file and `valueproof compare` prints each lever against the setup it changes, with your estimate and a keep-or-drop verdict, and writes `ledger.md`. Also as `lever_ledger(...)`.
- **`--from-results FILE`**: show a saved run again (table, ledger) and rate new checks on its replies without running the models.
- **Rate candidate eval checks**: add `"checks": {name: fn(case, text)}` to your test file and `valueproof compare` tries each on every distinct reply and rates it against the judge (caught, missed, false alarms, cost per check). A check that calls a model returns `(reason, cost_usd)`. Also as `rate_checks(...)`.
- The bundled support test has a "Haiku alone, no rescuer" setup, to show what the rescuer adds.
- The support test also has a policy check done by a model ("S&R + policy check (Haiku)") and `--rate-checks`.
- Docs: third support run (the cheap model alone was nearly as good), the check-quality finding, and the term "eval check".

## 0.5.0
- **`--max-spend USD`**: stops starting new requests once runs (and reviews) have spent this much. A request in progress is finished, so results stay paired; the review is skipped if it would pass the limit.
- **`--estimate`** (with `--sample N`, default 2): runs a small sample for real and prints the projected cost of the full run. It spends a little on purpose: a real call is the only reliable price.
- **Why results were rejected**: after the table, the check rules that fired most often, for the first try and the final result, plus the first-try pass rate. `Run(..., rejected_because=...)` carries the scout's reason; `Score(..., cost_usd=...)` counts what the review cost.

## 0.4.0 — renamed to valueproof
- **One name for everything:** `pip install valueproof`, `import valueproof`, `valueproof compare`.
- The old names keep working until 1.0, with a deprecation note: `pip install ai-mixed-model-cost-optimization` now installs `valueproof`; `import mixed_model_cost` and the `mmco` command still work.
- `valueproof init` writes `valueproof_test.py` by default.

## 0.3.0
- **Cost per outcome** in `mmco compare`: everything a setup spent, including failed and rescued attempts, divided by the requests whose final result passed the check and had no hard failure. It is now the first column, and "vs base" compares it. Also available as `summarize(report, setups)` and `is_outcome(row)`.
- Docs: positioning around outcomes and value shipped (three layers), how this differs from routers, gateways and eval suites, and what to track after shipping.

## 0.2.1
- Docs only, so the PyPI page matches GitHub: version text, install / import / command names side by side, a compact method diagram. No code changes.

## 0.2.0
- **OpenAI and Gemini adapters** (`[openai]`, `[gemini]`, `[all]` extras; Gemini needs Python 3.11+). You pass the prices; Gemini thinking tokens count as output. Tested against fake clients shaped like the real SDK responses. Live check after release: the Gemini and Claude adapters made real calls, and a mixed Gemini/Claude Scout & Rescue ran; the OpenAI adapter has not yet been run live.
- **`mmco init`** writes a starter test that runs offline straight away; edit four marked parts to make it yours.
- Claude adapter: `prices=(in, out)` for models not in the price table; `client=` for tests.
- **Tests** (`pytest`, no keys, no cost) run on every push for Python 3.10-3.13, and before every release.

## 0.1.0
- First release: `scout_and_rescue`, `run_pipeline`, `mmco compare`, Claude adapter.
