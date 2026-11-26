# Changelog

## 0.2.1
- Docs only, so the PyPI page matches GitHub: version text, install / import / command names side by side, a compact method diagram. No code changes.

## 0.2.0
- **OpenAI and Gemini adapters** (`[openai]`, `[gemini]`, `[all]` extras; Gemini needs Python 3.11+). You pass the prices; Gemini thinking tokens count as output. Tested against fake clients shaped like the real SDK responses. Live check after release: the Gemini and Claude adapters made real calls, and a mixed Gemini/Claude Scout & Rescue ran; the OpenAI adapter has not yet been run live.
- **`mmco init`** writes a starter test that runs offline straight away; edit four marked parts to make it yours.
- Claude adapter: `prices=(in, out)` for models not in the price table; `client=` for tests.
- **Tests** (`pytest`, no keys, no cost) run on every push for Python 3.10-3.13, and before every release.

## 0.1.0
- First release: `scout_and_rescue`, `run_pipeline`, `mmco compare`, Claude adapter.
