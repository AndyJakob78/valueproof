"""Adapters against fake SDK clients shaped like the real responses. No network, no key."""
from types import SimpleNamespace as NS

import pytest

from costproof.claude import claude
from costproof.gemini import gemini_model
from costproof.openai import openai_model


class Recorder:
    def __init__(self, response):
        self.response, self.kwargs = response, None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return self.response

    def generate_content(self, **kwargs):
        self.kwargs = kwargs
        return self.response


def test_claude_cost_text_and_effort():
    api = Recorder(NS(stop_reason="end_turn", content=[NS(type="text", text="hi")],
                      usage=NS(input_tokens=1000, output_tokens=200)))
    r = claude("claude-haiku-5-5", effort="low", client=NS(messages=api))("q")
    assert r.text == "hi" and abs(r.cost_usd - (1000 * 0.10 + 200 * 0.50) / 1e6) < 1e-15
    assert api.kwargs["output_config"] == {"effort": "low"}


def test_claude_refusal_is_empty_and_strong_models_use_fallbacks():
    api = Recorder(NS(stop_reason="refusal", content=[], usage=NS(input_tokens=10, output_tokens=0)))
    r = claude("claude-opus-5-5", client=NS(beta=NS(messages=api)))("q")
    assert r.text == "" and api.kwargs["fallbacks"] == "default"


def test_claude_unknown_model_needs_prices():
    with pytest.raises(ValueError):
        claude("claude-new-model")
    api = Recorder(NS(stop_reason="end_turn", content=[NS(type="text", text="x")], usage=NS(input_tokens=1e6, output_tokens=0)))
    assert claude("claude-new-model", prices=(3, 15), client=NS(messages=api))("q").cost_usd == 3


def test_openai_cost_text_and_effort():
    api = Recorder(NS(output_text="hello", usage=NS(input_tokens=2000, output_tokens=500)))
    r = openai_model("some-model", price_in=1.0, price_out=4.0, effort="low", client=NS(responses=api))("q")
    assert r.text == "hello" and abs(r.cost_usd - (2000 * 1 + 500 * 4) / 1e6) < 1e-15
    assert api.kwargs["reasoning"] == {"effort": "low"} and api.kwargs["input"] == "q"


def test_gemini_counts_thinking_as_output():
    pytest.importorskip("google.genai")
    usage = NS(prompt_token_count=1000, candidates_token_count=100, thoughts_token_count=300)
    api = Recorder(NS(text=None, usage_metadata=usage))
    r = gemini_model("some-model", price_in=0.5, price_out=2.0, thinking_level="low", client=NS(models=api))("q")
    assert r.text == "" and abs(r.cost_usd - (1000 * 0.5 + 400 * 2.0) / 1e6) < 1e-15
    assert api.kwargs["config"].thinking_config.thinking_level.name == "LOW"
