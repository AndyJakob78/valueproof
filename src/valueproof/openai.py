"""OpenAI adapter: turns an OpenAI model into a `Model` function (Responses API).

Requires: pip install "valueproof[openai]", and OPENAI_API_KEY.

    from valueproof.openai import openai_model
    cheap = openai_model("<model id>", price_in=..., price_out=..., effort="low")

Prices are USD per million tokens and must be passed in: they change often, so
copy them from the provider's current price list. Reasoning tokens are part of
`output_tokens` and billed as output. Cache discounts are ignored for simplicity.
"""

from __future__ import annotations

from typing import Optional

from .scout_rescue import Model, ModelResult

_client = None


def _get_client():
    global _client
    if _client is None:
        import openai

        _client = openai.OpenAI()
    return _client


def openai_model(
    model: str,
    price_in: float,
    price_out: float,
    effort: Optional[str] = None,
    instructions: Optional[str] = None,
    max_output_tokens: int = 16000,
    client=None,
) -> Model:
    """Return a Model function for one OpenAI model. `effort` sets reasoning effort, if the model supports it."""

    def call(prompt: str) -> ModelResult:
        kwargs = dict(model=model, input=prompt, max_output_tokens=max_output_tokens)
        if effort:
            kwargs["reasoning"] = {"effort": effort}
        if instructions:
            kwargs["instructions"] = instructions
        response = (client or _get_client()).responses.create(**kwargs)

        # An incomplete or refused answer still returns whatever text there is;
        # your check decides whether it is usable.
        text = response.output_text or ""
        usage = response.usage
        cost = (usage.input_tokens * price_in + usage.output_tokens * price_out) / 1_000_000 if usage else 0.0
        return ModelResult(text=text, cost_usd=cost, model=model)

    return call
