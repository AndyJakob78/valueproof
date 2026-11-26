# Changelog

## 0.4.0 — renamed to costproof
- **One name for everything:** `pip install costproof`, `import costproof`, `costproof compare`.
- The old names keep working until 1.0, with a deprecation note: `pip install ai-mixed-model-cost-optimization` now installs `costproof`; `import mixed_model_cost` and the `mmco` command still work.
- `costproof init` writes `costproof_test.py` by default.

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
