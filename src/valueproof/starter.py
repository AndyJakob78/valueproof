"""The file `valueproof init` writes: a test that runs offline straight away, ready to edit."""

STARTER = '''"""My cost test: compare today's setup with a cheaper one on the same requests.

    valueproof compare {name}           # fake models: checks the wiring, no cost
    valueproof compare {name} --live --estimate      # real models, 2 cases: prints the projected bill
    valueproof compare {name} --live --max-spend 5   # real models, stops once $5 is spent

Edit the four parts marked EDIT, from top to bottom.
"""

import time

from valueproof import ModelResult, Run, Score, scout_and_rescue

# EDIT 1 - your test requests: 20-100 real ones from your logs, including the hard ones.
CASES = [
    {{"request": "Where is my order 48213?", "must_mention": "48213"}},
    {{"request": "My order 77120 arrived broken. I want a refund.", "must_mention": "77120"}},
    {{"request": "Charged twice for order 50911, and the invoice name is wrong.", "must_mention": "50911"}},
]


def prompt_for(case: dict) -> str:
    return "Answer this customer briefly and helpfully:\\n\\n" + case["request"]


# EDIT 2 - your checks: plain code that says why a result is unusable (None = usable).
def check(text: str, case: dict):
    if len(text.strip()) < 40:
        return "too short"
    if case["must_mention"] not in text:
        return "does not mention the order number"
    return None


# EDIT 3 - your models. Fake ones first, so the file runs without a key.
def fake(name, cost, good=True):
    def call(prompt):
        order = next((w for w in prompt.split() if w.strip(".,?").isdigit()), "")
        hard = "invoice" in prompt  # the fake cheap model fails the hard request, so you see a rescue
        text = "Sorry!" if (hard and not good) else f"Thanks for your message about order {{order}}. We are on it and will email you today."
        return ModelResult(text, cost, name)
    return call


def models(live: bool):
    if not live:
        return {{"cheap": fake("fake-cheap", 0.0004, good=False), "strong": fake("fake-strong", 0.0100)}}
    # Pick one provider; pip install "valueproof[claude]" (or [openai], [gemini]).
    from valueproof.claude import claude
    return {{"cheap": claude("claude-haiku-5-5"), "strong": claude("claude-opus-5-5", effort="medium")}}
    # from valueproof.openai import openai_model
    # return {{"cheap": openai_model("<cheap model>", price_in=..., price_out=...),
    #          "strong": openai_model("<strong model>", price_in=..., price_out=...)}}
    # from valueproof.gemini import gemini_model
    # return {{"cheap": gemini_model("<cheap model>", price_in=..., price_out=...),
    #          "strong": gemini_model("<strong model>", price_in=..., price_out=...)}}


# EDIT 4 - the setups to compare. The first one is the baseline (what you run today).
def build(live: bool, args: list) -> dict:
    m = models(live)

    def today(case) -> Run:
        t0 = time.time()
        r = m["strong"](prompt_for(case))
        return Run(r.text, r.cost_usd, time.time() - t0, "single", check(r.text, case))

    def scout_rescue(case) -> Run:
        t0 = time.time()
        out = scout_and_rescue(prompt_for(case), m["cheap"], m["strong"], lambda t: check(t, case))
        return Run(out.text, out.cost_usd, time.time() - t0, out.path, check(out.text, case), out.rejected_because)

    return {{
        "cases": CASES,
        "setups": {{"today (strong model)": today, "Scout & Rescue": scout_rescue}},
        # Optional blind review: judge(case, text) -> Score. Use a person, or a strong model
        # with a fixed rubric. Leave it out and the table shows cost, speed and checks only.
        "judge": None,
        "describe": lambda case: case["request"],
    }}
'''
