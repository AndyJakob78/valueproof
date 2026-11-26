"""Gemini adapter: turns a Google Gemini model into a `Model` function.

Requires: pip install "ai-mixed-model-cost-optimization[gemini]", and GEMINI_API_KEY.

    from mixed_model_cost.gemini import gemini_model
    cheap = gemini_model("<model id>", price_in=..., price_out=..., thinking_level="low")

Prices are USD per million tokens and must be passed in: they change often, so
copy them from the provider's current price list. Thinking tokens are billed as
output and counted here. Cache discounts are ignored for simplicity.
"""

from __future__ import annotations

from typing import Optional

from .scout_rescue import Model, ModelResult

_client = None


def _get_client():
    global _client
    if _client is None:
        from google import genai

        _client = genai.Client()
    return _client


def gemini_model(
    model: str,
    price_in: float,
    price_out: float,
    thinking_level: Optional[str] = None,
    system: Optional[str] = None,
    max_output_tokens: int = 16000,
    client=None,
) -> Model:
    """Return a Model function for one Gemini model. `thinking_level`: "minimal", "low", "medium" or "high"."""

    def call(prompt: str) -> ModelResult:
        from google.genai import types

        config = types.GenerateContentConfig(
            max_output_tokens=max_output_tokens,
            system_instruction=system,
            thinking_config=types.ThinkingConfig(thinking_level=thinking_level.upper()) if thinking_level else None,
        )
        response = (client or _get_client()).models.generate_content(model=model, contents=prompt, config=config)

        # A blocked answer has no text; the check will treat "" as a failure.
        text = response.text or ""
        u = response.usage_metadata
        tokens_in = (u.prompt_token_count or 0) if u else 0
        tokens_out = ((u.candidates_token_count or 0) + (u.thoughts_token_count or 0)) if u else 0
        cost = (tokens_in * price_in + tokens_out * price_out) / 1_000_000
        return ModelResult(text=text, cost_usd=cost, model=model)

    return call
