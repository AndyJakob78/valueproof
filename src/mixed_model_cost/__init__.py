"""AI Mixed Model Cost Optimization: let cheap and strong models work together,
and measure what each change does to cost and quality before it ships.

    from mixed_model_cost import scout_and_rescue, ModelResult
    from mixed_model_cost.claude import claude      # needs the [claude] extra

Any provider works: a model is just a function `prompt -> ModelResult`.
"""

from .lever_runner import Report, Run, Score, print_table, run_levers, save
from .pipeline import RunResult, Step, StepLog, run_pipeline
from .scout_rescue import Check, Model, ModelResult, Outcome, handoff_prompt, scout_and_rescue

__version__ = "0.1.0"

__all__ = [
    "Check", "Model", "ModelResult", "Outcome", "handoff_prompt", "scout_and_rescue",
    "RunResult", "Step", "StepLog", "run_pipeline",
    "Report", "Run", "Score", "print_table", "run_levers", "save",
]
