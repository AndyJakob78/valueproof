"""Claude adapter: turns a Claude model into a `Model` function for
scout_rescue and pipeline. Other providers need only a function with the
same shape (prompt in, ModelResult out).

Requires: pip install "ai-mixed-model-cost-optimization[claude]" (or anthropic), and credentials (ANTHROPIC_API_KEY or `ant auth login`).
"""

from __future__ import annotations

from .scout_rescue import Model, ModelResult

# USD per million tokens: (input, output). Prices change - check the current
# price list before you trust any cost number. Haiku 5.5 price is for prompts
# up to 100K tokens. Cache discounts are ignored here for simplicity.
PRICES = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
}

# These models support server-side refusal fallbacks; we turn them on so a
# rare policy decline is retried on a suitable model instead of returning nothing.
_FALLBACK_MODELS = {"claude-opus-5-5", "claude-sonnet-5-5"}

_client = None


def _get_client():
    global _client
    if _client is None:
        import anthropic

        _client = anthropic.Anthropic()
    return _client


def claude(
    model: str,
    effort: str = "low",
    system: str | None = None,
    max_tokens: int = 16000,
    prices: tuple[float, float] | None = None,
    client=None,
) -> Model:
    """Return a Model function for one Claude model at one effort level.

    `prices` = (input, output) in USD per million tokens; needed for models not in PRICES.
    """
    if prices is None and model not in PRICES:
        raise ValueError(f"No price for {model!r}: pass prices=(input, output) in USD per million tokens.")
    price_in, price_out = prices or PRICES[model]

    def call(prompt: str) -> ModelResult:
        kwargs = dict(
            model=model,
            max_tokens=max_tokens,
            output_config={"effort": effort},
            messages=[{"role": "user", "content": prompt}],
        )
        if system:
            kwargs["system"] = system

        api = client or _get_client()
        if model in _FALLBACK_MODELS:
            response = api.beta.messages.create(
                betas=["server-side-fallback-2026-07-01"], fallbacks="default", **kwargs
            )
        else:
            response = api.messages.create(**kwargs)

        # A refusal returns no usable text; the check will treat "" as a failure.
        if response.stop_reason == "refusal":
            text = ""
        else:
            text = "".join(block.text for block in response.content if block.type == "text")

        usage = response.usage
        cost = (usage.input_tokens * price_in + usage.output_tokens * price_out) / 1_000_000
        return ModelResult(text=text, cost_usd=cost, model=model)

    return call
