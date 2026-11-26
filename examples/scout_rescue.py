"""Scout & Rescue: a cheap model tries first; a strong model runs only when
a check in code says the cheap result is not usable.

This file has no provider code. A "model" is any function that takes a prompt
and returns a ModelResult, so you can plug in Claude, OpenAI, Gemini, a local
model, or a stub for tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class ModelResult:
    text: str
    cost_usd: float
    model: str


# A model: prompt in, result out.
Model = Callable[[str], ModelResult]

# A check: returns None if the text is usable, or a short reason why it is not.
# Keep checks in plain code - free, instant, and predictable.
Check = Callable[[str], Optional[str]]


@dataclass
class Outcome:
    text: str
    path: str  # "scout" or "rescue"
    cost_usd: float
    model: str
    rejected_because: Optional[str] = None  # why the scout's result failed the check


def handoff_prompt(prompt: str, draft: str, problem: str) -> str:
    """The rescuer's prompt when it is told what the scout tried and why it failed."""
    return (
        f"{prompt}\n\n---\nA first draft of this answer was rejected by an automatic check.\n"
        f"Reason: {problem}\nRejected draft:\n{draft}\n---\n"
        "Write the answer again, fixing that problem. Do not copy mistakes from the draft."
    )


def scout_and_rescue(
    prompt: str, scout: Model, rescue: Model, check: Check, handoff: bool = False
) -> Outcome:
    """Run the cheap scout first; call the strong rescuer only if the check fails.

    handoff=True also gives the rescuer the scout's draft and the reason it was
    rejected. It may help the rescuer, or make it copy the scout's mistakes and
    read more tokens - treat it as a lever and test it before you turn it on.
    """
    first = scout(prompt)
    problem = check(first.text)
    if problem is None:
        return Outcome(first.text, "scout", first.cost_usd, first.model)

    second = rescue(handoff_prompt(prompt, first.text, problem) if handoff else prompt)
    return Outcome(
        text=second.text,
        path="rescue",
        cost_usd=first.cost_usd + second.cost_usd,  # you pay for both attempts
        model=second.model,
        rejected_because=problem,
    )
