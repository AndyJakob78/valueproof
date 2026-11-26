"""Split one AI job into steps and give each step the cheapest model that
does it well. A step either uses one model, or Scout & Rescue.

Typical split:
    read / extract   -> small, cheap model
    analyze / draft  -> Scout & Rescue (cheap first, strong only when needed)
    review           -> code checks where possible, a model only where needed
    aggregate        -> mid-size model, once per batch instead of once per item
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from scout_rescue import Model, Outcome, scout_and_rescue


@dataclass
class Step:
    name: str
    build_prompt: Callable[[dict], str]  # turns the data so far into a prompt
    model: Optional[Model] = None  # single model, or ...
    scout: Optional[Model] = None  # ... Scout & Rescue
    rescue: Optional[Model] = None
    # check(text, data) -> None if usable, else a reason. Gets the data so far,
    # so it can compare against earlier steps (e.g. "mentions the order id?").
    check: Optional[Callable[[str, dict], Optional[str]]] = None


@dataclass
class StepLog:
    step: str
    path: str
    model: str
    cost_usd: float
    note: str = ""


@dataclass
class RunResult:
    data: dict
    log: list[StepLog] = field(default_factory=list)

    @property
    def cost_usd(self) -> float:
        return sum(entry.cost_usd for entry in self.log)


def run_step(step: Step, data: dict) -> Outcome:
    prompt = step.build_prompt(data)
    if step.model is not None:
        result = step.model(prompt)
        return Outcome(result.text, "single", result.cost_usd, result.model)
    if step.scout and step.rescue and step.check:
        return scout_and_rescue(prompt, step.scout, step.rescue, lambda text: step.check(text, data))
    raise ValueError(f"Step {step.name!r} needs either `model` or `scout` + `rescue` + `check`.")


def run_pipeline(steps: list[Step], data: dict) -> RunResult:
    """Run the steps in order. Each step's output is stored under its name."""
    run = RunResult(data=dict(data))
    for step in steps:
        outcome = run_step(step, run.data)
        run.data[step.name] = outcome.text
        run.log.append(
            StepLog(step.name, outcome.path, outcome.model, outcome.cost_usd,
                    f"scout rejected: {outcome.rejected_because}" if outcome.rejected_because else "")
        )
    return run
